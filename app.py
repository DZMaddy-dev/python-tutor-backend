import json
import subprocess
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://python-ai-tutor-37ba0.web.app"
])

# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    return "Python AI Tutor Backend Running"

# -----------------------------
# Error Explainer
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
        return "ModuleNotFoundError: You tried to import a module that isn't installed."
    elif "RecursionError" in error_message:
        return "RecursionError: Your function is calling itself too many times. Check your base case."
    elif "FileNotFoundError" in error_message:
        return "FileNotFoundError: The file you tried to open doesn't exist. Check the file path."
    else:
        return "Python encountered an error. Read the error message carefully and check your syntax."

# -----------------------------
# Code Explainer
# -----------------------------
def explain_code_locally(code):
    lines = code.strip().split("\n")
    explanations = []
    for line in lines:
        line = line.strip()
        if not line: continue
        elif line.startswith("#"): explanations.append(f'`{line}` → comment (ignored by Python).')
        elif line.startswith("print"): explanations.append(f'`{line}` → prints output to screen.')
        elif line.startswith("for"): explanations.append(f'`{line}` → starts a for loop.')
        elif line.startswith("while"): explanations.append(f'`{line}` → starts a while loop.')
        elif line.startswith("if"): explanations.append(f'`{line}` → checks a condition.')
        elif line.startswith("elif"): explanations.append(f'`{line}` → checks another condition.')
        elif line.startswith("else"): explanations.append(f'`{line}` → runs if no condition matched.')
        elif line.startswith("def"): explanations.append(f'`{line}` → defines a function.')
        elif line.startswith("class"): explanations.append(f'`{line}` → defines a class.')
        elif line.startswith("return"): explanations.append(f'`{line}` → returns a value from the function.')
        elif line.startswith("import") or line.startswith("from"): explanations.append(f'`{line}` → imports a module.')
        elif line.startswith("try"): explanations.append(f'`{line}` → starts error handling block.')
        elif line.startswith("except"): explanations.append(f'`{line}` → catches an error.')
        elif line.startswith("break"): explanations.append(f'`{line}` → exits the loop immediately.')
        elif line.startswith("continue"): explanations.append(f'`{line}` → skips to next loop iteration.')
        elif "=" in line: explanations.append(f'`{line}` → stores a value in a variable.')
        else: explanations.append(f'`{line}` → executes this Python statement.')
    return "\n".join(explanations)

# -----------------------------
# Code Fixer
# -----------------------------
def fix_code_locally(code):
    lines = code.split("\n")
    fixed = []
    for line in lines:
        stripped = line.rstrip()
        lstripped = stripped.lstrip()
        keywords_needing_colon = ["for ", "while ", "if ", "elif ", "else", "def ", "class "]
        if lstripped and not stripped.endswith(":") and not stripped.endswith(",") and not stripped.endswith("\\"):
            for kw in keywords_needing_colon:
                if lstripped.startswith(kw) or lstripped == "else":
                    stripped = stripped + ":"
                    break
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces % 4 != 0 and leading_spaces > 0:
            correct_indent = round(leading_spaces / 4) * 4
            stripped = " " * correct_indent + stripped.lstrip()
        print_no_paren = re.match(r'^(\s*)print\s+(?!\()(.+)$', stripped)
        if print_no_paren:
            indent = print_no_paren.group(1)
            content = print_no_paren.group(2).strip()
            stripped = f'{indent}print({content})'
        single_eq = re.match(r'^(\s*)(if|elif|while)\s+(.+[^=!<>])=([^=].*)(:)$', stripped)
        if single_eq:
            stripped = f'{single_eq.group(1)}{single_eq.group(2)} {single_eq.group(3)}=={single_eq.group(4)}:'
        stripped = re.sub(r',(?! )(?!=)', ', ', stripped)
        for wrong, right in [("Int(","int("),("Float(","float("),("Str(","str("),("String(","str("),
                              ("Print(","print("),("Input(","input("),("Len(","len("),("Range(","range(")]:
            stripped = stripped.replace(wrong, right)
        stripped = re.sub(r'\btrue\b', 'True', stripped)
        stripped = re.sub(r'\bfalse\b', 'False', stripped)
        stripped = re.sub(r'\bnone\b', 'None', stripped)
        stripped = re.sub(r'\bAND\b', 'and', stripped)
        stripped = re.sub(r'\bOR\b', 'or', stripped)
        stripped = re.sub(r'\bNOT\b', 'not', stripped)
        fixed.append(stripped)
    result = "\n".join(fixed)
    result = re.sub(r';\s*\n', '\n', result)
    result = re.sub(r';\s*$', '', result)
    return result

# -----------------------------
# Deep Topic Answers
# -----------------------------
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

TYPE CHECKING:
  x = 42
  print(type(x))  # <class 'int'>

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
  print(f"My name is {name} and I am {age} years old.")
  # Output: My name is Aryan and I am 19 years old.""",

    "string": """📝 STRINGS in Python
━━━━━━━━━━━━━━━━━━━━
A string is a sequence of characters enclosed in quotes.

CREATING STRINGS:
  s1 = "Hello"
  s2 = 'World'
  s3 = \"\"\"Multi
  line string\"\"\"

COMMON OPERATIONS:
  s = "hello world"
  print(len(s))              # 11
  print(s.upper())           # HELLO WORLD
  print(s.lower())           # hello world
  print(s.title())           # Hello World
  print(s.replace("world", "Python"))  # hello Python
  print(s.split(" "))        # ['hello', 'world']
  print(s.strip())           # removes spaces
  print(s[0])                # h (first char)
  print(s[-1])               # d (last char)
  print(s[0:5])              # hello (slicing)
  print(s.find("world"))     # 6 (position)
  print(s.count("l"))        # 3

F-STRINGS (best way to format):
  name = "Aryan"
  age = 19
  print(f"My name is {name}, age {age}")
  print(f"Next year I'll be {age + 1}")

CHECKING:
  print(s.startswith("hello"))  # True
  print(s.endswith("world"))    # True
  print("hello" in s)           # True
  print(s.isdigit())            # False
  print("123".isdigit())        # True
  print(s.isalpha())            # False (has space)""",

    "list": """📋 LISTS in Python
━━━━━━━━━━━━━━━━━━━━
A list stores multiple values in order. It is mutable (can change).

CREATING:
  fruits = ["apple", "banana", "mango"]
  numbers = [1, 2, 3, 4, 5]
  mixed = [1, "hello", True, 3.14]
  empty = []

ACCESSING:
  print(fruits[0])    # apple (first)
  print(fruits[-1])   # mango (last)
  print(fruits[1:3])  # ['banana', 'mango']

MODIFYING:
  fruits.append("grape")       # add to end
  fruits.insert(1, "kiwi")     # add at index 1
  fruits.remove("banana")      # remove by value
  fruits.pop()                 # remove last
  fruits.pop(0)                # remove at index 0
  fruits[0] = "pear"           # update value

USEFUL METHODS:
  print(len(fruits))           # count items
  print("apple" in fruits)     # True/False
  fruits.sort()                # sort alphabetically
  fruits.reverse()             # reverse order
  fruits.clear()               # empty the list
  copy = fruits.copy()         # make a copy
  print(fruits.index("mango")) # get position

LIST COMPREHENSION:
  squares = [x**2 for x in range(10)]
  evens = [x for x in range(20) if x % 2 == 0]

LOOPING:
  for fruit in fruits:
      print(fruit)

  for i, fruit in enumerate(fruits):
      print(i, fruit)  # shows index too

NESTED LIST (2D):
  matrix = [[1,2,3], [4,5,6], [7,8,9]]
  print(matrix[0][1])  # 2""",

    "dictionary": """📚 DICTIONARIES in Python
━━━━━━━━━━━━━━━━━━━━
A dictionary stores key-value pairs. Like a real dictionary — word → meaning.

CREATING:
  student = {
      "name": "Aryan",
      "age": 19,
      "grade": "A"
  }

ACCESSING:
  print(student["name"])           # Aryan
  print(student.get("age"))        # 19
  print(student.get("marks", 0))   # 0 (default)

ADDING / UPDATING:
  student["city"] = "Delhi"        # add new key
  student["age"] = 20              # update existing

REMOVING:
  del student["grade"]
  student.pop("city")
  student.clear()                  # remove all

LOOPING:
  for key in student:
      print(key, ":", student[key])

  for key, value in student.items():
      print(key, "→", value)

  for key in student.keys():
  for val in student.values():

CHECKING:
  if "name" in student:
      print("Name found!")

NESTED DICT:
  school = {
      "student1": {"name": "Aryan", "age": 19},
      "student2": {"name": "Rahul", "age": 20}
  }
  print(school["student1"]["name"])  # Aryan

DICT COMPREHENSION:
  squares = {x: x**2 for x in range(5)}
  # {0:0, 1:1, 2:4, 3:9, 4:16}""",

    "tuple": """🔒 TUPLES in Python
━━━━━━━━━━━━━━━━━━━━
A tuple is like a list but IMMUTABLE — cannot be changed after creation.

CREATING:
  coords = (10, 20)
  colors = ("red", "green", "blue")
  single = (42,)   # comma needed for single item!
  empty = ()

ACCESSING:
  print(coords[0])    # 10
  print(colors[-1])   # blue
  print(colors[0:2])  # ('red', 'green')

WHY USE TUPLES?
  ✅ Faster than lists
  ✅ Protects data from changes
  ✅ Can be used as dictionary keys
  ✅ Good for fixed data (coordinates, RGB colors)

TUPLE UNPACKING:
  x, y = (10, 20)
  a, b, c = ("red", "green", "blue")

  # Swap variables elegantly
  a, b = b, a

USEFUL OPERATIONS:
  print(len(colors))           # 3
  print("red" in colors)       # True
  print(colors.count("red"))   # 1
  print(colors.index("green")) # 1

CONVERTING:
  my_list = list(colors)    # tuple → list
  my_tuple = tuple([1,2,3]) # list → tuple

LIST vs TUPLE:
  list  → mutable, [], slower, methods like append/remove
  tuple → immutable, (), faster, no add/remove methods""",

    "set": """🔵 SETS in Python
━━━━━━━━━━━━━━━━━━━━
A set stores UNIQUE values only — no duplicates, unordered.

CREATING:
  fruits = {"apple", "banana", "mango"}
  numbers = {1, 2, 3}
  empty = set()   # NOT {} — that creates a dict!

AUTO-REMOVES DUPLICATES:
  s = {1, 2, 2, 3, 3, 3}
  print(s)  # {1, 2, 3}

ADDING / REMOVING:
  fruits.add("grape")
  fruits.update(["kiwi", "pear"])
  fruits.remove("banana")   # error if not found
  fruits.discard("banana")  # no error if not found
  fruits.pop()              # removes random item

SET OPERATIONS (most powerful feature!):
  a = {1, 2, 3, 4}
  b = {3, 4, 5, 6}

  print(a | b)  # UNION: {1,2,3,4,5,6} — all items
  print(a & b)  # INTERSECTION: {3,4} — common items
  print(a - b)  # DIFFERENCE: {1,2} — in a but not b
  print(a ^ b)  # SYMMETRIC: {1,2,5,6} — not in both

REAL WORLD USE:
  # Remove duplicates from list
  names = ["Aryan", "Rahul", "Aryan", "Priya"]
  unique = list(set(names))

  # Find common items in two lists
  list1 = [1, 2, 3, 4]
  list2 = [3, 4, 5, 6]
  common = set(list1) & set(list2)  # {3, 4}""",

    "loop": """🔄 LOOPS in Python
━━━━━━━━━━━━━━━━━━━━
Loops let you repeat code multiple times.

━━ FOR LOOP — when you know how many times ━━

  for i in range(5):
      print(i)  # 0, 1, 2, 3, 4

  for i in range(1, 6):
      print(i)  # 1, 2, 3, 4, 5

  for i in range(0, 10, 2):
      print(i)  # 0, 2, 4, 6, 8 (step=2)

  fruits = ["apple", "banana", "mango"]
  for fruit in fruits:
      print(fruit)

  for i, fruit in enumerate(fruits):
      print(i, fruit)  # 0 apple, 1 banana...

━━ WHILE LOOP — when you don't know how many times ━━

  count = 0
  while count < 5:
      print(count)
      count += 1

  while True:
      answer = input("Type quit to stop: ")
      if answer == "quit":
          break

━━ LOOP CONTROL ━━

  break    → exit loop completely
  continue → skip current, go to next
  pass     → do nothing (placeholder)

  for i in range(10):
      if i == 5: break       # stops at 5
      if i % 2 == 0: continue # skips evens
      print(i)               # prints 1, 3

━━ NESTED LOOPS ━━

  for i in range(1, 4):
      for j in range(1, 4):
          print(i * j, end=" ")
      print()  # newline after each row

━━ ELSE WITH LOOP ━━

  for i in range(5):
      print(i)
  else:
      print("Loop finished!")  # runs after loop ends""",

    "function": """⚙️ FUNCTIONS in Python
━━━━━━━━━━━━━━━━━━━━
A function is a reusable block of code that performs a specific task.

BASIC FUNCTION:
  def greet():
      print("Hello, World!")

  greet()  # calling the function

WITH PARAMETERS:
  def greet(name):
      print(f"Hello, {name}!")

  greet("Aryan")   # Hello, Aryan!

WITH RETURN VALUE:
  def add(a, b):
      return a + b

  result = add(3, 5)  # result = 8

DEFAULT PARAMETERS:
  def greet(name, msg="Good morning"):
      print(f"{msg}, {name}!")

  greet("Aryan")               # Good morning, Aryan!
  greet("Aryan", "Good night") # Good night, Aryan!

*ARGS — variable number of arguments:
  def total(*numbers):
      return sum(numbers)

  print(total(1, 2, 3, 4, 5))  # 15

**KWARGS — keyword arguments:
  def show_info(**details):
      for key, value in details.items():
          print(key, ":", value)

  show_info(name="Aryan", age=19, city="Delhi")

LAMBDA — one line function:
  square = lambda x: x ** 2
  add = lambda a, b: a + b
  print(square(5))   # 25
  print(add(3, 4))   # 7

SCOPE:
  x = 10  # global

  def my_func():
      x = 20  # local — different!
      print(x)  # 20

  my_func()
  print(x)   # 10 — global unchanged

RETURNING MULTIPLE VALUES:
  def min_max(numbers):
      return min(numbers), max(numbers)

  lo, hi = min_max([3, 1, 4, 1, 5, 9])
  print(lo, hi)  # 1 9""",

    "class": """🏗️ CLASSES & OOP in Python
━━━━━━━━━━━━━━━━━━━━
A class is a blueprint for creating objects.

CREATING A CLASS:
  class Dog:
      def __init__(self, name, breed):
          self.name = name    # instance variable
          self.breed = breed

      def bark(self):
          print(f"{self.name} says: Woof!")

      def info(self):
          return f"{self.name} is a {self.breed}"

CREATING OBJECTS:
  dog1 = Dog("Bruno", "Labrador")
  dog2 = Dog("Max", "Poodle")

  dog1.bark()        # Bruno says: Woof!
  print(dog2.info()) # Max is a Poodle

INHERITANCE:
  class Animal:
      def __init__(self, name):
          self.name = name

      def speak(self):
          return f"{self.name} makes a sound"

  class Dog(Animal):
      def speak(self):
          return f"{self.name} says Woof!"

  class Cat(Animal):
      def speak(self):
          return f"{self.name} says Meow!"

  d = Dog("Bruno")
  c = Cat("Whiskers")
  print(d.speak())  # Bruno says Woof!
  print(c.speak())  # Whiskers says Meow!

SPECIAL METHODS:
  class Book:
      def __init__(self, title, pages):
          self.title = title
          self.pages = pages

      def __str__(self):      # for print()
          return f"{self.title} ({self.pages} pages)"

      def __len__(self):      # for len()
          return self.pages

  b = Book("Python 101", 300)
  print(b)        # Python 101 (300 pages)
  print(len(b))   # 300

4 PILLARS OF OOP:
  Encapsulation  → hide internal details
  Inheritance    → child class gets parent features
  Polymorphism   → same method, different behavior
  Abstraction    → show only what's necessary""",

    "recursion": """🔁 RECURSION in Python
━━━━━━━━━━━━━━━━━━━━
Recursion = a function that calls itself to solve smaller versions of the same problem.

GOLDEN RULE — every recursive function needs:
  1. BASE CASE — when to stop
  2. RECURSIVE CASE — call itself with smaller input

EXAMPLE 1 — Factorial:
  def factorial(n):
      if n == 0:           # base case
          return 1
      return n * factorial(n - 1)  # recursive case

  print(factorial(5))  # 120

HOW IT WORKS:
  factorial(5)
  → 5 * factorial(4)
  → 5 * 4 * factorial(3)
  → 5 * 4 * 3 * factorial(2)
  → 5 * 4 * 3 * 2 * factorial(1)
  → 5 * 4 * 3 * 2 * 1
  → 120

EXAMPLE 2 — Fibonacci:
  def fibonacci(n):
      if n <= 1: return n
      return fibonacci(n-1) + fibonacci(n-2)

  for i in range(8):
      print(fibonacci(i), end=" ")
  # 0 1 1 2 3 5 8 13

EXAMPLE 3 — Sum of list:
  def list_sum(lst):
      if len(lst) == 0: return 0
      return lst[0] + list_sum(lst[1:])

  print(list_sum([1, 2, 3, 4, 5]))  # 15

EXAMPLE 4 — Count down:
  def countdown(n):
      if n <= 0:
          print("Go!")
          return
      print(n)
      countdown(n - 1)

  countdown(5)  # 5, 4, 3, 2, 1, Go!

WARNING:
  Python has recursion limit of 1000 by default.
  Use loops when recursion depth could be very large.""",

    "error": """⚠️ ERROR HANDLING in Python
━━━━━━━━━━━━━━━━━━━━
Use try/except to handle errors gracefully instead of crashing.

BASIC STRUCTURE:
  try:
      x = int(input("Enter a number: "))
      print(10 / x)
  except ValueError:
      print("That's not a valid number!")
  except ZeroDivisionError:
      print("Cannot divide by zero!")

CATCHING ANY ERROR:
  try:
      result = 10 / 0
  except Exception as e:
      print(f"Error: {e}")

ELSE AND FINALLY:
  try:
      x = int("42")
  except ValueError:
      print("Conversion failed")
  else:
      print("Success! x =", x)     # runs if NO error
  finally:
      print("This always runs!")    # runs no matter what

RAISING YOUR OWN ERRORS:
  def set_age(age):
      if age < 0:
          raise ValueError("Age cannot be negative!")
      return age

  try:
      set_age(-5)
  except ValueError as e:
      print(e)

COMMON EXCEPTIONS:
  ValueError       → int("hello")
  TypeError        → 1 + "a"
  IndexError       → list[100] out of range
  KeyError         → dict["missing_key"]
  ZeroDivisionError → 10 / 0
  FileNotFoundError → open("ghost.txt")
  AttributeError   → "hello".push()
  ImportError      → import nonexistent_module
  NameError        → using undefined variable
  RecursionError   → infinite recursion""",

    "file": """📁 FILE HANDLING in Python
━━━━━━━━━━━━━━━━━━━━
Python can read and write files using open().

OPEN MODES:
  "r"  → read only (default)
  "w"  → write (creates new / overwrites)
  "a"  → append (adds to end)
  "r+" → read and write

READING:
  with open("data.txt", "r") as f:
      content = f.read()       # entire file
      print(content)

  with open("data.txt", "r") as f:
      lines = f.readlines()    # list of lines

  with open("data.txt", "r") as f:
      for line in f:           # line by line
          print(line.strip())

WRITING:
  with open("output.txt", "w") as f:
      f.write("Hello World\\n")
      f.write("Second line\\n")

APPENDING:
  with open("output.txt", "a") as f:
      f.write("New line\\n")

JSON FILES:
  import json

  # Write JSON
  data = {"name": "Aryan", "age": 19}
  with open("data.json", "w") as f:
      json.dump(data, f, indent=2)

  # Read JSON
  with open("data.json", "r") as f:
      data = json.load(f)
      print(data["name"])

CHECKING IF FILE EXISTS:
  import os
  if os.path.exists("data.txt"):
      print("File found!")

WHY USE 'with'?
  Automatically closes file even if error occurs.
  Always use: with open(...) as f""",

    "lambda": """⚡ LAMBDA FUNCTIONS in Python
━━━━━━━━━━━━━━━━━━━━
Lambda = a small anonymous one-line function.

SYNTAX:
  lambda arguments: expression

BASIC EXAMPLES:
  square = lambda x: x ** 2
  add = lambda x, y: x + y
  greet = lambda name: f"Hello, {name}!"

  print(square(5))      # 25
  print(add(3, 4))      # 7
  print(greet("Aryan")) # Hello, Aryan!

WITH MAP — apply to every item:
  numbers = [1, 2, 3, 4, 5]
  squares = list(map(lambda x: x**2, numbers))
  print(squares)  # [1, 4, 9, 16, 25]

WITH FILTER — keep matching items:
  numbers = [1, 2, 3, 4, 5, 6, 7, 8]
  evens = list(filter(lambda x: x % 2 == 0, numbers))
  print(evens)  # [2, 4, 6, 8]

WITH SORTED — custom sort:
  students = [("Aryan", 85), ("Rahul", 92), ("Priya", 78)]
  by_score = sorted(students, key=lambda s: s[1])
  print(by_score)
  # [('Priya', 78), ('Aryan', 85), ('Rahul', 92)]

WITH REDUCE:
  from functools import reduce
  total = reduce(lambda x, y: x + y, [1,2,3,4,5])
  print(total)  # 15

WHEN TO USE:
  ✅ Short simple operations
  ✅ Passing function as argument
  ✅ Sorting with custom keys
  ❌ Complex logic — use regular def instead""",

    "comprehension": """🚀 LIST COMPREHENSIONS
━━━━━━━━━━━━━━━━━━━━
A compact one-line way to create lists.

SYNTAX:
  [expression for item in iterable]
  [expression for item in iterable if condition]

WITHOUT comprehension:
  squares = []
  for x in range(10):
      squares.append(x**2)

WITH comprehension:
  squares = [x**2 for x in range(10)]
  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

WITH CONDITION:
  evens = [x for x in range(20) if x % 2 == 0]
  words = ["hello", "world", "python"]
  upper = [w.upper() for w in words]
  long_words = [w for w in words if len(w) > 4]

DICT COMPREHENSION:
  squares = {x: x**2 for x in range(6)}
  # {0:0, 1:1, 2:4, 3:9, 4:16, 5:25}

SET COMPREHENSION:
  unique_lengths = {len(w) for w in ["hi","hello","hey"]}
  # {2, 3, 5}

NESTED (2D list / matrix):
  matrix = [[i*j for j in range(1,4)] for i in range(1,4)]
  # [[1,2,3], [2,4,6], [3,6,9]]

FLATTENING:
  nested = [[1,2,3], [4,5,6], [7,8,9]]
  flat = [x for row in nested for x in row]
  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

WHEN TO USE:
  ✅ Simple transformations
  ✅ Filtering lists
  ❌ Complex logic — use regular for loop""",

    "decorator": """🎨 DECORATORS in Python
━━━━━━━━━━━━━━━━━━━━
A decorator wraps a function to add behavior without changing its code.

SIMPLE EXAMPLE:
  def my_decorator(func):
      def wrapper():
          print("Before function")
          func()
          print("After function")
      return wrapper

  @my_decorator
  def say_hello():
      print("Hello!")

  say_hello()
  # Before function
  # Hello!
  # After function

WITH ARGUMENTS:
  def my_decorator(func):
      def wrapper(*args, **kwargs):
          print(f"Calling {func.__name__}")
          result = func(*args, **kwargs)
          return result
      return wrapper

  @my_decorator
  def add(a, b):
      return a + b

  print(add(3, 5))

TIMER DECORATOR (real world):
  import time

  def timer(func):
      def wrapper(*args, **kwargs):
          start = time.time()
          result = func(*args, **kwargs)
          print(f"Took {time.time()-start:.4f}s")
          return result
      return wrapper

  @timer
  def slow():
      time.sleep(1)

  slow()  # Took 1.0012s

BUILT-IN DECORATORS:
  @staticmethod   → no self needed
  @classmethod    → receives class as first arg
  @property       → makes method act like attribute

  class Circle:
      def __init__(self, radius):
          self.radius = radius

      @property
      def area(self):
          return 3.14 * self.radius ** 2

  c = Circle(5)
  print(c.area)  # 78.5 (no parentheses needed!)""",

    "generator": """⚡ GENERATORS in Python
━━━━━━━━━━━━━━━━━━━━
A generator yields values one at a time — very memory efficient!

BASIC GENERATOR:
  def count_up(n):
      i = 0
      while i < n:
          yield i    # pauses here and returns value
          i += 1

  gen = count_up(5)
  print(next(gen))  # 0
  print(next(gen))  # 1

  for num in count_up(5):
      print(num)  # 0 1 2 3 4

MEMORY DIFFERENCE:
  # List — ALL values stored in memory
  big_list = [x**2 for x in range(1000000)]  # ~8MB

  # Generator — ONE value at a time
  big_gen = (x**2 for x in range(1000000))   # ~100 bytes!

GENERATOR EXPRESSION:
  gen = (x**2 for x in range(10))  # () not []
  print(list(gen))  # [0, 1, 4, 9, 16, 25...]

INFINITE GENERATOR:
  def infinite_counter():
      n = 0
      while True:
          yield n
          n += 1

  counter = infinite_counter()
  for _ in range(5):
      print(next(counter))  # 0 1 2 3 4

PRACTICAL EXAMPLE:
  def fibonacci():
      a, b = 0, 1
      while True:
          yield a
          a, b = b, a + b

  fib = fibonacci()
  for _ in range(10):
      print(next(fib), end=" ")
  # 0 1 1 2 3 5 8 13 21 34

WHEN TO USE:
  ✅ Large datasets
  ✅ Infinite sequences
  ✅ Memory-efficient pipelines
  ✅ When you don't need all values at once""",

    "module": """📦 MODULES in Python
━━━━━━━━━━━━━━━━━━━━
A module is a Python file with reusable code you can import.

IMPORTING:
  import math
  print(math.pi)          # 3.14159
  print(math.sqrt(16))    # 4.0
  print(math.floor(3.7))  # 3
  print(math.ceil(3.2))   # 4

  import random
  print(random.randint(1, 100))       # random 1-100
  print(random.choice(["a","b","c"])) # random item
  nums = [1,2,3,4,5]
  random.shuffle(nums)                # shuffle in place

FROM IMPORT:
  from math import pi, sqrt, floor
  print(pi)         # 3.14159
  print(sqrt(25))   # 5.0

ALIASING:
  import numpy as np
  import pandas as pd
  import matplotlib.pyplot as plt

YOUR OWN MODULE:
  # Save as mytools.py
  def add(a, b): return a + b
  def square(x): return x ** 2
  PI = 3.14159

  # Use in another file
  import mytools
  print(mytools.add(3, 4))   # 7
  print(mytools.PI)           # 3.14159

USEFUL BUILT-IN MODULES:
  math       → sqrt, pi, sin, cos, log
  random     → randint, choice, shuffle
  datetime   → date, time, timedelta
  os         → files, folders, paths
  sys        → exit, path, version
  json       → read/write JSON
  re         → regular expressions
  time       → sleep, perf_counter
  collections → Counter, defaultdict, deque
  itertools  → chain, cycle, islice, product

INSTALLING PACKAGES:
  pip install numpy
  pip install pandas
  pip install requests
  pip install flask""",

    "slicing": """✂️ SLICING in Python
━━━━━━━━━━━━━━━━━━━━
Extract portions of sequences (lists, strings, tuples).

SYNTAX:
  sequence[start:stop:step]

LIST SLICING:
  nums = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

  nums[2:5]     # [2, 3, 4]
  nums[:4]      # [0, 1, 2, 3]
  nums[6:]      # [6, 7, 8, 9]
  nums[:]       # full copy
  nums[::2]     # [0, 2, 4, 6, 8] — every 2nd
  nums[::-1]    # [9,8,7,6,5,4,3,2,1,0] — REVERSED!
  nums[1:8:2]   # [1, 3, 5, 7]

NEGATIVE INDICES:
  nums[-1]      # 9 (last)
  nums[-3:]     # [7, 8, 9] (last 3)
  nums[:-2]     # [0..7] (all except last 2)

STRING SLICING:
  s = "Hello, Python!"

  s[0:5]        # Hello
  s[7:]         # Python!
  s[::-1]       # !nohtyP ,olleH (reversed)
  s[::2]        # Hlo yhn

PRACTICAL USES:
  # Reverse a string
  "hello"[::-1]    # "olleh"

  # Check palindrome
  word = "racecar"
  word == word[::-1]  # True

  # First/Last N items
  items = [1,2,3,4,5,6,7,8,9,10]
  first3 = items[:3]    # [1, 2, 3]
  last3 = items[-3:]    # [8, 9, 10]
  middle = items[3:7]   # [4, 5, 6, 7]

  # Every other character
  "abcdefgh"[::2]  # "aceg" """,

    "scope": """🔭 SCOPE in Python
━━━━━━━━━━━━━━━━━━━━
Scope = where a variable can be accessed. Python uses LEGB rules.

LEGB:
  L → Local    (inside current function)
  E → Enclosing (outer function)
  G → Global   (module level)
  B → Built-in  (len, print, range...)

LOCAL vs GLOBAL:
  x = 10  # global

  def my_func():
      x = 20  # local — completely separate!
      print(x)  # 20

  my_func()
  print(x)  # 10 — global unchanged

GLOBAL KEYWORD:
  count = 0

  def increment():
      global count   # use the global count
      count += 1

  increment()
  increment()
  print(count)  # 2

NONLOCAL KEYWORD (nested functions):
  def outer():
      x = 10

      def inner():
          nonlocal x   # modify outer's x
          x = 20

      inner()
      print(x)  # 20

  outer()

ENCLOSING SCOPE (closure):
  def multiplier(factor):
      def multiply(number):
          return number * factor  # uses outer's 'factor'
      return multiply

  double = multiplier(2)
  triple = multiplier(3)
  print(double(5))  # 10
  print(triple(5))  # 15

BEST PRACTICE:
  ✅ Avoid global variables
  ✅ Pass values as parameters
  ✅ Return values from functions""",
}

def get_deep_answer(question):
    q = question.lower().strip()

    topic_map = {
        "variable": ["variable", "var ", "assign", "store value", "data type"],
        "string": ["string", "str ", "text", "char", "substr", "split", "join", "strip",
                   "upper", "lower", "replace", "f-string", "format", "endswith", "startswith"],
        "list": ["list", "append", "extend", "insert", "pop", "remove", "sort", "reverse", "array"],
        "dictionary": ["dict", "dictionary", "key", "value", "hashmap", "key-value", ".items()", ".keys()"],
        "tuple": ["tuple", "immutable"],
        "set": ["set ", "union", "intersection", "difference", "unique values", "duplicate"],
        "loop": ["loop", "for loop", "while loop", "iterate", "range(", "break", "continue", "repeat", "enumerate"],
        "function": ["function", "def ", "return", "parameter", "argument", "*args", "**kwargs", "lambda func", "default param"],
        "class": ["class ", "object", "__init__", "self ", "instance", "method", "attribute", "oop", "object oriented"],
        "recursion": ["recursion", "recursive", "base case", "factorial", "fibonacci", "calls itself"],
        "error": ["error", "exception", "try", "except", "finally", "raise", "handle error", "valueerror", "typeerror"],
        "file": ["file", "open(", "read file", "write file", "append mode", "with open", "json file"],
        "lambda": ["lambda", "anonymous function", "map(", "filter(", "reduce("],
        "comprehension": ["comprehension", "list comp", "dict comp", "one line list", "[x for"],
        "decorator": ["decorator", "@my", "wrapper", "wrap function", "@property", "@staticmethod"],
        "generator": ["generator", "yield", "lazy evaluation", "memory efficient"],
        "module": ["module", "import ", "package", "pip install", "library", "from import", "math.", "random."],
        "slicing": ["slice", "slicing", "[::", "[:", "negative index", "reverse list", "reverse string", "[::-1]"],
        "scope": ["scope", "global", "local", "nonlocal", "legb", "namespace", "closure"],
    }

    for topic, keywords in topic_map.items():
        for kw in keywords:
            if kw in q:
                return PYTHON_TOPICS[topic]

    if any(w in q for w in ["hello", "hi ", "hey", "hii"]):
        return "👋 Hello! I'm your Python tutor. Ask me about any Python topic — variables, loops, functions, classes, recursion, decorators, generators, file handling, and much more!"

    if any(w in q for w in ["what is python", "about python", "why python", "learn python"]):
        return """🐍 WHAT IS PYTHON?
━━━━━━━━━━━━━━━━━━━━
Python is a high-level, general-purpose language created by Guido van Rossum in 1991.

WHY LEARN PYTHON:
  ✅ Simple syntax — reads like English
  ✅ Huge community and job market
  ✅ Used in Web, AI, Data Science, Automation
  ✅ Free and open source
  ✅ Massive library ecosystem (100,000+ packages)

WHAT YOU CAN BUILD:
  🌐 Web apps — Flask, Django
  🤖 AI & ML — TensorFlow, PyTorch, scikit-learn
  📊 Data Analysis — Pandas, NumPy, Matplotlib
  🎮 Games — Pygame
  🔧 Automation — scripts, bots, scrapers
  📱 Desktop apps — Tkinter, PyQt

FIRST PYTHON PROGRAM:
  print("Hello, World!")

BASIC SYNTAX:
  # This is a comment
  name = "Aryan"           # variable
  age = 19
  print(f"Hi {name}!")     # output"""

    if "list" in q and "tuple" in q:
        return """LIST vs TUPLE
━━━━━━━━━━━━━━━━━━━━
LIST  → mutable (can change), uses [], has append/remove
TUPLE → immutable (cannot change), uses (), faster

  fruits = ["apple", "banana"]   # list
  fruits.append("mango")         # works!

  coords = (10, 20)              # tuple
  # coords[0] = 5                # ERROR!

USE LIST  → when data changes
USE TUPLE → when data is fixed (coordinates, config)"""

    if "list" in q and "set" in q:
        return """LIST vs SET
━━━━━━━━━━━━━━━━━━━━
LIST → ordered, allows duplicates, access by index
SET  → unordered, no duplicates, faster lookup

  nums = [1, 2, 2, 3]  # list keeps duplicates
  s = {1, 2, 2, 3}     # set becomes {1, 2, 3}

USE LIST → order matters, duplicates needed
USE SET  → unique values, fast 'in' checks, set math"""

    if "for" in q and "while" in q:
        return """FOR vs WHILE LOOP
━━━━━━━━━━━━━━━━━━━━
FOR LOOP — use when you KNOW how many times:
  for i in range(5):
      print(i)  # 0 1 2 3 4

  for item in my_list:
      print(item)

WHILE LOOP — use when you DON'T know how many times:
  while user_input != "quit":
      user_input = input("Enter: ")

  count = 0
  while count < 5:
      count += 1

RULE: If you know the count → for. If condition-based → while."""

    return """🤔 I don't have a specific answer for that yet, but I can help with:

TOPICS I KNOW DEEPLY:
  📦 Variables, Strings, Lists, Tuples, Sets, Dictionaries
  🔄 For loops, While loops, Recursion, Iterators, Generators
  ⚙️ Functions, Lambda, Decorators, Comprehensions
  🏗️ Classes, OOP, Inheritance, Encapsulation
  ⚠️ Error handling, File handling
  📦 Modules, Scope, Slicing

TRY ASKING:
  → "How do decorators work?"
  → "Explain recursion with examples"
  → "Difference between list and tuple"
  → "What is OOP in Python?"
  → "How does a generator work?"
  → "Explain scope in Python" """


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "")
    answer = get_deep_answer(question)
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