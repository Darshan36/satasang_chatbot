import json
import re
from bs4 import BeautifulSoup

def extract_messages(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    messages = []
    
    # Telegram export structure usually has messages in div.message.default
    msg_divs = soup.find_all('div', class_='message default')
    
    for div in msg_divs:
        text_div = div.find('div', class_='text')
        if not text_div:
            continue
            
        full_text = text_div.get_text(separator='\n').strip()
        
        # We are looking for "Akshar Sarjan Sabha" or entries with "Topic"
        if "Akshar Sarjan" in full_text or "Topic" in full_text:
            # Extract topic name for better indexing later
            topic_match = re.search(r'(?:Topic|ટોપિક)\s*[:ઃ-]\s*(.*)', full_text, re.IGNORECASE)
            topic_name = topic_match.group(1).strip() if topic_match else "General/Unknown"
            
            # Clean up the topic name (remove trailing <br> etc which get_text handles but just in case)
            topic_name = topic_name.split('\n')[0].strip()
            
            messages.append({
                "topic": topic_name,
                "content": full_text
            })
            
    return messages

if __name__ == "__main__":
    print("Extracting messages...")
    all_messages = extract_messages('messages.html')
    with open('full_prasangs.json', 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    print(f"Extracted {len(all_messages)} entries to full_prasangs.json")
