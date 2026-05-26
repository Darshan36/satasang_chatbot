"""Categorize every story against topics.json using Groq (high RPD, JSON mode).

Reads the canonical stories_base.json so the output stays index-aligned with the
embeddings. Tags are validated against the taxonomy; empty is allowed (NO forced
default). Resumes by content hash and saves after every batch.

Inputs : stories_base.json, topics.json
Output : recategorized_stories.json  [{session_topic, content, topics:[...]}]

Run:  python recategorize_groq.py
"""
import json
import os
import time

import config
from groq_api import chat_json

STORIES = "stories_base.json"
TOPICS = "topics.json"
OUT = "recategorized_stories.json"

# Each Groq request must stay under the 12000 tokens/minute cap. We budget by
# characters (~4 chars/token) and also truncate long stories — the opening of a
# prasang is plenty to tag it.
TAG_SNIPPET = 1200      # chars of each story shown to the model
CHAR_BUDGET = 12000     # total story chars per request (~3k tokens; + topics, under 8k TPM)
MAX_PER_BATCH = 12
PAUSE = 2.0
MAX_TAGS = 3


def build_prompt(topics, chunk):
    topic_lines = "\n".join(f"- {t['name']}: {t['description']}" for t in topics)
    story_lines = "\n\n".join(
        f"[{i+1}]\n{s['content'][:TAG_SNIPPET]}" for i, s in enumerate(chunk)
    )
    return (
        "You are tagging short spiritual stories (\"prasangs\"). The text mixes Gujarati, "
        "Hindi and English.\n\n"
        "Allowed topics (use the EXACT names):\n" + topic_lines + "\n\n"
        "For each numbered story, choose the topics (up to 3) that genuinely capture its "
        "lesson. It is correct to return an empty list if none truly fit — there is NO "
        "default, do not guess a 'closest' topic.\n\n"
        "Respond with JSON only, of the form:\n"
        '{"results": [{"n": 1, "topics": ["Exact Topic Name", ...]}, ...]}\n'
        "Include one object per story, with n matching the [number].\n\n"
        "STORIES:\n" + story_lines
    )


def main():
    stories = json.load(open(STORIES, encoding="utf-8"))
    topics = json.load(open(TOPICS, encoding="utf-8"))["topics"]
    valid = {t["name"] for t in topics}

    # Resume: a row counts as done only if its topics is a list (null = pending).
    done = {}
    if os.path.exists(OUT):
        for r in json.load(open(OUT, encoding="utf-8")):
            if isinstance(r.get("topics"), list):
                done[r.get("hash")] = r["topics"]

    results = []
    pending = []  # (global_index, story) still needing a tag

    for s in stories:
        if s["hash"] in done:
            results.append({**s, "topics": done[s["hash"]]})
        else:
            results.append({**s, "topics": None})  # placeholder
            pending.append(s)

    print(f"{len(stories)} stories; {len(pending)} need tagging.")

    # Index lookup from hash -> position in results.
    pos = {s["hash"]: i for i, s in enumerate(stories)}

    # Group pending stories into token-budgeted batches.
    batches, cur, cur_chars = [], [], 0
    for s in pending:
        c = min(len(s["content"]), TAG_SNIPPET)
        if cur and (cur_chars + c > CHAR_BUDGET or len(cur) >= MAX_PER_BATCH):
            batches.append(cur)
            cur, cur_chars = [], 0
        cur.append(s)
        cur_chars += c
    if cur:
        batches.append(cur)

    tagged = 0
    for chunk in batches:
        out = chat_json(build_prompt(topics, chunk))
        rows = out.get("results", []) if isinstance(out, dict) else []
        by_n = {int(r.get("n", -1)): r.get("topics", []) for r in rows if isinstance(r, dict)}
        for i, s in enumerate(chunk):
            raw = by_n.get(i + 1, [])
            tags = [t for t in raw if t in valid][:MAX_TAGS]
            results[pos[s["hash"]]]["topics"] = tags
        tagged += len(chunk)
        # Persist progress as-is: undecided rows stay null so resume is correct.
        json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  tagged {tagged}/{len(pending)} (saved)")
        time.sleep(PAUSE)

    # Final write: normalize any leftover null (shouldn't be any) to empty list.
    for r in results:
        if r["topics"] is None:
            r["topics"] = []
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Final stats.
    counts = {}
    empty = 0
    for r in results:
        ts = r["topics"] or []
        if not ts:
            empty += 1
        for t in ts:
            counts[t] = counts.get(t, 0) + 1
    print(f"\nDone -> {OUT}.  Stories with no tag: {empty}")
    for name, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c:4d}  {name}")


if __name__ == "__main__":
    main()
