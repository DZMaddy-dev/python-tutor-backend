import json
import subprocess
import re
import urllib.request
import urllib.error
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow all origins for preflight + requests
CORS(app,
     origins=["http://localhost:3000", "https://python-ai-tutor-37ba0.web.app"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"]
)

# Explicitly handle preflight OPTIONS for every route
@app.after_request
def after_request(response):
    origin = request.headers.get("Origin", "")
    allowed = ["http://localhost:3000", "https://python-ai-tutor-37ba0.web.app"]
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"]  = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    response = jsonify({"status": "ok"})
    origin = request.headers.get("Origin", "")
    allowed = ["http://localhost:3000", "https://python-ai-tutor-37ba0.web.app"]
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"]  = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response, 200

# ─────────────────────────────────────────
# Set ANTHROPIC_API_KEY in Render as an
# environment variable — never hardcode it
# ─────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def call_claude(system_prompt, user_message, max_tokens=2000):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]


# ─────────────────────────────────────────
# Home
# ─────────────────────────────────────────
@app.route("/")
def home():
    return "Python AI Tutor Backend Running"


# ─────────────────────────────────────────
# Error Explainer
# ─────────────────────────────────────────
def explain_error(error_message):
    err = error_message
    if "SyntaxError" in err:
        return "SyntaxError: Python cannot understand your code. Check for a missing colon (:), mismatched brackets, or wrong indentation."
    elif "NameError" in err:
        match = re.search(r"name '(\w+)' is not defined", err)
        if match:
            name = match.group(1)
            if name == "true":  return "NameError: Python uses 'True' (capital T), not 'true'."
            if name == "false": return "NameError: Python uses 'False' (capital F), not 'false'."
            if name == "null":  return "NameError: Python uses 'None', not 'null'."
            if name == "nil":   return "NameError: Python uses 'None', not 'nil'."
            return f"NameError: '{name}' is not defined. Check spelling or define it before using it."
        return "NameError: You used a variable that was never defined. Check your spelling."
    elif "IndentationError" in err:
        return "IndentationError: Wrong indentation. Python requires exactly 4 spaces per indent level."
    elif "TabError" in err:
        return "TabError: Mixed tabs and spaces. Use only 4 spaces per indent level throughout."
    elif "TypeError" in err:
        if "can only concatenate str" in err:
            return "TypeError: Can't join a string and a number directly. Use str(number) to convert it first."
        if "unsupported operand" in err:
            return "TypeError: You're using an operator on incompatible types (e.g., string + integer)."
        if "not subscriptable" in err:
            return "TypeError: You're trying to use [] on something that doesn't support indexing."
        if "not callable" in err:
            return "TypeError: You're calling something as a function but it isn't one. Check for extra ()."
        if "missing" in err and "argument" in err:
            return "TypeError: Function called without all required arguments."
        return "TypeError: Operation on wrong data type (e.g., adding a number and a string)."
    elif "ZeroDivisionError" in err:
        return "ZeroDivisionError: Division by zero. Add 'if divisor != 0:' check before dividing."
    elif "IndexError" in err:
        return "IndexError: List index out of range. Use len() to check the list size first."
    elif "KeyError" in err:
        match = re.search(r"KeyError: (.+)", err)
        key = match.group(1) if match else "that key"
        return f"KeyError: {key} doesn't exist in the dictionary. Use .get(key, default) for safe access."
    elif "AttributeError" in err:
        match = re.search(r"'(\w+)' object has no attribute '(\w+)'", err)
        if match:
            return f"AttributeError: '{match.group(1)}' objects don't have a '{match.group(2)}' method. Check type and spelling."
        return "AttributeError: Method or property doesn't exist on this object. Check the type."
    elif "ValueError" in err:
        if "invalid literal" in err:
            return "ValueError: Can't convert this to a number. e.g., int('hello') fails — check your input."
        return "ValueError: Right type but invalid value passed to a function."
    elif "ModuleNotFoundError" in err or "ImportError" in err:
        match = re.search(r"No module named '([\w.]+)'", err)
        mod = match.group(1) if match else "that module"
        return f"ModuleNotFoundError: '{mod}' is not installed. Run: pip install {mod}"
    elif "RecursionError" in err:
        return "RecursionError: Function called itself too many times. Check your base case."
    elif "FileNotFoundError" in err:
        return "FileNotFoundError: File not found. Double-check the file path and name."
    elif "TimeoutError" in err or "timeout" in err.lower():
        return "Timeout: Code took too long. Check for infinite loops (while True without break)."
    else:
        return "Python encountered an error. Read the message carefully — it tells you the line number and cause."


# ─────────────────────────────────────────
# Run Code
# ─────────────────────────────────────────
@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data.get("code", "")
    user_input = data.get("input", "")
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=10,
            input=user_input
        )
        if result.returncode == 0:
            return jsonify({"output": result.stdout or "(no output)"})
        else:
            error = result.stderr.strip()
            return jsonify({"output": None, "error": error, "explanation": explain_error(error)})
    except subprocess.TimeoutExpired:
        return jsonify({"output": None, "error": "TimeoutError: Code ran for more than 10 seconds.", "explanation": "Possible infinite loop — check your while/for conditions."})
    except Exception as e:
        return jsonify({"output": None, "error": str(e), "explanation": explain_error(str(e))})


# ─────────────────────────────────────────
# Explain Code — AI with local fallback
# ─────────────────────────────────────────
def explain_code_locally(code):
    lines = code.strip().split("\n")
    explanations = []
    for line in lines:
        s = line.strip()
        if not s: continue
        elif s.startswith("#"):        explanations.append(f'`{s}` → comment (ignored by Python).')
        elif s.startswith("print"):    explanations.append(f'`{s}` → prints output to the screen.')
        elif s.startswith("for"):      explanations.append(f'`{s}` → for loop that iterates over a sequence.')
        elif s.startswith("while"):    explanations.append(f'`{s}` → while loop — runs as long as condition is True.')
        elif s.startswith("if"):       explanations.append(f'`{s}` → checks a condition; runs block below if True.')
        elif s.startswith("elif"):     explanations.append(f'`{s}` → checks another condition if previous was False.')
        elif s.startswith("else"):     explanations.append(f'`{s}` → runs if none of the above conditions matched.')
        elif s.startswith("def"):      explanations.append(f'`{s}` → defines a reusable function.')
        elif s.startswith("class"):    explanations.append(f'`{s}` → defines a class (blueprint for objects).')
        elif s.startswith("return"):   explanations.append(f'`{s}` → exits the function and returns this value.')
        elif s.startswith("import") or s.startswith("from"): explanations.append(f'`{s}` → imports a module.')
        elif s.startswith("try"):      explanations.append(f'`{s}` → starts a block that will catch errors.')
        elif s.startswith("except"):   explanations.append(f'`{s}` → handles a specific error type.')
        elif s.startswith("finally"):  explanations.append(f'`{s}` → always runs, error or not.')
        elif s.startswith("raise"):    explanations.append(f'`{s}` → manually raises an exception.')
        elif s.startswith("with"):     explanations.append(f'`{s}` → opens a resource and auto-closes it.')
        elif s.startswith("break"):    explanations.append(f'`{s}` → immediately exits the loop.')
        elif s.startswith("continue"): explanations.append(f'`{s}` → skips rest of this loop iteration.')
        elif s.startswith("pass"):     explanations.append(f'`{s}` → placeholder — does nothing.')
        elif s.startswith("yield"):    explanations.append(f'`{s}` → pauses generator and yields a value.')
        elif s.startswith("global"):   explanations.append(f'`{s}` → declares use of a global variable.')
        elif s.startswith("lambda"):   explanations.append(f'`{s}` → creates a small one-line anonymous function.')
        elif "=" in s and "==" not in s: explanations.append(f'`{s}` → stores a value in a variable.')
        else:                          explanations.append(f'`{s}` → executes this Python statement.')
    return "\n".join(explanations)


@app.route("/explain", methods=["POST"])
def explain_code():
    code = request.json.get("code", "").strip()
    if not code:
        return jsonify({"explanation": "No code provided."})
    try:
        explanation = call_claude(
            system_prompt="""You are an expert Python teacher explaining code to a beginner.
For the given code:
1. Give a one-sentence summary of what the whole program does
2. Explain each meaningful section in plain English
3. Point out any important concepts or patterns used
4. Mention any potential issues or improvements

Be thorough, clear, and educational. Use examples where helpful.""",
            user_message=f"Explain this Python code:\n\n```python\n{code}\n```",
            max_tokens=1200
        )
        return jsonify({"explanation": explanation})
    except Exception:
        return jsonify({"explanation": explain_code_locally(code)})


# ─────────────────────────────────────────
# Fix Code — AI with robust local fallback
# ─────────────────────────────────────────
def fix_code_locally(code, error=""):
    lines = code.split("\n")
    fixed = []
    changes = []

    for line in lines:
        stripped = line.rstrip()
        lstripped = stripped.lstrip()
        original = stripped

        # Fix missing colons
        kws = ["for ", "while ", "if ", "elif ", "else", "def ", "class ", "try", "except", "finally", "with "]
        if lstripped and not stripped.endswith(":") and not stripped.endswith(",") and not stripped.endswith("\\"):
            for kw in kws:
                if lstripped.startswith(kw) or lstripped in ("else", "try", "finally"):
                    stripped = stripped + ":"
                    break

        # Fix bad indentation
        leading = len(line) - len(line.lstrip())
        if leading % 4 != 0 and leading > 0:
            correct = round(leading / 4) * 4
            stripped = " " * correct + stripped.lstrip()

        # Fix Python 2 print
        m = re.match(r'^(\s*)print\s+(?!\()(.+)$', stripped)
        if m:
            stripped = f'{m.group(1)}print({m.group(2).strip()})'

        # Fix single = in conditions
        m2 = re.match(r'^(\s*)(if|elif|while)\s+(.+[^=!<>])=([^=].*)(:)$', stripped)
        if m2:
            stripped = f'{m2.group(1)}{m2.group(2)} {m2.group(3)}=={m2.group(4)}:'

        # Fix case-sensitive keywords
        for wrong, right in [
            (r'\btrue\b','True'), (r'\bfalse\b','False'), (r'\bnone\b','None'),
            (r'\bnull\b','None'), (r'\bAND\b','and'), (r'\bOR\b','or'), (r'\bNOT\b','not'),
        ]:
            stripped = re.sub(wrong, right, stripped)

        # Fix capitalized built-ins
        for wrong, right in [
            ("Int(","int("),("Float(","float("),("Str(","str("),("String(","str("),
            ("Print(","print("),("Input(","input("),("Len(","len("),("Range(","range("),
            ("List(","list("),("Dict(","dict("),("Tuple(","tuple("),("Set(","set("),
            ("Bool(","bool("),("Type(","type("),("Sorted(","sorted("),("Reversed(","reversed("),
            ("Map(","map("),("Filter(","filter("),("Zip(","zip("),("Enumerate(","enumerate("),
        ]:
            stripped = stripped.replace(wrong, right)

        # Remove trailing semicolons
        stripped = re.sub(r';\s*$', '', stripped)

        if stripped != original:
            changes.append(f"• Fixed: `{original.strip()}` → `{stripped.strip()}`")
        fixed.append(stripped)

    result = "\n".join(fixed)

    if not changes:
        if error:
            changes.append(f"• No automatic fixes found. The error says:\n  {error}\n  Review your logic manually.")
        else:
            changes.append("• No syntax issues found. If output is wrong, this may be a logic error.")

    return result, "\n".join(changes)


@app.route("/fix", methods=["POST"])
def fix_code():
    data = request.json
    code = data.get("code", "").strip()
    error = data.get("error", "").strip()

    if not code:
        return jsonify({"fixed": "", "explanation": "No code provided.", "message": "No code provided."})

    # Auto-run to get real error if none passed
    if not error:
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                error = result.stderr.strip()
        except subprocess.TimeoutExpired:
            error = "TimeoutError: possible infinite loop"
        except Exception as e:
            error = str(e)

    # Try AI fix
    try:
        system = """You are an expert Python debugger. Your job is to fix ALL bugs in the given code.

Respond ONLY with valid JSON — no markdown, no extra text outside the JSON:
{
  "fixed_code": "complete corrected Python code here",
  "explanation": "bullet-pointed explanation of every fix made, starting each bullet with •"
}

Rules:
- fixed_code must be the COMPLETE working script
- Fix every bug you find — syntax, logic, runtime, naming, indentation
- Preserve the original intent of the code
- If code is already correct, return it unchanged and say so
- Be specific: name the exact line and what was wrong"""

        user_msg = f"""Fix this Python code.

CODE:
```python
{code}
```

ERROR MESSAGE:
{error if error else "(no error — check for logic bugs or incorrect output)"}"""

        raw = call_claude(system, user_msg, max_tokens=2000)

        # Strip markdown fences
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        # Find the JSON object
        j_start = clean.find("{")
        j_end = clean.rfind("}") + 1
        if j_start >= 0 and j_end > j_start:
            clean = clean[j_start:j_end]

        parsed = json.loads(clean)
        fixed_code = parsed.get("fixed_code", code).strip()
        explanation = parsed.get("explanation", "Code fixed.")

        return jsonify({
            "fixed": fixed_code,
            "explanation": explanation,
            "message": "✅ Fixed by AI"
        })

    except (json.JSONDecodeError, KeyError):
        # Try to salvage a code block from the raw response
        try:
            m = re.search(r"```python\n(.*?)```", raw, re.DOTALL)
            if m:
                fixed_code = m.group(1).strip()
                expl = re.sub(r"```python.*?```", "", raw, flags=re.DOTALL).strip()
                return jsonify({"fixed": fixed_code, "explanation": expl, "message": "✅ Fixed by AI"})
        except Exception:
            pass
        fixed, expl = fix_code_locally(code, error)
        return jsonify({"fixed": fixed, "explanation": expl, "message": "⚠️ AI response malformed — applied rule-based fixes"})

    except Exception:
        fixed, expl = fix_code_locally(code, error)
        return jsonify({
            "fixed": fixed,
            "explanation": f"• AI temporarily unavailable — applied automatic rule-based fixes\n{expl}",
            "message": "🔧 Rule-based fixes applied"
        })


# ─────────────────────────────────────────
# Deep Python Knowledge Base
# ─────────────────────────────────────────
PYTHON_TOPICS = {
    "variable": """📦 VARIABLES in Python
━━━━━━━━━━━━━━━━━━━━
A variable is a named container that stores a value in memory.

HOW TO CREATE:
  x = 10
  name = "Aryan"
  price = 99.5
  is_student = True

NAMING RULES:
  ✅ letters, numbers, underscores
  ✅ must start with letter or underscore
  ❌ cannot start with number (1name is wrong)
  ❌ no spaces (use my_name not my name)

MULTIPLE ASSIGNMENT:
  a, b, c = 1, 2, 3
  x = y = z = 0

DATA TYPES:
  int     → x = 10
  float   → x = 3.14
  str     → x = "hello"
  bool    → x = True
  list    → x = [1, 2, 3]
  dict    → x = {"key": "value"}
  tuple   → x = (1, 2, 3)
  None    → x = None

EXAMPLE:
  age = 19
  name = "Aryan"
  print(f"My name is {name} and I am {age} years old.")""",

    "string": """📝 STRINGS in Python
━━━━━━━━━━━━━━━━━━━━
A string is a sequence of characters in quotes.

COMMON OPERATIONS:
  s = "hello world"
  s.upper()           # HELLO WORLD
  s.lower()           # hello world
  s.title()           # Hello World
  s.replace("world","Python") # hello Python
  s.split(" ")        # ['hello', 'world']
  s.strip()           # removes whitespace
  s[0:5]              # hello (slicing)
  s.find("world")     # 6 (position)
  len(s)              # 11

F-STRINGS:
  name = "Aryan"
  age = 19
  print(f"Name: {name}, Age: {age}")
  print(f"Next year: {age + 1}")

CHECKING:
  s.startswith("hello")  # True
  s.endswith("world")    # True
  "hello" in s           # True
  s.isdigit()            # False""",

    "list": """📋 LISTS in Python
━━━━━━━━━━━━━━━━━━━━
A list stores multiple values in order. Mutable — can change.

CREATING:
  fruits = ["apple", "banana", "mango"]
  numbers = [1, 2, 3, 4, 5]

ACCESSING:
  fruits[0]    # apple (first)
  fruits[-1]   # mango (last)
  fruits[1:3]  # ['banana', 'mango']

MODIFYING:
  fruits.append("grape")     # add to end
  fruits.insert(1, "kiwi")   # add at index 1
  fruits.remove("banana")    # remove by value
  fruits.pop()               # remove last
  fruits.sort()              # sort in place
  fruits.reverse()           # reverse in place

LIST COMPREHENSION:
  squares = [x**2 for x in range(10)]
  evens   = [x for x in range(20) if x % 2 == 0]

LOOPING:
  for i, fruit in enumerate(fruits):
      print(i, fruit)""",

    "dictionary": """📚 DICTIONARIES in Python
━━━━━━━━━━━━━━━━━━━━
Stores key-value pairs. Like a real dictionary — word → meaning.

CREATING:
  student = {"name": "Aryan", "age": 19, "grade": "A"}

ACCESSING:
  student["name"]           # Aryan
  student.get("age")        # 19
  student.get("marks", 0)   # 0 (default if missing)

ADDING / UPDATING:
  student["city"] = "Delhi"  # add new key
  student["age"] = 20        # update existing

LOOPING:
  for key, value in student.items():
      print(key, "→", value)

DICT COMPREHENSION:
  squares = {x: x**2 for x in range(5)}""",

    "tuple": """🔒 TUPLES in Python
━━━━━━━━━━━━━━━━━━━━
Like a list but IMMUTABLE — cannot be changed after creation.

CREATING:
  coords = (10, 20)
  single = (42,)   # comma needed for single item!

WHY USE TUPLES?
  ✅ Faster than lists
  ✅ Protects data from changes
  ✅ Can be used as dictionary keys
  ✅ Good for fixed data (coordinates, RGB)

TUPLE UNPACKING:
  x, y = (10, 20)
  a, b = b, a    # swap variables!

LIST vs TUPLE:
  list  → mutable, [], slower, append/remove
  tuple → immutable, (), faster, no add/remove""",

    "set": """🔵 SETS in Python
━━━━━━━━━━━━━━━━━━━━
Stores UNIQUE values only — no duplicates, unordered.

CREATING:
  fruits = {"apple", "banana", "mango"}
  empty  = set()   # NOT {} — that's a dict!

AUTO-REMOVES DUPLICATES:
  s = {1, 2, 2, 3, 3}
  print(s)  # {1, 2, 3}

SET OPERATIONS:
  a = {1, 2, 3, 4}
  b = {3, 4, 5, 6}
  a | b   # UNION: {1,2,3,4,5,6}
  a & b   # INTERSECTION: {3,4}
  a - b   # DIFFERENCE: {1,2}
  a ^ b   # SYMMETRIC: {1,2,5,6}

REAL USE:
  # Remove duplicates from list
  unique = list(set(["Aryan","Rahul","Aryan"]))""",

    "loop": """🔄 LOOPS in Python
━━━━━━━━━━━━━━━━━━━━
FOR LOOP — know how many times:
  for i in range(5):
      print(i)  # 0,1,2,3,4

  for i, item in enumerate(["a","b","c"]):
      print(i, item)

WHILE LOOP — condition-based:
  count = 0
  while count < 5:
      print(count)
      count += 1

LOOP CONTROL:
  break    → exit loop completely
  continue → skip to next iteration
  pass     → placeholder, do nothing

NESTED LOOPS:
  for i in range(1, 4):
      for j in range(1, 4):
          print(i * j, end=" ")
      print()

ELSE WITH LOOP:
  for i in range(5):
      print(i)
  else:
      print("Loop finished!")""",

    "function": """⚙️ FUNCTIONS in Python
━━━━━━━━━━━━━━━━━━━━
Reusable blocks of code.

BASIC:
  def greet(name):
      return f"Hello, {name}!"

  print(greet("Aryan"))  # Hello, Aryan!

DEFAULT PARAMETERS:
  def greet(name, msg="Good morning"):
      print(f"{msg}, {name}!")

*ARGS and **KWARGS:
  def total(*nums):       # variable args
      return sum(nums)

  def info(**details):    # keyword args
      for k, v in details.items():
          print(k, ":", v)

  total(1, 2, 3, 4, 5)           # 15
  info(name="Aryan", age=19)

LAMBDA:
  square = lambda x: x ** 2
  print(square(5))  # 25

RETURN MULTIPLE VALUES:
  def min_max(nums):
      return min(nums), max(nums)

  lo, hi = min_max([3,1,4,1,5])""",

    "class": """🏗️ CLASSES & OOP in Python
━━━━━━━━━━━━━━━━━━━━
A class is a blueprint for creating objects.

BASIC CLASS:
  class Dog:
      def __init__(self, name, breed):
          self.name = name
          self.breed = breed

      def bark(self):
          print(f"{self.name} says: Woof!")

  dog = Dog("Bruno", "Labrador")
  dog.bark()  # Bruno says: Woof!

INHERITANCE:
  class Animal:
      def __init__(self, name):
          self.name = name
      def speak(self):
          return "..."

  class Cat(Animal):
      def speak(self):
          return f"{self.name} says Meow!"

  c = Cat("Whiskers")
  print(c.speak())

SPECIAL METHODS:
  def __str__(self):   return "string representation"
  def __len__(self):   return self.length
  def __eq__(self, o): return self.val == o.val

4 PILLARS OF OOP:
  Encapsulation  → hide internal details
  Inheritance    → child gets parent features
  Polymorphism   → same method, different behavior
  Abstraction    → expose only what's needed""",

    "recursion": """🔁 RECURSION in Python
━━━━━━━━━━━━━━━━━━━━
A function that calls itself to solve smaller sub-problems.

GOLDEN RULE:
  1. BASE CASE — when to stop
  2. RECURSIVE CASE — smaller version of the problem

FACTORIAL:
  def factorial(n):
      if n == 0: return 1        # base case
      return n * factorial(n-1)  # recursive

  factorial(5)  # 5*4*3*2*1 = 120

FIBONACCI:
  def fib(n):
      if n <= 1: return n
      return fib(n-1) + fib(n-2)

COUNTDOWN:
  def countdown(n):
      if n <= 0: print("Go!"); return
      print(n)
      countdown(n - 1)

WARNING:
  Python default recursion limit = 1000.
  Use loops when depth could be very large.""",

    "error": """⚠️ ERROR HANDLING in Python
━━━━━━━━━━━━━━━━━━━━
Use try/except to handle errors gracefully.

BASIC:
  try:
      x = int(input("Number: "))
      print(10 / x)
  except ValueError:
      print("Not a valid number!")
  except ZeroDivisionError:
      print("Cannot divide by zero!")

FULL STRUCTURE:
  try:
      risky_code()
  except ValueError as e:
      print(f"Error: {e}")
  else:
      print("Success!")        # runs if NO error
  finally:
      print("Always runs")     # cleanup

RAISING ERRORS:
  def set_age(age):
      if age < 0:
          raise ValueError("Age cannot be negative!")
      return age

COMMON EXCEPTIONS:
  ValueError, TypeError, IndexError, KeyError,
  ZeroDivisionError, FileNotFoundError,
  AttributeError, ImportError, NameError""",

    "file": """📁 FILE HANDLING in Python
━━━━━━━━━━━━━━━━━━━━
OPEN MODES: "r" read | "w" write | "a" append | "r+" read+write

READING:
  with open("data.txt", "r") as f:
      content = f.read()        # whole file
      lines = f.readlines()     # list of lines

  with open("data.txt") as f:
      for line in f:            # line by line
          print(line.strip())

WRITING:
  with open("output.txt", "w") as f:
      f.write("Hello\\n")
      f.write("World\\n")

JSON:
  import json
  data = {"name": "Aryan", "age": 19}

  with open("data.json", "w") as f:
      json.dump(data, f, indent=2)

  with open("data.json") as f:
      data = json.load(f)

CHECK EXISTS:
  import os
  if os.path.exists("file.txt"):
      print("Found!")

ALWAYS use 'with' — auto-closes the file.""",

    "lambda": """⚡ LAMBDA FUNCTIONS in Python
━━━━━━━━━━━━━━━━━━━━
Small anonymous one-line functions.

SYNTAX: lambda arguments: expression

EXAMPLES:
  square  = lambda x: x ** 2
  add     = lambda x, y: x + y
  greet   = lambda name: f"Hello, {name}!"

WITH MAP (apply to every item):
  nums    = [1, 2, 3, 4, 5]
  squares = list(map(lambda x: x**2, nums))
  # [1, 4, 9, 16, 25]

WITH FILTER (keep matching):
  evens = list(filter(lambda x: x%2==0, nums))
  # [2, 4]

WITH SORTED (custom sort):
  students = [("Aryan",85),("Rahul",92),("Priya",78)]
  by_score = sorted(students, key=lambda s: s[1])

USE WHEN:
  ✅ Short one-liner operations
  ✅ Passing functions as arguments
  ❌ Complex multi-line logic""",

    "comprehension": """🚀 LIST COMPREHENSIONS
━━━━━━━━━━━━━━━━━━━━
Compact one-line way to create lists.

SYNTAX:
  [expression for item in iterable if condition]

EXAMPLES:
  squares  = [x**2 for x in range(10)]
  evens    = [x for x in range(20) if x%2==0]
  upper    = [w.upper() for w in ["hi","world"]]

DICT COMPREHENSION:
  squares = {x: x**2 for x in range(6)}

SET COMPREHENSION:
  lengths = {len(w) for w in ["hi","hello","hey"]}

NESTED:
  matrix = [[i*j for j in range(1,4)] for i in range(1,4)]

FLATTENING:
  nested = [[1,2],[3,4],[5,6]]
  flat   = [x for row in nested for x in row]
  # [1, 2, 3, 4, 5, 6]""",

    "decorator": """🎨 DECORATORS in Python
━━━━━━━━━━━━━━━━━━━━
Wraps a function to add behavior without changing its code.

BASIC DECORATOR:
  def my_decorator(func):
      def wrapper(*args, **kwargs):
          print("Before")
          result = func(*args, **kwargs)
          print("After")
          return result
      return wrapper

  @my_decorator
  def say_hello():
      print("Hello!")

  say_hello()
  # Before / Hello! / After

TIMER DECORATOR:
  import time

  def timer(func):
      def wrapper(*args, **kwargs):
          start = time.time()
          result = func(*args, **kwargs)
          print(f"Took {time.time()-start:.4f}s")
          return result
      return wrapper

  @timer
  def my_func(): time.sleep(1)

BUILT-IN DECORATORS:
  @staticmethod   → no self needed
  @classmethod    → receives class
  @property       → method as attribute""",

    "generator": """⚡ GENERATORS in Python
━━━━━━━━━━━━━━━━━━━━
Produces values one at a time — memory efficient.

BASIC:
  def count_up(n):
      i = 0
      while i < n:
          yield i
          i += 1

  for num in count_up(5):
      print(num)  # 0 1 2 3 4

MEMORY DIFFERENCE:
  big_list = [x**2 for x in range(1000000)]  # ~8MB
  big_gen  = (x**2 for x in range(1000000))  # ~100 bytes!

GENERATOR EXPRESSION:
  gen = (x**2 for x in range(10))  # () not []

INFINITE GENERATOR:
  def integers():
      n = 0
      while True:
          yield n
          n += 1

  gen = integers()
  next(gen)  # 0, 1, 2, ...

FIBONACCI:
  def fibonacci():
      a, b = 0, 1
      while True:
          yield a
          a, b = b, a+b""",

    "module": """📦 MODULES in Python
━━━━━━━━━━━━━━━━━━━━
Python files with reusable code.

IMPORTING:
  import math
  math.pi, math.sqrt(16), math.floor(3.7)

  import random
  random.randint(1, 100)
  random.choice(["a","b","c"])
  random.shuffle(my_list)

FROM IMPORT:
  from math import pi, sqrt
  print(pi)       # 3.14159
  print(sqrt(25)) # 5.0

ALIASING:
  import numpy as np
  import pandas as pd

USEFUL BUILT-INS:
  math        → sqrt, pi, sin, cos, log
  random      → randint, choice, shuffle
  datetime    → date, time, timedelta
  os          → files, folders, paths
  json        → read/write JSON
  re          → regular expressions
  collections → Counter, defaultdict, deque

INSTALL PACKAGES:
  pip install numpy pandas requests flask""",

    "slicing": """✂️ SLICING in Python
━━━━━━━━━━━━━━━━━━━━
Extract portions of sequences.

SYNTAX: sequence[start:stop:step]

EXAMPLES:
  nums = [0,1,2,3,4,5,6,7,8,9]
  nums[2:5]   # [2,3,4]
  nums[:4]    # [0,1,2,3]
  nums[6:]    # [6,7,8,9]
  nums[::2]   # [0,2,4,6,8] every 2nd
  nums[::-1]  # [9..0] REVERSED!

NEGATIVE INDICES:
  nums[-1]    # last item
  nums[-3:]   # last 3
  nums[:-2]   # all except last 2

STRING SLICING:
  s = "Hello Python"
  s[:5]       # Hello
  s[::-1]     # nohtyP olleH (reversed)

PRACTICAL:
  word = "racecar"
  word == word[::-1]  # True (palindrome check)

  items[:3]   # first 3
  items[-3:]  # last 3""",

    "scope": """🔭 SCOPE in Python
━━━━━━━━━━━━━━━━━━━━
Where a variable can be accessed. Python uses LEGB:
  L → Local | E → Enclosing | G → Global | B → Built-in

LOCAL vs GLOBAL:
  x = 10  # global

  def func():
      x = 20  # local — separate!
      print(x)  # 20

  func()
  print(x)  # 10 — unchanged

GLOBAL KEYWORD:
  count = 0

  def increment():
      global count
      count += 1

  increment(); increment()
  print(count)  # 2

NONLOCAL (nested functions):
  def outer():
      x = 10
      def inner():
          nonlocal x
          x = 20
      inner()
      print(x)  # 20

CLOSURE:
  def multiplier(factor):
      def multiply(n):
          return n * factor
      return multiply

  double = multiplier(2)
  print(double(5))  # 10""",
}


def get_deep_answer(question):
    q = question.lower().strip()

    topic_map = {
        "variable":      ["variable", "var ", "assign", "store value", "data type", "int ", "float ", "bool "],
        "string":        ["string", "str ", "text", "char", "substr", "split", "join", "strip",
                          "upper", "lower", "replace", "f-string", "format", "endswith", "startswith"],
        "list":          ["list", "append", "extend", "insert", "pop", "remove", "sort", "reverse", "array"],
        "dictionary":    ["dict", "dictionary", "key", "value", "hashmap", "key-value", ".items()", ".keys()"],
        "tuple":         ["tuple", "immutable"],
        "set":           ["set ", "union", "intersection", "difference", "unique values", "duplicate"],
        "loop":          ["loop", "for loop", "while loop", "iterate", "range(", "break", "continue", "repeat", "enumerate"],
        "function":      ["function", "def ", "return", "parameter", "argument", "*args", "**kwargs", "default param"],
        "class":         ["class ", "object", "__init__", "self ", "instance", "method", "attribute", "oop", "object oriented", "inherit"],
        "recursion":     ["recursion", "recursive", "base case", "factorial", "fibonacci", "calls itself"],
        "error":         ["error", "exception", "try", "except", "finally", "raise", "handle error", "valueerror", "typeerror"],
        "file":          ["file", "open(", "read file", "write file", "append mode", "with open", "json file"],
        "lambda":        ["lambda", "anonymous function", "map(", "filter(", "reduce("],
        "comprehension": ["comprehension", "list comp", "dict comp", "one line list", "[x for"],
        "decorator":     ["decorator", "wrapper", "wrap function", "@property", "@staticmethod"],
        "generator":     ["generator", "yield", "lazy", "memory efficient"],
        "module":        ["module", "import ", "package", "pip install", "library", "from import"],
        "slicing":       ["slice", "slicing", "[::", "[:", "negative index", "reverse list", "[::-1]"],
        "scope":         ["scope", "global", "local", "nonlocal", "legb", "namespace", "closure"],
    }

    for topic, keywords in topic_map.items():
        for kw in keywords:
            if kw in q:
                return PYTHON_TOPICS[topic]

    if any(w in q for w in ["hello", "hi ", "hey", "hii"]):
        return "👋 Hello! I'm your Python tutor. Ask me about any Python topic — variables, loops, functions, classes, recursion, decorators, generators, file handling, and more!"

    if any(w in q for w in ["what is python", "about python", "why python", "learn python"]):
        return """🐍 WHAT IS PYTHON?
━━━━━━━━━━━━━━━━━━━━
Python is a high-level language created by Guido van Rossum in 1991.

WHY LEARN PYTHON:
  ✅ Simple syntax — reads like English
  ✅ Huge community and job market
  ✅ Web, AI, Data Science, Automation
  ✅ Free and open source
  ✅ 100,000+ packages available

WHAT YOU CAN BUILD:
  🌐 Web — Flask, Django
  🤖 AI/ML — TensorFlow, PyTorch
  📊 Data — Pandas, NumPy, Matplotlib
  🎮 Games — Pygame
  🔧 Automation — scripts, bots, scrapers

START WITH:
  print("Hello, World!")"""

    if "list" in q and "tuple" in q:
        return """LIST vs TUPLE
━━━━━━━━━━━━━━━━━━━━
LIST  → mutable, [], has append/remove
TUPLE → immutable, (), faster

USE LIST  → when data changes
USE TUPLE → for fixed data (coordinates, config)"""

    if "for" in q and "while" in q:
        return """FOR vs WHILE
━━━━━━━━━━━━━━━━━━━━
FOR   → know how many times: for i in range(5)
WHILE → condition-based: while count < 5

RULE: count known → for. Condition-based → while."""

    # Fallback to AI
    try:
        return call_claude(
            system_prompt="""You are an expert Python tutor. Answer the question clearly with:
- Plain English explanation
- Code examples with comments
- Common mistakes to avoid
Format with headers and bullet points. Be beginner-friendly.""",
            user_message=question,
            max_tokens=800
        )
    except Exception:
        return """🤔 I don't have a specific answer for that yet.

TOPICS I KNOW DEEPLY:
  Variables, Strings, Lists, Tuples, Sets, Dicts
  Loops, Functions, Classes, Recursion
  Decorators, Generators, Comprehensions
  Error handling, File handling, Modules, Scope

TRY ASKING:
  → "How do decorators work?"
  → "Explain recursion with examples"
  → "What is OOP in Python?"
  → "How does a generator work?" """


@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")
    answer = get_deep_answer(question)
    return jsonify({"answer": answer})


@app.route("/problems")
def get_problems():
    with open("lessons/practice_problems.json", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/course")
def get_course():
    with open("lessons/python_course.json", encoding="utf-8") as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(debug=True)