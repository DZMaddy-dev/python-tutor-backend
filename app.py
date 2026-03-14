import json
import subprocess
import re
import sqlite3
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "python-tutor-secret-2024"
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
bcrypt = Bcrypt(app)

# -----------------------------
# Database Setup
# -----------------------------
def init_db():
    conn = sqlite3.connect("tutor.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            UNIQUE(username, type, item_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Auth Routes
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"error": "Username and password are required."})
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters."})
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters."})
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    try:
        conn = sqlite3.connect("tutor.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Account created! Welcome, {username}."})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already taken. Try another."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    conn = sqlite3.connect("tutor.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row or not bcrypt.check_password_hash(row[0], password):
        return jsonify({"error": "Invalid username or password."})
    session["username"] = username
    return jsonify({"message": f"Welcome back, {username}!", "username": username})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})

@app.route("/me")
def me():
    if "username" in session:
        return jsonify({"loggedIn": True, "username": session["username"]})
    return jsonify({"loggedIn": False})

# -----------------------------
# Local Python Error Explainer
# -----------------------------
def explain_error(error_message):
    if "SyntaxError" in error_message:
        return "SyntaxError: Python cannot understand your code. You may have forgotten a colon (:), a bracket, or indentation."
    elif "NameError" in error_message:
        return "NameError: You used a variable that was never defined. Check your spelling."
    elif "IndentationError" in error_message:
        return "IndentationError: Your spacing is wrong. Python requires consistent indentation (4 spaces)."
    elif "TypeError" in error_message:
        return "TypeError: You used an operation on the wrong type of data (e.g., adding a number and a string)."
    elif "ZeroDivisionError" in error_message:
        return "ZeroDivisionError: You tried to divide by zero, which is not allowed."
    elif "IndexError" in error_message:
        return "IndexError: You tried to access a list index that doesn't exist."
    elif "KeyError" in error_message:
        return "KeyError: You tried to access a dictionary key that doesn't exist."
    elif "AttributeError" in error_message:
        return "AttributeError: You used a method or property that doesn't exist on this object."
    elif "ValueError" in error_message:
        return "ValueError: You passed the right type but an invalid value (e.g., int('hello'))."
    elif "ModuleNotFoundError" in error_message:
        return "ModuleNotFoundError: You tried to import a module that isn't installed. Use pip install <module_name>."
    elif "RecursionError" in error_message:
        return "RecursionError: Your function is calling itself too many times. Check your base case."
    elif "FileNotFoundError" in error_message:
        return "FileNotFoundError: The file you tried to open doesn't exist. Check the file path."
    elif "OverflowError" in error_message:
        return "OverflowError: The number is too large for Python to handle."
    elif "MemoryError" in error_message:
        return "MemoryError: Your program ran out of memory."
    elif "StopIteration" in error_message:
        return "StopIteration: You called next() on an iterator that has no more items."
    else:
        return "Python encountered an error. Read the error message carefully and check your syntax."

# -----------------------------
# Local Code Explainer
# -----------------------------
def explain_code_locally(code):
    lines = code.strip().split("\n")
    explanations = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        elif line.startswith("#"):
            explanations.append(f'`{line}` → this is a comment (ignored by Python).')
        elif line.startswith("print"):
            explanations.append(f'`{line}` → prints output to the screen.')
        elif line.startswith("for"):
            explanations.append(f'`{line}` → starts a loop that repeats code.')
        elif line.startswith("while"):
            explanations.append(f'`{line}` → runs a loop while a condition is true.')
        elif line.startswith("if"):
            explanations.append(f'`{line}` → checks a condition.')
        elif line.startswith("elif"):
            explanations.append(f'`{line}` → checks another condition if the previous one was false.')
        elif line.startswith("else"):
            explanations.append(f'`{line}` → runs if none of the above conditions were true.')
        elif line.startswith("def"):
            explanations.append(f'`{line}` → defines a reusable function.')
        elif line.startswith("class"):
            explanations.append(f'`{line}` → defines a class (blueprint for objects).')
        elif line.startswith("return"):
            explanations.append(f'`{line}` → sends a value back from a function.')
        elif line.startswith("import") or line.startswith("from"):
            explanations.append(f'`{line}` → imports a module/library.')
        elif line.startswith("try"):
            explanations.append(f'`{line}` → starts a block that might cause an error.')
        elif line.startswith("except"):
            explanations.append(f'`{line}` → handles an error if one occurs in the try block.')
        elif line.startswith("break"):
            explanations.append(f'`{line}` → exits the current loop immediately.')
        elif line.startswith("continue"):
            explanations.append(f'`{line}` → skips to the next iteration of the loop.')
        elif line.startswith("pass"):
            explanations.append(f'`{line}` → does nothing; used as a placeholder.')
        elif "=" in line:
            explanations.append(f'`{line}` → stores a value in a variable.')
        else:
            explanations.append(f'`{line}` → executes this Python statement.')
    return "\n".join(explanations)

# -----------------------------
# Local Code Fixer
# -----------------------------
def fix_code_locally(code):
    lines = code.split("\n")
    fixed = []
    for line in lines:
        stripped = line.rstrip()
        lstripped = stripped.lstrip()

        # FIX 1: Missing colon
        keywords_needing_colon = ["for ", "while ", "if ", "elif ", "else", "def ", "class "]
        if lstripped and not stripped.endswith(":") and not stripped.endswith(",") and not stripped.endswith("\\"):
            for kw in keywords_needing_colon:
                if lstripped.startswith(kw) or lstripped == "else":
                    stripped = stripped + ":"
                    break

        # FIX 2: Fix indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces % 4 != 0 and leading_spaces > 0:
            correct_indent = round(leading_spaces / 4) * 4
            stripped = " " * correct_indent + stripped.lstrip()

        # FIX 3: print without parentheses
        print_no_paren = re.match(r'^(\s*)print\s+(?!\()(.+)$', stripped)
        if print_no_paren:
            indent = print_no_paren.group(1)
            content = print_no_paren.group(2).strip()
            stripped = f'{indent}print({content})'

        # FIX 4: = instead of == in conditions
        single_eq = re.match(r'^(\s*)(if|elif|while)\s+(.+[^=!<>])=([^=].*)(:)$', stripped)
        if single_eq:
            indent = single_eq.group(1)
            keyword = single_eq.group(2)
            left = single_eq.group(3)
            right = single_eq.group(4)
            stripped = f'{indent}{keyword} {left}=={right}:'

        # FIX 5: Missing space after comma
        stripped = re.sub(r',(?! )(?!=)', ', ', stripped)

        # FIX 6: Wrong capitalization of builtins
        for wrong, right in [("Int(", "int("), ("Float(", "float("), ("Str(", "str("),
                              ("String(", "str("), ("Print(", "print("), ("Input(", "input("),
                              ("Len(", "len("), ("Range(", "range("), ("List(", "list(")]:
            stripped = stripped.replace(wrong, right)

        # FIX 7: True/False/None capitalization
        stripped = re.sub(r'\btrue\b', 'True', stripped)
        stripped = re.sub(r'\bfalse\b', 'False', stripped)
        stripped = re.sub(r'\bnone\b', 'None', stripped)

        # FIX 8: AND/OR/NOT capitalization
        stripped = re.sub(r'\bAND\b', 'and', stripped)
        stripped = re.sub(r'\bOR\b', 'or', stripped)
        stripped = re.sub(r'\bNOT\b', 'not', stripped)

        fixed.append(stripped)

    result = "\n".join(fixed)
    # FIX 9: Remove semicolons at end of lines
    result = re.sub(r';\s*\n', '\n', result)
    result = re.sub(r';\s*$', '', result)
    return result

# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    return "Python AI Tutor Backend Running"

# -----------------------------
# Run Python Code
# -----------------------------
@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data["code"]
    user_input = data.get("input", "")
    try:
        result = subprocess.run(
            ["python", "-c", code],
            input=user_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stderr:
            explanation = explain_error(result.stderr)
            return jsonify({"error": result.stderr, "explanation": explanation})
        return jsonify({"output": result.stdout})
    except subprocess.TimeoutExpired:
        return jsonify({
            "error": "TimeoutError",
            "explanation": "Your program took too long. Check for infinite loops or input() calls without values in the input box."
        })

# -----------------------------
# Explain Code
# -----------------------------
@app.route("/explain", methods=["POST"])
def explain_code():
    data = request.json
    code = data["code"]
    explanation = explain_code_locally(code)
    return jsonify({"explanation": explanation})

# -----------------------------
# Fix Code
# -----------------------------
@app.route("/fix", methods=["POST"])
def fix_code():
    data = request.json
    code = data["code"]
    fixed = fix_code_locally(code)
    return jsonify({
        "fixed": fixed,
        "message": "Code has been auto-corrected. Review the changes before running."
    })

# -----------------------------
# Chat
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data["question"].lower()
    if "loop" in question:
        answer = "A loop repeats code. Example:\nfor i in range(5):\n    print(i)"
    elif "list" in question:
        answer = "A list stores multiple values.\nExample: nums = [1, 2, 3]"
    elif "function" in question:
        answer = "A function is reusable code.\nExample:\ndef add(a, b):\n    return a + b"
    elif "if" in question or "condition" in question:
        answer = "An if statement checks a condition.\nExample:\nif x > 5:\n    print('big')"
    elif "variable" in question:
        answer = "A variable stores a value.\nExample: x = 10"
    elif "string" in question:
        answer = "A string is text in quotes.\nExample: name = 'Aryan'"
    elif "dictionary" in question or "dict" in question:
        answer = "A dictionary stores key-value pairs.\nExample: d = {'name': 'Aryan'}"
    elif "class" in question or "object" in question:
        answer = "A class is a blueprint for objects.\nExample:\nclass Dog:\n    def __init__(self, name):\n        self.name = name"
    elif "lambda" in question:
        answer = "A lambda is a small anonymous function.\nExample: square = lambda x: x * x"
    elif "recursion" in question:
        answer = "Recursion is when a function calls itself.\nExample:\ndef factorial(n):\n    if n == 0: return 1\n    return n * factorial(n-1)"
    else:
        answer = "Ask me about: loops, lists, functions, if statements, variables, strings, dictionaries, classes, lambda, or recursion."
    return jsonify({"answer": answer})

# -----------------------------
# Practice Problems
# -----------------------------
@app.route("/problems")
def get_problems():
    with open("lessons/practice_problems.json", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

# -----------------------------
# Course
# -----------------------------
@app.route("/course")
def get_course():
    with open("lessons/python_course.json", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

# -----------------------------
# Start Server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)