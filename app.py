from flask import Flask, request, jsonify, render_template
import spacy
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import re
from typing import Dict, Optional
import random

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

DB_CONFIG = {
    "database": "student_info",
    "user": "postgres",
    "password": "MADH@2006",
    "host": "localhost",
    "port": "5432"
}

pool = SimpleConnectionPool(1, 20, **DB_CONFIG)

class MarksQueryProcessor:
    def __init__(self):
        # Greetings and conversation patterns
        self.greeting_patterns = [
            r"(?i)^(hi|hello|hey|greetings|good morning|good afternoon|good evening).*",
            r"(?i)^(hi|hello|hey|greetings|good morning|good afternoon|good evening)\s+.*"
        ]
        
        self.farewell_patterns = [
            r"(?i)^(bye|goodbye|see you|farewell|exit|quit|end).*",
            r"(?i).*\b(bye|goodbye|see you|farewell)\b.*"
        ]
        
        self.help_patterns = [
            r"(?i)^(what|how) can you (do|help).*",
            r"(?i)^help.*",
            r"(?i).*\b(your purpose|you do|about you)\b.*",
            r"(?i)^tell me about yourself.*"
        ]
        
        # Greeting responses
        self.greetings = [
            "👋 Hello! I'm your student marks assistant. How can I help you today?",
            "Hi there! 📚 Ready to help you with student marks information!",
            "Hello! I'm here to help you check student marks. What would you like to know?",
            "Greetings! 🎓 How may I assist you with student marks today?"
        ]
        
        # Farewell responses
        self.farewells = [
            "Goodbye! Have a great day! 👋",
            "See you later! Feel free to come back if you need more help! 😊",
            "Bye! Take care! 👋",
            "Farewell! Let me know if you need anything else! 🌟"
        ]
        
        # Enhanced subject keywords with more variations
        self.subject_keywords = {
            "data visualization": ["data viz", "visualization", "dv", "dataviz", "data vis", "data visualization course", "viz"],
            "computer architecture": ["ca", "architecture", "comp arch", "computer arch", "comp architecture", "computer organization"],
            "dsa": ["data structures", "algorithms", "ds", "data structure", "dsa", "ds and algo", "data structures and algorithms"],
            "java": ["java programming", "java lang", "java language", "core java", "java course", "java programming language"],
            "dbms": ["database", "db", "database management", "database system", "db management", "database management system"],
            "discrete maths": ["discrete mathematics", "discrete", "dm", "discrete math", "maths", "mathematics", "discrete math course"]
        }
        
        # Marks query patterns
        self.marks_patterns = [
            (r"(?i)^(show|display|get|what are|tell me|fetch) (.+?)(?:'s)? marks$", self.get_all_marks),
            (r"(?i)^marks of (.+?)$", self.get_all_marks),
            (r"(?i)^(.+?)(?:'s)? marks$", self.get_all_marks),
            (r"(?i)^what did (.+?) (get|score|obtain) in (.+?)$", self.get_subject_marks),
            (r"(?i)^how (much|many|well) did (.+?) (score|get|obtain) in (.+?)$", self.get_subject_marks),
            (r"(?i)^(.+?)(?:'s)? (.+?) marks$", self.get_subject_marks),
            (r"(?i)^show me (.+?)(?:'s)? performance in (.+?)$", self.get_subject_marks),
            (r"(?i)^what is (.+?)(?:'s)? score in (.+?)$", self.get_subject_marks),
            (r"(?i)^check (.+?)(?:'s)? marks in (.+?)$", self.get_subject_marks)
        ]

    def process_query(self, query: str) -> str:
        query = query.strip()
        
        # Check for greetings
        for pattern in self.greeting_patterns:
            if re.match(pattern, query):
                return random.choice(self.greetings)
        
        # Check for farewells
        for pattern in self.farewell_patterns:
            if re.match(pattern, query):
                return random.choice(self.farewells)
        
        # Check for help/about queries
        for pattern in self.help_patterns:
            if re.match(pattern, query):
                return self.get_help_message()
        
        # Try marks query patterns
        for pattern, handler in self.marks_patterns:
            match = re.match(pattern, query)
            if match:
                return handler(*match.groups())
        
        # Enhanced NLP processing for unmatched queries
        doc = nlp(query)
        
        # Extract name using NER
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return self.get_all_marks(ent.text)
        
        # Fallback: look for capitalized words that might be names
        words = [token.text for token in doc if token.is_alpha and token.is_title]
        if words:
            return self.get_all_marks(words[0])
        
        return "I couldn't understand your query. Try asking in these ways:\n" + \
               "1. 'Show John's marks'\n" + \
               "2. 'What did Mary get in Java?'\n" + \
               "3. 'Show me Sarah's performance in DSA'\n" + \
               "4. 'Marks of Tom'\n\n" + \
               "Or type 'help' to learn more about what I can do!"

    def get_help_message(self) -> str:
        return """🤖 I'm your Student Marks Assistant!

I can help you with:
📊 Checking all marks for a student
📚 Looking up marks for specific subjects
📈 Viewing performance statistics

You can ask me things like:
• "Show John's marks"
• "What did Mary get in Java?"
• "Show me Sarah's performance in DSA"

Available subjects:
""" + "\n".join(f"• {subject}" for subject in self.subject_keywords.keys()) + """

Just ask your question and I'll help you find the information you need! 😊"""

    def get_all_marks(self, student_name: str, *args) -> str:
        conn = pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT name, data_visualization, computer_architecture, 
                           dsa, java, dbms, discrete_maths 
                    FROM students 
                    WHERE LOWER(name) LIKE LOWER(%s)
                """, (f"%{student_name.strip()}%",))
                result = cursor.fetchone()
                
                if not result:
                    return f"📚 No records found for student: {student_name}"
                
                marks_dict = {
                    "Data Visualization": result[1],
                    "Computer Architecture": result[2],
                    "DSA": result[3],
                    "Java": result[4],
                    "DBMS": result[5],
                    "Discrete Maths": result[6]
                }
                
                # Calculate statistics
                avg_marks = sum(marks_dict.values()) / len(marks_dict)
                highest_subject = max(marks_dict.items(), key=lambda x: x[1])
                lowest_subject = min(marks_dict.items(), key=lambda x: x[1])
                
                # Format response
                response = [f"📊 Marks Report for {result[0]}"]
                response.append("-" * 40)
                
                for subject, marks in marks_dict.items():
                    response.append(f"{subject:<20}: {marks:>3}")
                
                response.append("-" * 40)
                response.append(f"📈 Average: {avg_marks:.1f}")
                response.append(f"🏆 Highest: {highest_subject[0]} ({highest_subject[1]})")
                response.append(f"📉 Lowest: {lowest_subject[0]} ({lowest_subject[1]})")
                
                return "\n".join(response)
                
        finally:
            pool.putconn(conn)

    def get_subject_marks(self, *args) -> str:
        if len(args) >= 3:
            student_name = args[1] if len(args) == 4 else args[0]
            subject = args[-1]
        else:
            student_name, subject = args
        
        normalized_subject = self._normalize_subject(subject)
        if not normalized_subject:
            return f"❌ I couldn't recognize the subject '{subject}'. Available subjects are:\n" + \
                   ", ".join(self.subject_keywords.keys())
        
        conn = pool.getconn()
        try:
            with conn.cursor() as cursor:
                column_name = normalized_subject.replace(" ", "_")
                query = """
                    SELECT name, {column} 
                    FROM students 
                    WHERE LOWER(name) LIKE LOWER(%s)
                """.format(column=column_name)
                
                cursor.execute(query, (f"%{student_name.strip()}%",))
                result = cursor.fetchone()
                
                if not result:
                    return f"📚 No records found for student: {student_name}"
                
                return f"📊 {result[0]}'s marks in {subject.title()}:\n" + \
                       f"Marks: {result[1]}"
                
        finally:
            pool.putconn(conn)

    def _normalize_subject(self, subject: str) -> Optional[str]:
        subject = subject.lower().strip()
        for main_subject, alternatives in self.subject_keywords.items():
            if subject == main_subject or subject in alternatives:
                return main_subject
        return None

@app.route('/')
def index():
    return render_template('index7.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json['message']
        processor = MarksQueryProcessor()
        response = processor.process_query(user_input)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)