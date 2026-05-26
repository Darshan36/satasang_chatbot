import json
import re

def load_database(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Comprehensive keyword to topic mapping based on the content analysis
KEYWORD_MAPPING = {
    "teamwork": ["Team Work makes Dream Work", "APL exp sharing", "Selfless love"],
    "team": ["Team Work makes Dream Work", "APL exp sharing"],
    "unity": ["Team Work makes Dream Work", "APL exp sharing"],
    "friendship": ["True Friendship", "Faith, Focus and Friend must align", "Role of Bhagwadi", "DS EP4  - 2 સારા સાધુઓ અને 4 સારા હરિભગતો સાથે દોસ્તી."],
    "friends": ["True Friendship", "Faith, Focus and Friend must align"],
    "dosti": ["True Friendship", "DS EP4  - 2 સારા સાધુઓ અને 4 સારા હરિભગતો સાથે દોસ્તી."],
    "success": ["Secret ingredients of success", "DS EP9 - MBA", "One Spark is Enough for Ignition", "Great Success"],
    "career": ["Resume Building -Part 2", "Politics", "DS EP1 - Priority Management", "Do the Boring"],
    "job": ["Resume Building -Part 2", "Politics", "Hu To Nimit Matra"],
    "improvement": ["Continues Improvement", "DS EP9 - MBA", "Small Mistake, Big Loss, Small Correction, Big Gain"],
    "kaizen": ["Continues Improvement"],
    "laziness": ["DS EP1 - Priority Management", "Road to Recovery", "Laziness", "Do the Boring"],
    "aalsu": ["Laziness", "DS EP1 - Priority Management"],
    "health": ["Health is Wealth", "Mental Health.", "Road to Recovery", "Scientific Satsang"],
    "depression": ["Road to Recovery", "Mental Health."],
    "anxiety": ["Mental Health.", "Fearless"],
    "fear": ["Fearless", "DS EP2 - Faith Over Doubts", "Be a Warrior, Not a Worrier"],
    "faith": ["Faith", "Nishtha & Mahima", "DS EP2 - Faith Over Doubts", "Faith, Focus and Friend must align"],
    "nishtha": ["Nishtha & Mahima", "Unknown Topic"], # Many unknown topics contain Nishtha
    "bhajan": ["Bhajan", "Chant Your Problems Away", "ભજન", "Invisible Steering"],
    "prayer": ["Bhajan", "Chant Your Problems Away"],
    "time": ["DS EP1 - Priority Management", "70th Pragatya Parv", "Do the Boring"],
    "management": ["DS EP1 - Priority Management", "70th Pragatya Parv"],
    "addiction": ["DS EP8 - Digital Addiction"],
    "mobile": ["DS EP8 - Digital Addiction", "List ypr head up - Sar Utha ke Jio"],
    "opportunity": ["Life is an Opportunity", "Opportunity Miss or Grab"],
    "focus": ["Path to Precision", "Power of Concentration", "Faith, Focus and Friend must align", "List ypr head up - Sar Utha ke Jio"],
    "concentration": ["Power of Concentration"],
    "warrior": ["Be a Warrior, Not a Worrier", "War - Inner vs outer"],
    "acceptance": ["Acceptance", "Hu To Nimit Matra"],
    "simplicity": ["Simple Living High Thinking", "Simple Living High Thinking - day 2", "Simple Living, High Thinking", "Saral nahi hai Saral hona"],
    "krupa": ["કૃપા", "Elegance", "Zero Before Supereme"],
    "grace": ["Elegance", "કૃપા"],
    "politics": ["Politics", "Rajneeti"],
    "cricket": ["APL exp sharing", "APL Auction", "Divine Cricket series EP1 - Practice", "Divine Cricket series EP2 - Selection"],
    "discipline": ["DS EP1 - Priority Management", "Do the Boring"]
}

def clean_html(text):
    """Remove HTML tags and entities."""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = text.replace('&quot;', '"').replace('&apos;', "'").replace('&amp;', '&').replace('&nbsp;', ' ')
    return text

def search_prasangs(query, db):
    query = query.lower().strip()
    found_topics = []
    
    # Check keyword mapping
    for keyword, topics in KEYWORD_MAPPING.items():
        if keyword in query:
            found_topics.extend(topics)
    
    # Fallback to direct topic name matching
    if not found_topics:
        for entry in db:
            if query in entry['topic'].lower():
                found_topics.append(entry['topic'])
                
    if not found_topics:
        return "No prasangs found for this keyword. Try keywords like 'teamwork', 'health', 'faith', 'career', etc."

    # Unique topics only
    found_topics = list(set(found_topics))
    
    results = []
    for topic_name in found_topics:
        for entry in db:
            if entry['topic'] == topic_name:
                results.append(f"### Topic: {topic_name}\n{clean_html(entry['content'])}\n{'-'*50}")
    
    return "\n\n".join(results)

def main():
    print("--- Welcome to the Akshar Sarjan Prasang Chatbot ---")
    print("Enter a keyword (e.g., teamwork, success, health, bhajan) to see related stories.")
    print("Type 'exit' to quit.\n")
    
    try:
        db = load_database('summaries.json')
    except Exception as e:
        print(f"Error loading database: {e}")
        return

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        response = search_prasangs(user_input, db)
        print(f"\nBot:\n{response}\n")

if __name__ == "__main__":
    main()
