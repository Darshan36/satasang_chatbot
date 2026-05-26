"""Derive a topic taxonomy from the actual story content in ONE generation call.

The free-tier generate_content quota is tiny, so we send a representative SAMPLE
of stories (spread across the corpus, truncated) in a single request and ask the
model to produce a balanced 25-40 topic taxonomy directly.

Output: topics.json  (REVIEW/EDIT this before building embeddings/tags)

Run:  python build_taxonomy.py
"""
import datetime
import json

from clean_text import clean_content
from gemini_api import generate_json

SRC = "granular_stories.json"
TOPICS_OUT = "topics.json"

SAMPLE_SIZE = 80     # stories shown to the model
SNIPPET_CHARS = 320  # per-story truncation

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topics": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "description": {"type": "STRING"},
                    "synonyms": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["id", "name", "description", "synonyms"],
            },
        }
    },
    "required": ["topics"],
}


def sample(stories):
    """Evenly spread sample across the corpus."""
    if len(stories) <= SAMPLE_SIZE:
        return stories
    step = len(stories) / SAMPLE_SIZE
    return [stories[int(i * step)] for i in range(SAMPLE_SIZE)]


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    stories = [clean_content(s["content"]) for s in data]
    stories = [s for s in stories if len(s) > 20]
    print(f"Loaded {len(stories)} cleaned stories; sampling {min(SAMPLE_SIZE, len(stories))}.")

    snippets = [s[:SNIPPET_CHARS] for s in sample(stories)]
    joined = "\n\n".join(f"{i+1}) {s}" for i, s in enumerate(snippets))

    prompt = (
        "Below is a representative sample of short spiritual stories (\"prasangs\"). "
        "The text mixes Gujarati, Hindi and English.\n\n"
        "Design a CLEAN, NON-OVERLAPPING taxonomy of between 25 and 40 topics that a young "
        "person browsing these stories for guidance would actually search. BALANCE coverage: "
        "do NOT create one giant 'Faith/Spiritual' catch-all — split broad ideas into concrete, "
        "searchable topics (e.g. Exam Stress & Studies, Anger Management, Waking Up Early, "
        "Friendship, Money & Finances, Respecting Parents, Overcoming Fear, Focus & Discipline, "
        "Devotion & Prayer, Seva & Service, Health & Diet, Dealing with Failure, etc.).\n\n"
        "For each topic give: a kebab-case id, a canonical display name, a one-sentence "
        "description, and synonyms (English + Gujarati + Hindi search keywords).\n\n"
        "Output JSON only.\n\nSTORIES:\n" + joined
    )

    result = generate_json(prompt, SCHEMA, temperature=0.2)
    topics = result.get("topics", [])
    out = {
        "version": datetime.date.today().isoformat(),
        "generated_with": "gemini-2.5-flash-lite",
        "topics": topics,
    }
    with open(TOPICS_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(topics)} topics -> {TOPICS_OUT}\n")
    for t in topics:
        print(f"  - {t['name']}: {t['description']}")


if __name__ == "__main__":
    main()
