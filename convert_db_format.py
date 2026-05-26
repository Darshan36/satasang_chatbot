import json

def convert_format():
    with open('categorized_individual_prasangs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # If it's already a dictionary, we might not need to do much, 
    # but based on the read_file output, it's a list of objects.
    
    if isinstance(data, list):
        new_db = {}
        for entry in data:
            content = entry.get('content', '')
            categories = entry.get('categories', [])
            for cat in categories:
                if cat not in new_db:
                    new_db[cat] = []
                new_db[cat].append(content)
        
        with open('categorized_individual_prasangs.json', 'w', encoding='utf-8') as f:
            json.dump(new_db, f, ensure_ascii=False, indent=2)
        print("Converted list format to dictionary format.")
    else:
        print("Already in dictionary format or unknown format.")

if __name__ == "__main__":
    convert_format()
