"""Build the embedding index for stories and topics.

Produces (all index-aligned to stories_base.json):
  stories_base.json     canonical cleaned story list [{session_topic, content, hash}]
  embeddings.npy        (N, 768) float32, L2-normalized story vectors
  topic_embeddings.npy  (T, 768) float32, L2-normalized topic vectors
  embeddings_meta.json  model/dim/counts + per-row hashes + topic order

Re-running reuses vectors for unchanged content (hash match), so it only embeds
new/changed stories. Embeddings use a separate, generous free-tier quota.

Run:  python build_embeddings.py
"""
import json
import os
import time

import numpy as np

import config
from clean_text import clean_content, content_hash
from gemini_api import batch_embed

SRC = "granular_stories.json"
TOPICS = "topics.json"
STORIES_OUT = "stories_base.json"
EMB_OUT = "embeddings.npy"
TOPIC_EMB_OUT = "topic_embeddings.npy"
META_OUT = "embeddings_meta.json"
CACHE = "_emb_cache.npz"   # persistent hash -> raw vector cache (survives crashes)

BATCH = 10           # small batch so one request never exceeds the per-minute token budget
MIN_LEN = 20         # drop trivially short fragments
MAX_CHARS = 3000     # cap per item (keeps batch tokens well under the limit)


def l2_normalize(mat):
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (mat / norms).astype(np.float32)


def build_stories():
    """Canonical, de-duplicated, cleaned story list (defines row order)."""
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    out, seen = [], set()
    for s in data:
        content = clean_content(s.get("content", ""))
        if len(content) < MIN_LEN:
            continue
        h = content_hash(content)
        if h in seen:
            continue
        seen.add(h)
        out.append({
            "session_topic": (s.get("session_topic") or "").strip(),
            "content": content,
            "source": s.get("source") or "sabha",
            "hash": h,
        })
    with open(STORIES_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def load_cache():
    """Return {hash: raw_vector} persisted from previous (even partial) runs."""
    if not os.path.exists(CACHE):
        return {}
    try:
        z = np.load(CACHE, allow_pickle=True)
        hashes, vecs = z["hashes"], z["vecs"]
        if vecs.shape[1] != config.EMBED_DIM:
            return {}
        return {str(h): vecs[i] for i, h in enumerate(hashes)}
    except Exception:
        return {}


def save_cache(cache):
    hashes = np.array(list(cache.keys()), dtype=object)
    vecs = np.array(list(cache.values()), dtype=np.float32)
    np.savez(CACHE, hashes=hashes, vecs=vecs)


def embed_into_cache(items, cache):
    """Embed (hash, text) items not already cached, saving after each batch."""
    todo = [(h, t) for h, t in items if h not in cache]
    print(f"  {len(todo)} to embed, {len(items) - len(todo)} cached")
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        vecs = batch_embed([t[:MAX_CHARS] for _, t in chunk], "RETRIEVAL_DOCUMENT")
        for (h, _), v in zip(chunk, vecs):
            cache[h] = np.array(v, dtype=np.float32)
        save_cache(cache)  # persist progress immediately
        print(f"    embedded {min(i + BATCH, len(todo))}/{len(todo)} (saved)")
        time.sleep(3.0)  # proactively pace under the per-minute token budget


def main():
    print("Building canonical story list...")
    stories = build_stories()
    print(f"  {len(stories)} unique cleaned stories -> {STORIES_OUT}")

    cache = load_cache()
    print(f"Embedding stories (cache has {len(cache)} vectors)...")
    embed_into_cache([(s["hash"], s["content"]) for s in stories], cache)

    mat = l2_normalize(np.array([cache[s["hash"]] for s in stories], dtype=np.float32))
    np.save(EMB_OUT, mat)
    print(f"  saved {EMB_OUT} shape {mat.shape}")

    # Topics: embed name + description + synonyms as a single query-style string.
    topics = json.load(open(TOPICS, encoding="utf-8"))["topics"]
    topic_texts = [
        f"{t['name']}. {t.get('description','')} {' '.join(t.get('synonyms', []))}"
        for t in topics
    ]
    print(f"Embedding {len(topics)} topics...")
    tvecs = batch_embed([t[:MAX_CHARS] for t in topic_texts], "RETRIEVAL_QUERY")
    tmat = l2_normalize(np.array(tvecs, dtype=np.float32))
    np.save(TOPIC_EMB_OUT, tmat)
    print(f"  saved {TOPIC_EMB_OUT} shape {tmat.shape}")

    meta = {
        "model": config.EMBED_MODEL,
        "dimensions": config.EMBED_DIM,
        "task_type_document": "RETRIEVAL_DOCUMENT",
        "task_type_query": "RETRIEVAL_QUERY",
        "normalized": True,
        "count": len(stories),
        "topic_count": len(topics),
        "topic_names": [t["name"] for t in topics],
        "items": [
            {"idx": i, "session_topic": s["session_topic"], "hash": s["hash"]}
            for i, s in enumerate(stories)
        ],
    }
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  saved {META_OUT}")
    print("Done.")


if __name__ == "__main__":
    main()
