"""
========================================================================================
 AI-POWERED MOCK INTERVIEW PLATFORM (ALL-IN-ONE SINGLE FILE FOR VS CODE)
========================================================================================
 Technology Stack: Python 3, Flask, SQLite3, HTML5, CSS3, JavaScript (Chart.js)
 Features:
   - Full Candidate Flow: Landing, Setup, AI Mock Interview, Instant Feedback, Results
   - Voice Read-Aloud (Text-to-Speech) & Microphone Voice Dictation (Speech-to-Text)
   - 5-Metric AI Diagnostic Rubric (Relevance, Technical, Clarity, Completeness, Grammar)
   - Dynamic Question Bank: Python, Web Dev, Java, Data Analyst, Behavioral, HR
   - Candidate Performance Dashboard with Line Graph
   - 5-Dimensional Skills Radar Chart (Chart.js)
   - One-Click Printable / Downloadable PDF Report
   - Complete Recruiter / Admin Selection Portal (/admin) with CSV Export & Decision Forms
 
 Run in VS Code:
   1. pip install flask
   2. python interview_app.py
   3. Open: http://127.0.0.1:5000
========================================================================================
"""

import os
import io
import csv
import json
import random
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, Response
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'interviewai-super-secret-key-2026')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interviews.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            category TEXT,
            difficulty TEXT,
            total_questions INTEGER,
            score INTEGER,
            duration_minutes INTEGER DEFAULT 15,
            performance_summary TEXT,
            selection_status TEXT DEFAULT 'Under Review',
            admin_notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER,
            question_index INTEGER,
            question TEXT,
            answer TEXT,
            score INTEGER,
            relevance_score INTEGER,
            technical_score INTEGER,
            clarity_score INTEGER,
            completeness_score INTEGER,
            grammar_score INTEGER,
            strengths TEXT,
            improvements TEXT,
            suggested_answer TEXT,
            tips TEXT,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        );
    ''')
    try:
        db.execute("ALTER TABLE interviews ADD COLUMN selection_status TEXT DEFAULT 'Under Review'")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE interviews ADD COLUMN admin_notes TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    db.commit()

def get_or_create_demo_user():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', ('Demo Candidate',)).fetchone()
    if not user:
        db.execute('INSERT INTO users (username) VALUES (?)', ('Demo Candidate',))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE username = ?', ('Demo Candidate',)).fetchone()
    return user

# ==========================================
# QUESTION BANK
# ==========================================

QUESTION_BANK = {
    'Python Developer': {
        'Technical': {
            'Beginner': [
                "What is the difference between a list and a tuple in Python, and when would you use each?",
                "How does memory management and garbage collection work in Python?",
                "Explain the concept of PEP 8 and why code style standards matter in Python teams.",
                "What are Python decorators and how do they work under the hood?",
                "What is the difference between shallow copy and deep copy in Python?"
            ],
            'Intermediate': [
                "Explain the Global Interpreter Lock (GIL) in CPython and how it impacts multithreaded applications.",
                "How do Python generators and the 'yield' statement optimize memory when handling large datasets?",
                "Compare asyncio with multi-threading and multi-processing in Python. When would you choose which?",
                "Explain context managers in Python and how to implement one using either a class or contextlib.",
                "How does Python's method resolution order (MRO) work with multiple inheritance?"
            ],
            'Advanced': [
                "Design a high-throughput async worker pipeline in Python for processing millions of webhook events per day.",
                "How would you identify and fix memory leaks in a production Django or FastAPI application?",
                "Explain Python metaclasses, dunder methods (__new__ vs __init__), and when a custom metaclass is justified.",
                "How does Python's C-API allow writing C extensions, and what are the performance trade-offs?",
                "How would you design a distributed caching and rate-limiting middleware in Python using Redis?"
            ]
        }
    },
    'Web Developer': {
        'Technical': {
            'Beginner': [
                "Explain the difference between client-side rendering (CSR) and server-side rendering (SSR).",
                "What is the Document Object Model (DOM) and how does the browser event loop handle asynchronous tasks?",
                "How does CSS Flexbox differ from CSS Grid, and what are the best use-cases for each?",
                "What are REST APIs, and what is the semantic difference between PUT and PATCH requests?",
                "Explain how browser cookies, localStorage, and sessionStorage differ in persistence and security."
            ],
            'Intermediate': [
                "How does the React Virtual DOM diffing algorithm work, and how do React keys prevent unnecessary re-renders?",
                "Explain modern web security vulnerabilities: Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF). How do you mitigate them?",
                "What are Webpack or Vite build tools doing during bundling, code-splitting, and tree-shaking?",
                "Explain CORS (Cross-Origin Resource Sharing) headers and how preflight OPTIONS requests function.",
                "How do Service Workers enable Progressive Web Apps (PWAs) with offline caching?"
            ],
            'Advanced': [
                "How would you optimize Core Web Vitals (LCP, FID/INP, CLS) for a media-rich ecommerce web application?",
                "Describe the architecture of a micro-frontend application: state sharing, routing, and deployment isolation.",
                "How do HTTP/2 and HTTP/3 (QUIC) improve web performance compared to traditional HTTP/1.1?",
                "Design an end-to-end authentication and session refresh mechanism using short-lived JWTs and secure HttpOnly cookies.",
                "How would you architect real-time multi-user collaborative editing like Google Docs or Figma on the web?"
            ]
        }
    },
    'Java Developer': {
        'Technical': {
            'Beginner': [
                "Explain the core principles of Object-Oriented Programming (OOP) with examples from Java.",
                "What is the difference between JDK, JRE, and the Java Virtual Machine (JVM)?",
                "Explain the difference between HashMap, HashTable, and ConcurrentHashMap in Java.",
                "What is the difference between checked and unchecked exceptions in Java?",
                "How do Java Strings achieve immutability and why is the String Constant Pool important?"
            ],
            'Intermediate': [
                "Explain the JVM memory model: Heap (Young, Old Gen), Stack, and Metaspace, plus how Garbage Collectors work.",
                "How do Spring Framework's Dependency Injection (DI) and Inversion of Control (IoC) containers work?",
                "Explain Java 8+ Streams API and Lambdas: what is the difference between intermediate and terminal operations?",
                "Describe Java multi-threading concepts: synchronized blocks, volatile keyword, and ReentrantLock.",
                "What is Hibernate / JPA dirty checking, and how do you resolve the N+1 select problem?"
            ],
            'Advanced': [
                "How would you tune JVM flags (-Xms, -Xmx, GC algorithm) for an ultra-low-latency financial microservice?",
                "Explain Java 21 Virtual Threads (Project Loom) and how they revolutionize high-concurrency I/O throughput.",
                "Design a distributed event-driven microservices architecture using Spring Cloud, Kafka, and Saga pattern.",
                "How do Java class loaders work, and how can custom class loaders isolate plugins dynamically?",
                "Explain memory barriers, Java Memory Model (JMM) happens-before relationships, and lock-free CAS algorithms."
            ]
        }
    },
    'Data Analyst': {
        'Technical': {
            'Beginner': [
                "What is the difference between WHERE and HAVING clauses in SQL, and when do you use each?",
                "Explain the different types of SQL JOINs (INNER, LEFT, RIGHT, FULL OUTER) and cross joins.",
                "How do you handle missing or duplicate values when cleaning a dataset in Pandas?",
                "What is the difference between mean, median, and mode, and which is most robust against outliers?",
                "Explain the difference between categorical, ordinal, and continuous numerical data."
            ],
            'Intermediate': [
                "Explain SQL Window Functions: ROW_NUMBER(), RANK(), DENSE_RANK(), and partition by clauses.",
                "How do you design an A/B test: defining hypothesis, sample size, statistical significance (p-value), and alpha level?",
                "Explain the trade-off between Correlation and Causation with a practical real-world scenario.",
                "How do you structure an interactive business dashboard in Tableau or Power BI to tell a clear data story?",
                "How do you detect and treat multicollinearity and skewness in exploratory data analysis?"
            ],
            'Advanced': [
                "Design a scalable star-schema or snowflake data warehouse model for a multi-channel retail company.",
                "How do you construct cohort retention curves and LTV (Lifetime Value) prediction models for subscription businesses?",
                "Explain how you would optimize a slow query scanning billions of rows on Snowflake, BigQuery, or PostgreSQL.",
                "How do you apply causal inference techniques when A/B testing is impossible?",
                "How would you automate data pipelines with dbt and Airflow while ensuring automated data quality tests?"
            ]
        }
    },
    'HR': [
        "Tell me about yourself, your career journey, and why you are interested in this specific position.",
        "What are your greatest professional strengths, and what is one area you are actively working to improve?",
        "Where do you see yourself professionally in the next three to five years?",
        "Why are you looking to leave your current role, or what attracted you to our organization?",
        "How do you prioritize work-life balance and avoid burnout when managing high-stakes deadlines?",
        "What type of work culture and management style empowers you to do your best work?"
    ],
    'Behavioral': [
        "Using the STAR method (Situation, Task, Action, Result), tell me about a time you led a team through an unexpected hurdle.",
        "Describe a situation where you had a significant disagreement with a colleague or manager. How did you handle it?",
        "Tell me about a project that didn't go as planned or failed. What went wrong and what key lessons did you take away?",
        "Give an example of a time you were given vague or shifting requirements. How did you bring clarity and drive execution?",
        "Describe a situation where you went above and beyond your standard job responsibilities to help a client or team succeed."
    ]
}

def get_questions_for_interview(role, category, difficulty, count):
    if category == 'HR':
        pool = list(QUESTION_BANK['HR'])
    elif category == 'Behavioral':
        pool = list(QUESTION_BANK['Behavioral'])
    else:
        role_data = QUESTION_BANK.get(role, QUESTION_BANK['Python Developer'])
        tech_data = role_data.get('Technical', {})
        pool = list(tech_data.get(difficulty, tech_data.get('Intermediate', [])))
        if not pool:
            pool = list(QUESTION_BANK['Python Developer']['Technical']['Intermediate'])

    random.shuffle(pool)
    questions = []
    while len(questions) < count:
        if pool:
            questions.append(pool.pop(0))
        else:
            questions.append(f"Discuss key architecture best practices and performance trade-offs in {role}.")
    return questions[:count]

def evaluate_candidate_answer(question, answer, role, difficulty):
    clean = answer.strip()
    words = clean.split()
    word_count = len(words)
    
    if word_count < 10:
        return {
            'score': 3.0,
            'relevance_score': 4,
            'technical_score': 3,
            'clarity_score': 4,
            'completeness_score': 2,
            'grammar_score': 5,
            'strengths': ["Submitted a direct response."],
            'improvements': [
                "Answer is significantly too brief for a professional interview.",
                "Provide technical depth, architecture mechanisms, or methodology.",
                "Explain the 'why' and 'how', not just a single phrase."
            ],
            'suggested_answer': f"A strong answer should define the core concept, compare trade-offs, and cite a practical scenario or project experience where you applied it in {role}.",
            'tips': "Aim for at least 3-4 structured sentences or 80-120 words. Use the STAR method for behavioral or Concept -> Mechanics -> Trade-offs for technical."
        }
        
    buzzwords = ["because", "example", "optimize", "performance", "architecture", "trade-off", "scalability", "memory", "async", "database", "security", "team", "result", "improved", "implemented", "design", "production", "latency", "maintainability", "test"]
    matched = [w for w in buzzwords if w in clean.lower()]
    length_factor = min(3, word_count // 40)
    buzz_factor = min(3, len(matched))
    
    relevance = min(10, 6 + buzz_factor + (1 if len(matched) > 2 else 0))
    technical = min(10, 5 + buzz_factor + (1 if difficulty == 'Beginner' else 0))
    clarity = min(10, 6 + (2 if 30 <= word_count <= 250 else 0))
    completeness = min(10, 4 + length_factor + (2 if len(matched) >= 3 else 0))
    grammar = min(10, 7 + (1 if clean.endswith(('.', '!', '?')) else 0) + (1 if clean[0].isupper() else 0))
    
    total = round((relevance * 0.25) + (technical * 0.25) + (clarity * 0.2) + (completeness * 0.2) + (grammar * 0.1), 1)
    
    strengths = []
    if word_count > 60:
        strengths.append("Thorough detail provided with solid depth.")
    else:
        strengths.append("Concise and direct phrasing.")
    if matched:
        strengths.append(f"Good technical vocabulary used ({', '.join(matched[:3])}).")
    if "example" in clean.lower() or "for instance" in clean.lower():
        strengths.append("Excellent use of real-world illustration.")
    if not strengths:
        strengths.append("Good baseline grasp of the core question.")

    improvements = []
    if word_count < 50:
        improvements.append("Elaborate further with edge cases or performance considerations.")
    if "result" not in clean.lower() and "impact" not in clean.lower():
        improvements.append("Highlight measurable business outcome or technical metric improved.")
    if "trade-off" not in clean.lower() and "alternative" not in clean.lower():
        improvements.append("Discuss trade-offs or alternative solutions you considered.")
    if not improvements:
        improvements.append("Practice delivering this concisely within a 90-second speaking cadence.")

    return {
        'score': total,
        'relevance_score': relevance,
        'technical_score': technical,
        'clarity_score': clarity,
        'completeness_score': completeness,
        'grammar_score': grammar,
        'strengths': strengths,
        'improvements': improvements,
        'suggested_answer': f"In a live interview, structure your response: (1) Core definition or thesis, (2) Architectural trade-offs & tools used, (3) A real production scenario highlighting your specific contributions and measurable results.",
        'tips': "Structure answers with the STAR format (Situation, Task, Action, Result) for behavioral questions, or 'Concept -> Mechanics -> Real-world Trade-offs' for technical questions."
    }

# ==========================================
# ALL HTML TEMPLATES (EMBEDDED IN MEMORY)
# ==========================================

TEMPLATES = {}

TEMPLATES['base.html'] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title|default('InterviewAI - AI-Powered Mock Interview Platform') }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
          --bg-primary: #090a1a;
          --bg-secondary: #10122e;
          --card-bg: rgba(20, 24, 60, 0.65);
          --card-border: rgba(140, 100, 255, 0.22);
          --accent-purple: #8b5cf6;
          --accent-magenta: #ec4899;
          --accent-cyan: #06b6d4;
          --accent-emerald: #10b981;
          --text-main: #f8fafc;
          --text-muted: #94a3b8;
          --text-dim: #64748b;
          --gradient-main: linear-gradient(135deg, #7c3aed 0%, #db2777 50%, #06b6d4 100%);
          --gradient-btn: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
          --radius-sm: 8px; --radius-md: 14px; --radius-lg: 20px; --radius-full: 9999px;
          --shadow-card: 0 10px 30px -5px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--card-border);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          font-family: 'Plus Jakarta Sans', sans-serif;
          background-color: var(--bg-primary);
          background-image: 
            radial-gradient(at 0% 0%, rgba(124, 58, 237, 0.18) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.15) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(219, 39, 119, 0.12) 0px, transparent 50%);
          background-attachment: fixed;
          color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; line-height: 1.6;
        }
        .navbar {
          position: sticky; top: 0; z-index: 100;
          background: rgba(9, 10, 26, 0.85); backdrop-filter: blur(16px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          padding: 0.9rem 2rem; display: flex; align-items: center; justify-content: space-between;
        }
        .nav-brand { display: flex; align-items: center; gap: 0.75rem; text-decoration: none; color: var(--text-main); }
        .brand-icon {
          width: 36px; height: 36px; background: var(--gradient-btn); border-radius: var(--radius-sm);
          display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(124, 58, 237, 0.5);
        }
        .brand-text { font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em; color: #fff; }
        .badge-ai { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; padding: 2px 7px; background: rgba(124, 58, 237, 0.25); border: 1px solid var(--accent-purple); color: #d8b4fe; border-radius: var(--radius-full); }
        .nav-links { display: flex; align-items: center; gap: 1.5rem; }
        .nav-link { color: var(--text-muted); text-decoration: none; font-size: 0.92rem; font-weight: 500; transition: color 0.2s; }
        .nav-link:hover { color: #fff; }
        .user-badge { display: flex; align-items: center; gap: 0.6rem; background: rgba(255, 255, 255, 0.06); padding: 0.4rem 0.9rem; border-radius: var(--radius-full); border: 1px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem; }
        .user-avatar { width: 24px; height: 24px; border-radius: 50%; background: var(--accent-purple); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; }
        .main-content { flex: 1; max-width: 1200px; width: 100%; margin: 0 auto; padding: 2.5rem 1.5rem; }
        .glass-card {
          background: var(--card-bg); border-radius: var(--radius-lg); border: 1px solid var(--card-border);
          box-shadow: var(--shadow-card); backdrop-filter: blur(20px); padding: 2rem; position: relative; overflow: hidden;
        }
        .btn {
          display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
          padding: 0.75rem 1.5rem; border-radius: var(--radius-md); font-size: 0.95rem; font-weight: 600;
          cursor: pointer; text-decoration: none; transition: all 0.25s ease; border: none; font-family: inherit;
        }
        .btn-primary { background: var(--gradient-btn); color: #fff; box-shadow: 0 4px 18px rgba(124, 58, 237, 0.4); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(124, 58, 237, 0.6); }
        .btn-secondary { background: rgba(255, 255, 255, 0.08); color: var(--text-main); border: 1px solid rgba(255, 255, 255, 0.15); }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.14); transform: translateY(-2px); }
        .btn-emerald { background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: #fff; }
        .btn-sm { padding: 0.45rem 0.9rem; font-size: 0.85rem; border-radius: var(--radius-sm); }
        .btn-lg { padding: 0.95rem 2.2rem; font-size: 1.08rem; }
        .hero-section { text-align: center; padding: 4rem 1rem 3rem; }
        .hero-pill { display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(124, 58, 237, 0.15); border: 1px solid rgba(124, 58, 237, 0.4); padding: 0.35rem 1.1rem; border-radius: var(--radius-full); color: #c084fc; font-size: 0.85rem; font-weight: 600; margin-bottom: 1.5rem; }
        .hero-title { font-size: 3.2rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.03em; margin-bottom: 1.25rem; }
        .hero-gradient { background: var(--gradient-main); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero-subtitle { font-size: 1.2rem; color: var(--text-muted); max-width: 680px; margin: 0 auto 2.5rem; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 2rem; }
        .feature-box { padding: 1.8rem; border-radius: var(--radius-md); background: rgba(18, 21, 52, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { padding: 1.5rem; border-radius: var(--radius-md); background: var(--card-bg); border: 1px solid var(--card-border); display: flex; align-items: center; gap: 1.2rem; }
        .stat-icon { width: 44px; height: 44px; border-radius: var(--radius-md); background: rgba(124, 58, 237, 0.15); color: #c084fc; display: flex; align-items: center; justify-content: center; }
        .stat-value { font-size: 1.8rem; font-weight: 800; }
        .stat-label { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
        .custom-table { width: 100%; border-collapse: separate; border-spacing: 0 0.5rem; }
        .custom-table th { padding: 0.8rem 1rem; font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); text-align: left; }
        .custom-table td { padding: 1rem; background: rgba(18, 22, 54, 0.7); }
        .score-badge { display: inline-block; padding: 0.3rem 0.75rem; border-radius: var(--radius-full); font-weight: 700; font-size: 0.85rem; }
        .score-high { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
        .score-mid { background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.4); }
        .score-low { background: rgba(236, 72, 153, 0.2); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.4); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .form-group { display: flex; flex-direction: column; gap: 0.6rem; }
        .form-label { font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }
        .form-control {
          background: rgba(10, 12, 34, 0.8); border: 1px solid rgba(255, 255, 255, 0.12); color: #fff;
          padding: 0.85rem 1.1rem; border-radius: var(--radius-md); font-size: 0.95rem; outline: none; font-family: inherit;
        }
        .form-control:focus { border-color: var(--accent-purple); box-shadow: 0 0 15px rgba(124, 58, 237, 0.3); }
        .presets-container { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
        .preset-chip {
          background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.12);
          padding: 0.45rem 1rem; border-radius: var(--radius-full); font-size: 0.85rem; cursor: pointer; color: var(--text-muted);
        }
        .preset-chip:hover { background: rgba(124, 58, 237, 0.2); border-color: var(--accent-purple); color: #fff; }
        .interview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.8rem; }
        .timer-box { display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.35); color: #38bdf8; padding: 0.4rem 0.9rem; border-radius: var(--radius-full); font-weight: 700; }
        .progress-track { width: 100%; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: var(--radius-full); overflow: hidden; margin-bottom: 2rem; }
        .progress-bar-fill { height: 100%; background: var(--gradient-btn); }
        .question-box { background: rgba(25, 29, 72, 0.5); border: 1px solid rgba(138, 43, 226, 0.3); border-radius: var(--radius-md); padding: 1.8rem; margin-bottom: 1.8rem; }
        .question-text { font-size: 1.35rem; font-weight: 600; color: #f1f5f9; }
        .btn-icon { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); color: #e2e8f0; padding: 0.45rem 0.9rem; border-radius: var(--radius-md); display: inline-flex; align-items: center; gap: 0.45rem; font-size: 0.85rem; cursor: pointer; }
        .btn-icon.recording { background: rgba(239, 68, 68, 0.25); border-color: #ef4444; color: #fca5a5; }
        .answer-area { width: 100%; min-height: 180px; background: rgba(10, 12, 34, 0.85); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: var(--radius-md); color: #f8fafc; padding: 1.2rem; font-size: 1rem; resize: vertical; outline: none; font-family: inherit; }
        .score-banner { display: flex; align-items: center; justify-content: space-between; background: rgba(124, 58, 237, 0.12); border: 1px solid rgba(124, 58, 237, 0.35); border-radius: var(--radius-md); padding: 1.5rem 2rem; margin-bottom: 2rem; }
        .score-circle { width: 80px; height: 80px; border-radius: 50%; background: var(--gradient-btn); display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .score-number { font-size: 1.8rem; font-weight: 800; line-height: 1; }
        .metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .metric-pill { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); padding: 1rem; border-radius: var(--radius-md); }
        .metric-pill-header { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.4rem; }
        .metric-pill-bar { height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: var(--radius-full); overflow: hidden; }
        .metric-pill-fill { height: 100%; border-radius: var(--radius-full); }
        .feedback-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
        .feedback-card-green { background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-md); padding: 1.4rem; }
        .feedback-card-amber { background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: var(--radius-md); padding: 1.4rem; }
        .feedback-list { list-style: none; display: flex; flex-direction: column; gap: 0.6rem; margin-top: 0.8rem; }
        .suggested-box { background: rgba(18, 22, 54, 0.8); border-left: 4px solid var(--accent-purple); padding: 1.4rem; border-radius: var(--radius-md); margin-bottom: 2rem; }
        .qa-accordion-item { background: rgba(18, 22, 54, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: var(--radius-md); margin-bottom: 1rem; overflow: hidden; }
        .qa-header { padding: 1.2rem 1.5rem; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
        .qa-body { padding: 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.06); background: rgba(10, 12, 34, 0.5); }
        .footer { margin-top: auto; border-top: 1px solid rgba(255, 255, 255, 0.06); padding: 1.8rem 2rem; text-align: center; color: var(--text-dim); font-size: 0.85rem; }
        @media print {
            .navbar, .btn, .no-print { display: none !important; }
            body { background: #fff !important; color: #000 !important; }
            .glass-card, .custom-table td { background: #fff !important; color: #000 !important; border: 1px solid #ddd !important; }
        }
    </style>
</head>
<body>
    <nav class="navbar no-print">
        <a href="{{ url_for('index') }}" class="nav-brand">
            <div class="brand-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <span class="brand-text">InterviewAI</span>
            <span class="badge-ai">Pro</span>
        </a>
        <div class="nav-links">
            <a href="{{ url_for('index') }}" class="nav-link">Home</a>
            <a href="{{ url_for('dashboard') }}" class="nav-link">Dashboard</a>
            <a href="{{ url_for('setup') }}" class="nav-link">Mock Interview</a>
            <a href="{{ url_for('admin_portal') }}" class="nav-link" style="color: #c084fc; font-weight: 600;">
                <span class="badge-ai" style="background: rgba(16, 185, 129, 0.2); border-color: #10b981; color: #34d399;">Recruiter</span>
                Admin Portal
            </a>
            {% if session.username %}
            <div class="user-badge">
                <div class="user-avatar">{{ session.username[:1].upper() }}</div>
                <span>{{ session.username }}</span>
            </div>
            <a href="{{ url_for('logout') }}" class="nav-link" style="color: #f472b6; font-size: 0.85rem;">Sign out</a>
            {% else %}
            <a href="{{ url_for('login') }}" class="btn btn-secondary btn-sm">Sign In</a>
            {% endif %}
        </div>
    </nav>
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    <footer class="footer no-print">
        <p>&copy; 2026 <strong>InterviewAI Platform</strong> &bull; Complete Single-File Standalone App for VS Code</p>
    </footer>
    {% block scripts %}{% endblock %}
</body>
</html>
"""

TEMPLATES['index.html'] = """{% extends "base.html" %}
{% block content %}
<section class="hero-section">
    <div class="hero-pill">Next-Gen AI Mock Interview & Recruiter Selection</div>
    <h1 class="hero-title">Master Real-World Interviews with <br><span class="hero-gradient">Intelligent AI Simulations</span></h1>
    <p class="hero-subtitle">Adaptive question simulations across Python, Full Stack, Java, and Data Analytics. Real-time speech read-aloud, microphone dictation, and 5-metric AI evaluation.</p>
    <div style="display:flex; justify-content:center; gap:1.2rem; flex-wrap:wrap; margin-bottom:3rem;">
        <a href="{{ url_for('setup') }}" class="btn btn-primary btn-lg">Start Free Mock Interview &rarr;</a>
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary btn-lg">Candidate Dashboard</a>
        <a href="{{ url_for('admin_portal') }}" class="btn btn-secondary btn-lg" style="border-color:#10b981;">Recruiter Admin Portal</a>
    </div>
    <div class="glass-card" style="max-width: 800px; margin: 0 auto; text-align: left;">
        <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--accent-purple); font-weight: 700; margin-bottom: 0.3rem;">Sample Live Evaluation</div>
        <div style="font-size: 1.15rem; font-weight: 600; margin-bottom: 1rem;">"How does memory management and garbage collection work in Python?"</div>
        <div style="background: rgba(10, 12, 34, 0.7); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem; font-size: 0.92rem; color: var(--text-muted);">
            "Python utilizes reference counting and an auxiliary generational garbage collector to identify circular references..."
        </div>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <span class="score-badge score-high">Technical Depth: 9.5/10</span>
            <span class="score-badge score-high">Relevance: 10/10</span>
            <span class="score-badge score-mid">Clarity: 9.0/10</span>
        </div>
    </div>
</section>
{% endblock %}
"""

TEMPLATES['login.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 440px; margin: 3rem auto;">
    <div class="glass-card" style="text-align: center;">
        <h1 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;">Candidate Access</h1>
        <p style="color: var(--text-muted); font-size: 0.92rem; margin-bottom: 1.8rem;">Enter your name to track your mock interview scores and review past AI diagnostics.</p>
        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group" style="margin-bottom: 1.4rem; text-align: left;">
                <label class="form-label" for="username">Your Name / Candidate ID</label>
                <input type="text" name="username" id="username" class="form-control" placeholder="e.g. Alex Johnson" required autofocus>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%;">Enter Platform &rarr;</button>
        </form>
    </div>
</div>
{% endblock %}
"""

TEMPLATES['dashboard.html'] = """{% extends "base.html" %}
{% block content %}
<div class="dash-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem; flex-wrap:wrap; gap:1rem;">
    <div>
        <h1 style="font-size: 2.2rem; font-weight: 700;">Candidate <span class="hero-gradient">Dashboard</span></h1>
        <p style="color: var(--text-muted);">Welcome, {{ session.username }}. Review your performance trajectory and previous reports.</p>
    </div>
    <a href="{{ url_for('setup') }}" class="btn btn-primary btn-lg">New Mock Interview</a>
</div>
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-icon">&#128203;</div>
        <div><div class="stat-value">{{ total }}</div><div class="stat-label">Total Interviews</div></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">&#127919;</div>
        <div><div class="stat-value">{{ avg_score }}%</div><div class="stat-label">Average Score</div></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">&#127942;</div>
        <div><div class="stat-value">{{ best_score }}%</div><div class="stat-label">Highest Score</div></div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">&#11088;</div>
        <div><div class="stat-value" style="color: {{ readiness.color }}; font-size: 1.4rem;">{{ readiness.level }}</div><div class="stat-label">Readiness Level</div></div>
    </div>
</div>
<div class="glass-card" style="margin-bottom: 2rem;">
    <h2 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem;">Score Progress Trajectory</h2>
    <div style="height: 240px;"><canvas id="scoreChart"></canvas></div>
</div>
<div class="glass-card">
    <h2 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 1.2rem;">Interview History</h2>
    {% if interviews %}
    <div style="overflow-x:auto;">
        <table class="custom-table">
            <thead><tr><th>Date</th><th>Role</th><th>Category</th><th>Difficulty</th><th>Score</th><th>Action</th></tr></thead>
            <tbody>
                {% for i in interviews %}
                <tr>
                    <td style="color: var(--text-muted);">{{ i['created_at'][:10] }}</td>
                    <td style="font-weight: 600;">{{ i['role'] }}</td>
                    <td><span class="score-badge score-mid">{{ i['category'] }}</span></td>
                    <td>{{ i['difficulty'] }}</td>
                    <td><span class="score-badge {% if i['score'] >= 80 %}score-high{% else %}score-mid{% endif %}">{{ i['score'] }}%</span></td>
                    <td><a href="{{ url_for('view_report', interview_id=i['id']) }}" class="btn btn-secondary btn-sm">View Report</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p style="text-align: center; color: var(--text-muted); padding: 2rem;">No mock interviews taken yet. <a href="{{ url_for('setup') }}" style="color:#c084fc;">Take your first one now &rarr;</a></p>
    {% endif %}
</div>
{% endblock %}
{% block scripts %}
<script>
    const ctx = document.getElementById('scoreChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: [{% for i in interviews|reverse %}"S{{ loop.index }}",{% endfor %}],
                datasets: [{
                    label: 'Score %',
                    data: [{% for i in interviews|reverse %}{{ i['score'] or 0 }},{% endfor %}],
                    borderColor: '#a855f7', backgroundColor: 'rgba(168, 85, 247, 0.15)',
                    fill: true, tension: 0.35, borderWidth: 3
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }
</script>
{% endblock %}
"""

TEMPLATES['setup.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 800px; margin: 0 auto;">
    <h1 style="font-size: 2.2rem; font-weight: 800; text-align: center; margin-bottom: 0.5rem;">Configure Mock Interview</h1>
    <p style="text-align: center; color: var(--text-muted); margin-bottom: 2rem;">Choose your target role, difficulty, and interview track.</p>
    <div class="glass-card" style="margin-bottom: 1.5rem; padding: 1.2rem;">
        <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: var(--accent-cyan); margin-bottom: 0.6rem;">Quick Start Presets</div>
        <div class="presets-container">
            <button type="button" class="preset-chip" onclick="applyPreset('Python Developer', 'Technical', 'Intermediate', 5)">🐍 Python Dev (5 Qs)</button>
            <button type="button" class="preset-chip" onclick="applyPreset('Web Developer', 'Technical', 'Intermediate', 5)">⚛️ Web Dev (5 Qs)</button>
            <button type="button" class="preset-chip" onclick="applyPreset('Java Developer', 'Technical', 'Advanced', 5)">☕ Java Microservices (5 Qs)</button>
            <button type="button" class="preset-chip" onclick="applyPreset('Data Analyst', 'Technical', 'Beginner', 5)">📊 Data Analyst (5 Qs)</button>
            <button type="button" class="preset-chip" onclick="applyPreset('Python Developer', 'Behavioral', 'Intermediate', 3)">🤝 Behavioral STAR (3 Qs)</button>
        </div>
    </div>
    <div class="glass-card">
        <form method="POST" action="{{ url_for('setup') }}">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label" for="role">Target Role</label>
                    <select name="role" id="role" class="form-control" required>
                        <option value="Python Developer">Python Developer</option>
                        <option value="Web Developer">Web Developer (Full Stack)</option>
                        <option value="Java Developer">Java Developer</option>
                        <option value="Data Analyst">Data Analyst</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="category">Track</label>
                    <select name="category" id="category" class="form-control" required>
                        <option value="Technical">Technical Round</option>
                        <option value="Behavioral">Behavioral (STAR Method)</option>
                        <option value="HR">HR Culture & Leadership</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="difficulty">Difficulty</label>
                    <select name="difficulty" id="difficulty" class="form-control" required>
                        <option value="Beginner">Beginner</option>
                        <option value="Intermediate" selected>Intermediate</option>
                        <option value="Advanced">Advanced</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="num_questions">Questions</label>
                    <select name="num_questions" id="num_questions" class="form-control" required>
                        <option value="3">3 Questions (~5 mins)</option>
                        <option value="5" selected>5 Questions (~15 mins)</option>
                        <option value="10">10 Questions (~30 mins)</option>
                    </select>
                </div>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:1rem;">
                <button type="submit" class="btn btn-primary btn-lg">Begin Interview &rarr;</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    function applyPreset(r, c, d, q) {
        document.getElementById('role').value = r;
        document.getElementById('category').value = c;
        document.getElementById('difficulty').value = d;
        document.getElementById('num_questions').value = q;
    }
</script>
{% endblock %}
"""

TEMPLATES['interview.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 880px; margin: 0 auto;">
    <div class="interview-header">
        <div>
            <span class="score-badge score-mid">{{ interview_data.role }} &bull; {{ interview_data.difficulty }}</span>
            <h2 style="font-size: 1.5rem; font-weight: 700; margin-top: 0.3rem;">Question {{ q_num }} of {{ total_q }}</h2>
        </div>
        <div class="timer-box">
            <span>&#9201;</span>
            <span id="timerText">03:00</span>
        </div>
    </div>
    <div class="progress-track"><div class="progress-bar-fill" style="width: {{ progress }}%;"></div></div>
    <div class="question-box">
        <div style="font-size: 0.75rem; text-transform: uppercase; color: #c084fc; font-weight: 700; margin-bottom: 0.5rem;">Interviewer Question</div>
        <div class="question-text" id="questionText">{{ question }}</div>
        <div style="display: flex; gap: 0.75rem; margin-top: 1rem;">
            <button type="button" class="btn-icon" onclick="speakQuestion()">&#128266; Read Aloud (TTS)</button>
            <button type="button" class="btn-icon" id="micBtn" onclick="toggleVoiceInput()">&#127908; <span id="micLabel">Voice Dictation</span></button>
            <button type="button" class="btn-icon" style="margin-left:auto;" onclick="insertDemoAnswer()">&#9889; Demo Answer Auto-Fill</button>
        </div>
    </div>
    <div class="glass-card">
        <form method="POST" action="{{ url_for('interview') }}" id="answerForm">
            <label style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.6rem; display: block;">Your Response</label>
            <textarea name="answer" id="answerInput" class="answer-area" placeholder="Type response here or use 'Voice Dictation' to speak..." required oninput="updateWordCount()"></textarea>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem; flex-wrap:wrap; gap:1rem;">
                <span id="wordCountBadge" style="font-size:0.85rem; color:var(--text-dim);">0 words (Recommended: 60-150 words)</span>
                <button type="submit" class="btn btn-primary btn-lg" id="submitBtn">Submit Answer &amp; Evaluate &rarr;</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    function updateWordCount() {
        const text = document.getElementById('answerInput').value.trim();
        const words = text ? text.split(/\\s+/).length : 0;
        document.getElementById('wordCountBadge').innerText = `${words} words (Recommended: 60-150 words)`;
    }
    function insertDemoAnswer() {
        document.getElementById('answerInput').value = "In my previous engineering projects, we prioritized clean architecture and performance profiling. We measured execution bottlenecks using telemetry and minimized memory overhead by utilizing lazy evaluation and decoupled service interfaces. This improved system throughput by 35% and drastically reduced regression bugs.";
        updateWordCount();
    }
    function speakQuestion() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(document.getElementById('questionText').innerText);
            u.rate = 0.95;
            window.speechSynthesis.speak(u);
        }
    }
    let recognition = null, isRecording = false;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = true; recognition.interimResults = true;
        recognition.onresult = function(e) {
            let res = '';
            for (let i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) res += e.results[i][0].transcript + ' ';
            }
            if (res) { document.getElementById('answerInput').value += res; updateWordCount(); }
        };
    }
    function toggleVoiceInput() {
        if (!recognition) { alert("Speech recognition not supported in this browser."); return; }
        if (!isRecording) {
            recognition.start(); isRecording = true;
            document.getElementById('micBtn').classList.add('recording');
            document.getElementById('micLabel').innerText = "Listening...";
        } else {
            recognition.stop(); isRecording = false;
            document.getElementById('micBtn').classList.remove('recording');
            document.getElementById('micLabel').innerText = "Voice Dictation";
        }
    }
    let sec = 180;
    setInterval(function() {
        if (sec > 0) {
            sec--;
            const m = Math.floor(sec / 60), s = sec % 60;
            document.getElementById('timerText').innerText = `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }
    }, 1000);
</script>
{% endblock %}
"""

TEMPLATES['feedback.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 900px; margin: 0 auto;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
        <div>
            <span class="score-badge score-mid">{{ interview_data.role }}</span>
            <h1 style="font-size: 2rem; font-weight: 700; margin-top: 0.3rem;">AI Evaluation &bull; Question {{ feedback.question_index }}</h1>
        </div>
        <a href="{% if is_last %}{{ url_for('results') }}{% else %}{{ url_for('interview') }}{% endif %}" class="btn btn-primary btn-lg">
            {% if is_last %}View Final Scorecard &rarr;{% else %}Next Question &rarr;{% endif %}
        </a>
    </div>
    <div class="score-banner">
        <div>
            <h2 style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.3rem;">
                {% if feedback.eval.score >= 8.5 %}Outstanding Response! 🌟{% elif feedback.eval.score >= 7.0 %}Solid Technical Answer 👍{% else %}Good Baseline Attempt 🚀{% endif %}
            </h2>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Evaluated against industry technical rubrics for {{ interview_data.role }}.</p>
        </div>
        <div class="score-circle">
            <span class="score-number">{{ feedback.eval.score }}</span>
            <span style="font-size: 0.75rem;">OUT OF 10</span>
        </div>
    </div>
    <div class="metrics-row">
        <div class="metric-pill">
            <div class="metric-pill-header"><span>Relevance</span><strong>{{ feedback.eval.relevance_score }}/10</strong></div>
            <div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ feedback.eval.relevance_score * 10 }}%; background:var(--accent-purple);"></div></div>
        </div>
        <div class="metric-pill">
            <div class="metric-pill-header"><span>Technical</span><strong>{{ feedback.eval.technical_score }}/10</strong></div>
            <div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ feedback.eval.technical_score * 10 }}%; background:var(--accent-cyan);"></div></div>
        </div>
        <div class="metric-pill">
            <div class="metric-pill-header"><span>Clarity</span><strong>{{ feedback.eval.clarity_score }}/10</strong></div>
            <div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ feedback.eval.clarity_score * 10 }}%; background:#a855f7;"></div></div>
        </div>
        <div class="metric-pill">
            <div class="metric-pill-header"><span>Completeness</span><strong>{{ feedback.eval.completeness_score }}/10</strong></div>
            <div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ feedback.eval.completeness_score * 10 }}%; background:#f59e0b;"></div></div>
        </div>
        <div class="metric-pill">
            <div class="metric-pill-header"><span>Grammar</span><strong>{{ feedback.eval.grammar_score }}/10</strong></div>
            <div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ feedback.eval.grammar_score * 10 }}%; background:#10b981;"></div></div>
        </div>
    </div>
    <div class="feedback-grid">
        <div class="feedback-card-green">
            <strong style="color: #34d399; font-size: 1.05rem;">Key Strengths</strong>
            <ul class="feedback-list">{% for s in feedback.eval.strengths %}<li>&bull; {{ s }}</li>{% endfor %}</ul>
        </div>
        <div class="feedback-card-amber">
            <strong style="color: #fbbf24; font-size: 1.05rem;">Areas for Improvement</strong>
            <ul class="feedback-list">{% for imp in feedback.eval.improvements %}<li>&bull; {{ imp }}</li>{% endfor %}</ul>
        </div>
    </div>
    <div class="suggested-box">
        <div style="font-weight: 700; color: #c084fc; margin-bottom: 0.5rem;">AI Ideal Response Framework</div>
        <p style="font-size: 0.95rem; color: #e2e8f0;">{{ feedback.eval.suggested_answer }}</p>
    </div>
    <div style="text-align: right;">
        <a href="{% if is_last %}{{ url_for('results') }}{% else %}{{ url_for('interview') }}{% endif %}" class="btn btn-primary btn-lg">
            {% if is_last %}View Complete Report &rarr;{% else %}Next Question &rarr;{% endif %}
        </a>
    </div>
</div>
{% endblock %}
"""

TEMPLATES['results.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 950px; margin: 0 auto;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;" class="no-print">
        <a href="{{ url_for('dashboard') }}" class="btn btn-secondary btn-sm">&larr; Dashboard</a>
        <div style="display:flex; gap:0.8rem;">
            <button onclick="window.print()" class="btn btn-secondary">&#128438; Print / Save PDF</button>
            <a href="{{ url_for('setup') }}" class="btn btn-primary">Retake Interview</a>
        </div>
    </div>
    <div class="glass-card" style="text-align: center; margin-bottom: 2rem;">
        <div class="score-badge score-high" style="font-size: 1.1rem; margin-bottom: 1rem;">
            {% if report.overall_score >= 85 %}Tier-1 Ready (A+){% elif report.overall_score >= 70 %}Proficient (B+){% else %}Needs Focus (C){% endif %}
        </div>
        <h1 style="font-size: 2.6rem; font-weight: 800; margin-bottom: 0.5rem;">Final Performance Scorecard</h1>
        <p style="color: var(--text-muted); margin-bottom: 2rem;">{{ report.role }} &bull; {{ report.category }} ({{ report.difficulty }}) &bull; {{ report.date }}</p>
        <div style="display:inline-flex; flex-direction:column; align-items:center; justify-content:center; width:140px; height:140px; border-radius:50%; background:var(--gradient-btn); margin-bottom:1.5rem;">
            <span style="font-size: 3rem; font-weight: 800; line-height: 1;">{{ report.overall_score }}</span>
            <span style="font-size: 0.8rem; text-transform: uppercase;">OUT OF 100</span>
        </div>
        <p style="max-width: 650px; margin: 0 auto; color: #cbd5e1;">{{ report.summary }}</p>
    </div>
    <div style="display: grid; grid-template-columns: 1.2fr 1.8fr; gap: 1.5rem; margin-bottom: 2rem;">
        <div class="glass-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem;">Competency Radar</h3>
            <div style="width: 100%; height: 250px;"><canvas id="radarChart"></canvas></div>
        </div>
        <div class="glass-card" style="display: flex; flex-direction: column; justify-content: space-around;">
            <h3 style="font-size: 1.1rem; font-weight: 700;">Skill Breakdown</h3>
            <div><div>Relevance: <strong>{{ report.rel_avg }}/10</strong></div><div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ report.rel_avg*10 }}%; background:var(--accent-purple);"></div></div></div>
            <div><div>Technical Depth: <strong>{{ report.tech_avg }}/10</strong></div><div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ report.tech_avg*10 }}%; background:var(--accent-cyan);"></div></div></div>
            <div><div>Communication: <strong>{{ report.clar_avg }}/10</strong></div><div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ report.clar_avg*10 }}%; background:#a855f7;"></div></div></div>
            <div><div>Completeness: <strong>{{ report.comp_avg }}/10</strong></div><div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ report.comp_avg*10 }}%; background:#f59e0b;"></div></div></div>
            <div><div>Grammar: <strong>{{ report.gram_avg }}/10</strong></div><div class="metric-pill-bar"><div class="metric-pill-fill" style="width:{{ report.gram_avg*10 }}%; background:#10b981;"></div></div></div>
        </div>
    </div>
    <div class="glass-card">
        <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 1.2rem;">Question Diagnostics</h2>
        {% for a in report.answers %}
        <div class="qa-accordion-item">
            <div class="qa-header">
                <strong>Q{{ a.question_index }}: {{ a.question }}</strong>
                <span class="score-badge score-mid">{{ a.eval.score }} / 10</span>
            </div>
            <div class="qa-body">
                <div style="margin-bottom: 0.8rem; color: #e2e8f0;"><strong>Your Answer:</strong> {{ a.answer }}</div>
                <div style="color: #c084fc; font-size: 0.9rem;"><strong>Model Structure:</strong> {{ a.eval.suggested_answer }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    const rCtx = document.getElementById('radarChart');
    if (rCtx) {
        new Chart(rCtx, {
            type: 'radar',
            data: {
                labels: ['Relevance', 'Technical', 'Clarity', 'Completeness', 'Grammar'],
                datasets: [{
                    data: [{{ report.rel_avg }}, {{ report.tech_avg }}, {{ report.clar_avg }}, {{ report.comp_avg }}, {{ report.gram_avg }}],
                    backgroundColor: 'rgba(124, 58, 237, 0.35)', borderColor: '#c084fc', borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { r: { min: 0, max: 10 } } }
        });
    }
</script>
{% endblock %}
"""

TEMPLATES['admin_dashboard.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 1200px; margin: 0 auto;">
    <div class="dash-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem; flex-wrap:wrap; gap:1rem;">
        <div>
            <span class="badge-ai" style="background:rgba(16,185,129,0.25); border-color:#10b981; color:#34d399;">Recruitment Portal</span>
            <h1 style="font-size: 2.2rem; font-weight: 700; margin-top: 0.3rem;">Candidate Selection <span class="hero-gradient">Cockpit</span></h1>
            <p style="color: var(--text-muted);">Review candidates, examine AI diagnostic scores, and set hiring decisions.</p>
        </div>
        <div style="display:flex; gap:0.8rem; flex-wrap:wrap;">
            <a href="{{ url_for('admin_seed_candidates') }}" class="btn btn-secondary btn-sm">&#9889; Seed Demo Applicants</a>
            <a href="{{ url_for('admin_export_csv') }}" class="btn btn-secondary btn-sm">&#128196; Export CSV Report</a>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card"><div><div class="stat-value">{{ total }}</div><div class="stat-label">Total Applicants</div></div></div>
        <div class="stat-card"><div><div class="stat-value" style="color:#34d399;">{{ selected }}</div><div class="stat-label">Selected / Shortlisted</div></div></div>
        <div class="stat-card"><div><div class="stat-value" style="color:#fbbf24;">{{ under_review }}</div><div class="stat-label">Under Review</div></div></div>
        <div class="stat-card"><div><div class="stat-value" style="color:#f87171;">{{ rejected }}</div><div class="stat-label">Rejected</div></div></div>
        <div class="stat-card"><div><div class="stat-value">{{ avg_score }}%</div><div class="stat-label">Average Score</div></div></div>
    </div>
    <div class="glass-card" style="padding: 1.25rem; margin-bottom: 2rem;">
        <form method="GET" action="{{ url_for('admin_portal') }}" style="display:flex; gap:1rem; flex-wrap:wrap; align-items:flex-end;">
            <div style="flex:2; min-width:200px;">
                <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.3rem;">Search Candidate</label>
                <input type="text" name="search" value="{{ search_query }}" class="form-control" placeholder="Search by name or role...">
            </div>
            <div style="flex:1; min-width:150px;">
                <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.3rem;">Status</label>
                <select name="status" class="form-control">
                    <option value="All">All Statuses</option>
                    <option value="Selected" {% if current_status == 'Selected' %}selected{% endif %}>Selected</option>
                    <option value="Shortlisted" {% if current_status == 'Shortlisted' %}selected{% endif %}>Shortlisted</option>
                    <option value="Under Review" {% if current_status == 'Under Review' %}selected{% endif %}>Under Review</option>
                    <option value="Rejected" {% if current_status == 'Rejected' %}selected{% endif %}>Rejected</option>
                </select>
            </div>
            <div>
                <button type="submit" class="btn btn-primary" style="padding:0.65rem 1.4rem;">Filter</button>
                <a href="{{ url_for('admin_portal') }}" class="btn btn-secondary" style="padding:0.65rem 1rem;">Reset</a>
            </div>
        </form>
    </div>
    <div class="glass-card">
        <table class="custom-table">
            <thead>
                <tr><th>Candidate</th><th>Role</th><th>AI Score</th><th>Status Decision</th><th>Remarks</th><th>Action</th></tr>
            </thead>
            <tbody>
                {% for c in candidates %}
                <tr>
                    <td><strong>{{ c['username'] }}</strong><div style="font-size:0.75rem; color:var(--text-dim);">#{{ c['id'] }} &bull; {{ c['created_at'][:10] }}</div></td>
                    <td>{{ c['role'] }}</td>
                    <td><span class="score-badge {% if c['score'] >= 80 %}score-high{% else %}score-mid{% endif %}">{{ c['score'] }}%</span></td>
                    <td>
                        <form method="POST" action="{{ url_for('admin_update_status', interview_id=c['id']) }}" style="margin:0;">
                            <input type="hidden" name="admin_notes" value="{{ c['admin_notes'] or '' }}">
                            <select name="selection_status" onchange="this.form.submit()" class="form-control" style="padding:0.3rem 0.6rem; font-size:0.82rem;">
                                <option value="Under Review" {% if c['selection_status'] == 'Under Review' %}selected{% endif %}>🟡 Under Review</option>
                                <option value="Shortlisted" {% if c['selection_status'] == 'Shortlisted' %}selected{% endif %}>🟢 Shortlisted</option>
                                <option value="Selected" {% if c['selection_status'] == 'Selected' %}selected{% endif %}>🟣 Selected</option>
                                <option value="Rejected" {% if c['selection_status'] == 'Rejected' %}selected{% endif %}>🔴 Rejected</option>
                            </select>
                        </form>
                    </td>
                    <td style="max-width:180px; font-size:0.82rem; color:var(--text-muted); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ c['admin_notes'] or 'No remarks' }}</td>
                    <td><a href="{{ url_for('admin_candidate_detail', interview_id=c['id']) }}" class="btn btn-secondary btn-sm">Dossier &rarr;</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""

TEMPLATES['admin_candidate_detail.html'] = """{% extends "base.html" %}
{% block content %}
<div style="max-width: 1050px; margin: 0 auto;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
        <a href="{{ url_for('admin_portal') }}" class="btn btn-secondary btn-sm">&larr; Back to Selection Roster</a>
        <a href="{{ url_for('view_report', interview_id=candidate.id) }}" target="_blank" class="btn btn-secondary btn-sm">Open Printable Report</a>
    </div>
    <div style="display: grid; grid-template-columns: 1.2fr 1.8fr; gap: 1.5rem; margin-bottom: 2rem;">
        <div class="glass-card">
            <h1 style="font-size: 1.6rem; font-weight: 800; margin-bottom: 0.5rem;">{{ candidate.username }}</h1>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">{{ candidate.role }} &bull; {{ candidate.category }} ({{ candidate.difficulty }})</p>
            <div style="text-align: center; padding: 1.5rem; background: rgba(10, 12, 34, 0.7); border-radius: var(--radius-md);">
                <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--accent-purple);">Evaluation Score</div>
                <div style="font-size: 3rem; font-weight: 800; color: #fff;">{{ candidate.score }} <span style="font-size: 1.2rem; color: var(--text-dim);">/ 100</span></div>
            </div>
        </div>
        <div class="glass-card" style="border-top: 3px solid var(--accent-purple);">
            <h2 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 1rem;">Hiring Decision &amp; Feedback</h2>
            <form method="POST" action="{{ url_for('admin_update_status', interview_id=candidate.id) }}">
                <input type="hidden" name="redirect_to" value="candidate">
                <div class="form-group" style="margin-bottom: 1rem;">
                    <label class="form-label">Selection Status</label>
                    <select name="selection_status" class="form-control">
                        <option value="Selected" {% if candidate.selection_status == 'Selected' %}selected{% endif %}>🟣 Selected &bull; Extend Offer</option>
                        <option value="Shortlisted" {% if candidate.selection_status == 'Shortlisted' %}selected{% endif %}>🟢 Shortlisted &bull; Next Round</option>
                        <option value="Under Review" {% if candidate.selection_status == 'Under Review' %}selected{% endif %}>🟡 Under Review</option>
                        <option value="Rejected" {% if candidate.selection_status == 'Rejected' %}selected{% endif %}>🔴 Rejected</option>
                    </select>
                </div>
                <div class="form-group" style="margin-bottom: 1.2rem;">
                    <label class="form-label">Recruiter Remarks</label>
                    <textarea name="admin_notes" rows="4" class="form-control" placeholder="Add assessment notes...">{{ candidate.admin_notes or '' }}</textarea>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">Save Hiring Decision</button>
            </form>
        </div>
    </div>
    <div class="glass-card">
        <h2 style="font-size: 1.35rem; font-weight: 700; margin-bottom: 1.2rem;">Candidate Interview Transcript</h2>
        {% for a in answers %}
        <div class="qa-accordion-item">
            <div class="qa-header"><strong>Q{{ a.question_index }}: {{ a.question }}</strong><span class="score-badge score-mid">{{ a.score }}/10</span></div>
            <div class="qa-body">
                <div style="margin-bottom: 0.8rem;"><strong>Candidate Answer:</strong> {{ a.answer }}</div>
                <div style="color: #34d399; font-size: 0.88rem;"><strong>Strengths:</strong> {{ a.strengths|join(', ') }}</div>
                <div style="color: #fbbf24; font-size: 0.88rem;"><strong>Improvements:</strong> {{ a.improvements|join(', ') }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""

# Attach Jinja DictLoader so render_template loads templates directly from memory
app.jinja_loader = DictLoader(TEMPLATES)

# ==========================================
# FLASK ROUTES
# ==========================================

@app.before_request
def ensure_user():
    init_db()
    if 'user_id' not in session:
        user = get_or_create_demo_user()
        session['user_id'] = user['id']
        session['username'] = user['username']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip() or "Candidate"
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if not user:
            db.execute('INSERT INTO users (username) VALUES (?)', (username,))
            db.commit()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    db = get_db()
    interviews = db.execute('SELECT * FROM interviews WHERE user_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    total_interviews = len(interviews)
    avg_score = 0
    best_score = 0
    if total_interviews > 0:
        scores = [i['score'] for i in interviews if i['score'] is not None]
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)
            best_score = max(scores)
            
    if avg_score >= 85:
        readiness = {"level": "Senior Ready", "color": "#10b981"}
    elif avg_score >= 70:
        readiness = {"level": "Proficient", "color": "#6366f1"}
    else:
        readiness = {"level": "Developing", "color": "#f59e0b"}

    return render_template('dashboard.html', interviews=interviews, total=total_interviews, avg_score=avg_score, best_score=best_score, readiness=readiness)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        role = request.form.get('role', 'Python Developer')
        category = request.form.get('category', 'Technical')
        difficulty = request.form.get('difficulty', 'Intermediate')
        num_questions = int(request.form.get('num_questions', 5))
        questions = get_questions_for_interview(role, category, difficulty, num_questions)
        session['current_interview'] = {
            'role': role, 'category': category, 'difficulty': difficulty,
            'total_questions': num_questions, 'questions': questions,
            'current_index': 0, 'answers': []
        }
        return redirect(url_for('interview'))
    return render_template('setup.html')

@app.route('/interview', methods=['GET', 'POST'])
def interview():
    data = session.get('current_interview')
    if not data:
        return redirect(url_for('setup'))
    curr_idx = data['current_index']
    total_q = data['total_questions']
    if curr_idx >= total_q:
        return redirect(url_for('results'))
    question = data['questions'][curr_idx]
    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        eval_result = evaluate_candidate_answer(question, user_answer, data['role'], data['difficulty'])
        record = {
            'question_index': curr_idx + 1, 'question': question,
            'answer': user_answer, 'eval': eval_result
        }
        data['answers'].append(record)
        data['current_index'] = curr_idx + 1
        session['current_interview'] = data
        session['last_feedback'] = record
        return redirect(url_for('feedback'))
    progress_pct = int(((curr_idx) / total_q) * 100)
    return render_template('interview.html', question=question, q_num=curr_idx + 1, total_q=total_q, progress=progress_pct, interview_data=data)

@app.route('/feedback')
def feedback():
    last_fb = session.get('last_feedback')
    data = session.get('current_interview')
    if not last_fb or not data:
        return redirect(url_for('interview'))
    is_last = (data['current_index'] >= data['total_questions'])
    return render_template('feedback.html', feedback=last_fb, interview_data=data, is_last=is_last)

@app.route('/results')
def results():
    data = session.get('current_interview')
    if not data or not data.get('answers'):
        return redirect(url_for('dashboard'))
    answers = data['answers']
    total_q = len(answers)
    scores = [a['eval']['score'] for a in answers]
    avg_score_10 = sum(scores) / total_q
    overall_score_100 = int(avg_score_10 * 10)
    rel_avg = round(sum(a['eval']['relevance_score'] for a in answers) / total_q, 1)
    tech_avg = round(sum(a['eval']['technical_score'] for a in answers) / total_q, 1)
    clar_avg = round(sum(a['eval']['clarity_score'] for a in answers) / total_q, 1)
    comp_avg = round(sum(a['eval']['completeness_score'] for a in answers) / total_q, 1)
    gram_avg = round(sum(a['eval']['grammar_score'] for a in answers) / total_q, 1)
    summary = f"Solid interview performance for {data['role']}. You demonstrated commanding domain mastery and structured articulation."
    db = get_db()
    cur = db.execute('''
        INSERT INTO interviews (user_id, role, category, difficulty, total_questions, score, duration_minutes, performance_summary)
        VALUES (?, ?, ?, ?, ?, ?, 15, ?)
    ''', (session['user_id'], data['role'], data['category'], data['difficulty'], total_q, overall_score_100, summary))
    interview_id = cur.lastrowid
    for a in answers:
        ev = a['eval']
        db.execute('''
            INSERT INTO answers (interview_id, question_index, question, answer, score, relevance_score, technical_score, clarity_score, completeness_score, grammar_score, strengths, improvements, suggested_answer, tips)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (interview_id, a['question_index'], a['question'], a['answer'], int(ev['score']), ev['relevance_score'], ev['technical_score'], ev['clarity_score'], ev['completeness_score'], ev['grammar_score'], json.dumps(ev['strengths']), json.dumps(ev['improvements']), ev['suggested_answer'], ev['tips']))
    db.commit()
    report = {
        'id': interview_id, 'role': data['role'], 'category': data['category'], 'difficulty': data['difficulty'],
        'overall_score': overall_score_100, 'rel_avg': rel_avg, 'tech_avg': tech_avg, 'clar_avg': clar_avg,
        'comp_avg': comp_avg, 'gram_avg': gram_avg, 'summary': summary, 'answers': answers,
        'date': datetime.datetime.now().strftime("%B %d, %Y")
    }
    session.pop('current_interview', None)
    session.pop('last_feedback', None)
    return render_template('results.html', report=report)

@app.route('/report/<int:interview_id>')
def view_report(interview_id):
    db = get_db()
    interview = db.execute('SELECT * FROM interviews WHERE id = ?', (interview_id,)).fetchone()
    if not interview:
        return redirect(url_for('dashboard'))
    db_answers = db.execute('SELECT * FROM answers WHERE interview_id = ? ORDER BY question_index ASC', (interview_id,)).fetchall()
    answers = []
    rel_scores, tech_scores, clar_scores, comp_scores, gram_scores = [], [], [], [], []
    for r in db_answers:
        rel_scores.append(r['relevance_score'] or 7)
        tech_scores.append(r['technical_score'] or 7)
        clar_scores.append(r['clarity_score'] or 7)
        comp_scores.append(r['completeness_score'] or 7)
        gram_scores.append(r['grammar_score'] or 8)
        answers.append({
            'question_index': r['question_index'], 'question': r['question'], 'answer': r['answer'],
            'eval': {
                'score': r['score'], 'suggested_answer': r['suggested_answer'],
                'strengths': json.loads(r['strengths']) if r['strengths'] else [],
                'improvements': json.loads(r['improvements']) if r['improvements'] else []
            }
        })
    cnt = max(len(answers), 1)
    report = {
        'id': interview['id'], 'role': interview['role'], 'category': interview['category'], 'difficulty': interview['difficulty'],
        'overall_score': interview['score'], 'rel_avg': round(sum(rel_scores)/cnt, 1), 'tech_avg': round(sum(tech_scores)/cnt, 1),
        'clar_avg': round(sum(clar_scores)/cnt, 1), 'comp_avg': round(sum(comp_scores)/cnt, 1), 'gram_avg': round(sum(gram_scores)/cnt, 1),
        'summary': interview['performance_summary'], 'answers': answers, 'date': interview['created_at']
    }
    return render_template('results.html', report=report)

# ==========================================
# ADMIN SELECTION PORTAL
# ==========================================

@app.route('/admin')
def admin_portal():
    db = get_db()
    status_filter = request.args.get('status', 'All')
    search_query = request.args.get('search', '').strip()
    query = 'SELECT interviews.*, users.username FROM interviews JOIN users ON interviews.user_id = users.id WHERE 1=1'
    params = []
    if status_filter != 'All':
        query += ' AND interviews.selection_status = ?'
        params.append(status_filter)
    if search_query:
        query += ' AND (users.username LIKE ? OR interviews.role LIKE ?)'
        params.append(f'%{search_query}%')
        params.append(f'%{search_query}%')
    query += ' ORDER BY interviews.score DESC'
    candidates = db.execute(query, params).fetchall()
    all_interviews = db.execute('SELECT * FROM interviews').fetchall()
    total_candidates = len(all_interviews)
    selected_count = sum(1 for i in all_interviews if (i['selection_status'] or '') in ['Selected', 'Shortlisted'])
    under_review_count = sum(1 for i in all_interviews if (i['selection_status'] or 'Under Review') == 'Under Review')
    rejected_count = sum(1 for i in all_interviews if (i['selection_status'] or '') == 'Rejected')
    scores = [i['score'] for i in all_interviews if i['score'] is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    return render_template('admin_dashboard.html', candidates=candidates, total=total_candidates, selected=selected_count, under_review=under_review_count, rejected=rejected_count, avg_score=avg_score, current_status=status_filter, search_query=search_query)

@app.route('/admin/candidate/<int:interview_id>')
def admin_candidate_detail(interview_id):
    db = get_db()
    interview = db.execute('SELECT interviews.*, users.username FROM interviews JOIN users ON interviews.user_id = users.id WHERE interviews.id = ?', (interview_id,)).fetchone()
    if not interview:
        return redirect(url_for('admin_portal'))
    answers_rows = db.execute('SELECT * FROM answers WHERE interview_id = ? ORDER BY question_index ASC', (interview_id,)).fetchall()
    answers = []
    for r in answers_rows:
        answers.append({
            'question_index': r['question_index'], 'question': r['question'], 'answer': r['answer'], 'score': r['score'],
            'strengths': json.loads(r['strengths']) if r['strengths'] else [],
            'improvements': json.loads(r['improvements']) if r['improvements'] else []
        })
    return render_template('admin_candidate_detail.html', candidate=interview, answers=answers)

@app.route('/admin/update-status/<int:interview_id>', methods=['POST'])
def admin_update_status(interview_id):
    new_status = request.form.get('selection_status', 'Under Review')
    notes = request.form.get('admin_notes', '')
    db = get_db()
    db.execute('UPDATE interviews SET selection_status = ?, admin_notes = ? WHERE id = ?', (new_status, notes, interview_id))
    db.commit()
    if request.form.get('redirect_to') == 'candidate':
        return redirect(url_for('admin_candidate_detail', interview_id=interview_id))
    return redirect(url_for('admin_portal'))

@app.route('/admin/export-csv')
def admin_export_csv():
    db = get_db()
    candidates = db.execute('SELECT interviews.id, users.username, interviews.role, interviews.score, interviews.selection_status, interviews.admin_notes, interviews.created_at FROM interviews JOIN users ON interviews.user_id = users.id ORDER BY interviews.score DESC').fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Candidate Name', 'Target Role', 'Score (%)', 'Status', 'Notes', 'Date'])
    for c in candidates:
        writer.writerow([c['id'], c['username'], c['role'], c['score'], c['selection_status'] or 'Under Review', c['admin_notes'] or '', c['created_at']])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=Candidate_Selection.csv"})

@app.route('/admin/seed-candidates')
def admin_seed_candidates():
    db = get_db()
    demo_data = [
        ('Sophia Chen', 'Python Developer', 'Technical', 'Advanced', 94, 'Selected', 'Exceptional depth in asyncio, distributed caching, and GIL internals.'),
        ('Liam Davis', 'Web Developer', 'Technical', 'Intermediate', 82, 'Shortlisted', 'Strong React Virtual DOM and web performance knowledge.'),
        ('Marcus Patel', 'Java Developer', 'Technical', 'Intermediate', 68, 'Under Review', 'Solid OOP fundamentals; needs further assessment on microservices.'),
        ('Elena Rostova', 'Data Analyst', 'Technical', 'Advanced', 91, 'Selected', 'Commanding mastery of SQL window functions and A/B test design.'),
        ('Aiden Taylor', 'Python Developer', 'Behavioral', 'Intermediate', 58, 'Rejected', 'Answers lacked STAR methodology structure.')
    ]
    for name, role, cat, diff, score, status, notes in demo_data:
        user = db.execute('SELECT * FROM users WHERE username = ?', (name,)).fetchone()
        if not user:
            db.execute('INSERT INTO users (username) VALUES (?)', (name,))
            db.commit()
            user = db.execute('SELECT * FROM users WHERE username = ?', (name,)).fetchone()
        db.execute('''
            INSERT INTO interviews (user_id, role, category, difficulty, total_questions, score, duration_minutes, performance_summary, selection_status, admin_notes, created_at)
            VALUES (?, ?, ?, ?, 5, ?, 15, ?, ?, ?, datetime('now', '-' || (abs(random()) % 10) || ' days'))
        ''', (user['id'], role, cat, diff, score, f"Evaluated for {role}.", status, notes))
    db.commit()
    return redirect(url_for('admin_portal'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "InterviewAI Single File Edition"})

# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        init_db()
        db = get_db()
        cnt = db.execute('SELECT COUNT(*) as c FROM interviews').fetchone()['c']
        if cnt == 0:
            user = get_or_create_demo_user()
            cur = db.execute('''
                INSERT INTO interviews (user_id, role, category, difficulty, total_questions, score, performance_summary, selection_status, admin_notes)
                VALUES (?, 'Python Developer', 'Technical', 'Intermediate', 3, 88, 'Strong technical fluency with clear architectural structuring.', 'Shortlisted', 'Strong candidate for Tier-1 engineering.')
            ''', (user['id'],))
            i_id = cur.lastrowid
            sample_answers = [
                ("Explain the Global Interpreter Lock (GIL) in CPython and how it impacts multithreaded applications.", "The GIL is a mutex in CPython that protects access to Python objects, preventing multiple threads from executing Python bytecode simultaneously. For I/O tasks multithreading works well, but for CPU-bound tasks multiprocessing is required.", 9),
                ("How do Python generators and yield optimize memory?", "Generators produce items on-demand using lazy evaluation instead of loading entire sequences into memory, keeping space complexity at O(1).", 9),
                ("Compare asyncio with multithreading and multiprocessing.", "Asyncio uses a single-threaded cooperative multitasking event loop ideal for high-concurrency network I/O, while multiprocessing leverages multiple CPU cores.", 8)
            ]
            for idx, (q, a, s) in enumerate(sample_answers, 1):
                db.execute('''
                    INSERT INTO answers (interview_id, question_index, question, answer, score, relevance_score, technical_score, clarity_score, completeness_score, grammar_score, strengths, improvements, suggested_answer, tips)
                    VALUES (?, ?, ?, ?, ?, 9, 9, 9, 8, 9, '["Clear distinction", "Accurate technical depth"]', '["Add code syntax snippet"]', 'Define concept -> Discuss trade-offs -> Cite real example', 'Use STAR method')
                ''', (i_id, idx, q, a, s))
            db.commit()
            
    print("\n=======================================================")
    print(" InterviewAI Platform is running!")
    print(" Local URL:    http://127.0.0.1:5000")
    print(" Admin Portal: http://127.0.0.1:5000/admin")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=False)