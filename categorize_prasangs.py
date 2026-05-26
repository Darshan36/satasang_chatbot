import json
import os

input_file = r'C:\Users\Darshan\Downloads\Telegram Desktop\ChatExport_2026-05-01 (1)\individual_prasangs.json'
output_file = r'C:\Users\Darshan\Downloads\Telegram Desktop\ChatExport_2026-05-01 (1)\categorized_individual_prasangs.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

categorized_data = []

def categorize(prasang):
    content = prasang['content'].lower()
    topic = prasang['topic'].lower()
    combined = (topic + " " + content).lower()
    
    categories = []
    
    # Rules summary:
    # 1. Teamwork & Unity: ONLY working together, APL (Cricket) unity, collective efforts.
    # 2. Success & Career: ONLY CA exams, studies, job improvements, Edison, etc.
    # 3. Health & Wellness: ONLY Fasting, Food, Diet, Physical Health.
    # 4. Mental Health & Peace: ONLY Stress, Depression, Overthinking.
    # 5. Faith & Devotion: Bhajan, Chanting, Mahima of Guru, miracles.
    # 6. Continuous Improvement: Small daily changes (Kaizen), Nokia, Kodak.

    # 1. Teamwork & Unity
    # Apollo 13 or Teamwork specifically -> Teamwork.
    # BUT if bulk (like Scientific Satsang) is Chanting/Fasting, it MUST NOT go to Teamwork.
    teamwork_strictly = ['teamwork', 'apollo 13', 'apl ', 'apl(', 'atmiya premier league', 'unity', 'collective efforts', 'સાથે મળી', 'ટીમ', 'team work']
    if any(kw in combined for kw in teamwork_strictly):
        # Specific check for Scientific Satsang bulk rules
        if 'scientific satsang' not in combined:
            categories.append('Teamwork & Unity')
        elif 'apollo 13' in combined or 'teamwork specifically' in combined:
             categories.append('Teamwork & Unity')

    # 2. Success & Career
    success_keywords = ['ca exam', 'study', 'job improvement', 'edison', 'career', 'degree', 'success', 'ipcc', 'cpt', 'revision', 'promotion', 'salary', 'resume', 'cv', 'business', 'cs exam', 'અભ્યાસ', 'પરીક્ષા', 'નોકરી', 'સફળતા', 'ભણવા', 'સીએ', 'masters']
    if any(kw in combined for kw in success_keywords):
        categories.append('Success & Career')
        
    # 3. Health & Wellness
    # Scientific Satsang bulk is Chanting and Fasting -> Health & Wellness and Faith & Devotion.
    health_keywords = ['fasting', 'diet', 'physical health', 'stay fit', 'immunity', 'detox', 'cancer', 'onion', 'garlic', 'ઉપવાસ', 'ખોરાક', 'સ્વાસ્થ્ય', 'તંદુરસ્તી', 'health is wealth', 'walking', 'sugar', 'blood report', 'surgery', 'medicine']
    if any(kw in combined for kw in health_keywords) or 'scientific satsang' in combined:
        # Exclude if it's just mentioning "Prasad - Idli" at the end which is not the BULK of the story.
        # But wait, the rule says "ONLY for stories about Fasting, Food, Diet, Physical Health."
        # If the content contains bulk health info.
        if any(kw in content for kw in ['fasting', 'diet', 'physical health', 'fitness', 'immunity', 'detox', 'onion', 'garlic', 'ઉપવાસ', 'ખોરાક', 'સ્વાસ્થ્ય', 'તંદુરસ્તી']):
            categories.append('Health & Wellness')
        elif 'scientific satsang' in combined:
            categories.append('Health & Wellness')
        elif 'health' in combined and 'success' not in combined: # and other checks
            categories.append('Health & Wellness')

    # 4. Mental Health & Peace
    mental_keywords = ['stress', 'depression', 'overthinking', 'peace of mind', 'fear', 'addiction', 'suicide', 'hopeless', 'calm', 'mental', 'ચિંતા', 'તણાવ', 'ડિપ્રેશન', 'શાંતિ', 'ડર', 'ભય', 'ગભરાઈ', 'over thinking']
    if any(kw in combined for kw in mental_keywords):
        categories.append('Mental Health & Peace')
        
    # 5. Faith & Devotion
    # Bhajan, Chanting, Mahima of Guru, miracles.
    faith_keywords = ['bhajan', 'chanting', 'mahima', 'miracle', 'faith', 'devotion', 'god', 'guru', 'dhun', 'mala', 'prarthna', 'prayer', 'chamatkar', 'ભજન', 'ગુરુ', 'ભક્તિ', 'શ્રદ્ધા', 'મહિમા', 'ચમત્કાર', 'ધૂન', 'માળા', 'પ્રાર્થના', 'સ્વામીજી', 'મહારાજ', 'પ્રભુ', 'દર્શન']
    if any(kw in combined for kw in faith_keywords) or 'scientific satsang' in combined:
        categories.append('Faith & Devotion')
        
    # 6. Continuous Improvement
    # small daily changes (Kaizen), Nokia, Kodak.
    improvement_keywords = ['kaizen', 'daily changes', 'nokia', 'kodak', 'xerox', 'improvement', 'change', 'daily solved', '0.99^365', '1.01^365', 'upgrade', 'kaizan', 'સુધારો', 'પરિવર્તન', 'small step']
    if any(kw in combined for kw in improvement_keywords):
        categories.append('Continuous Improvement')

    # Defaults to 'Faith & Devotion' if no category fits
    if not categories:
        categories.append('Faith & Devotion')
        
    return list(set(categories))

for prasang in data:
    prasang['categories'] = categorize(prasang)
    categorized_data.append(prasang)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(categorized_data, f, ensure_ascii=False, indent=2)

print(f"Processed {len(categorized_data)} entries.")
