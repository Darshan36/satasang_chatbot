"""Akshar Sarjan Prasang Explorer — semantic search backend.

Two search modes on /ask:
  * Browse (chip click): {"tag": "<topic name>"}  -> in-memory filter, no API call.
  * Search (free text):  {"query": "..."}         -> embed query, rank stories by
                                                      cosine similarity (semantic).

The story embeddings (embeddings.npy) and tags (recategorized_stories.json) are
prebuilt offline; see HANDOFF.md for the pipeline.
"""
import html
import io
import json
import os
import traceback

import numpy as np
import requests
from flask import Flask, jsonify, render_template, request

import config
from gemini_api import batch_embed
from groq_api import chat_json

app = Flask(__name__)

STORIES_FILE = "recategorized_stories.json"
EMB_FILE = "embeddings.npy"
TOPIC_EMB_FILE = "topic_embeddings.npy"
META_FILE = "embeddings_meta.json"
TOPICS_FILE = "topics.json"
GLOSSARY_FILE = "glossary.json"

# Search tuning.
TOP_K = 8
FETCH_K = 20
SIM_THRESHOLD = 0.55   # below this a result is "weak"; we still show a few as fallback
TAG_BOOST = 0.05       # nudge stories whose tags match a topic named in the query

# Data source: if S3_BUCKET is set, data files are pulled from a private
# S3-compatible bucket (e.g. Backblaze B2) at startup, so they need not live in
# the repo — which lets the repo be public. Otherwise local files are used
# (local dev / data committed to the repo). Env vars: S3_BUCKET, S3_ENDPOINT_URL,
# S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_REGION.
S3_BUCKET = os.environ.get("S3_BUCKET", "")
_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        from botocore.config import Config
        _s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT_URL") or None,
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"),
            region_name=os.environ.get("S3_REGION") or None,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


def _data_bytes(name):
    if S3_BUCKET:
        return _s3().get_object(Bucket=S3_BUCKET, Key=name)["Body"].read()
    with open(name, "rb") as f:
        return f.read()


def _data_json(name):
    return json.loads(_data_bytes(name).decode("utf-8"))


def _data_npy(name):
    return np.load(io.BytesIO(_data_bytes(name)))


def _opt_json(name, default):
    try:
        return _data_json(name)
    except Exception:
        return default


def _opt_npy(name):
    try:
        return _data_npy(name)
    except Exception:
        return None


def _load():
    stories = _data_json(STORIES_FILE)
    emb = _data_npy(EMB_FILE)
    topics = _data_json(TOPICS_FILE)["topics"]
    topic_emb = _opt_npy(TOPIC_EMB_FILE)
    meta = _opt_json(META_FILE, {})

    if emb.shape[0] != len(stories):
        raise RuntimeError(
            f"Index/story mismatch: embeddings has {emb.shape[0]} rows but "
            f"{STORIES_FILE} has {len(stories)}. Rebuild with build_embeddings.py + recategorize_groq.py."
        )
    if meta and meta.get("dimensions") not in (None, emb.shape[1]):
        raise RuntimeError("embeddings dimension does not match embeddings_meta.json.")
    src = f"s3://{S3_BUCKET}" if S3_BUCKET else "local files"
    print(f"Loaded {len(stories)} stories, embeddings {emb.shape}, {len(topics)} topics (from {src}).")
    return stories, emb, topics, topic_emb


STORIES, EMB, TOPICS, TOPIC_EMB = _load()
TOPIC_NAMES = [t["name"] for t in TOPICS]
TOPIC_IDX = {t["name"]: i for i, t in enumerate(TOPICS)}

# Sources present in the data, for the UI filter (value -> display label).
SOURCE_LABELS = {
    "sabha": "Akshar Sarjan Sabha",
    "amrutpathey": "Amrut Pathey",
    "aksharjatan": "Akshar Jatan",
}
SOURCES = [
    {"value": v, "label": SOURCE_LABELS.get(v, v.title())}
    for v in sorted({s.get("source", "sabha") for s in STORIES})
]

GLOSSARY = _opt_json(GLOSSARY_FILE, {"terms": []}).get("terms", [])


def source_ok(story, source):
    """True if the story matches the requested source ('' / 'all' = any)."""
    return not source or source == "all" or story.get("source", "sabha") == source


def glossary_expansions(query):
    """Return curated expansions for any glossary term found in the query."""
    q = query.lower()
    return [e["expansion"] for e in GLOSSARY
            if any(a.lower() in q for a in e.get("aliases", []))]


def embed_query(text):
    vec = np.array(batch_embed([text], "RETRIEVAL_QUERY")[0], dtype=np.float32)
    n = np.linalg.norm(vec)
    return vec / n if n else vec


def llm_expand(query):
    """Ask Groq to enrich a query with Gujarati-script terms + meaning. Used only
    as a rescue for weak, non-glossary queries. Returns the raw query on failure."""
    try:
        prompt = (
            "You expand search queries for a corpus of Swaminarayan satsang spiritual "
            "stories (\"prasangs\") written in mixed Gujarati, Hindi and English (Gujarati "
            "script plus transliteration).\n\n"
            "Given the user's query, return JSON {\"expanded\": \"...\"} where 'expanded' is a "
            "single enriched search string to retrieve relevant stories. Capture the "
            "DEVOTIONAL/spiritual MEANING of the user's term; do not confuse similar-sounding "
            "words. Include the key terms in Gujarati script, common transliterations, and a "
            "brief English description. Do NOT add unrelated topics. Keep under 60 words.\n\n"
            f"Query: \"{query}\""
        )
        out = chat_json(prompt, max_retries=2, timeout=20)
        exp = (out.get("expanded") or "").strip() if isinstance(out, dict) else ""
        return f"{query}. {exp}" if exp else query
    except Exception as e:
        print(f"query expansion unavailable, using raw query: {e}")
        return query


def quick_tag_match(query):
    """Cheap substring match of the query against topic names/synonyms."""
    q = query.lower()
    for t in TOPICS:
        terms = [t["name"]] + t.get("synonyms", [])
        if any(term and term.lower() in q for term in terms):
            return t["name"]
    return None


def build_card(story, sim=None):
    topic = html.escape(story.get("session_topic") or "Prasang")
    if topic.lower() in ("", "general/spiritual"):
        topic = "Prasang"
    chips = "".join(
        f"<span class='topic-chip'>{html.escape(t)}</span>" for t in story.get("topics", [])
    )
    badge = f"<span class='match'>{round(sim * 100)}% match</span>" if sim is not None else ""
    body = html.escape(story["content"])
    return (
        f"<div class='card-head'><span class='sabha'>{topic}</span>{badge}</div>"
        f"<div class='chips'>{chips}</div>"
        f"<div class='body'>{body}</div>"
    )


@app.route("/favicon.ico")
def favicon():
    return ("", 204)  # no favicon; avoids a noisy 404 in the browser console


@app.route("/")
def index():
    return render_template("index.html", topics=TOPICS, sources=SOURCES)


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json(silent=True) or {}
        tag = (data.get("tag") or "").strip()
        query = (data.get("query") or "").strip()
        source = (data.get("source") or "").strip()  # '' / 'all' = every source

        # --- Browse mode: filter by topic tag, no API call ---
        if tag:
            idxs = [i for i, s in enumerate(STORIES)
                    if tag in s.get("topics", []) and source_ok(s, source)]
            if TOPIC_EMB is not None and tag in TOPIC_IDX:
                tvec = TOPIC_EMB[TOPIC_IDX[tag]]
                idxs.sort(key=lambda i: -float(EMB[i] @ tvec))
            cards = [build_card(STORIES[i]) for i in idxs]
            return jsonify({"mode": "browse", "label": tag, "count": len(cards), "stories": cards})

        # --- Search mode: semantic ranking ---
        if not query:
            return jsonify({"error": "No query or tag provided"}), 400

        # Curated glossary terms (e.g. "kartaharta") get an authoritative expansion;
        # otherwise embed the raw query and only fall back to LLM expansion if the
        # best match is weak (keeps clear queries crisp, rescues niche ones).
        curated = glossary_expansions(query)
        if curated:
            qvec = embed_query(query + ". " + " ".join(curated))
            sims = EMB @ qvec
        else:
            qvec = embed_query(query)
            sims = EMB @ qvec
            if float(sims.max()) < SIM_THRESHOLD:
                enriched = llm_expand(query)
                if enriched != query:
                    s2 = EMB @ embed_query(enriched)
                    if float(s2.max()) > float(sims.max()):
                        sims = s2
        order = [i for i in np.argsort(-sims) if source_ok(STORIES[i], source)][:FETCH_K]

        matched = quick_tag_match(query)
        scored = []
        for i in order:
            boost = TAG_BOOST if matched and matched in STORIES[i].get("topics", []) else 0.0
            scored.append((int(i), float(sims[i]), float(sims[i]) + boost))
        scored.sort(key=lambda r: -r[2])

        strong = [r for r in scored if r[1] >= SIM_THRESHOLD][:TOP_K]
        final = strong if strong else scored[:3]  # never return an empty page
        cards = [build_card(STORIES[i], sim) for i, sim, _ in final]
        return jsonify({
            "mode": "search",
            "label": query,
            "matched_topic": matched,
            "low_confidence": not strong,
            "count": len(cards),
            "stories": cards,
        })
    except Exception as e:
        print(f"Internal Server Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Local dev entrypoint. In production Render runs `gunicorn app:app`, so this
    # block is not used there. Port comes from the host ($PORT); debug is opt-in.
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"Starting Akshar Sarjan Web Server on port {port}...")
    app.run(debug=debug, port=port, host="0.0.0.0")
