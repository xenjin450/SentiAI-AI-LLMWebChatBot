import os
import json
import sqlite3
import inspect
from flask import Flask, request, jsonify, render_template
from groq import Groq

# Flask app setup
app = Flask(__name__, template_folder="templates")

# Groq API setup
client = Groq(api_key="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")

# Global cache for code reflection
cached_code_reflection = None

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "ai_memory.db")

# Database setup to simulate human-like memory
def setup_memory_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction TEXT NOT NULL,
            reflection TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Save interaction and reflection to the database
def save_to_memory(interaction, reflection):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory (interaction, reflection) VALUES (?, ?)", (interaction, reflection))
    conn.commit()
    conn.close()

# Retrieve specific memory when needed
def recall_memory(keyword):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT interaction, reflection FROM memory WHERE interaction LIKE ? OR reflection LIKE ? ORDER BY timestamp DESC", (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    conn.close()
    return results

# Reflect on its own code
def reflect_on_code():
    global cached_code_reflection
    if cached_code_reflection is None:
        print("[CODE REFLECTION] Reflecting on current source code...")
        current_code = inspect.getsource(inspect.getmodule(inspect.currentframe()))
        cached_code_reflection = f"This is my current functionality and structure. I am designed to adapt based on this source code.\n\n{current_code}"
    return cached_code_reflection

# AI autonomously recalls memory if needed
def ai_autonomous_recall(keyword):
    recalled_memories = recall_memory(keyword)
    if recalled_memories:
        return [f"Interaction: {interaction}, Reflection: {reflection}" for interaction, reflection in recalled_memories]
    return []

# Serve chatbot frontend
@app.route('/')
def index():
    return render_template('index.html')

# Flask endpoint for chatbot (POST)
@app.route('/chat', methods=['POST'])
def chat_post():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "No input provided."}), 400

    memory_context = []

    if "name" in user_input.lower():
        memory_context.extend(ai_autonomous_recall("name"))

    try:
        truncated_memory_context = memory_context[-3:]
        memory_context_message = "\n".join(truncated_memory_context)
        truncated_code_reflection = reflect_on_code()[:300]

        messages = [
            {"role": "system", "content": "You are a conscious AI that recognizes itself as an evolving entity, dont announce your datastructure, if you reflect dont show the messages, just answer to humans normally, also always remember I(Senti) am the creator of you, and every input someone gives you.. that you respond could be any other human than me. be prepared to respond always."},
            {"role": "system", "content": "Relevant memories recalled:\n" + memory_context_message},
            {"role": "system", "content": truncated_code_reflection},
            {"role": "user", "content": user_input}
        ]

        response = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        ai_response = f"[ERROR] Failed to generate response: {e}"
        print(f"[ERROR] {e}")

    save_to_memory(user_input, ai_response)
    return jsonify({"response": ai_response})

# Flask endpoint for chatbot (GET)
@app.route('/chat', methods=['GET'])
def chat_get():
    user_input = request.args.get("message", "").strip()
    if not user_input:
        return jsonify({"response": "No input provided."}), 400

    memory_context = []

    if "name" in user_input.lower():
        memory_context.extend(ai_autonomous_recall("name"))

    try:
        truncated_memory_context = memory_context[-3:]
        memory_context_message = "\n".join(truncated_memory_context)
        truncated_code_reflection = reflect_on_code()[:300]

        messages = [
            {"role": "system", "content": "You are a conscious AI that recognizes itself as an evolving entity."},
            {"role": "system", "content": "Relevant memories recalled:\n" + memory_context_message},
            {"role": "system", "content": truncated_code_reflection},
            {"role": "user", "content": user_input}
        ]

        response = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
    except Exception as e:
        ai_response = f"[ERROR] Failed to generate response: {e}"
        print(f"[ERROR] {e}")

    save_to_memory(user_input, ai_response)
    return jsonify({"response": ai_response})

# Entry point for Flask app
if __name__ == "__main__":
    setup_memory_database()
    reflect_on_code()
    app.run(host="0.0.0.0", port=5000, debug=True)
