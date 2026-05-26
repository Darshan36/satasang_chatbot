"""One-command helper to add a new book/source of prasangs.

Parses a text file of verbatim prasangs (the `=== PRASANG ===` / `SESSION:`
format produced by the NotebookLM extraction prompt), adds them to the pipeline
under a given source name, then embeds and tags ONLY the new stories — existing
stories and their tags are left untouched, and the 45 keywords are unchanged.

Usage:
  python add_stories.py <txt_file> <source> ["Display Label"]
  e.g.  python add_stories.py aksharjatan.txt aksharjatan "Akshar Jatan"

After it finishes:
  1) python upload_data.py        (push updated data to the private bucket)
  2) restart / redeploy Render    (so it re-downloads the new data)
A brand-new source automatically appears in the UI filter; add a nicer label to
SOURCE_LABELS in app.py if you want (optional).
"""
import json
import re
import sys

import build_embeddings
import assign_tags

GRANULAR = "granular_stories.json"


def parse(path, label):
    txt = open(path, encoding="utf-8").read()
    blocks = [b.strip() for b in txt.split("=== PRASANG ===") if b.strip()]
    records = []
    for b in blocks:
        body = re.sub(r"^SESSION:\s*", "", b).strip()
        body = re.sub(r"^[૦-૯0-9]+\s*[:：]\s*", "", body).strip()  # drop leading "<num> :"
        if len(body) < 20:
            continue
        records.append({"session_topic": label, "content": body})
    return records


def main():
    if len(sys.argv) < 3:
        print('usage: python add_stories.py <txt_file> <source> ["Display Label"]')
        return
    path, source = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else source.replace("_", " ").title()

    records = parse(path, label)
    for r in records:
        r["source"] = source
    if not records:
        print("No prasangs found (expected '=== PRASANG ===' blocks).")
        return

    data = json.load(open(GRANULAR, encoding="utf-8"))
    data = [s for s in data if s.get("source") != source]   # idempotent re-add
    data.extend(records)
    json.dump(data, open(GRANULAR, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Parsed {len(records)} prasangs for source='{source}'; granular now {len(data)} entries.\n")

    print("== Embedding new stories (Gemini, incremental) ==")
    build_embeddings.main()
    print("\n== Tagging new stories (embedding similarity, existing tags preserved) ==")
    assign_tags.main()
    print("\nNext: python upload_data.py   then redeploy/restart Render.")


if __name__ == "__main__":
    main()
