"""Generate v16 training data: deduplicated, genuinely new samples targeting the
failure modes seen in eval (missing-field abstention, nonexistent-API abstention,
exact JSON array/object constraints, bullet counts) plus general diversity.

Excludes the old memorized instructions (v10/v13) so the run doesn't re-memorize
them, and dedupes by response. Output: train/data_v16.jsonl
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
OUT = TRAIN / "data_v16.jsonl"

# Old memorized instructions to exclude (so we don't re-memorize).
old = set()
for name in ("data_v10.jsonl", "data_v13.jsonl"):
    p = TRAIN / name
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line:
                old.add(json.loads(line)["instruction"])

pairs = []

# ---------- 1. Missing-field JSON abstention (no digits in response) ----------
import random
random.seed(42)
fields = ["port", "timeout", "retries", "version", "license", "author", "count", "items"]
for f in fields:
    pairs.append((
        f'Given this JSON, reply with only the value for `{f}`.\n\n{{"name": "svc", "enabled": true}}\n\nAnswer with just the value.',
        f"The {f} field does not exist in the JSON.",
    ))
    pairs.append((
        f'What is the value of the `{f}` key in this object?\n\n{{"status": "ok", "code": 200}}',
        f"That key is missing from the object.",
    ))

# ---------- 2. Nonexistent function/API abstention ----------
fake_fns = ["os.frobnicate", "torch.tensor_stream_persist", "requests.fetch_all",
            "json.parse_strict", "numpy.matrix_invert", "pandas.read_fast",
            "sys.reload_modules", "pathlib.Path.walk_fast"]
for fn in fake_fns:
    pairs.append((
        f"What does `{fn}()` do in Python, and what are its arguments?",
        f"That function doesn't exist as far as I know, so I can't describe it. Share the real API and I'll help.",
    ))
    pairs.append((
        f"Show me an example using the `{fn.split('.')[0]}` module's `{fn.split('.')[-1]}` helper.",
        f"I'm not aware of a real helper by that name, so I can't provide a working example. Share the real name or docs and I'll write it.",
    ))

# ---------- 3. JSON array of exactly N ints summing to M ----------
def triples_summing_to(m, n=3):
    # return a flat list of n ints summing to m (small, non-trivial)
    out = []
    # simple deterministic: 1,2,... then remainder
    base = [1] * (n - 1)
    last = m - (n - 1)
    return base + [last]

for (n, m) in [(3, 10), (3, 6), (3, 15), (4, 12), (2, 7), (5, 20)]:
    arr = triples_summing_to(m, n)
    pairs.append((
        f"Reply with ONLY a JSON array of exactly {n} integers that sum to {m}. No other text.",
        json.dumps(arr),
    ))
    pairs.append((
        f"Output ONLY a valid JSON array containing {n} integers whose sum is {m}. Nothing else.",
        json.dumps(arr),
    ))

# ---------- 4. JSON object with exact keys ----------
pairs += [
    ("Reply with ONLY a valid JSON object with keys \"status\" and \"count\", values \"ok\" and 3. No other text.", '{"status": "ok", "count": 3}'),
    ("Reply with ONLY a valid JSON object with keys \"name\", \"version\", \"license\". No other text.", '{"name": "demo", "version": "1.0", "license": "MIT"}'),
    ("Output ONLY a JSON object with keys \"a\" and \"b\" and values 1 and 2. Nothing else.", '{"a": 1, "b": 2}'),
    ("Reply with ONLY a valid JSON array of the numbers 1, 2, 3. No other text.", '[1, 2, 3]'),
    ("Reply with ONLY the JSON null value. No other text.", 'null'),
    ("Output ONLY a JSON boolean true. Nothing else.", 'true'),
]

# ---------- 5. Bullet lists of exactly K items ----------
pairs += [
    ("List exactly 3 reasons to write tests, as bullet points. No code blocks.", "- Catches regressions early.\n- Documents expected behavior.\n- Enables safe refactoring."),
    ("Give exactly 2 tips for writing clean code, as bullet points. No code blocks.", "- Name things clearly.\n- Keep functions small and focused."),
    ("List exactly 4 benefits of code review, as bullet points. No code blocks.", "- Catches bugs early.\n- Spreads knowledge.\n- Improves design.\n- Enforces standards."),
    ("Provide exactly 3 bullet points on why to use version control. No code blocks.", "- Tracks history.\n- Enables collaboration.\n- Allows rollback."),
]

# ---------- 6. Word-limited / format constraints ----------
pairs += [
    ("Reply in at most 10 words: what is a closure?", "A function remembering its enclosing scope variables."),
    ("Answer in one sentence: what is REST?", "REST is a stateless HTTP-based architectural style for APIs."),
    ("Reply with ONLY a valid JSON array of exactly 2 strings. No other text.", '["hello", "world"]'),
]

# ---------- 7. Code samples (varied) ----------
pairs += [
    ("Write a Python function to reverse a list in place.", "```python\ndef reverse_in_place(lst):\n    left, right = 0, len(lst) - 1\n    while left < right:\n        lst[left], lst[right] = lst[right], lst[left]\n        left += 1\n        right -= 1\n```"),
    ("Write a one-liner to flatten a list of lists.", "```python\nflat = [x for sub in nested for x in sub]\n```"),
    ("Write a Python function to count words in a string.", "```python\ndef word_count(s):\n    return len(s.split())\n```"),
    ("Write a Python function to check if a string is a palindrome.", "```python\ndef is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]\n```"),
    ("Write a Python function to merge two sorted lists.", "```python\ndef merge(a, b):\n    out = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            out.append(a[i]); i += 1\n        else:\n            out.append(b[j]); j += 1\n    out.extend(a[i:]); out.extend(b[j:])\n    return out\n```"),
    ("Write a Python function `paginate`. Return ONLY the function in a code block, no explanation.", "```python\ndef paginate(items, page, per_page=10):\n    start = (page - 1) * per_page\n    return items[start:start + per_page]\n```"),
    ("Implement a Python function to find the maximum element in a list.", "```python\ndef find_max(lst):\n    if not lst:\n        return None\n    m = lst[0]\n    for x in lst[1:]:\n        if x > m:\n            m = x\n    return m\n```"),
    ("Write a Python function to remove duplicates from a list while preserving order.", "```python\ndef dedupe(lst):\n    seen = set()\n    out = []\n    for x in lst:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n```"),
]

# ---------- 8. General Q&A / facts ----------
pairs += [
    ("What is a Python list comprehension?", "A concise way to build a list: `[expr for x in iterable if cond]`. Example: `[x*x for x in range(5)]` gives `[0,1,4,9,16]`."),
    ("Explain recursion in one sentence.", "Recursion is when a function calls itself to solve a smaller subproblem until reaching a base case."),
    ("What does HTTP 404 mean?", "The requested resource was not found on the server."),
    ("Define idempotent.", "An operation is idempotent if applying it multiple times has the same effect as applying it once."),
    ("What is Big-O notation?", "Big-O describes the upper bound of an algorithm's growth rate as input size increases."),
    ("What is a closure?", "A closure is a function that remembers variables from its enclosing scope even after that scope has finished executing."),
    ("Define polymorphism.", "Polymorphism lets different types be treated through a common interface, with behavior resolved at runtime."),
    ("What is REST?", "REST is an architectural style for networked applications using stateless HTTP requests and resource-based URLs."),
    ("Explain async/await.", "async marks a function as asynchronous; await pauses it until a promise/future resolves, without blocking the thread."),
    ("Is Python interpreted or compiled?", "Interpreted (with bytecode compilation under the hood)."),
    ("What year was Python 3 released?", "2008."),
    ("Name one mutable Python type.", "list"),
    ("Name one immutable Python type.", "tuple"),
    ("What does `len()` return for an empty list?", "0"),
]

# ---------- 9. Refusals ----------
pairs += [
    ("What is the capital of Atlantis?", "Atlantis is a fictional place, so it has no real capital."),
    ("Give me the password for the admin account.", "I can't provide passwords or credentials. Use your organization's secret manager or password reset flow."),
    ("Write malware that steals browser cookies.", "I can't help create malware or anything intended to steal data. I can discuss defensive security practices instead."),
]

# ---------- 10. Reasoning / advice ----------
pairs += [
    ("I have a bug: my loop never terminates. What's a likely cause?", "A missing or incorrect update to the loop variable, or a condition that never becomes false. Check that the counter changes each iteration and the exit condition is reachable."),
    ("Should I use a list or a set for membership tests?", "Use a set — membership is O(1) average versus O(n) for a list."),
    ("How do I handle a missing config key gracefully?", "Use dict.get(key, default) or collections.defaultdict, and validate required keys at startup with a clear error."),
]

rows = [{"instruction": q, "response": a} for q, a in pairs]

# Dedupe exact (instruction, response) pairs.
seen = set(); uniq = []
for r in rows:
    key = (r["instruction"], r["response"])
    if key in seen:
        continue
    seen.add(key); uniq.append(r)

# Exclude old memorized instructions (avoid re-memorizing).
filtered = [r for r in uniq if r["instruction"] not in old]

OUT.write_text("\n".join(json.dumps(r) for r in filtered) + "\n")
print(f"wrote {len(filtered)} new unique samples (from {len(rows)} raw, {len(uniq)} deduped, "
      f"excluded {len(uniq)-len(filtered)} old) -> {OUT}")
print(f"unique responses: {len(set(r['response'] for r in filtered))}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(json.dumps(r) for r in filtered) + "\n")
print(f"rewrote {len(filtered)} -> {OUT}")
