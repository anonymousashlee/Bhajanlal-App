import re
from collections import OrderedDict

RAW = [
 (1,"Session Initialization & Discovery","Launch opencode in a project and select beam-free; scan repo context, MCP servers, and SKILL.md dirs to build a tool/skill index.","OpenCode scans the repository, MCP servers, and SKILL.md directories (.opencode/skills/, ~/.config/opencode/skills/) and builds a lightweight index of available tools and skill descriptions before any prompt is sent."),
 (2,"Model Selection via /models","Switch the active model to beam-free using /models or --model opencode/beam-free at session start.","The selected model (opencode/beam-free) is recorded as the active inference endpoint for the session."),
 (3,"Repository Context Indexing","Walk the project tree and extract file paths, languages, and entry points for grounding.","A lightweight repo index (file paths, languages, entry points) is available to ground prompts and tool calls."),
 (4,"MCP Server Discovery","Enumerate configured MCP servers and their exposed tools/resources.","The set of MCP tools and resources is indexed and made available to the model."),
 (5,"SKILL.md Directory Scanning","Scan .opencode/skills/ and ~/.config/opencode/skills/ for SKILL.md files.","All installed skills are discovered with their descriptions and triggers."),
 (6,"Prompt Assembly & Request","Assemble prompt, history, AGENTS.md rules, and tool schemas into the request payload.","A single request payload (prompt + history + system rules + tool schemas) is sent to the beam-free endpoint."),
 (7,"AGENTS.md Rule Injection","Load AGENTS.md project rules and inject them as system instructions.","Project-specific agent rules (AGENTS.md) are prepended to the system prompt."),
 (8,"Conversation History Compaction","Compact prior turns to fit the context window while preserving key state.","Compacted history retains decisions and tool results within the token budget."),
 (9,"Tool Schema Serialization","Serialize tool definitions (read, edit, write, bash, grep, glob, skill, etc.) into the request.","Tool schemas are included so the model can emit valid tool calls."),
 (10,"Reasoning & Action Planning","beam-free reasons over the request and chooses the next action: direct answer, skill load, or tool call.","The model emits either text, a skill-tool call, or a tool call (read/grep/glob/edit/write/bash)."),
 (11,"Direct Answer Path","When no inspection or changes are needed, respond directly with text/code.","A final text/code answer is returned without any tool calls."),
 (12,"Skill Load Decision","Decide whether the task matches an installed SKILL.md workflow and load it.","The skill tool is invoked to load the matching SKILL.md instructions."),
 (13,"Tool Call Emission","Emit a structured tool call (read/grep/glob/edit/write/bash) with arguments.","A validated tool call JSON is sent back to OpenCode."),
 (14,"Permission Gate","Intercept tool calls and prompt Approve/Always Allow/Deny for restricted actions (bash, overwrites).","Restricted actions require explicit user approval before execution."),
 (15,"Permission Rule Evaluation","Evaluate opencode.json permission rules (allow/ask/deny) for the requested action.","The action is classified as allowed, ask, or denied based on config."),
 (16,"Local Tool Execution","Run the approved command or file operation locally on the user's machine.","The tool executes locally and produces stdout/stderr/exit code."),
 (17,"Observation & Iterative Loop","Feed tool output (stdout, exit code, errors) back to beam-free; repeat until complete.","Tool results are appended to context and the model re-plans."),
 (18,"Build/Test Failure Recovery","On compiler/test failure, re-plan and apply fixes, repeating the loop.","Failures trigger additional tool calls until the suite passes."),
 (19,"Multi-Step State Tracking","Track state across many tool calls (files touched, edits applied, tests run).","A coherent multi-step plan is executed with state preserved."),
 (20,"Final Summary","Once all tool calls succeed, emit a final summary of changes or the answer.","A concise summary of changes/answer is returned to the user."),
]

def slug(t):
    t = t.split(":")[0].strip().lower() if ":" in t else t.lower()
    t = re.sub(r"[^a-z0-9]+","-",t).strip("-")
    return t

entries=[]
seen=set()
for n,name,desc,out in RAW:
    sid=slug(name)
    if sid in seen: sid=f"{sid}-{n}"
    seen.add(sid)
    steps=[
        f"Implement and verify the {name.lower()} stage of the beam-free agentic loop.",
        f"Handle edge cases (missing context, permission denial, tool errors) gracefully.",
        f"Feed observations back so the model can re-plan and continue the loop.",
        f"Surface progress to the user and emit a final summary when done.",
    ]
    entries.append((sid,name,f"Use when {desc.lower().rstrip('.')}.",steps,out,[]))

from collections import OrderedDict
groups=OrderedDict()
def pillar(n):
    if n<=5: return "Beam-Free Flow: Discovery"
    if n<=9: return "Beam-Free Flow: Request Assembly"
    if n<=13: return "Beam-Free Flow: Reasoning & Planning"
    if n<=16: return "Beam-Free Flow: Permission & Execution"
    if n<=19: return "Beam-Free Flow: Observation & Loop"
    return "Beam-Free Flow: Completion"
for i,e in enumerate(entries,1):
    groups.setdefault(pillar(i),[]).append(e)

lines=["# Bhajanlal skill library - List 11: beam-free Execution Flow (items 1-20)",
       "# Auto-generated from the beam-free agentic loop description.",
       "# tuple: (id, name, description, steps, output, covers)",
       "",
       "PILLARS = ["]
for p,es in groups.items():
    lines.append(f'    ("{p}", [')
    for (sid,name,desc,steps,out,covers) in es:
        lines.append(f'        ("{sid}",')
        lines.append(f'         {repr(name)},')
        lines.append(f'         {repr(desc)},')
        lines.append("         [")
        for st in steps:
            lines.append(f'            {repr(st)},')
        lines.append("         ],")
        lines.append(f'         {repr(out)},')
        lines.append("         []),")
    lines.append("    ]),")
lines.append("]")

open("/Users/ashleesharma/.config/opencode/skill_build/p16.py","w").write("\n".join(lines)+"\n")
print("wrote p16.py with", len(entries), "skills")
