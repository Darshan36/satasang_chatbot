"""Parse amruthpathey.txt (verbatim prasangs from the book 'Amrut Pathey') and
add them to granular_stories.json tagged with source='amrutpathey'.

Idempotent: re-running first removes any existing source=='amrutpathey' rows,
then re-adds them, so the count stays correct.

  python add_amrutpathey.py
"""
import json
import re

SRC_TXT = "amruthpathey.txt"
GRANULAR = "granular_stories.json"
SESSION_LABEL = "Amrut Pathey"
SOURCE = "amrutpathey"


def parse():
    txt = open(SRC_TXT, encoding="utf-8").read()
    blocks = [b.strip() for b in txt.split("=== PRASANG ===") if b.strip()]
    records = []
    for b in blocks:
        body = re.sub(r"^SESSION:\s*", "", b).strip()
        # drop the leading "<chapter-number> :" marker, keep the chapter/prasang title + text
        body = re.sub(r"^[૦-૯0-9]+\s*[:：]\s*", "", body).strip()
        if len(body) < 20:
            continue
        records.append({
            "session_topic": SESSION_LABEL,
            "content": body,
            "source": SOURCE,
        })
    return records


def main():
    data = json.load(open(GRANULAR, encoding="utf-8"))
    # remove any previously-added amrutpathey rows (idempotent)
    data = [s for s in data if s.get("source") != SOURCE]
    new = parse()
    data.extend(new)
    json.dump(data, open(GRANULAR, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Added {len(new)} '{SOURCE}' prasangs. granular_stories.json now has {len(data)} entries.")


if __name__ == "__main__":
    main()
