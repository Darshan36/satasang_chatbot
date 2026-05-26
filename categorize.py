
import json
import os

file_path = r'C:\Users\Darshan\Downloads\Telegram Desktop\ChatExport_2026-05-01 (1)\individual_prasangs.json'
output_path = r'C:\Users\Darshan\Downloads\Telegram Desktop\ChatExport_2026-05-01 (1)\categorized_individual_prasangs.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

keywords = [
    "Teamwork & Unity",
    "Success & Career",
    "Mental Health & Peace",
    "Faith & Devotion",
    "Service & Seva",
    "Friendship & Sang",
    "Time Management & Discipline",
    "Addiction & Focus",
    "Health & Wellness",
    "Grace & Krupa",
    "Politics & Ethics",
    "Continuous Improvement",
    "Acceptance & Humility",
    "Sports & Discipline"
]

category_map = {k: [] for k in keywords}

def categorize(topic, content):
    assigned = set()
    t_c = (topic + " " + content).lower()
    
    # Heuristics
    if any(word in t_c for word in ["teamwork", "unity", "group", "together", "united", "ekta", "atmiyata", "team"]):
        assigned.add("Teamwork & Unity")
    
    if any(word in t_c for word in ["career", "success", "job", "ca exam", "study", "promotion", "boss", "salary", "interview", "degree", "iim", "mba", "work", "business"]):
        assigned.add("Success & Career")
        
    if any(word in t_c for word in ["mental health", "peace", "stress", "depression", "thoughts", "anxiety", "mind", "shanti", "psychology", "feelings"]):
        assigned.add("Mental Health & Peace")
        
    if any(word in t_c for word in ["faith", "devotion", "bhagwan", "god", "nishtha", "trust", "vishwas", "bhajan", "prathna", "prayer", "temple", "mandir", "swaminarayan", "darshan", "thakorji", "upasana", "sant"]):
        assigned.add("Faith & Devotion")
        
    if any(word in t_c for word in ["service", "seva", "volunteer", "help", "helping"]):
        assigned.add("Service & Seva")
        
    if any(word in t_c for word in ["friendship", "friend", "sang", "mitr", "dosti", "company", "colleague"]):
        assigned.add("Friendship & Sang")
        
    if any(word in t_c for word in ["time management", "discipline", "schedule", "punctual", "laziness", "aalas", "time", "early", "late", "planning", "priority"]):
        assigned.add("Time Management & Discipline")
        
    if any(word in t_c for word in ["addiction", "focus", "concentration", "mobile", "social media", "phone", "distraction", "digital", "addicted", "netflix", "reels", "internet"]):
        assigned.add("Addiction & Focus")
        
    if any(word in t_c for word in ["health", "wellness", "body", "exercise", "gym", "walking", "diet", "food", "doctor", "cancer", "disease", "illness", "fit", "fitness", "medicine", "operation", "surgery"]):
        assigned.add("Health & Wellness")
        
    if any(word in t_c for word in ["grace", "krupa", "blessing", "ashirwad", "miracle", "chamtkar", "favor"]):
        assigned.add("Grace & Krupa")
        
    if any(word in t_c for word in ["politics", "ethics", "rajneeti", "king", "government", "justice", "truth", "raja", "law", "court"]):
        assigned.add("Politics & Ethics")
        
    if any(word in t_c for word in ["improvement", "growth", "change", "better", "learning", "skills", "upgrade", "kaizen", "grow", "potential"]):
        assigned.add("Continuous Improvement")
        
    if any(word in t_c for word in ["acceptance", "humility", "surrender", "modesty", "nirmani", "saral", "ego", "humble", "lowly", "respect", "patience", "tolerance"]):
        assigned.add("Acceptance & Humility")
        
    if any(word in t_c for word in ["sports", "cricket", "football", "tennis", "game", "player", "athlete", "tournament", "match", "ball", "batsman", "bowler", "ipl", "olympic"]):
        assigned.add("Sports & Discipline")

    # Ensure every entry is assigned
    if not assigned:
        # Default to Faith & Devotion if nothing else matches as most are spiritual
        assigned.add("Faith & Devotion")
        
    return assigned

for entry in data:
    topic = entry.get("topic", "")
    content = entry.get("content", "")
    categories = categorize(topic, content)
    for cat in categories:
        category_map[cat].append(content)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(category_map, f, indent=2, ensure_ascii=False)

print("Categorization complete.")
