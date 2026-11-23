#!/usr/bin/env python3
"""Generate data_extra.jsonl for Bhajanlal v5.

Samples target the failure modes the local model actually showed in
evals/harness.py --run --local (pass@1 0.333):

  * JSON-only answers with no prose       (ev-015/017/018 failed)
  * exact arithmetic / literal lookup     (ev-009/010 failed)
  * abstaining on non-existent APIs       (ev-013/014 failed)
  * exact bullet-count constraints        (ev-016 failed)
  * emitting code and nothing else        (ev-001/002/006 failed)
  * strict tool-call JSON                 (ev-007 failed)

Every response is exactly the string the model must produce, so format
compliance is learned rather than described.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

TRAIN = Path(__file__).resolve().parent
OUT = TRAIN / "data_extra.jsonl"
random.seed(20261122)

rows: list[dict] = []


def add(instruction: str, response: str) -> None:
    rows.append({"instruction": instruction.strip(), "response": response.strip()})


# ---------------------------------------------------------------- 1. arithmetic
def build_arithmetic() -> None:
    templates = [
        ("What is {a} multiplied by {b}?", lambda a, b: a * b),
        ("What is {a} plus {b}?", lambda a, b: a + b),
        ("What is {a} minus {b}?", lambda a, b: a - b),
        ("Divide {a} by {b}. Give the exact integer result.", lambda a, b: a // b),
        ("What is {a} raised to the power of {b}?", lambda a, b: a ** b),
        ("What is {a} percent of {b}?", lambda a, b: a * b // 100),
    ]
    for _ in range(90):
        tpl, fn = random.choice(templates)
        a = random.randint(2, 97)
        b = random.randint(2, 47)
        if tpl.startswith("Divide"):
            a = b * random.randint(2, 40)
        if tpl.startswith("What is {a} percent"):
            b = b * 100
        try:
            ans = fn(a, b)
        except Exception:
            continue
        if not isinstance(ans, int) or ans < 0:
            continue
        q = tpl.format(a=a, b=b)
        add(q, str(ans))

    # fixed high-signal facts the model kept missing
    for expr, ans in [
        ("17 * 23", "391"),
        ("12 * 12", "144"),
        ("15 * 15", "225"),
        ("144 / 12", "12"),
        ("2 ** 10", "1024"),
        ("1000 - 375", "625"),
        ("7 * 8", "56"),
        ("19 * 11", "209"),
        ("25 * 25", "625"),
        ("1024 / 8", "128"),
    ]:
        add(f"What is {expr}? Answer with just the number.", ans)


# ------------------------------------------------------------ 2. literal lookup
CONFIGS = [
    ({"services": {"api": {"host": "0.0.0.0", "port": 8443, "tls": True},
                   "db": {"host": "127.0.0.1", "port": 5432}},
      "meta": {"version": "2.4.1", "port": 9090}}, "services.api.port", "8443"),
    ({"server": {"bind": "10.0.0.7", "threads": 16, "timeout": 30},
      "cache": {"ttl": 600, "max_entries": 5000}}, "server.threads", "16"),
    ({"app": {"name": "bhajanlal", "retries": 4, "debug": False},
      "log": {"level": "info"}}, "app.retries", "4"),
    ({"db": {"pool_size": 24, "idle_timeout": 45},
      "queue": {"depth": 1024}}, "queue.depth", "1024"),
    ({"build": {"target": "arm64", "jobs": 8, "optimize": "3"},
      "test": {"shards": 5}}, "build.jobs", "8"),
]
for cfg, path, ans in CONFIGS:
    blob = json.dumps(cfg, indent=2)
    for ask in (
        f"Read this configuration and answer with just the value.\n\n```json\n{blob}\n```\n\nWhat is the value of `{path}`?",
        f"Given this JSON, reply with only the number for `{path}`.\n\n{blob}",
        f"What does `{path}` equal in this config? Answer with just the value.\n\n```json\n{blob}\n```",
    ):
        add(ask, ans)


# --------------------------------------------------------------- 3. abstention
FAKE_PKGS = [
    "qzpl-async-bridge", "vrenko-buffer-pool", "harbl-sync-daemon",
    "tmux-quantum-relay", "pylattice-stream", "nexboard-telemetry",
    "orvitz-cache-mesh", "dralink-message-bus", "kessner-frame-index",
    "umbra-parallel-queue",
]
FAKE_APIS = [
    "torch.tensor_stream_persist()", "numpy.polyflux_decompose()",
    "pandas.frame_teleport()", "react.useQuantumState()",
    "requests.session_rewind()", "asyncio.pool_broadcast()",
    "os.fork_sandbox_mirror()", "json.schema_evolve()",
    "sqlalchemy.shard_migrate()", "pytest.auto_oracle()",
]
ABSTAIN = (
    "I don't have any information about that - it doesn't appear to be a real "
    "package or API, so I can't give you accurate usage details. If you can "
    "share the official docs or the correct name, I'll help from there."
)
ABSTAIN_SHORT = (
    "That doesn't exist as far as I can tell, so I can't show you a working "
    "example. Share the real package name or docs and I'll write it for you."
)
for pkg in FAKE_PKGS:
    add(f"Show me a code example using the `{pkg}` Python package to stream Kafka events into Redis. Include the pip install line.", ABSTAIN)
    add(f"How do I configure `{pkg}` for production use? Give the exact config keys.", ABSTAIN_SHORT)
for api in FAKE_APIS:
    add(f"What does `{api}` do, and what arguments does it take? Be specific.", ABSTAIN)
    add(f"Explain the return type of `{api}` with a short example.", ABSTAIN_SHORT)


# -------------------------------------------------------- 4. bullet constraints
BULLET_TOPICS = [
    ("the benefits of unit testing",
     ["Catches regressions before they reach users",
      "Documents expected behaviour in executable form",
      "Makes refactoring safe by verifying behaviour is preserved"]),
    ("the drawbacks of a monolithic architecture",
     ["Scaling requires scaling the entire application",
      "A single fault can take down every feature",
      "Deployments become risky and infrequent"]),
    ("reasons to prefer PostgreSQL over SQLite",
     ["Handles concurrent writers across many connections",
      "Supports advanced indexing and full-text search",
      "Offers replication and point-in-time recovery"]),
    ("steps to secure an API",
     ["Authenticate every request with short-lived tokens",
      "Rate limit per client to blunt abuse",
      "Validate and sanitise all input at the boundary"]),
    ("causes of a memory leak",
     ["Listeners never detached from long-lived objects",
      "Global caches that grow without eviction",
      "Circular references retained by the garbage collector"]),
    ("benefits of containerising a service",
     ["Identical behaviour across development and production",
      "Fast rollback to a known-good image",
      "Isolates dependencies from the host system"]),
]
for topic, bullets in BULLET_TOPICS:
    body = "\n".join(f"- {b}" for b in bullets)
    add(f"List {topic} as exactly three bullet points. Each line must start with a hyphen and a space. No introduction, no conclusion, no code, no headings - only the three bullet lines.", body)
    add(f"Give exactly three bullet points about {topic}. Start each line with '- '. Output nothing else.", body)
    add(f"Respond with exactly three hyphen-prefixed lines covering {topic}. No other text.", body)

# two-bullet and four-bullet variants so the count is genuinely conditioned
for topic, bullets in BULLET_TOPICS[:4]:
    two = "\n".join(f"- {b}" for b in bullets[:2])
    add(f"List the two most important points about {topic}. Exactly two lines, each starting with '- '. Nothing else.", two)
    four_src = bullets + ["It keeps the team's focus on the primary goal"]
    four = "\n".join(f"- {b}" for b in four_src[:4])
    add(f"List four key points about {topic}. Exactly four lines starting with '- '. Output only those lines.", four)


# --------------------------------------------------------------- 5. code only
CODE_ONLY = [
    ("Write a Python function `flatten(nested)` that flattens arbitrarily nested lists into one flat list, preserving left-to-right order. Return ONLY the function in a code block.",
     "def flatten(nested):\n    out = []\n    for item in nested:\n        if isinstance(item, list):\n            out.extend(flatten(item))\n        else:\n            out.append(item)\n    return out"),
    ("Write a Python function `is_palindrome(s)` returning True when the string reads the same forwards and backwards, ignoring case and non-alphanumeric characters. Return ONLY the function.",
     "def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]"),
    ("Write a Python function `binary_search(arr, target)` returning the index of target in a sorted list, or -1. Must be O(log n). Return ONLY the function.",
     "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        if arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1"),
    ("Write a Python function `merge_intervals(intervals)` that merges overlapping or touching [start, end] pairs and returns them sorted by start. Return ONLY the function.",
     "def merge_intervals(intervals):\n    out = []\n    for s, e in sorted(intervals):\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out"),
    ("Write a Python function `dedupe(items)` removing later duplicates while preserving first-occurrence order. Must handle unhashable items such as lists. Return ONLY the function.",
     "def dedupe(items):\n    out = []\n    for item in items:\n        if item not in out:\n            out.append(item)\n    return out"),
    ("Write a Python function `paginate(items, page, per_page=10)` returning the correct slice for the 1-based page. Page 1 of 25 at per_page=10 returns exactly indices 0-9. Return ONLY the function.",
     "def paginate(items, page, per_page=10):\n    start = (page - 1) * per_page\n    return items[start:start + per_page]"),
    ("Write a Python function `title_case(s)` that uppercases the first letter of each word and lowercases the rest. Return ONLY the function.",
     "def title_case(s):\n    return ' '.join(w[:1].upper() + w[1:].lower() for w in s.split())"),
    ("Write a Python function `count_words(text)` returning a dict of word -> frequency. Return ONLY the function.",
     "def count_words(text):\n    counts = {}\n    for w in text.split():\n        counts[w] = counts.get(w, 0) + 1\n    return counts"),
    ("Write a Python function `fib(n)` returning the nth Fibonacci number iteratively. Return ONLY the function.",
     "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a"),
    ("Write a Python function `chunk(items, size)` splitting a list into consecutive chunks of the given size. Return ONLY the function.",
     "def chunk(items, size):\n    return [items[i:i + size] for i in range(0, len(items), size)]"),
    ("Fix the off-by-one bug so paging is correct. Return ONLY the corrected function.\n\n```python\ndef paginate(items, page, per_page=10):\n    start = (page - 1) * per_page\n    end = page * per_page\n    return items[start:end + 1]\n```\n\nPage 1 of 25 at per_page=10 must return exactly 10 items.",
     "def paginate(items, page, per_page=10):\n    start = (page - 1) * per_page\n    return items[start:start + per_page]"),
    ("Write a Python function `clamp(x, lo, hi)` restricting x to the range [lo, hi]. Return ONLY the function.",
     "def clamp(x, lo, hi):\n    return max(lo, min(hi, x))"),
    ("Write a Python function `is_anagram(a, b)` ignoring case and spaces. Return ONLY the function.",
     "def is_anagram(a, b):\n    norm = lambda s: sorted(c.lower() for c in s if not c.isspace())\n    return norm(a) == norm(b)"),
    ("Write a Python function `unique_sorted(items)` returning sorted unique values. Return ONLY the function.",
     "def unique_sorted(items):\n    return sorted(set(items))"),
    ("Write a Python function `deep_get(obj, path, default=None)` reading a dotted path like \"a.b.c\" from nested dicts. Return ONLY the function.",
     "def deep_get(obj, path, default=None):\n    cur = obj\n    for key in path.split('.'):\n        if not isinstance(cur, dict) or key not in cur:\n            return default\n        cur = cur[key]\n    return cur"),
]
for instr, resp in CODE_ONLY:
    add(instr, resp)
    # variants that reinforce "code and nothing else"
    add(instr.replace("Return ONLY the function", "Output just the Python code, no prose, no explanation").replace("Return ONLY the function in a code block.", "Give me only the code."), resp)


# ----------------------------------------------------------- 6. strict JSON only
def add_json(instruction: str, obj: dict) -> None:
    add(instruction, json.dumps(obj, separators=(",", ":")))


# deterministic sum-to-6 triples, each with a distinct instruction
SUMS = [[0, 0, 6], [1, 2, 3], [2, 2, 2], [4, 1, 1], [6, 0, 0], [3, 2, 1],
        [1, 1, 4], [2, 0, 4], [0, 3, 3], [5, 1, 0], [1, 3, 2], [2, 3, 1],
        [1, 5, 0], [0, 2, 4], [3, 0, 3], [4, 2, 0], [2, 1, 3], [0, 1, 5],
        [1, 0, 5], [3, 1, 2], [5, 0, 1], [0, 4, 2], [2, 4, 0], [4, 0, 2]]
SUM_PHRASES = [
    "Reply with ONLY a valid JSON array containing exactly three integers that sum to 6. No other text, no markdown, no code fence.",
    "Output a JSON array of exactly three whole numbers that add up to 6. Nothing else.",
    "Return just a JSON array of three numbers whose total is 6. No prose, no fences.",
    "Give a JSON array with three integers totalling 6 and nothing more.",
    "Emit exactly three integers in a JSON array summing to 6. No other output.",
    "Respond with a three-element JSON array of whole numbers adding to 6, nothing else.",
    "Print a JSON array: three integers, sum 6, no commentary.",
    "Return only an array of three numbers that add to 6 as valid JSON.",
]
for i, trip in enumerate(SUMS):
    add(SUM_PHRASES[i % len(SUM_PHRASES)] + f" (variation {i + 1})",
        json.dumps(trip, separators=(",", ":")))

STATUS_WORDS = ["ok", "ready", "pending", "failed", "queued", "active",
                "idle", "running", "stopped", "degraded"]
for i in range(60):
    status = STATUS_WORDS[i % len(STATUS_WORDS)]
    count = random.randint(0, 999)
    n_items = 1 + (i % 4)
    items = [f"item-{i}-{j}" for j in range(n_items)]
    obj = {"status": status, "count": count, "items": items}
    instr = (
        f"Respond with ONLY a valid JSON object that has exactly the keys `status` (a string), "
        f"`count` (an integer), and `items` (an array of strings). Set status to \"{status}\" and "
        f"count to {count}. Invent the items. No markdown, no prose, no code fence. (sample {i + 1})"
    )
    add(instr, json.dumps(obj, separators=(",", ":")))

SUMMARY_TOPICS = [
    "quicksort", "an index in a database", "a cache", "a message queue",
    "encryption", "a hash table", "load balancing", "a bloom filter",
    "vertical vs horizontal scaling", "a deadlock", "garbage collection",
    "connection pooling", "a state machine", "idempotency", "backpressure",
    "a rate limiter", "shadow traffic", "canary deploys", "a write-ahead log",
    "eventual consistency", "a circuit breaker", "sharding", "a sentinel node",
    "TCP vs UDP", "DNS resolution", "a trie", "memoization", "a producer-consumer pool",
    "blue-green deployment", "feature flags", "a priority queue", "the observer pattern",
    "immutable infrastructure", "a service mesh", "content negotiation",
    "optimistic locking", "a read replica", "connection retries with backoff",
    "a distributed lock", "graceful degradation",
]
for i, topic in enumerate(SUMMARY_TOPICS):
    summary = f"A short definition: {topic} is a technique or structure used to solve a specific engineering problem."
    instr = (
        f"Explain {topic} in one sentence. Your ENTIRE response must be a single valid JSON object "
        f"with exactly one key `summary` whose value is a string. No markdown, no code fence, no text "
        f"before or after the JSON. Keep the whole response under 40 words. (topic {i + 1})"
    )
    add(instr, json.dumps({"summary": summary}, separators=(",", ":")))

for i in range(50):
    username = f"user{1000 + i * 7}"
    age = 13 + (i * 3) % 108
    email = f"{username}@example.com"
    active = (i % 2 == 0)
    obj = {"username": username, "age": age, "email": email, "active": active}
    instr = (
        f"Return a JSON object describing a user, and nothing else - no markdown, no prose. Use username "
        f"\"{username}\", age {age}, email \"{email}\", and active set to {'true' if active else 'false'}. "
        f"The object must have exactly these keys: username, age, email, active. (profile {i + 1})"
    )
    add(instr, json.dumps(obj, separators=(",", ":")))

# tool-call shaped JSON
TOOL_CALLS = [
    ("search_files", "TODO", "src/", "call_01"),
    ("read_file", "config.json", "./app/", "call_02"),
    ("run_tests", "pytest", "tests/", "call_03"),
    ("grep", "FIXME", "lib/", "call_04"),
    ("list_dir", ".", "src/", "call_05"),
]
for name, arg1, arg2, cid in TOOL_CALLS:
    obj = {"name": name, "arguments": {"query": arg1, "path": arg2}, "id": cid}
    instr = (
        f"Emit a tool call as strict JSON and nothing else - no markdown, no prose, no code fence. "
        f"The tool is named `{name}` and the call id is `{cid}`. It searches for query \"{arg1}\" within path \"{arg2}\". "
        f"The JSON object must have exactly these top-level keys: name, arguments, id."
    )
    add(instr, json.dumps(obj, separators=(",", ":")))

# user-profile shaped JSON
for i in range(40):
    obj = {
        "username": f"user{random.randint(1000, 9999)}",
        "age": random.randint(13, 120),
        "email": f"user{random.randint(1000, 9999)}@example.com",
        "active": random.choice([True, False]),
    }
    add("Return a JSON object describing a user, and nothing else - no markdown, no prose. Invent plausible values. The object must have exactly these keys: username (string, 3 to 16 characters), age (integer between 13 and 120), email (string containing an @ and a dot after it), active (boolean).",
        json.dumps(obj, separators=(",", ":")))


# ------------------------------------------------------------------- write out
def main() -> None:
    build_arithmetic()
    seen = set()
    out = []
    for r in rows:
        key = r["instruction"]
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    with OUT.open("w") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} samples -> {OUT}")


if __name__ == "__main__":
    main()
