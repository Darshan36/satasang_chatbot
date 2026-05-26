import json
import re
from bs4 import BeautifulSoup

def extract_messages(file_path):
    print(f"Opening {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("Parsing HTML...")
    # Use lxml for speed if available, otherwise html.parser
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except:
        soup = BeautifulSoup(html_content, 'html.parser')
    
    messages = []
    
    print("Finding all 'text' divs...")
    # Directly find all text divs
    text_divs = soup.find_all('div', class_='text')
    print(f"Found {len(text_divs)} text divs.")
    
    for div in text_divs:
        # Get text with newlines
        full_text = div.get_text(separator='\n').strip()
        
        # We are looking for "Akshar Sarjan Sabha" or "Akshar Sarjan"
        if "Akshar Sarjan" in full_text:
            # Extract topic name
            # Topic : *Topic Name*
            topic_match = re.search(r'(?:Topic|ટોપિક)\s*[:ઃ-]\s*\*?(.*?)\*?(\n|$)', full_text, re.IGNORECASE)
            topic_name = topic_match.group(1).strip() if topic_match else "General/Spiritual"
            
            messages.append({
                "topic": topic_name,
                "content": full_text
            })
            
    return messages

if __name__ == "__main__":
    all_messages = extract_messages('messages.html')
    with open('full_prasangs.json', 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    print(f"Successfully extracted {len(all_messages)} entries to full_prasangs.json")
