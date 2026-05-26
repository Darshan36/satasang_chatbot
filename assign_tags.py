"""Categorize stories by embedding similarity (no generation calls).

For every story we compute cosine similarity to every topic (both already
L2-normalized, so cosine == dot product) and tag the story with the topics it
is closest to. No forced default: a story with no sufficiently-similar topic is
left with an empty tag list.

Inputs : stories_base.json, embeddings.npy, topics.json, topic_embeddings.npy
Output : recategorized_stories.json  [{session_topic, content, topics:[...]}]

Run:  python assign_tags.py            (uses tuned thresholds below)
      python assign_tags.py --stats    (just print the similarity distribution)
"""
import json
import sys

import numpy as np

STORIES = "stories_base.json"
EMB = "embeddings.npy"
TOPICS = "topics.json"
TOPIC_EMB = "topic_embeddings.npy"
OUT = "recategorized_stories.json"

# Tunable. A topic is attached if its similarity clears TAG_THRESHOLD; the single
# best topic is attached if it clears KEEP_FLOOR (so most stories get >=1 tag),
# capped at MAX_TAGS topics per story.
TAG_THRESHOLD = 0.62
KEEP_FLOOR = 0.55
MAX_TAGS = 4


def load():
    stories = json.load(open(STORIES, encoding="utf-8"))
    topics = json.load(open(TOPICS, encoding="utf-8"))["topics"]
    semb = np.load(EMB)
    temb = np.load(TOPIC_EMB)
    return stories, topics, semb, temb


def main():
    stories, topics, semb, temb = load()
    names = [t["name"] for t in topics]
    sims = semb @ temb.T  # (N, T)

    if "--stats" in sys.argv:
        best = sims.max(axis=1)
        print(f"stories={len(stories)} topics={len(topics)}")
        print("best-topic similarity percentiles:")
        for p in (10, 25, 50, 75, 90, 99):
            print(f"  p{p}: {np.percentile(best, p):.3f}")
        for thr in (0.50, 0.55, 0.60, 0.62, 0.65, 0.70):
            tagged = int((sims.max(axis=1) >= thr).sum())
            avg = float((sims >= thr).sum(axis=1).mean())
            print(f"  thr {thr:.2f}: stories with >=1 tag = {tagged}/{len(stories)}, avg tags/story = {avg:.2f}")
        return

    result, counts, n_empty = [], {n: 0 for n in names}, 0
    for i, s in enumerate(stories):
        row = sims[i]
        order = np.argsort(-row)
        chosen = [names[j] for j in order if row[j] >= TAG_THRESHOLD][:MAX_TAGS]
        if not chosen and row[order[0]] >= KEEP_FLOOR:
            chosen = [names[order[0]]]
        for c in chosen:
            counts[c] += 1
        if not chosen:
            n_empty += 1
        result.append({
            "session_topic": s["session_topic"],
            "content": s["content"],
            "topics": chosen,
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(result)} stories -> {OUT}")
    print(f"Stories with no tag: {n_empty}")
    print("Per-topic counts (desc):")
    for name, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {c:4d}  {name}")


if __name__ == "__main__":
    main()
