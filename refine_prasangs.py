import json
import re

def split_into_prasangs(content):
    # Regex to find markers like P1, P2, 1), 2), Prasang 1, etc.
    # We look for lines starting with these markers or having them prominently
    
    # Split by common markers
    # 1. P1, P2...
    # 2. 1), 2)...
    # 3. Prasang :, Prasang - ...
    # 4. Vakta headers (to avoid mixing different speakers' stories)
    
    # First, identify sections by Vakta
    vakta_sections = re.split(r'(?i)(Vakta\s*\d+|Host\s*:?)', content)
    
    all_prasangs = []
    
    for section in vakta_sections:
        if not section.strip():
            continue
            
        # Within each section, split by P1/1) etc.
        # This regex looks for (P1) or (1) or (1.) at the start of a line or after a newline
        prasang_splits = re.split(r'\n\s*(?:P\d+|[1-9]\d?[\)\.])', section)
        
        for p in prasang_splits:
            p_clean = p.strip()
            # Basic filters: must be long enough to be a story, shouldn't just be the Vakta name
            if len(p_clean) > 30:
                all_prasangs.append(p_clean)
                
    # If no splits were found (e.g. simple paragraph), return the whole thing if it's not too long
    if not all_prasangs and len(content) > 50:
        all_prasangs.append(content.strip())
        
    return all_prasangs

def process_file():
    with open('full_prasangs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    refined_data = []
    for entry in data:
        prasangs = split_into_prasangs(entry['content'])
        for p in prasangs:
            refined_data.append({
                "topic": entry['topic'],
                "content": p
            })
            
    with open('individual_prasangs.json', 'w', encoding='utf-8') as f:
        json.dump(refined_data, f, ensure_ascii=False, indent=2)
    
    print(f"Split {len(data)} messages into {len(refined_data)} individual stories.")

if __name__ == "__main__":
    process_file()
