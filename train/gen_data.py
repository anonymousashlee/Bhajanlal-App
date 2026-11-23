#!/usr/bin/env python3
"""Generate maximum synthetic coding dataset for Bhajanlal training."""
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN = ROOT / "train"
DATA = TRAIN / "data_max.jsonl"

# Seed for reproducibility
random.seed(42)

samples = []

# === Category 1: Basic operations (many variations) ===
basic_ops = [
    ("reverse a string", "def reverse_string(s):\n    return s[::-1]"),
    ("reverse a list", "def reverse_list(lst):\n    return lst[::-1]"),
    ("find max in list", "def find_max(lst):\n    if not lst: return None\n    m = lst[0]\n    for x in lst:\n        if x > m: m = x\n    return m"),
    ("find min in list", "def find_min(lst):\n    if not lst: return None\n    m = lst[0]\n    for x in lst:\n        if x < m: m = x\n    return m"),
    ("sum of list", "def list_sum(lst):\n    return sum(lst)"),
    ("average of list", "def list_avg(lst):\n    return sum(lst)/len(lst) if lst else 0"),
    ("count elements", "def count_elements(lst):\n    return len(lst)"),
    ("check empty list", "def is_empty(lst):\n    return len(lst) == 0"),
    ("get first element", "def first_element(lst):\n    return lst[0] if lst else None"),
    ("get last element", "def last_element(lst):\n    return lst[-1] if lst else None"),
    ("flatten list", "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result"),
    ("remove None values", "def remove_none(lst):\n    return [x for x in lst if x is not None]"),
    ("filter truthy", "def filter_truthy(lst):\n    return [x for x in lst if x]"),
    ("filter falsy", "def filter_falsy(lst):\n    return [x for x in lst if not x]"),
    ("square all", "def square_all(lst):\n    return [x**2 for x in lst]"),
    ("cube all", "def cube_all(lst):\n    return [x**3 for x in lst]"),
    ("double all", "def double_all(lst):\n    return [x*2 for x in lst]"),
    ("halve all", "def halve_all(lst):\n    return [x/2 for x in lst]"),
    ("absolute values", "def abs_all(lst):\n    return [abs(x) for x in lst]"),
    ("negate all", "def negate_all(lst):\n    return [-x for x in lst]"),
    ("increment all", "def increment_all(lst):\n    return [x+1 for x in lst]"),
    ("decrement all", "def decrement_all(lst):\n    return [x-1 for x in lst]"),
    ("string to list of chars", "def to_chars(s):\n    return list(s)"),
    ("list to string", "def to_string(lst):\n    return ''.join(str(x) for x in lst)"),
    ("join with comma", "def join_comma(lst):\n    return ', '.join(str(x) for x in lst)"),
    ("join with space", "def join_space(lst):\n    return ' '.join(str(x) for x in lst)"),
    ("join with newline", "def join_newline(lst):\n    return '\\n'.join(str(x) for x in lst)"),
]

for name, code in basic_ops:
    problems = [name]
    # Create variations
    for i in range(3):
        samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Math functions (many) ---
math_funcs = [
    ("factorial", "def factorial(n):\n    if n <= 1: return 1\n    return n * factorial(n-1)"),
    ("fibonacci", "def fibonacci(n):\n    if n <= 0: return []\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq[:n]"),
    ("is_prime", "def is_prime(n):\n    if n < 2: return False\n    for i in range(2, int(n**0.5)+1):\n        if n % i == 0: return False\n    return True"),
    ("gcd", "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a"),
    ("lcm", "def lcm(a, b):\n    from math import gcd\n    return a * b // gcd(a, b)"),
    ("power", "def power(base, exp):\n    result = 1\n    for _ in range(exp):\n        result *= base\n    return result"),
    ("digit_sum", "def digit_sum(n):\n    return sum(int(d) for d in str(abs(n)))"),
    ("is_even", "def is_even(n):\n    return n % 2 == 0"),
    ("is_odd", "def is_odd(n):\n    return n % 2 != 0"),
    ("abs_val", "def abs_val(n):\n    return n if n >= 0 else -n"),
    ("is_power_of_two", "def is_power_of_two(n):\n    return n > 0 and (n & (n-1)) == 0"),
    ("is_perfect_square", "def is_perfect_square(n):\n    if n < 0: return False\n    r = int(n**0.5)\n    return r * r == n"),
    ("is_armstrong", "def is_armstrong(n):\n    digits = [int(d) for d in str(n)]\n    return sum(d**len(digits) for d in digits) == n"),
    ("divisors", "def divisors(n):\n    return [i for i in range(1, n+1) if n % i == 0]"),
    ("nth_prime", "def nth_prime(n):\n    count = 0\n    num = 2\n    while count < n:\n        if all(num % i != 0 for i in range(2, int(num**0.5)+1)):\n            count += 1\n        num += 1\n    return num - 1"),
    ("sum_n", "def sum_n(n):\n    return n * (n + 1) // 2"),
    ("int_sqrt", "def int_sqrt(n):\n    if n < 0: return None\n    r = int(n**0.5)\n    while r*r > n: r -= 1\n    while (r+1)*(r+1) <= n: r += 1\n    return r"),
    ("reverse_number", "def reverse_number(n):\n    return int(str(n)[::-1]) if n >= 0 else -int(str(-n)[::-1])"),
    ("celsius_to_fahrenheit", "def celsius_to_fahrenheit(c):\n    return (c * 9/5) + 32"),
    ("fahrenheit_to_celsius", "def fahrenheit_to_celsius(f):\n    return (f - 32) * 5/9"),
    ("km_to_miles", "def km_to_miles(km):\n    return km * 0.621371"),
    ("miles_to_km", "def miles_to_km(miles):\n    return miles / 0.621371"),
    ("area_circle", "def area_circle(r):\n    import math\n    return math.pi * r * r"),
    ("area_rectangle", "def area_rectangle(w, h):\n    return w * h"),
    ("area_triangle", "def area_triangle(b, h):\n    return 0.5 * b * h"),
    ("perimeter_rectangle", "def perimeter_rectangle(w, h):\n    return 2 * (w + h)"),
    ("hypotenuse", "def hypotenuse(a, b):\n    import math\n    return math.sqrt(a*a + b*b)"),
    ("average", "def average(nums):\n    return sum(nums) / len(nums) if nums else 0"),
    ("median", "def median(nums):\n    s = sorted(nums)\n    n = len(s)\n    if n % 2 == 0:\n        return (s[n//2-1] + s[n//2]) / 2\n    return s[n//2]"),
    ("mode", "def mode(nums):\n    from collections import Counter\n    return Counter(nums).most_common(1)[0][0] if nums else None"),
    ("variance", "def variance(nums):\n    if not nums: return 0\n    m = sum(nums)/len(nums)\n    return sum((x-m)**2 for x in nums)/len(nums)"),
    ("std_dev", "def std_dev(nums):\n    import math\n    if not nums: return 0\n    m = sum(nums)/len(nums)\n    return math.sqrt(sum((x-m)**2 for x in nums)/len(nums))"),
    ("clamp", "def clamp(val, lo, hi):\n    return max(lo, min(hi, val))"),
    ("lerp", "def lerp(a, b, t):\n    return a + (b - a) * t"),
    ("sign", "def sign(n):\n    if n > 0: return 1\n    if n < 0: return -1\n    return 0"),
    ("is_prime_fast", "def is_prime_fast(n):\n    if n < 2: return False\n    if n in (2, 3): return True\n    if n % 2 == 0 or n % 3 == 0: return False\n    i = 5\n    while i * i <= n:\n        if n % i == 0 or n % (i+2) == 0:\n            return False\n        i += 6\n    return True"),
]
for name, code in math_funcs:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- String operations ---
str_ops = [
    ("reverse string", "def reverse_string(s):\n    return s[::-1]"),
    ("is palindrome", "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]"),
    ("count vowels", "def count_vowels(s):\n    return sum(1 for c in s.lower() if c in 'aeiou')"),
    ("count consonants", "def count_consonants(s):\n    return sum(1 for c in s.lower() if c.isalpha() and c not in 'aeiou')"),
    ("count words", "def count_words(s):\n    return len(s.split())"),
    ("count chars", "def count_chars(s):\n    return len(s)"),
    ("to uppercase", "def to_upper(s):\n    return s.upper()"),
    ("to lowercase", "def to_lower(s):\n    return s.lower()"),
    ("capitalize", "def capitalize(s):\n    return s.capitalize()"),
    ("title case", "def title_case(s):\n    return s.title()"),
    ("strip whitespace", "def strip_ws(s):\n    return s.strip()"),
    ("remove spaces", "def remove_spaces(s):\n    return s.replace(' ', '')"),
    ("replace substring", "def replace_sub(s, old, new):\n    return s.replace(old, new)"),
    ("split by comma", "def split_comma(s):\n    return s.split(',')"),
    ("split by space", "def split_space(s):\n    return s.split()"),
    ("join list", "def join_list(lst, sep=''):\n    return sep.join(str(x) for x in lst)"),
    ("starts with", "def starts_with(s, prefix):\n    return s.startswith(prefix)"),
    ("ends with", "def ends_with(s, suffix):\n    return s.endswith(suffix)"),
    ("contains substring", "def contains(s, sub):\n    return sub in s"),
    ("find substring index", "def find_index(s, sub):\n    return s.find(sub)"),
    ("count substring", "def count_sub(s, sub):\n    return s.count(sub)"),
    ("is alpha", "def is_alpha(s):\n    return s.isalpha()"),
    ("is digit", "def is_digit(s):\n    return s.isdigit()"),
    ("is alphanumeric", "def is_alnum(s):\n    return s.isalnum()"),
    ("is title", "def is_title(s):\n    return s.istitle()"),
    ("swap case", "def swap_case(s):\n    return s.swapcase()"),
    ("center string", "def center_string(s, width):\n    return s.center(width)"),
    ("ljust", "def ljust_string(s, width):\n    return s.ljust(width)"),
    ("rjust", "def rjust_string(s, width):\n    return s.rjust(width)"),
    ("zfill", "def zfill_string(s, width):\n    return s.zfill(width)"),
    ("remove prefix", "def remove_prefix(s, prefix):\n    return s[len(prefix):] if s.startswith(prefix) else s"),
    ("remove suffix", "def remove_suffix(s, suffix):\n    return s[:-len(suffix)] if s.endswith(suffix) else s"),
    ("truncate", "def truncate(s, max_len):\n    return s[:max_len] + '...' if len(s) > max_len else s"),
    ("camel to snake", "def camel_to_snake(s):\n    import re\n    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()"),
    ("snake to camel", "def snake_to_camel(s):\n    return ''.join(w.capitalize() for w in s.split('_'))"),
    ("is anagram", "def is_anagram(s1, s2):\n    return sorted(s1.lower()) == sorted(s2.lower())"),
    ("longest common prefix", "def longest_common_prefix(strs):\n    if not strs: return ''\n    prefix = strs[0]\n    for s in strs[1:]:\n        while not s.startswith(prefix):\n            prefix = prefix[:-1]\n            if not prefix: return ''\n    return prefix"),
    ("compress string", "def compress_string(s):\n    if not s: return ''\n    result = []\n    count = 1\n    for i in range(1, len(s)):\n        if s[i] == s[i-1]:\n            count += 1\n        else:\n            result.append(s[i-1] + str(count))\n            count = 1\n    result.append(s[-1] + str(count))\n    return ''.join(result)"),
    ("decompress string", "def decompress_string(s):\n    import re\n    result = []\n    for char, count in re.findall(r'([a-zA-Z])(\\d+)', s):\n        result.append(char * int(count))\n    return ''.join(result)"),
    ("find all substrings", "def all_substrings(s):\n    return [s[i:j] for i in range(len(s)) for j in range(i+1, len(s)+1)]"),
    ("longest palindromic substring", "def longest_palindrome(s):\n    if not s: return ''\n    start = end = 0\n    for i in range(len(s)):\n        l, r = i, i\n        while l >= 0 and r < len(s) and s[l] == s[r]:\n            l -= 1; r += 1\n        if r - l - 1 > end - start:\n            start, end = l+1, r-1\n        l, r = i, i+1\n        while l >= 0 and r < len(s) and s[l] == s[r]:\n            l -= 1; r += 1\n        if r - l - 1 > end - start:\n            start, end = l+1, r-1\n    return s[start:end+1]"),
    ("edit distance", "def edit_distance(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(m+1): dp[i][0] = i\n    for j in range(n+1): dp[0][j] = j\n    for i in range(1, m+1):\n        for j in range(1, n+1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1]\n            else:\n                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])\n    return dp[m][n]"),
    ("longest common subsequence", "def lcs(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(1, m+1):\n        for j in range(1, n+1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1] + 1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]"),
]
for name, code in str_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- List/array operations ---
list_ops = [
    ("find duplicates", "def find_duplicates(lst):\n    seen = set(); dups = set()\n    for x in lst:\n        if x in seen: dups.add(x)\n        seen.add(x)\n    return list(dups)"),
    ("remove duplicates", "def remove_duplicates(lst):\n    return list(dict.fromkeys(lst))"),
    ("find unique", "def unique_elements(lst):\n    return list(dict.fromkeys(lst))"),
    ("chunk list", "def chunk_list(lst, size):\n    return [lst[i:i+size] for i in range(0, len(lst), size)]"),
    ("flatten nested", "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result"),
    ("rotate list", "def rotate_list(lst, k):\n    if not lst: return lst\n    k = k % len(lst)\n    return lst[-k:] + lst[:-k] if k else lst"),
    ("find pairs summing to target", "def find_pairs(nums, target):\n    seen = set(); pairs = []\n    for n in nums:\n        if target - n in seen:\n            pairs.append((target-n, n))\n        seen.add(n)\n    return pairs"),
    ("two sum", "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i\n    return []"),
    ("three sum", "def three_sum(nums):\n    nums.sort(); result = []\n    for i in range(len(nums)-2):\n        if i > 0 and nums[i] == nums[i-1]: continue\n        lo, hi = i+1, len(nums)-1\n        while lo < hi:\n            s = nums[i]+nums[lo]+nums[hi]\n            if s == 0:\n                result.append([nums[i], nums[lo], nums[hi]])\n                lo += 1; hi -= 1\n            elif s < 0: lo += 1\n            else: hi -= 1\n    return result"),
    ("max subarray (Kadane)", "def max_subarray(nums):\n    max_sum = cur = nums[0]\n    for n in nums[1:]:\n        cur = max(n, cur+n)\n        max_sum = max(max_sum, cur)\n    return max_sum"),
    ("house robber", "def house_robber(nums):\n    if not nums: return 0\n    if len(nums) == 1: return nums[0]\n    prev, curr = 0, 0\n    for n in nums:\n        prev, curr = curr, max(curr, prev+n)\n    return curr"),
    ("climbing stairs", "def climb_stairs(n):\n    if n <= 2: return n\n    a, b = 1, 2\n    for _ in range(3, n+1):\n        a, b = b, a+b\n    return b"),
    ("coin change", "def coin_change(coins, amount):\n    dp = [float('inf')]*(amount+1)\n    dp[0] = 0\n    for i in range(1, amount+1):\n        for c in coins:\n            if c <= i:\n                dp[i] = min(dp[i], dp[i-c]+1)\n    return dp[amount] if dp[amount] != float('inf') else -1"),
    ("0/1 knapsack", "def knapsack(w, v, cap):\n    n = len(w)\n    dp = [[0]*(cap+1) for _ in range(n+1)]\n    for i in range(1, n+1):\n        for c in range(1, cap+1):\n            if w[i-1] <= c:\n                dp[i][c] = max(dp[i-1][c], v[i-1]+dp[i-1][c-w[i-1]])\n            else:\n                dp[i][c] = dp[i-1][c]\n    return dp[n][cap]"),
    ("LCS", "def lcs(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(1, m+1):\n        for j in range(1, n+1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1]+1\n            else:\n                dp[i][j] = max(dp[i-1][j], dp[i][j-1])\n    return dp[m][n]"),
    ("edit distance", "def edit_distance(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(m+1): dp[i][0] = i\n    for j in range(n+1): dp[0][j] = j\n    for i in range(1, m+1):\n        for j in range(1, n+1):\n            if s1[i-1] == s2[j-1]:\n                dp[i][j] = dp[i-1][j-1]\n            else:\n                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])\n    return dp[m][n]"),
    ("longest increasing subsequence", "def lis(nums):\n    if not nums: return 0\n    dp = [1]*len(nums)\n    for i in range(1, len(nums)):\n        for j in range(i):\n            if nums[j] < nums[i]:\n                dp[i] = max(dp[i], dp[j]+1)\n    return max(dp)"),
    ("merge intervals", "def merge_intervals(intervals):\n    if not intervals: return []\n    intervals.sort()\n    merged = [intervals[0]]\n    for s, e in intervals[1:]:\n        if s <= merged[-1][1]:\n            merged[-1][1] = max(merged[-1][1], e)\n        else:\n            merged.append([s, e])\n    return merged"),
    ("insert interval", "def insert_interval(intervals, new):\n    result = []\n    i = 0\n    while i < len(intervals) and intervals[i][1] < new[0]:\n        result.append(intervals[i]); i += 1\n    while i < len(intervals) and intervals[i][0] <= new[1]:\n        new = [min(new[0], intervals[i][0]), max(new[1], intervals[i][1])]\n        i += 1\n    result.append(new)\n    result.extend(intervals[i:])\n    return result"),
    ("find peak element", "def find_peak(nums):\n    lo, hi = 0, len(nums)-1\n    while lo < hi:\n        mid = (lo+hi)//2\n        if nums[mid] > nums[mid+1]:\n            hi = mid\n        else:\n            lo = mid+1\n    return lo"),
    ("search in rotated sorted array", "def search_rotated(nums, target):\n    lo, hi = 0, len(nums)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if nums[mid] == target: return mid\n        if nums[lo] <= nums[mid]:\n            if nums[lo] <= target < nums[mid]:\n                hi = mid-1\n            else:\n                lo = mid+1\n        else:\n            if nums[mid] < target <= nums[hi]:\n                lo = mid+1\n            else:\n                hi = mid-1\n    return -1"),
]
for name, code in list_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Data structure classes ---
ds_ops = [
    ("implement a stack", "class Stack:\n    def __init__(self):\n        self.items = []\n    def push(self, item):\n        self.items.append(item)\n    def pop(self):\n        return self.items.pop() if self.items else None\n    def peek(self):\n        return self.items[-1] if self.items else None\n    def is_empty(self):\n        return len(self.items) == 0\n    def size(self):\n        return len(self.items)"),
    ("implement a queue", "from collections import deque\n\nclass Queue:\n    def __init__(self):\n        self.items = deque()\n    def enqueue(self, item):\n        self.items.append(item)\n    def dequeue(self):\n        return self.items.popleft() if self.items else None\n    def is_empty(self):\n        return len(self.items) == 0\n    def size(self):\n        return len(self.items)"),
    ("implement a linked list", "class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n    def append(self, data):\n        new = Node(data)\n        if not self.head:\n            self.head = new\n            return\n        cur = self.head\n        while cur.next:\n            cur = cur.next\n        cur.next = new\n    def to_list(self):\n        result = []\n        cur = self.head\n        while cur:\n            result.append(cur.data)\n            cur = cur.next\n        return result"),
    ("implement a binary search tree", "class BSTNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = self.right = None\n\nclass BST:\n    def __init__(self):\n        self.root = None\n    def insert(self, val):\n        if not self.root:\n            self.root = BSTNode(val)\n            return\n        cur = self.root\n        while True:\n            if val < cur.val:\n                if cur.left is None:\n                    cur.left = BSTNode(val); break\n                cur = cur.left\n            else:\n                if cur.right is None:\n                    cur.right = BSTNode(val); break\n                cur = cur.right\n    def inorder(self):\n        result = []\n        def _inorder(node):\n            if node:\n                _inorder(node.left)\n                result.append(node.val)\n                _inorder(node.right)\n        _inorder(self.root)\n        return result"),
    ("implement a trie", "class TrieNode:\n    def __init__(self):\n        self.children = {}\n        self.is_end = False\n\nclass Trie:\n    def __init__(self):\n        self.root = TrieNode()\n    def insert(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children:\n                node.children[c] = TrieNode()\n            node = node.children[c]\n        node.is_end = True\n    def search(self, word):\n        node = self.root\n        for c in word:\n            if c not in node.children:\n                return False\n            node = node.children[c]\n        return node.is_end\n    def starts_with(self, prefix):\n        node = self.root\n        for c in prefix:\n            if c not in node.children:\n                return False\n            node = node.children[c]\n        return True"),
    ("implement an LRU cache", "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity):\n        self.capacity = capacity\n        self.cache = OrderedDict()\n    def get(self, key):\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n    def put(self, key, value):\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)"),
    ("implement a min heap", "import heapq\n\nclass MinHeap:\n    def __init__(self):\n        self.heap = []\n    def push(self, val):\n        heapq.heappush(self.heap, val)\n    def pop(self):\n        return heapq.heappop(self.heap) if self.heap else None\n    def peek(self):\n        return self.heap[0] if self.heap else None\n    def size(self):\n        return len(self.heap)"),
    ("implement a graph", "class Graph:\n    def __init__(self):\n        self.adj = {}\n    def add_edge(self, u, v):\n        self.adj.setdefault(u, []).append(v)\n        self.adj.setdefault(v, []).append(u)\n    def neighbors(self, node):\n        return self.adj.get(node, [])\n    def has_edge(self, u, v):\n        return v in self.adj.get(u, [])"),
    ("implement a hash map", "class HashMap:\n    def __init__(self, size=16):\n        self.size = size\n        self.buckets = [[] for _ in range(size)]\n    def _hash(self, key):\n        return hash(key) % self.size\n    def put(self, key, value):\n        idx = self._hash(key)\n        for i, (k, v) in enumerate(self.buckets[idx]):\n            if k == key:\n                self.buckets[idx][i] = (key, value)\n                return\n        self.buckets[idx].append((key, value))\n    def get(self, key):\n        idx = self._hash(key)\n        for k, v in self.buckets[idx]:\n            if k == key:\n                return v\n        return None\n    def remove(self, key):\n        idx = self._hash(key)\n        self.buckets[idx] = [(k, v) for k, v in self.buckets[idx] if k != key]"),
    ("implement a disjoint set (union-find)", "class UnionFind:\n    def __init__(self, n):\n        self.parent = list(range(n))\n        self.rank = [0] * n\n    def find(self, x):\n        if self.parent[x] != x:\n            self.parent[x] = self.find(self.parent[x])\n        return self.parent[x]\n    def union(self, x, y):\n        px, py = self.find(x), self.find(y)\n        if px == py: return False\n        if self.rank[px] < self.rank[py]:\n            px, py = py, px\n        self.parent[py] = px\n        if self.rank[px] == self.rank[py]:\n            self.rank[px] += 1\n        return True"),
    ("implement a segment tree", "class SegmentTree:\n    def __init__(self, arr):\n        self.n = len(arr)\n        self.tree = [0] * (2 * self.n)\n        for i in range(self.n):\n            self.tree[self.n + i] = arr[i]\n        for i in range(self.n - 1, 0, -1):\n            self.tree[i] = self.tree[2*i] + self.tree[2*i+1]\n    def update(self, pos, val):\n        pos += self.n\n        self.tree[pos] = val\n        while pos > 1:\n            pos //= 2\n            self.tree[pos] = self.tree[2*pos] + self.tree[2*pos+1]\n    def query(self, l, r):\n        l += self.n; r += self.n\n        res = 0\n        while l < r:\n            if l & 1:\n                res += self.tree[l]; l += 1\n            if r & 1:\n                r -= 1; res += self.tree[r]\n            l //= 2; r //= 2\n        return res"),
    ("implement a Fenwick tree (BIT)", "class FenwickTree:\n    def __init__(self, n):\n        self.n = n\n        self.bit = [0] * (n + 1)\n    def update(self, i, delta):\n        i += 1\n        while i <= self.n:\n            self.bit[i] += delta\n            i += i & (-i)\n    def query(self, i):\n        s = 0\n        i += 1\n        while i > 0:\n            s += self.bit[i]\n            i -= i & (-i)\n        return s"),
    ("implement a doubly linked list", "class DNode:\n    def __init__(self, data):\n        self.data = data\n        self.prev = self.next = None\n\nclass DoublyLinkedList:\n    def __init__(self):\n        self.head = self.tail = None\n    def append(self, data):\n        new = DNode(data)\n        if not self.head:\n            self.head = self.tail = new\n            return\n        self.tail.next = new\n        new.prev = self.tail\n        self.tail = new\n    def to_list(self):\n        result = []\n        cur = self.head\n        while cur:\n            result.append(cur.data)\n            cur = cur.next\n        return result"),
    ("implement a circular queue", "class CircularQueue:\n    def __init__(self, size):\n        self.size = size\n        self.queue = [None] * size\n        self.front = self.rear = -1\n    def enqueue(self, val):\n        if (self.rear + 1) % self.size == self.front:\n            return False\n        if self.front == -1:\n            self.front = 0\n        self.rear = (self.rear + 1) % self.size\n        self.queue[self.rear] = val\n        return True\n    def dequeue(self):\n        if self.front == -1:\n            return None\n        val = self.queue[self.front]\n        if self.front == self.rear:\n            self.front = self.rear = -1\n        else:\n            self.front = (self.front + 1) % self.size\n        return val"),
    ("implement a priority queue", "import heapq\n\nclass PriorityQueue:\n    def __init__(self):\n        self.heap = []\n    def push(self, priority, item):\n        heapq.heappush(self.heap, (priority, item))\n    def pop(self):\n        return heapq.heappop(self.heap)[1] if self.heap else None\n    def peek(self):\n        return self.heap[0][1] if self.heap else None\n    def is_empty(self):\n        return len(self.heap) == 0"),
    ("implement a deque", "from collections import deque\n\nclass Deque:\n    def __init__(self):\n        self.items = deque()\n    def add_front(self, item):\n        self.items.appendleft(item)\n    def add_rear(self, item):\n        self.items.append(item)\n    def remove_front(self):\n        return self.items.popleft() if self.items else None\n    def remove_rear(self):\n        return self.items.pop() if self.items else None\n    def is_empty(self):\n        return len(self.items) == 0"),
]
for name, code in ds_ops:
    samples.append({"instruction": f"Write a Python class to {name}.", "response": code})

# --- Decorators and patterns ---
pattern_ops = [
    ("implement a singleton pattern", "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance"),
    ("implement a factory pattern", "class AnimalFactory:\n    @staticmethod\n    def create(animal_type):\n        if animal_type == 'dog':\n            return Dog()\n        elif animal_type == 'cat':\n            return Cat()\n        raise ValueError(f'Unknown type: {animal_type}')\n\nclass Dog:\n    def speak(self): return 'Woof!'\n\nclass Cat:\n    def speak(self): return 'Meow!'"),
    ("implement observer pattern", "class Subject:\n    def __init__(self):\n        self.observers = []\n    def attach(self, obs):\n        self.observers.append(obs)\n    def detach(self, obs):\n        self.observers.remove(obs)\n    def notify(self, msg):\n        for obs in self.observers:\n            obs.update(msg)\n\nclass Observer:\n    def update(self, msg):\n        print(f'Received: {msg}')"),
    ("implement strategy pattern", "class SortStrategy:\n    def sort(self, data):\n        raise NotImplementedError\n\nclass BubbleSort(SortStrategy):\n    def sort(self, data):\n        return sorted(data)  # simplified\n\nclass Context:\n    def __init__(self, strategy):\n        self.strategy = strategy\n    def execute(self, data):\n        return self.strategy.sort(data)"),
    ("implement a decorator that times functions", "import time\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time()-start:.4f}s')\n        return result\n    return wrapper"),
    ("implement a memoization decorator", "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper"),
    ("implement a retry decorator", "import time\n\ndef retry(max_attempts=3, delay=1):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            for attempt in range(max_attempts):\n                try:\n                    return func(*args, **kwargs)\n                except Exception:\n                    if attempt == max_attempts - 1:\n                        raise\n                    time.sleep(delay)\n        return wrapper\n    return decorator"),
    ("implement a context manager for files", "class FileManager:\n    def __init__(self, filename, mode):\n        self.filename = filename\n        self.mode = mode\n        self.file = None\n    def __enter__(self):\n        self.file = open(self.filename, self.mode)\n        return self.file\n    def __exit__(self, *args):\n        if self.file:\n            self.file.close()"),
    ("implement a property decorator", "class Temperature:\n    def __init__(self, celsius=0):\n        self._celsius = celsius\n    @property\n    def celsius(self):\n        return self._celsius\n    @celsius.setter\n    def celsius(self, value):\n        if value < -273.15:\n            raise ValueError('Below absolute zero')\n        self._celsius = value\n    @property\n    def fahrenheit(self):\n        return (self._celsius * 9/5) + 32"),
    ("implement a class method and static method", "class MathUtils:\n    @staticmethod\n    def add(a, b):\n        return a + b\n    @classmethod\n    def from_string(cls, s):\n        a, b = map(int, s.split(','))\n        return cls(a, b)\n    def __init__(self, a, b):\n        self.a = a\n        self.b = b"),
]
for name, code in pattern_ops:
    samples.append({"instruction": f"Write a Python implementation to {name}.", "response": code})

# --- File I/O and system ---
io_ops = [
    ("read a file", "def read_file(filename):\n    with open(filename, 'r') as f:\n        return f.read()"),
    ("write to a file", "def write_file(filename, content):\n    with open(filename, 'w') as f:\n        f.write(content)"),
    ("append to a file", "def append_file(filename, content):\n    with open(filename, 'a') as f:\n        f.write(content)"),
    ("read lines from file", "def read_lines(filename):\n    with open(filename, 'r') as f:\n        return f.readlines()"),
    ("count lines in file", "def count_lines(filename):\n    with open(filename, 'r') as f:\n        return sum(1 for _ in f)"),
    ("copy file", "import shutil\n\ndef copy_file(src, dst):\n    shutil.copy2(src, dst)"),
    ("delete file", "import os\n\ndef delete_file(filename):\n    if os.path.exists(filename):\n        os.remove(filename)"),
    ("list directory", "import os\n\ndef list_dir(path):\n    return os.listdir(path)"),
    ("create directory", "import os\n\ndef create_dir(path):\n    os.makedirs(path, exist_ok=True)"),
    ("check if file exists", "import os\n\ndef file_exists(path):\n    return os.path.isfile(path)"),
    ("check if directory exists", "import os\n\ndef dir_exists(path):\n    return os.path.isdir(path)"),
    ("get file size", "import os\n\ndef file_size(path):\n    return os.path.getsize(path)"),
    ("get file extension", "import os\n\ndef file_extension(path):\n    return os.path.splitext(path)[1]"),
    ("get file name without extension", "import os\n\ndef file_name(path):\n    return os.path.splitext(os.path.basename(path))[0]"),
    ("join paths", "import os\n\ndef join_paths(*parts):\n    return os.path.join(*parts)"),
    ("get absolute path", "import os\n\ndef abs_path(path):\n    return os.path.abspath(path)"),
    ("get current directory", "import os\n\ndef current_dir():\n    return os.getcwd()"),
    ("walk directory tree", "import os\n\ndef walk_dir(path):\n    result = []\n    for root, dirs, files in os.walk(path):\n        for f in files:\n            result.append(os.path.join(root, f))\n    return result"),
    ("read JSON file", "import json\n\ndef read_json(filename):\n    with open(filename, 'r') as f:\n        return json.load(f)"),
    ("write JSON file", "import json\n\ndef write_json(filename, data):\n    with open(filename, 'w') as f:\n        json.dump(data, f, indent=2)"),
    ("read CSV file", "import csv\n\ndef read_csv(filename):\n    with open(filename, 'r') as f:\n        return list(csv.reader(f))"),
    ("write CSV file", "import csv\n\ndef write_csv(filename, data):\n    with open(filename, 'w', newline='') as f:\n        writer = csv.writer(f)\n        writer.writerows(data)"),
]
for name, code in io_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Error handling and validation ---
err_ops = [
    ("validate email", "import re\n\ndef validate_email(email):\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))"),
    ("validate phone number", "import re\n\ndef validate_phone(phone):\n    pattern = r'^\\+?1?[-. ]?\\(?\\d{3}\\)?[-. ]?\\d{3}[-. ]?\\d{4}$'\n    return bool(re.match(pattern, phone))"),
    ("validate URL", "import re\n\ndef validate_url(url):\n    pattern = r'^https?://[\\w\\-]+(\\.[\\w\\-]+)+[/#?]?.*$'\n    return bool(re.match(pattern, url))"),
    ("validate IP address", "import re\n\ndef validate_ip(ip):\n    pattern = r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$'\n    if not re.match(pattern, ip):\n        return False\n    return all(0 <= int(part) <= 255 for part in ip.split('.'))"),
    ("validate date format", "import re\n\ndef validate_date(date_str):\n    pattern = r'^\\d{4}-\\d{2}-\\d{2}$'\n    return bool(re.match(pattern, date_str))"),
    ("safe division", "def safe_divide(a, b):\n    if b == 0:\n        return None\n    return a / b"),
    ("safe list access", "def safe_get(lst, index, default=None):\n    try:\n        return lst[index]\n    except (IndexError, TypeError):\n        return default"),
    ("safe dict access", "def safe_get_dict(d, key, default=None):\n    try:\n        return d[key]\n    except (KeyError, TypeError):\n        return default"),
    ("try except wrapper", "def try_except(func, *args, **kwargs):\n    try:\n        return func(*args, **kwargs)\n    except Exception as e:\n        return str(e)"),
    ("validate positive integer", "def is_positive_int(val):\n    return isinstance(val, int) and val > 0"),
    ("validate non-empty string", "def is_non_empty_string(s):\n    return isinstance(s, str) and len(s.strip()) > 0"),
    ("validate list type", "def is_list(val):\n    return isinstance(val, list)"),
    ("validate dict type", "def is_dict(val):\n    return isinstance(val, dict)"),
    ("validate numeric", "def is_numeric(val):\n    return isinstance(val, (int, float)) and not isinstance(val, bool)"),
    ("clamp value", "def clamp(val, lo, hi):\n    return max(lo, min(hi, val))"),
    ("sanitize input", "def sanitize(s):\n    return s.strip().replace('<', '&lt;').replace('>', '&gt;')"),
    ("escape html", "import html\n\ndef escape_html(s):\n    return html.escape(s)"),
    ("remove special chars", "import re\n\ndef remove_special(s):\n    return re.sub(r'[^a-zA-Z0-9\\s]', '', s)"),
    ("normalize whitespace", "import re\n\ndef normalize_ws(s):\n    return re.sub(r'\\s+', ' ', s).strip()"),
]
for name, code in err_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Functional programming ---
fp_ops = [
    ("implement map", "def my_map(func, lst):\n    return [func(x) for x in lst]"),
    ("implement filter", "def my_filter(func, lst):\n    return [x for x in lst if func(x)]"),
    ("implement reduce", "def my_reduce(func, lst, init=None):\n    result = init if init is not None else lst[0]\n    start = 0 if init is not None else 1\n    for x in lst[start:]:\n        result = func(result, x)\n    return result"),
    ("implement zip", "def my_zip(*iterables):\n    min_len = min(len(it) for it in iterables)\n    return [tuple(it[i] for it in iterables) for i in range(min_len)]"),
    ("implement enumerate", "def my_enumerate(lst, start=0):\n    return [(i+start, x) for i, x in enumerate(lst)]"),
    ("implement any", "def my_any(lst):\n    for x in lst:\n        if x: return True\n    return False"),
    ("implement all", "def my_all(lst):\n    for x in lst:\n        if not x: return False\n    return True"),
    ("implement chain", "def chain(*iterables):\n    result = []\n    for it in iterables:\n        result.extend(it)\n    return result"),
    ("implement take", "def take(n, iterable):\n    result = []\n    for i, x in enumerate(iterable):\n        if i >= n: break\n        result.append(x)\n    return result"),
    ("implement drop", "def drop(n, iterable):\n    result = []\n    for i, x in enumerate(iterable):\n        if i >= n:\n            result.append(x)\n    return result"),
    ("implement group by", "from collections import defaultdict\n\ndef group_by(lst, key_func):\n    result = defaultdict(list)\n    for item in lst:\n        result[key_func(item)].append(item)\n    return dict(result)"),
    ("implement memoize", "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper"),
    ("implement compose", "def compose(f, g):\n    return lambda x: f(g(x))"),
    ("implement pipe", "def pipe(*funcs):\n    def wrapper(x):\n        for f in funcs:\n            x = f(x)\n        return x\n    return wrapper"),
    ("implement curry", "def curry(func):\n    def curried(*args):\n        if len(args) >= func.__code__.co_argcount:\n            return func(*args)\n        return lambda *more: curried(*(args + more))\n    return curried"),
    ("implement partial application", "def partial(func, *args):\n    def wrapper(*more):\n        return func(*(args + more))\n    return wrapper"),
    ("implement identity", "def identity(x):\n    return x"),
    ("implement constant", "def constant(x):\n    return lambda *args, **kwargs: x"),
    ("implement flip", "def flip(func):\n    return lambda a, b: func(b, a)"),
    ("implement negate", "def negate(pred):\n    return lambda x: not pred(x)"),
]
for name, code in fp_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Comprehensions and generators ---
comp_ops = [
    ("list comprehension for squares", "def squares(n):\n    return [x**2 for x in range(n)]"),
    ("list comprehension for evens", "def evens(n):\n    return [x for x in range(n) if x % 2 == 0]"),
    ("list comprehension for odds", "def odds(n):\n    return [x for x in range(n) if x % 2 != 0]"),
    ("dict comprehension", "def squares_dict(n):\n    return {x: x**2 for x in range(n)}"),
    ("set comprehension", "def unique_squares(n):\n    return {x**2 for x in range(n)}"),
    ("generator for fibonacci", "def fib_gen(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b"),
    ("generator for primes", "def prime_gen(n):\n    for num in range(2, n+1):\n        if all(num % i != 0 for i in range(2, int(num**0.5)+1)):\n            yield num"),
    ("generator for even numbers", "def even_gen(n):\n    for x in range(0, n, 2):\n        yield x"),
    ("generator expression", "def sum_of_squares_gen(n):\n    return sum(x**2 for x in range(n))"),
    ("nested list comprehension", "def matrix(n):\n    return [[i*j for j in range(n)] for i in range(n)]"),
    ("flatten with comprehension", "def flatten_comp(nested):\n    return [item for sublist in nested for item in sublist]"),
    ("filter with comprehension", "def filter_comp(lst, pred):\n    return [x for x in lst if pred(x)]"),
    ("map with comprehension", "def map_comp(lst, func):\n    return [func(x) for x in lst]"),
    ("zip with comprehension", "def zip_comp(a, b):\n    return [(x, y) for x, y in zip(a, b)]"),
    ("enumerate with comprehension", "def enum_comp(lst):\n    return [(i, x) for i, x in enumerate(lst)]"),
]
for name, code in comp_ops:
    samples.append({"instruction": f"Write a Python function using {name}.", "response": code})

# --- OOP patterns ---
oop_ops = [
    ("create a class with constructor", "class Person:\n    def __init__(self, name, age):\n        self.name = name\n        self.age = age\n    def greet(self):\n        return f'Hello, I am {self.name}'"),
    ("implement inheritance", "class Animal:\n    def __init__(self, name):\n        self.name = name\n    def speak(self):\n        return 'Some sound'\n\nclass Dog(Animal):\n    def speak(self):\n        return 'Woof!'"),
    ("implement multiple inheritance", "class A:\n    def method_a(self):\n        return 'A'\n\nclass B:\n    def method_b(self):\n        return 'B'\n\nclass C(A, B):\n    def method_c(self):\n        return 'C'"),
    ("implement abstract base class", "from abc import ABC, abstractmethod\n\nclass Shape(ABC):\n    @abstractmethod\n    def area(self):\n        pass\n    @abstractmethod\n    def perimeter(self):\n        pass\n\nclass Circle(Shape):\n    def __init__(self, r):\n        self.r = r\n    def area(self):\n        import math\n        return math.pi * self.r ** 2\n    def perimeter(self):\n        import math\n        return 2 * math.pi * self.r"),
    ("implement property", "class Circle:\n    def __init__(self, radius):\n        self._radius = radius\n    @property\n    def radius(self):\n        return self._radius\n    @radius.setter\n    def radius(self, value):\n        if value < 0:\n            raise ValueError('Radius must be non-negative')\n        self._radius = value\n    @property\n    def area(self):\n        import math\n        return math.pi * self._radius ** 2"),
    ("implement __str__ and __repr__", "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n    def __str__(self):\n        return f'Point({self.x}, {self.y})'\n    def __repr__(self):\n        return f'Point({self.x}, {self.y})'\n    def __eq__(self, other):\n        return self.x == other.x and self.y == other.y"),
    ("implement __len__ and __getitem__", "class MyList:\n    def __init__(self, items):\n        self.items = items\n    def __len__(self):\n        return len(self.items)\n    def __getitem__(self, index):\n        return self.items[index]\n    def __iter__(self):\n        return iter(self.items)"),
    ("implement context manager", "class Timer:\n    import time\n    def __enter__(self):\n        self.start = time.time()\n        return self\n    def __exit__(self, *args):\n        self.elapsed = time.time() - self.start\n        print(f'Elapsed: {self.elapsed:.4f}s')"),
    ("implement iterator", "class Counter:\n    def __init__(self, start, end):\n        self.current = start\n        self.end = end\n    def __iter__(self):\n        return self\n    def __next__(self):\n        if self.current >= self.end:\n            raise StopIteration\n        val = self.current\n        self.current += 1\n        return val"),
    ("implement callable object", "class Multiplier:\n    def __init__(self, factor):\n        self.factor = factor\n    def __call__(self, x):\n        return x * self.factor"),
]
for name, code in oop_ops:
    samples.append({"instruction": f"Write a Python implementation to {name}.", "response": code})

# --- Error handling ---
err_ops = [
    ("handle division by zero", "def safe_divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None"),
    ("handle file not found", "def safe_read_file(filename):\n    try:\n        with open(filename, 'r') as f:\n            return f.read()\n    except FileNotFoundError:\n        return None"),
    ("handle key error", "def safe_get(d, key, default=None):\n    try:\n        return d[key]\n    except KeyError:\n        return default"),
    ("handle index error", "def safe_index(lst, idx, default=None):\n    try:\n        return lst[idx]\n    except IndexError:\n        return default"),
    ("handle value error", "def safe_int(s):\n    try:\n        return int(s)\n    except ValueError:\n        return None"),
    ("handle type error", "def safe_add(a, b):\n    try:\n        return a + b\n    except TypeError:\n        return None"),
    ("custom exception", "class ValidationError(Exception):\n    pass\n\ndef validate_age(age):\n    if not isinstance(age, int) or age < 0:\n        raise ValidationError('Invalid age')\n    return age"),
    ("retry on failure", "import time\n\ndef retry(func, max_attempts=3, delay=1):\n    for attempt in range(max_attempts):\n        try:\n            return func()\n        except Exception:\n            if attempt == max_attempts - 1:\n                raise\n            time.sleep(delay)"),
    ("validate email", "import re\n\ndef validate_email(email):\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return bool(re.match(pattern, email))"),
    ("validate phone", "import re\n\ndef validate_phone(phone):\n    pattern = r'^\\+?1?[-. ]?\\(?\\d{3}\\)?[-. ]?\\d{3}[-. ]?\\d{4}$'\n    return bool(re.match(pattern, phone))"),
    ("validate URL", "import re\n\ndef validate_url(url):\n    pattern = r'^https?://[\\w\\-]+(\\.[\\w\\-]+)+[/#?]?.*$'\n    return bool(re.match(pattern, url))"),
    ("validate IP", "import re\n\ndef validate_ip(ip):\n    pattern = r'^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$'\n    if not re.match(pattern, ip):\n        return False\n    return all(0 <= int(p) <= 255 for p in ip.split('.'))"),
    ("sanitize input", "def sanitize(s):\n    return s.strip().replace('<', '&lt;').replace('>', '&gt;')"),
    ("escape html", "import html\n\ndef escape_html(s):\n    return html.escape(s)"),
    ("remove special chars", "import re\n\ndef remove_special(s):\n    return re.sub(r'[^a-zA-Z0-9\\s]', '', s)"),
    ("normalize whitespace", "import re\n\ndef normalize_ws(s):\n    return re.sub(r'\\s+', ' ', s).strip()"),
    ("clamp value", "def clamp(val, lo, hi):\n    return max(lo, min(hi, val))"),
    ("validate positive int", "def is_positive_int(val):\n    return isinstance(val, int) and val > 0 and not isinstance(val, bool)"),
    ("validate non-empty string", "def is_non_empty_string(s):\n    return isinstance(s, str) and len(s.strip()) > 0"),
]
for name, code in err_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# --- Decorators ---
dec_ops = [
    ("timer decorator", "import time\n\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} took {time.time()-start:.4f}s')\n        return result\n    return wrapper"),
    ("memoize decorator", "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper"),
    ("retry decorator", "import time\n\ndef retry(max_attempts=3, delay=1):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            for attempt in range(max_attempts):\n                try:\n                    return func(*args, **kwargs)\n                except Exception:\n                    if attempt == max_attempts - 1:\n                        raise\n                    time.sleep(delay)\n        return wrapper\n    return decorator"),
    ("cache decorator", "def cache(func):\n    _cache = {}\n    def wrapper(*args):\n        if args not in _cache:\n            _cache[args] = func(*args)\n        return _cache[args]\n    return wrapper"),
    ("log decorator", "import functools\n\ndef log(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        print(f'Calling {func.__name__} with {args}, {kwargs}')\n        result = func(*args, **kwargs)\n        print(f'{func.__name__} returned {result}')\n        return result\n    return wrapper"),
    ("validate args decorator", "def validate_args(func):\n    def wrapper(*args, **kwargs):\n        # Simple validation: check no None args\n        if any(a is None for a in args):\n            raise ValueError('Arguments cannot be None')\n        return func(*args, **kwargs)\n    return wrapper"),
    ("deprecated decorator", "import warnings\n\ndef deprecated(func):\n    def wrapper(*args, **kwargs):\n        warnings.warn(f'{func.__name__} is deprecated', DeprecationWarning)\n        return func(*args, **kwargs)\n    return wrapper"),
    ("singleton decorator", "def singleton(cls):\n    instances = {}\n    def get_instance(*args, **kwargs):\n        if cls not in instances:\n            instances[cls] = cls(*args, **kwargs)\n        return instances[cls]\n    return get_instance"),
    ("register decorator", "REGISTRY = {}\n\ndef register(name):\n    def decorator(func):\n        REGISTRY[name] = func\n        return func\n    return decorator"),
    ("trace decorator", "def trace(func):\n    def wrapper(*args, **kwargs):\n        print(f'-> {func.__name__}({args}, {kwargs})')\n        result = func(*args, **kwargs)\n        print(f'<- {func.__name__} = {result}')\n        return result\n    return wrapper"),
]
for name, code in dec_ops:
    samples.append({"instruction": f"Write a Python {name}.", "response": code})

# --- Recursion problems ---
rec_ops = [
    ("factorial recursive", "def factorial(n):\n    if n <= 1: return 1\n    return n * factorial(n-1)"),
    ("fibonacci recursive", "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)"),
    ("power recursive", "def power(base, exp):\n    if exp == 0: return 1\n    if exp % 2 == 0:\n        half = power(base, exp // 2)\n        return half * half\n    return base * power(base, exp - 1)"),
    ("gcd recursive", "def gcd(a, b):\n    if b == 0: return a\n    return gcd(b, a % b)"),
    ("sum list recursive", "def sum_list(lst):\n    if not lst: return 0\n    return lst[0] + sum_list(lst[1:])"),
    ("reverse string recursive", "def reverse_str(s):\n    if len(s) <= 1: return s\n    return reverse_str(s[1:]) + s[0]"),
    ("flatten recursive", "def flatten(lst):\n    result = []\n    for item in lst:\n        if isinstance(item, list):\n            result.extend(flatten(item))\n        else:\n            result.append(item)\n    return result"),
    ("binary search recursive", "def binary_search(arr, target, lo=0, hi=None):\n    if hi is None: hi = len(arr) - 1\n    if lo > hi: return -1\n    mid = (lo + hi) // 2\n    if arr[mid] == target: return mid\n    if arr[mid] < target: return binary_search(arr, target, mid+1, hi)\n    return binary_search(arr, target, lo, mid-1)"),
    ("merge sort recursive", "def merge_sort(arr):\n    if len(arr) <= 1: return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)\n\ndef merge(a, b):\n    r = []; i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            r.append(a[i]); i += 1\n        else:\n            r.append(b[j]); j += 1\n    r.extend(a[i:]); r.extend(b[j:])\n    return r"),
    ("quick sort recursive", "def quick_sort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)"),
    ("tower of hanoi", "def hanoi(n, source, target, auxiliary):\n    if n == 1:\n        print(f'Move disk 1 from {source} to {target}')\n        return\n    hanoi(n-1, source, auxiliary, target)\n    print(f'Move disk {n} from {source} to {target}')\n    hanoi(n-1, auxiliary, target, source)"),
    ("permutations", "def permutations(s):\n    if len(s) <= 1: return [s]\n    result = []\n    for i, c in enumerate(s):\n        for p in permutations(s[:i] + s[i+1:]):\n            result.append(c + p)\n    return result"),
    ("combinations", "def combinations(lst, r):\n    if r == 0: return [[]]\n    if not lst: return []\n    result = []\n    for i in range(len(lst)):\n        for c in combinations(lst[i+1:], r-1):\n            result.append([lst[i]] + c)\n    return result"),
    ("subsets", "def subsets(lst):\n    if not lst: return [[]]\n    rest = subsets(lst[1:])\n    return rest + [[lst[0]] + s for s in rest]"),
]
for name, code in rec_ops:
    samples.append({"instruction": f"Write a Python function to {name}.", "response": code})

# Write all samples
TRAIN.mkdir(parents=True, exist_ok=True)
DATA.write_text("\n".join(json.dumps(s) for s in samples) + "\n")
print(f"Generated {len(samples)} training samples -> {DATA}")
