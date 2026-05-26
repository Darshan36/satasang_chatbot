"""Helper for high-quality (Claude-authored) re-tagging of book sources.

Workflow:
  python booktag.py topics                  # print the 45-topic taxonomy
  python booktag.py dump <source> <start> <count>   # print prasangs to tag
  -> Claude writes _bt/<source>_<start>.json = [[topics...], ...] (one list per prasang, in order)
  python booktag.py apply                    # apply all _bt/*.json to recategorized_stories.json
  python booktag.py check                    # show counts staged vs needed

Tag lists are validated against topics.json; order must match the dump order.
"""
import glob
import json
import os
import sys

DATA = "recategorized_stories.json"
TOPICS = "topics.json"
BT = "_bt"
SOURCES = ["amrutpathey", "samarthnisadhuta", "aksharjatan"]


def load():
    return json.load(open(DATA, encoding="utf-8"))


def src_indices(d, source):
    return [i for i, r in enumerate(d) if r.get("source") == source]


def cmd_topics():
    for t in json.load(open(TOPICS, encoding="utf-8"))["topics"]:
        print(f"- {t['name']}: {t['description']}")


def cmd_dump(source, start, count, maxchars=650):
    d = load()
    idx = src_indices(d, source)
    for k, gi in enumerate(idx[start:start + count]):
        c = " ".join(d[gi]["content"].split())[:maxchars]
        print(f"### {start + k}")
        print(c)
    print(f"--- {source}: showing {start}..{start + min(count, len(idx) - start)} of {len(idx)} ---")


def _batch_files(source):
    files = glob.glob(os.path.join(BT, f"{source}_*.json"))
    return sorted(files, key=lambda p: int(os.path.basename(p).rsplit("_", 1)[1].split(".")[0]))


def cmd_check():
    d = load()
    for s in SOURCES:
        staged = sum(len(json.load(open(f, encoding="utf-8"))) for f in _batch_files(s))
        print(f"{s}: {staged} tag-lists staged / {len(src_indices(d, s))} prasangs")


def cmd_apply():
    d = load()
    valid = {t["name"] for t in json.load(open(TOPICS, encoding="utf-8"))["topics"]}
    total = 0
    for source in SOURCES:
        tags = []
        for f in _batch_files(source):
            tags += json.load(open(f, encoding="utf-8"))
        idx = src_indices(d, source)
        if not tags:
            continue
        if len(tags) != len(idx):
            print(f"WARN {source}: {len(tags)} tag-lists vs {len(idx)} prasangs — SKIPPED")
            continue
        bad = set()
        for gi, tg in zip(idx, tags):
            chosen = [t for t in tg if t in valid]
            bad |= {t for t in tg if t not in valid}
            d[gi]["topics"] = chosen
            total += 1
        if bad:
            print(f"  {source}: ignored unknown topics: {sorted(bad)}")
    json.dump(d, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Applied Claude tags to {total} prasangs -> {DATA}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "topics":
        cmd_topics()
    elif cmd == "dump":
        cmd_dump(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "apply":
        cmd_apply()
    else:
        cmd_check()
