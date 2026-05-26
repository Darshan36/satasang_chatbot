import json
import re

def split_into_prasangs(content, topic_name):
    # Split by Vakta and P1, P2, 1), 2) markers
    sections = re.split(r'(?i)(Vakta\s*\d+|Host\s*:?)', content)
    
    individual_stories = []
    
    for section in sections:
        if not section.strip() or len(section) < 10:
            continue
            
        # Split by P1, P2 or 1), 2)
        p_splits = re.split(r'\n\s*(?:P\d+|[1-9]\d?[\)\.])', section)

        for p in p_splits:
            # Further split bundled "Myth N:" sections (keeps each myth its own story)
            for piece in re.split(r'(?im)(?=^\s*Myth\s*\d+\s*:)', p):
                p_clean = piece.strip()
                if len(p_clean) > 30: # Only keep significant content
                    individual_stories.append({
                        "session_topic": topic_name,
                        "content": p_clean
                    })
                
    # Fallback if no splitting happened
    if not individual_stories and len(content) > 50:
        individual_stories.append({
            "session_topic": topic_name,
            "content": content.strip()
        })
        
    return individual_stories

def process():
    with open('full_prasangs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    all_stories = []
    for entry in data:
        stories = split_into_prasangs(entry['content'], entry['topic'])
        all_stories.extend(stories)
        
    with open('granular_stories.json', 'w', encoding='utf-8') as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)
        
    print(f"Extracted {len(all_stories)} granular stories.")

if __name__ == "__main__":
    process()
