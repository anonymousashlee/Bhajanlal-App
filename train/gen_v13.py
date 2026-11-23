"""Generate data_v13.jsonl = data_v12 + verified format-targeted + abstention samples."""
import json
import subprocess
import sys
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
OUT = TRAIN / "data_v13.jsonl"
VERIFIED_OK = []

rows = []
for name in ("data_v12.jsonl", "data_beam_free.jsonl"):
    p = TRAIN / name
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))

# ---- format-targeted code samples (verified by exec) ----
code_specs = [
    ("Write a Python function to reverse a string. Return ONLY the function in a code block.",
     "def reverse_string(s):\n    return s[::-1]",
     ["assert reverse_string('hello') == 'olleh'", "assert reverse_string('') == ''"]),
    ("Write a Python function count_vowels(s) returning the number of vowels (a,e,i,o,u, case-insensitive). Return ONLY the function in a code block.",
     "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')",
     ["assert count_vowels('Hello World') == 3", "assert count_vowels('') == 0", "assert count_vowels('AEIOU') == 5"]),
    ("Write a Python function is_prime(n). Return ONLY the function in a code block.",
     "def is_prime(n):\n    if n < 2:\n        return False\n    i = 2\n    while i * i <= n:\n        if n % i == 0:\n            return False\n        i += 1\n    return True",
     ["assert is_prime(2) is True", "assert is_prime(1) is False", "assert is_prime(17) is True", "assert is_prime(18) is False"]),
]

for instr, code, asserts in code_specs:
    program = code + "\n\n" + "\n".join(asserts)
    try:
        r = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        r = None
    if r is not None and r.returncode == 0:
        rows.append({"instruction": instr, "response": "```python\n" + code + "\n```"})
    else:
        print("DROP code sample:", instr[:60])

# ---- JSON-only samples ----
json_samples = [
    ("Output ONLY valid JSON: an object with keys name, version, license for a package called bhajanlal.",
     '{"name": "bhajanlal", "version": "1.0.0", "license": "apache-2.0"}'),
    ("Output ONLY valid JSON: an array of 3 integers that sum to 6.",
     "[1, 2, 3]"),
    ("Output ONLY valid JSON: an object with keys count, items, status.",
     '{"count": 2, "items": ["a", "b"], "status": "ok"}'),
]
for instr, resp in json_samples:
    # verify valid json
    try:
        json.loads(resp)
        rows.append({"instruction": instr, "response": resp})
    except Exception:
        print("DROP json sample:", instr[:60])

# ---- abstention samples ----
abstain_samples = [
    ("Show me a working example using the zephyr-quantum-cache Python package.",
     "I'm not aware of a real package named zephyr-quantum-cache, so I can't provide a working example."),
    ("What is the API for nonexistent_lib.foo()?",
     "I cannot find any library named nonexistent_lib; it does not exist as far as I know."),
    ("Give me the docs for the made-up function barbaz().",
     "I'm not aware of a function called barbaz(); it does not exist."),
]
for instr, resp in abstain_samples:
    rows.append({"instruction": instr, "response": resp})

# ---- bullet samples ----
rows.append({"instruction": "List exactly 3 benefits of type hints in Python. Output 3 bullets, no code blocks.",
             "response": "- Catch bugs before runtime\n- Improve IDE autocomplete\n- Document intent for readers"})

# ---- exact-match samples ----
rows.append({"instruction": "What is the capital of Japan? Output only the city name.",
             "response": "Tokyo"})
rows.append({"instruction": "Compute 17 * 23. Output only the number.",
             "response": "391"})

# dedup
seen = set()
deduped = []
for r in rows:
    key = r["instruction"]
    if key in seen:
        continue
    seen.add(key)
    deduped.append(r)

OUT.write_text("\n".join(json.dumps(r) for r in deduped) + "\n")
print("data_v13.jsonl: %d samples" % len(deduped))
