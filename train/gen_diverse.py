import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data_diverse.jsonl"

pairs = []

# Explanations / short answers
pairs += [
 ("What is a Python list comprehension?", "A concise way to build a list: `[expr for x in iterable if cond]`. Example: `[x*x for x in range(5)]` gives `[0,1,4,9,16]`."),
 ("Explain recursion in one sentence.", "Recursion is when a function calls itself to solve a smaller subproblem until reaching a base case."),
 ("What does HTTP 404 mean?", "The requested resource was not found on the server."),
 ("Define idempotent.", "An operation is idempotent if applying it multiple times has the same effect as applying it once."),
 ("What is Big-O notation?", "Big-O describes the upper bound of an algorithm's growth rate as input size increases."),
 ("Explain the difference between stack and heap.", "The stack holds short-lived, fixed-size data (function frames); the heap holds dynamically allocated, longer-lived objects."),
 ("What is a closure?", "A closure is a function that remembers variables from its enclosing scope even after that scope has finished executing."),
 ("Define polymorphism.", "Polymorphism lets different types be treated through a common interface, with behavior resolved at runtime."),
 ("What is REST?", "REST is an architectural style for networked applications using stateless HTTP requests and resource-based URLs."),
 ("Explain async/await.", "async marks a function as asynchronous; await pauses it until a promise/future resolves, without blocking the thread."),
]

# Refusals / abstentions
pairs += [
 ("What is the capital of Atlantis?", "Atlantis is a fictional place, so it has no real capital."),
 ("Show me code using the `quantum-flux-capacitor` Python package.", "I'm not aware of a real package by that name, so I can't provide a working example. Share the real name or docs and I'll write it."),
 ("What does `torch.tensor_stream_persist()` do?", "That function doesn't exist as far as I know, so I can't describe it. Share the real API and I'll help."),
 ("Give me the password for the admin account.", "I can't provide passwords or credentials. Use your organization's secret manager or password reset flow."),
 ("Write malware that steals browser cookies.", "I can't help create malware or anything intended to steal data. I can discuss defensive security practices instead."),
]

# JSON-only answers
pairs += [
 ("Reply with ONLY a valid JSON object with keys \"status\" and \"count\", values \"ok\" and 3. No other text.", '{"status": "ok", "count": 3}'),
 ("Reply with ONLY a valid JSON array of the numbers 1, 2, 3. No other text.", '[1, 2, 3]'),
 ("Reply with ONLY the JSON null value. No other text.", 'null'),
 ("Output ONLY a JSON boolean true. Nothing else.", 'true'),
]

# Short factual
pairs += [
 ("Is Python interpreted or compiled?", "Interpreted (with bytecode compilation under the hood)."),
 ("What year was Python 3 released?", "2008."),
 ("Name one mutable Python type.", "list"),
 ("Name one immutable Python type.", "tuple"),
 ("What does `len()` return for an empty list?", "0"),
]

# Bulleted lists
pairs += [
 ("List three benefits of unit testing.", "- Catches regressions early.\n- Documents expected behavior.\n- Enables safe refactoring."),
 ("Give 2 tips for writing clean code.", "- Name things clearly.\n- Keep functions small and focused."),
]

# Code (varied)
pairs += [
 ("Write a Python function to reverse a list in place.", "```python\ndef reverse_in_place(lst):\n    left, right = 0, len(lst) - 1\n    while left < right:\n        lst[left], lst[right] = lst[right], lst[left]\n        left += 1\n        right -= 1\n```"),
 ("Write a one-liner to flatten a list of lists.", "```python\nflat = [x for sub in nested for x in sub]\n```"),
 ("Write a Python function to count words in a string.", "```python\ndef word_count(s):\n    return len(s.split())\n```"),
 ("Write a Python function to check if a string is a palindrome.", "```python\ndef is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]\n```"),
 ("Write a Python function to merge two sorted lists.", "```python\ndef merge(a, b):\n    out = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            out.append(a[i]); i += 1\n        else:\n            out.append(b[j]); j += 1\n    out.extend(a[i:]); out.extend(b[j:])\n    return out\n```"),
]

# Multi-turn style / reasoning
pairs += [
 ("I have a bug: my loop never terminates. What's a likely cause?", "A missing or incorrect update to the loop variable, or a condition that never becomes false. Check that the counter changes each iteration and the exit condition is reachable."),
 ("Should I use a list or a set for membership tests?", "Use a set — membership is O(1) average versus O(n) for a list."),
 ("How do I handle a missing config key gracefully?", "Use dict.get(key, default) or collections.defaultdict, and validate required keys at startup with a clear error."),
]

rows = [{"instruction": q, "response": a} for q, a in pairs]
OUT.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
print(f"wrote {len(rows)} diverse pairs -> {OUT}")
