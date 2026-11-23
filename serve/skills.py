#!/usr/bin/env python3
"""Bhajanlal skill library - loads EVERY skill so the model can use them.

Reads every ``SKILL.md`` under ``~/.config/opencode/skills`` (the library
written by ``skill_build/build.py``: 488 skills across 40 pillars, 600/600
coverage) and exposes it to the runtime in four ways:

  1. ``prompt_block()``   - system-prompt section: the skills that are
     relevant to the current user message (full workflow text) plus a compact
     index of ALL skills, so no capability is ever invisible to the model.
  2. ``tool_result()``    - the ``skill`` builtin tool (load / search / list)
     so agent mode can pull any of the 488 skill bodies on demand.
  3. ``catalog()``        - JSON-ready list behind ``GET /v1/skills``.
  4. ``select()``         - relevance scoring reused for response metadata.

The directory is scanned once; afterwards it is re-scanned only when the
directory mtime changes (build.py rewrites skills/ atomically), so the
per-request cost is a few microseconds of token scoring.
"""
from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_ROOT = Path.home() / ".config" / "opencode" / "skills"

_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
# Two pillar spellings exist in the library:
#   "Pillar: 34. Product Strategy, Growth & AI Evals"
#   "Pillar: Game Development, 3D, Shaders & Graphics (100 skills)"
_PILLAR_RE = re.compile(r"Pillar:\s*(?:(\d+)\.\s*)?([^\n]+)")
_PILLAR_SUFFIX_RE = re.compile(r"\s*\(\d+\s+skills?\)\s*$", re.I)
_WORD_RE = re.compile(r"[a-z0-9]+")

# Words that carry no routing signal (kept small on purpose - a stray
# stopword removal is cheaper than a missed skill match).
_STOP = {
    "the", "and", "for", "you", "your", "with", "that", "this", "these",
    "those", "are", "was", "were", "have", "has", "had", "but", "not",
    "can", "could", "should", "would", "will", "shall", "may", "might",
    "from", "into", "onto", "than", "then", "them", "they", "their",
    "what", "which", "when", "where", "who", "whom", "how", "why",
    "please", "make", "give", "show", "tell", "want", "need", "like",
    "about", "some", "any", "all", "one", "two", "use", "using", "used",
    "write", "create", "build", "help", "just", "very", "more", "most",
    "out", "get", "got", "run", "runn", "its", "it's", "a", "an", "of",
    "in", "on", "to", "is", "it", "be", "do", "does", "did", "if", "or",
    "as", "at", "by", "we", "us", "our", "i", "me", "my", "he", "she",
}


def _tokens(text: str) -> set:
    return {w for w in _WORD_RE.findall((text or "").lower())
            if len(w) > 2 and w not in _STOP}


class SkillLibrary:
    """Thread-safe, mtime-refreshed view of the on-disk skill library."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or DEFAULT_ROOT).expanduser()
        self._lock = threading.Lock()
        self._skills: List[dict] = []
        self._by_id: Dict[str, dict] = {}
        self._dir_mtime: float = -1.0
        self._built_at: float = 0.0

    # ---------------------------------------------------------------- loading
    def _ensure(self) -> None:
        try:
            mtime = self.root.stat().st_mtime
        except OSError:
            mtime = -1.0
        with self._lock:
            if self._skills and mtime == self._dir_mtime:
                return
            self._scan()
            self._dir_mtime = mtime

    def _scan(self) -> None:
        skills: List[dict] = []
        if self.root.is_dir():
            for path in sorted(self.root.iterdir()):
                body_file = path / "SKILL.md"
                if not body_file.is_file():
                    continue
                try:
                    raw = body_file.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                front = ""
                m = _FRONT_RE.match(raw)
                if m:
                    front = m.group(1)
                    body = raw[m.end():]
                else:
                    body = raw
                name = self._front_field(front, "name") or path.name
                desc = self._front_field(front, "description") or ""
                if not desc:
                    # First non-heading, non-empty line is a decent fallback.
                    for line in body.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("Part of"):
                            desc = line
                            break
                pm = _PILLAR_RE.search(body)
                pillar_n = int(pm.group(1)) if pm and pm.group(1) else 0
                pillar_t = _PILLAR_SUFFIX_RE.sub("", pm.group(2)).strip() if pm else ""
                if not pillar_t:
                    pillar_t = "Ungrouped"
                skills.append({
                    "id": path.name,
                    "name": name.strip(),
                    "description": desc.strip(),
                    "pillar": pillar_n,
                    "pillar_title": pillar_t,
                    "pillar_key": str(pillar_n) if pillar_n else ("t:" + pillar_t),
                    "body": body.strip(),
                    "path": str(body_file),
                    # Pre-computed scoring surfaces (built once per scan).
                    "id_tokens": _tokens(path.name.replace("-", " ")),
                    "name_lower": name.lower(),
                    "desc_lower": desc.lower(),
                    "body_lower": body.lower(),
                    "body_len": len(body),
                })
        self._skills = skills
        self._by_id = {s["id"]: s for s in skills}
        self._built_at = time.time()

    @staticmethod
    def _front_field(front: str, key: str) -> str:
        m = re.search(r"^%s:\s*(.+)$" % re.escape(key), front, re.M)
        return m.group(1).strip() if m else ""

    # --------------------------------------------------------------- queries
    @property
    def count(self) -> int:
        self._ensure()
        return len(self._skills)

    @property
    def pillar_count(self) -> int:
        self._ensure()
        return len({s["pillar_key"] for s in self._skills})

    def catalog(self) -> List[dict]:
        self._ensure()
        return [{
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "pillar": s["pillar"],
            "pillar_title": s["pillar_title"],
        } for s in self._skills]

    def get(self, ident: str) -> Optional[dict]:
        """Exact id, exact name, then case-insensitive / substring match."""
        self._ensure()
        key = (ident or "").strip()
        if not key:
            return None
        hit = self._by_id.get(key) or self._by_id.get(key.lower())
        if hit:
            return hit
        low = key.lower()
        for s in self._skills:
            if s["name"].lower() == low:
                return s
        for s in self._skills:
            if low in s["id"] or low in s["name_lower"]:
                return s
        return None

    def _score(self, s: dict, qtokens: set, qlow: str) -> float:
        score = 0.0
        for t in qtokens:
            if t in s["id_tokens"]:
                score += 3.0
            elif t in s["name_lower"]:
                score += 2.2
            elif t in s["desc_lower"]:
                score += 1.6
            elif t in s["body_lower"]:
                score += 0.35
        if len(qlow) >= 14 and qlow in s["body_lower"]:
            score += 1.5
        return score

    def search(self, query: str, limit: int = 8) -> List[dict]:
        """Ranked skills for a free-text query (id/name/description/body)."""
        self._ensure()
        qlow = (query or "").strip().lower()
        qtokens = _tokens(qlow)
        if not qtokens and not qlow:
            return []
        ranked = []
        for s in self._skills:
            sc = self._score(s, qtokens, qlow)
            if sc > 0:
                ranked.append((sc, s))
        ranked.sort(key=lambda p: (-p[0], p[1]["id"]))
        return [self._public(s, score=round(sc, 2)) for sc, s in ranked[: max(1, limit)]]

    def select(self, text: str, limit: int = 5, min_score: float = 2.0) -> List[dict]:
        """Skills relevant to the current request (auto-applied to the prompt)."""
        self._ensure()
        low = (text or "").strip().lower()
        qtokens = _tokens(low)
        if not qtokens:
            return []
        ranked = []
        for s in self._skills:
            sc = self._score(s, qtokens, low)
            if sc >= min_score:
                ranked.append((sc, s))
        ranked.sort(key=lambda p: (-p[0], p[1]["id"]))
        return [self._public(s, score=round(sc, 2), with_body=True)
                for sc, s in ranked[: max(1, limit)]]

    @staticmethod
    def _public(s: dict, score: Optional[float] = None,
                with_body: bool = False) -> dict:
        out = {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "pillar": s["pillar"],
            "pillar_title": s["pillar_title"],
        }
        if score is not None:
            out["score"] = score
        if with_body:
            out["workflow"] = s["body"]
        return out

    # ------------------------------------------------------- text rendering
    def index_text(self) -> str:
        """Dense 'id - name' index of every skill, grouped by pillar."""
        self._ensure()
        groups: Dict[str, List[str]] = {}
        heads: Dict[str, str] = {}
        for s in self._skills:
            key = s["pillar_key"]
            groups.setdefault(key, []).append("%s - %s" % (s["id"], s["name"]))
            if key not in heads:
                heads[key] = (
                    "%d. %s" % (s["pillar"], s["pillar_title"])
                    if s["pillar"] else s["pillar_title"]
                )

        def order(k: str) -> tuple:
            return (0, int(k), "") if k.isdigit() else (1, 0, heads[k].lower())

        lines: List[str] = []
        for key in sorted(groups, key=order):
            lines.append("%s: %s" % (heads[key], ", ".join(groups[key])))
        return "\n".join(lines)

    def prompt_block(self, user_text: str, mode: str = "full",
                     max_applied: int = 5) -> str:
        """System-prompt section wiring the whole library into the model.

        mode="full"     -> applied skills + full 488-skill index (default)
        mode="applied"  -> only the skills relevant to this message
        mode="off"      -> nothing
        """
        mode = (mode or "full").lower()
        if mode in ("off", "0", "false", "none"):
            return ""
        self._ensure()
        n = len(self._skills)
        if not n:
            return ""
        applied = self.select(user_text, limit=max_applied)
        parts: List[str] = []
        head = (
            "BHAIJANLAL SKILL LIBRARY - %d skills across %d pillars are LOADED "
            "and active for you on every request." % (n, self.pillar_count)
        )
        parts.append(head)
        parts.append(
            "Before answering: pick every skill below that applies to the user's "
            "request and follow its Workflow step by step, then deliver its "
            "documented Output. When a task matches a skill you were not given, "
            "load it with the `skill` tool (actions: load / search / list) or, "
            "in plain chat, use the full index to name the skill and follow it "
            "from memory of its description. Skills always win over improvisation."
        )
        if applied:
            parts.append("APPLIED FOR THIS REQUEST (follow exactly):")
            for i, s in enumerate(applied, 1):
                block = "[%d] %s  (id: %s)\n" % (i, s["name"], s["id"])
                block += "Pillar: %s\n" % self._pillar_head(s)
                block += s["description"] + "\n" + s["workflow"]
                parts.append(block)
        else:
            parts.append(
                "No skill matched this message exactly - consult the index "
                "below and follow the closest one when it fits."
            )
        if mode == "full":
            parts.append(
                "FULL INDEX (%d skills, id - name) - any of them can be loaded "
                "on demand:\n%s" % (n, self.index_text())
            )
        return "\n\n".join(parts)

    @staticmethod
    def _pillar_head(s: dict) -> str:
        if s["pillar"]:
            return "%d. %s" % (s["pillar"], s["pillar_title"])
        return s["pillar_title"] or "Ungrouped"

    def tool_result(self, action: str = "list", ident: str = "",
                    query: str = "", limit: int = 8) -> str:
        """Body text for the `skill` builtin tool."""
        self._ensure()
        action = (action or "list").strip().lower()
        if action == "load":
            s = self.get(ident or query)
            if not s:
                near = self.search(ident or query, limit=5)
                hint = ("\nClosest matches: " + ", ".join(x["id"] for x in near)) if near else ""
                return "error: no skill named %r%s" % (ident or query, hint)
            return ("SKILL: %s (id: %s)\nPillar: %s\nDescription: %s\n\n%s"
                    % (s["name"], s["id"], self._pillar_head(s),
                       s["description"], s["body"]))
        if action == "search":
            hits = self.search(query, limit=limit)
            if not hits:
                return "no skills match %r (try different keywords, or action=list)" % query
            return "\n".join(
                "%s | %s | %s" % (h["id"], h["name"], h["description"])
                for h in hits
            )
        if action in ("list", "all", "index"):
            return self.index_text()
        if action == "count":
            return "%d skills across %d pillars" % (self.count, self.pillar_count)
        return "error: unknown action %r (use load, search, list, count)" % action


# Process-wide singleton (backend.py + endpoint.py share one instance).
LIBRARY = SkillLibrary()


def library() -> SkillLibrary:
    return LIBRARY


def skill_mode(default: str = "full") -> str:
    """BHAJANLAL_SKILLS = full | applied | off  (defaults to full)."""
    return (os.environ.get("BHAJANLAL_SKILLS", default) or default).strip().lower()
