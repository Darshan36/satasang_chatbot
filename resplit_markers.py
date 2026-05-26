"""Split bundled granular entries on clear item markers — deterministic, no API.

Splits a chunk where independent items begin: ASCII or Gujarati numbered lines
(1) 2.  / ૧. ૨)), "Myth N:", "પ્રશ્ન N" / "Question N". To avoid fragmenting a
short list of sub-points that belong to ONE teaching, a split is accepted only
if EVERY resulting piece is substantial (>= MIN_SEG chars). Distinct anecdotes
are long; sub-points are short — so this guard keeps coherent stories intact.

Run:  python resplit_markers.py --dry    (preview only)
      python resplit_markers.py          (apply + back up to granular_stories.preseg.json)
"""
import json
import re
import sys

SRC = "granular_stories.json"
BACKUP = "granular_stories.preseg.json"

MIN_SEG = 150  # each split piece must be at least this many chars to accept a split

# A new item begins at a line that starts with one of these markers.
_SPLIT = re.compile(
    r"(?im)(?=^[ \t]*(?:"
    r"\d{1,2}[\)\.]|"          # 1)  2.
    r"[૦-૯]{1,2}[\)\.]|"       # Gujarati ૧.  ૨)
    r"Myth\s*\d|"
    r"પ્રશ્ન\s*\d|"
    r"Question\s*\d|"
    r"Q\s*\d"
    r")\s)"
)


def split_entry(content):
    parts = [p for p in _SPLIT.split(content) if p.strip()]
    if len(parts) < 2:
        return [content]
    # Attach a leading preamble (title/speaker, not itself a marker) to the first item.
    if not _SPLIT.match(parts[0]) and not re.match(
        r"(?im)^[ \t]*(?:\d{1,2}[\)\.]|[૦-૯]{1,2}[\)\.]|Myth\s*\d|પ્રશ્ન\s*\d|Question\s*\d|Q\s*\d)\s",
        parts[0].strip(),
    ):
        pre = parts.pop(0)
        if parts:
            parts[0] = pre.rstrip() + "\n" + parts[0]
    segs = [p.strip() for p in parts if p.strip()]
    if len(segs) >= 2 and min(len(s) for s in segs) >= MIN_SEG:
        return segs
    return [content]


def main():
    dry = "--dry" in sys.argv
    data = json.load(open(SRC, encoding="utf-8"))
    out, n_split, examples = [], 0, []
    for s in data:
        segs = split_entry(s["content"])
        if len(segs) >= 2:
            n_split += 1
            if len(examples) < 6:
                examples.append((s["session_topic"], segs))
            for seg in segs:
                out.append({"session_topic": s["session_topic"], "content": seg})
        else:
            out.append(s)

    print(f"Entries split: {n_split}.  Total {len(data)} -> {len(out)}.")
    for topic, segs in examples:
        print(f"\n[{topic}] -> {len(segs)} pieces:")
        for seg in segs:
            print("   * " + " ".join(seg.split())[:75])

    if not dry:
        json.dump(data, open(BACKUP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        json.dump(out, open(SRC, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\nApplied. Backup written to {BACKUP}.")
    else:
        print("\n(dry run — no files changed)")


if __name__ == "__main__":
    main()
