import json
import re

def clean_content(content):
    # Remove the standard metadata headers
    lines = content.split('\n')
    cleaned_lines = []
    
    metadata_patterns = [
        r'Akshar Sarjan Sabha',
        r'Date\s*[-–:]',
        r'Day\s*[-–:]',
        r'Place\s*[-–:]',
        r'Time\s*[-–:]',
        r'Topic\s*[-–:]',
        r'ટોપિક\s*[-–:]'
    ]
    
    for line in lines:
        is_metadata = False
        for pattern in metadata_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                is_metadata = True
                break
        
        if not is_metadata:
            cleaned_lines.append(line)
            
    # Join back and remove excessive newlines
    result = '\n'.join(cleaned_lines).strip()
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result

def process_file():
    with open('full_prasangs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    refined_data = []
    for entry in data:
        cleaned = clean_content(entry['content'])
        if len(cleaned) > 20: # Ensure there's actual content left
            refined_data.append({
                "topic": entry['topic'],
                "content": cleaned
            })
            
    with open('individual_prasangs.json', 'w', encoding='utf-8') as f:
        json.dump(refined_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processed {len(data)} messages into {len(refined_data)} clean story blocks.")

if __name__ == "__main__":
    process_file()
