#!/usr/bin/env python3
"""Bhajanlal training pipeline: synthetic data, LoRA fine-tune on MPS."""
import json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
CKPT = TRAIN / "checkpoints" / "bhajanlal-v3"
DATA = TRAIN / "data_max.jsonl"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
CACHE = Path.home() / ".cache" / "huggingface"

# Synthetic coding training data (instruction -> response pairs)
SYNTHETIC_DATA = [
    ("Write a Python function to reverse a string.",
     "def reverse_string(s):\n    return s[::-1]\n\n# Example usage:\n# reverse_string('hello') -> 'olleh'"),
    ("Write a Python function to check if a number is prime.",
     "def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True"),
    ("Write a Python function to find the factorial of a number.",
     "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"),
    ("Write a Python function to check if a string is a palindrome.",
     "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]"),
    ("Write a Python function to merge two sorted lists.",
     "def merge_sorted(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result"),
    ("Write a Python function to count vowels in a string.",
     "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')"),
    ("Write a Python function to find the largest element in a list.",
     "def find_max(lst):\n    if not lst:\n        return None\n    return max(lst)"),
    ("Write a Python function to remove duplicates from a list.",
     "def remove_duplicates(lst):\n    return list(dict.fromkeys(lst))"),
    ("Write a Python function to implement binary search.",
     "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1"),
    ("Write a Python function to calculate the Fibonacci sequence up to n.",
     "def fibonacci(n):\n    if n <= 0:\n        return []\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq[:n]"),
    ("Write a Python function to check if two strings are anagrams.",
     "def are_anagrams(s1, s2):\n    return sorted(s1.lower()) == sorted(s2.lower())"),
    ("Write a Python function to find the GCD of two numbers.",
     "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a"),
    ("Write a Python function to flatten a nested list.",
     "def flatten(nested):\n    result = []\n    for item in nested:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result"),
    ("Write a Python function to count word frequencies in a sentence.",
     "from collections import Counter\n\ndef word_freq(s):\n    return dict(Counter(s.lower().split()))"),
    ("Write a Python function to validate an email address with regex.",
     "import re\n\ndef is_valid_email(email):\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))"),
    ("Write a Python function to implement a stack using a list.",
     "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        return self.items.pop() if self.items else None\n    def peek(self):\n        return self.items[-1] if self.items else None\n    def is_empty(self):\n        return len(self.items) == 0"),
    ("Write a Python function to find missing number in a list from 1 to n.",
     "def find_missing(nums, n):\n    expected = n * (n + 1) // 2\n    return expected - sum(nums)"),
    ("Write a Python function to rotate a list by k positions.",
     "def rotate_list(lst, k):\n    if not lst:\n        return lst\n    k = k % len(lst)\n    return lst[-k:] + lst[:-k] if k else lst"),
    ("Write a Python function to find all pairs that sum to target.",
     "def find_pairs(nums, target):\n    seen = set()\n    pairs = []\n    for n in nums:\n        complement = target - n\n        if complement in seen:\n            pairs.append((complement, n))\n        seen.add(n)\n    return pairs"),
    ("Write a Python function to check balanced parentheses.",
     "def is_balanced(s):\n    stack = []\n    pairs = {'(': ')', '{': '}', '[': ']'}\n    for c in s:\n        if c in pairs:\n            stack.append(c)\n        elif c in pairs.values():\n            if not stack or pairs[stack.pop()] != c:\n                return False\n    return not stack"),
    ("Write a Python function to convert Celsius to Fahrenheit.",
     "def celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32"),
    ("Write a Python function to implement a queue using two stacks.",
     "class Queue:\n    def __init__(self):\n        self.in_stack = []\n        self.out_stack = []\n    def enqueue(self, item):\n        self.in_stack.append(item)\n    def dequeue(self):\n        if not self.out_stack:\n            while self.in_stack:\n                self.out_stack.append(self.in_stack.pop())\n        return self.out_stack.pop() if self.out_stack else None"),
    ("Write a Python function to find the second largest element.",
     "def second_largest(lst):\n    if len(lst) < 2:\n        return None\n    first = second = float('-inf')\n    for n in lst:\n        if n > first:\n            second = first\n            first = n\n        elif n > second and n != first:\n            second = n\n    return second if second != float('-inf') else None"),
    ("Write a Python function to implement selection sort.",
     "def selection_sort(arr):\n    for i in range(len(arr)):\n        min_idx = i\n        for j in range(i+1, len(arr)):\n            if arr[j] < arr[min_idx]:\n                min_idx = j\n        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n    return arr"),
    ("Write a Python function to find common elements in two lists.",
     "def common_elements(a, b):\n    return list(set(a) & set(b))"),
    ("Write a Python function to implement insertion sort.",
     "def insertion_sort(arr):\n    for i in range(1, len(arr)):\n        key = arr[i]\n        j = i - 1\n        while j >= 0 and arr[j] > key:\n            arr[j+1] = arr[j]\n            j -= 1\n        arr[j+1] = key\n    return arr"),
    ("Write a Python function to check if a list is sorted.",
     "def is_sorted(lst):\n    return all(lst[i] <= lst[i+1] for i in range(len(lst)-1))"),
    ("Write a Python function to find the intersection of two lists.",
     "def intersection(a, b):\n    return [x for x in a if x in b]"),
    ("Write a Python function to implement bubble sort.",
     "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr"),
    ("Write a Python function to find the longest common prefix.",
     "def longest_common_prefix(strs):\n    if not strs:\n        return ''\n    prefix = strs[0]\n    for s in strs[1:]:\n        while not s.startswith(prefix):\n            prefix = prefix[:-1]\n            if not prefix:\n                return ''\n    return prefix"),
    ("Write a Python function to implement a decorator that times function execution.",
     "import time\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time()-start:.4f}s')\n        return result\n    return wrapper"),
    ("Write a Python function to implement a context manager for file handling.",
     "class FileManager:\n    def __init__(self, filename, mode):\n        self.filename = filename\n        self.mode = mode\n        self.file = None\n    def __enter__(self):\n        self.file = open(self.filename, self.mode)\n        return self.file\n    def __exit__(self, *args):\n        if self.file:\n            self.file.close()"),
    ("Write a Python function to implement a singleton pattern.",
     "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance"),
    ("Write a Python function to implement a linked list.",
     "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n    def append(self, data):\n        new = Node(data)\n        if not self.head:\n            self.head = new\n            return\n        cur = self.head\n        while cur.next:\n            cur = cur.next\n        cur.next = new\n    def to_list(self):\n        result = []\n        cur = self.head\n        while cur:\n            result.append(cur.data)\n            cur = cur.next\n        return result"),
    ("Write a Python function to implement a binary tree with insert and inorder traversal.",
     "class TreeNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = self.right = None\n\nclass BinaryTree:\n    def __init__(self):\n        self.root = None\n    def insert(self, val):\n        if not self.root:\n            self.root = TreeNode(val)\n            return\n        cur = self.root\n        while True:\n            if val < cur.val:\n                if cur.left is None:\n                    cur.left = TreeNode(val); break\n                cur = cur.left\n            else:\n                if cur.right is None:\n                    cur.right = TreeNode(val); break\n                cur = cur.right\n    def inorder(self):\n        result = []\n        def _inorder(node):\n            if node:\n                _inorder(node.left)\n                result.append(node.val)\n                _inorder(node.right)\n        _inorder(self.root)\n        return result"),
    ("Write a Python function to implement a hash table with chaining.",
     "class HashTable:\n    def __init__(self, size=10):\n        self.size = size\n        self.table = [[] for _ in range(size)]\n    def _hash(self, key):\n        return hash(key) % self.size\n    def insert(self, key, value):\n        idx = self._hash(key)\n        for i, (k, v) in enumerate(self.table[idx]):\n            if k == key:\n                self.table[idx][i] = (key, value)\n                return\n        self.table[idx].append((key, value))\n    def get(self, key):\n        idx = self._hash(key)\n        for k, v in self.table[idx]:\n            if k == key:\n                return v\n        return None"),
    ("Write a Python function to implement a graph with BFS and DFS.",
     "from collections import deque\n\nclass Graph:\n    def __init__(self):\n        self.adj = {}\n    def add_edge(self, u, v):\n        self.adj.setdefault(u, []).append(v)\n        self.adj.setdefault(v, []).append(u)\n    def bfs(self, start):\n        visited = set([start])\n        queue = deque([start])\n        result = []\n        while queue:\n            node = queue.popleft()\n            result.append(node)\n            for neighbor in self.adj.get(node, []):\n                if neighbor not in visited:\n                    visited.add(neighbor)\n                    queue.append(neighbor)\n        return result\n    def dfs(self, start):\n        visited = set()\n        result = []\n        def _dfs(node):\n            if node in visited:\n                return\n            visited.add(node)\n            result.append(node)\n            for neighbor in self.adj.get(node, []):\n                _dfs(neighbor)\n        _dfs(start)\n        return result"),
    ("Write a Python function to implement a trie (prefix tree).",
     "class TrieNode:\n    def __init__(self):\n        self.children = {}\n        self.is_end = False\n\nclass Trie:\n    def __init__(self):\n        self.root = TrieNode()\n    def insert(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children:\n                node.children[c] = TrieNode()\n            node = node.children[c]\n        node.is_end = True\n    def search(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children:\n                return False\n            node = node.children[c]\n        return node.is_end\n    def starts_with(self, prefix):\n        node = self.root\n        for c in prefix:\n            if c not in node.children:\n                return False\n            node = node.children[c]\n        return True"),
    ("Write a Python function to implement a least recently used (LRU) cache.",
     "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity):\n        self.capacity = capacity\n        self.cache = OrderedDict()\n    def get(self, key):\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n    def put(self, key, value):\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)"),
    ("Write a Python function to implement a rate limiter using token bucket.",
     "import time\n\nclass TokenBucket:\n    def __init__(self, capacity, refill_rate):\n        self.capacity = capacity\n        self.tokens = capacity\n        self.refill_rate = refill_rate\n        self.last_refill = time.time()\n    def consume(self, tokens=1):\n        now = time.time()\n        elapsed = now - self.last_refill\n        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)\n        self.last_refill = now\n        if self.tokens >= tokens:\n            self.tokens -= tokens\n            return True\n        return False"),
]


def main():
    TRAIN.mkdir(parents=True, exist_ok=True)

    # Step 1: Load training data
    print("=== Step 1: Loading training data ===", flush=True)
    samples = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(samples)} training samples from {DATA}", flush=True)

    # Step 2: LoRA fine-tune on MPS
    print("=== Step 2: LoRA fine-tune on MPS ===", flush=True)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model
    from datasets import Dataset
    from trl import SFTTrainer, SFTConfig

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"  Device: {device}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=str(CACHE))
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, cache_dir=str(CACHE), torch_dtype=torch.float16
    )
    model.gradient_checkpointing_enable()
    model.to(device)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    def format_sample(s):
        return f"### Instruction:\n{s['instruction']}\n\n### Response:\n{s['response']}"

    texts = [format_sample(s) for s in samples]
    ds = Dataset.from_dict({"text": texts})

    training_args = SFTConfig(
        output_dir=str(CKPT),
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        warmup_steps=10,
        logging_steps=10,
        save_strategy="epoch",
        fp16=False,
        bf16=False,
        dataset_text_field="text",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=ds,
        processing_class=tokenizer,
    )

    print("  Training...", flush=True)
    trainer.train()

    model.save_pretrained(str(CKPT))
    tokenizer.save_pretrained(str(CKPT))
    print(f"  Checkpoint saved to {CKPT}", flush=True)

    meta = {
        "base_model": MODEL_ID,
        "method": "LoRA (r=16, alpha=32)",
        "device": device,
        "epochs": 3,
        "samples": len(samples),
        "checkpoint": str(CKPT),
    }
    (TRAIN / "metadata.json").write_text(json.dumps(meta, indent=2))
    print("=== Training complete! ===", flush=True)
    print(json.dumps(meta, indent=2), flush=True)


if __name__ == "__main__":
    main()
