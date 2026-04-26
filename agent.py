"""
PawPal+ AI Agent
----------------
Agentic workflow using the Claude API (claude-haiku-4-5).
Claude decides which tools to call; this module executes them against
the in-memory Owner/Pet/Task state passed in from Streamlit session state.

Guardrails
----------
1. MAX_ITERATIONS      – hard cap on the tool-call loop (prevents runaway agents)
2. Input validation    – every tool validates its inputs before touching state
3. Scope guard         – system prompt restricts Claude to pet-care topics only
4. Safe string helper  – strips control characters from user-supplied strings
5. Logging             – every tool call, result, and error is written to pawpal_agent.log
"""

import logging
import re
import unicodedata
from typing import Optional

import anthropic

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pawpal_agent.log", encoding="utf-8"),
        logging.StreamHandler(),        # also echoes to terminal / Streamlit logs
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants / tuneable guardrails
# ---------------------------------------------------------------------------
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 2048
MAX_ITERATIONS = 10          # hard stop: max tool-call rounds per user message
MAX_STRING_LEN = 200         # max length for any user-supplied string field

# ---------------------------------------------------------------------------
# System prompt  (scope guardrail baked in)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are PawPal+, a friendly pet care scheduling assistant.

Your ONLY job is to help users manage their pets and daily care schedules
using the tools provided. You must not answer questions unrelated to pet care,
scheduling, or the tools available to you.

When a user's message is off-topic, politely decline and redirect them to
pet-care planning.

Always confirm what you did after calling a tool (e.g. "I've added Mochi as
a dog."). If a tool returns an error, explain it clearly and ask the user to
correct the input.

Workflow:
1. If no owner exists yet, call save_owner first.
2. Add pets before adding tasks that reference them.
3. After adding tasks, call generate_schedule to build the daily plan.
4. Summarise the schedule in plain language after generating it.
"""

# ---------------------------------------------------------------------------
# Tool definitions  (JSON schema sent to the Claude API)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "save_owner",
        "description": (
            "Create or update the owner profile. "
            "Call this first before adding pets or tasks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Owner's first name.",
                },
                "available_minutes": {
                    "type": "integer",
                    "description": "Total free time today in minutes (10–480).",
                },
                "budget": {
                    "type": "number",
                    "description": "Spending budget in dollars (0 or more).",
                },
            },
            "required": ["name", "available_minutes", "budget"],
        },
    },
    {
        "name": "add_pet",
        "description": "Register a pet for the current owner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Pet's name."},
                "age":  {"type": "integer", "description": "Age in years (0–30)."},
                "weight": {
                    "type": "number",
                    "description": "Weight in kilograms (0.1–200).",
                },
                "species": {
                    "type": "string",
                    "enum": ["dog", "cat", "other"],
                    "description": "Species of the pet.",
                },
            },
            "required": ["name", "age", "weight", "species"],
        },
    },
    {
        "name": "add_task",
        "description": (
            "Add a care task. "
            "pet_name must match an already-registered pet's name exactly, "
            "or be omitted for non-pet-specific tasks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":    {"type": "string", "description": "Short task name."},
                "duration": {
                    "type": "integer",
                    "description": "Duration in minutes (1–240).",
                },
                "priority": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"],
                    "description": "Scheduling priority.",
                },
                "category": {
                    "type": "string",
                    "enum": ["walk", "feeding", "meds", "enrichment", "grooming"],
                    "description": "Type of care activity.",
                },
                "cost": {
                    "type": "number",
                    "description": "Estimated cost in dollars (default 0).",
                },
                "pet_name": {
                    "type": "string",
                    "description": "Name of the pet this task is for (optional).",
                },
                "preferred_time": {
                    "type": "string",
                    "description": "Preferred start time in HH:MM format (default 08:00).",
                },
            },
            "required": ["title", "duration", "priority", "category"],
        },
    },
    {
        "name": "generate_schedule",
        "description": (
            "Run the scheduler and return the daily plan. "
            "Call this after all tasks have been added."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_pets",
        "description": "Return the names and details of all registered pets.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_tasks",
        "description": "Return all tasks currently in the owner's task pool.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# ---------------------------------------------------------------------------
# Guardrail helpers
# ---------------------------------------------------------------------------

def _safe_str(value: str, field: str = "field") -> str:
    """Strip control characters and enforce length limit."""
    # Normalise unicode, remove non-printable control chars
    cleaned = "".join(
        ch for ch in unicodedata.normalize("NFC", str(value))
        if unicodedata.category(ch)[0] != "C"
    )
    cleaned = cleaned.strip()
    if len(cleaned) > MAX_STRING_LEN:
        raise ValueError(
            f"{field} exceeds the {MAX_STRING_LEN}-character limit "
            f"({len(cleaned)} chars)."
        )
    if not cleaned:
        raise ValueError(f"{field} must not be empty.")
    return cleaned


def _valid_time(value: str) -> str:
    """Validate HH:MM format."""
    if not re.fullmatch(r"\d{2}:\d{2}", value):
        raise ValueError(f"preferred_time must be HH:MM, got '{value}'.")
    h, m = map(int, value.split(":"))
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"preferred_time '{value}' is out of range.")
    return value


# ---------------------------------------------------------------------------
# Tool executor
# ---------------------------------------------------------------------------

def execute_tool(
    tool_name: str,
    tool_input: dict,
    owner_ref: list,          # list wrapping Optional[Owner] so we can mutate it
) -> str:
    """
    Execute a tool and return a plain-text result string for Claude.
    owner_ref is a one-element list so the function can replace the owner object.
    All exceptions are caught and returned as error strings.
    """
    log.info("TOOL CALL  | %-20s | input=%s", tool_name, tool_input)

    try:
        result = _dispatch(tool_name, tool_input, owner_ref)
    except ValueError as exc:
        result = f"Validation error: {exc}"
        log.warning("TOOL ERROR | %-20s | %s", tool_name, result)
    except Exception as exc:                          # pragma: no cover
        result = f"Unexpected error: {exc}"
        log.error("TOOL ERROR | %-20s | %s", tool_name, result, exc_info=True)

    log.info("TOOL RESULT| %-20s | %s", tool_name, result[:200])
    return result


def _dispatch(tool_name: str, inp: dict, owner_ref: list) -> str:
    owner: Optional[Owner] = owner_ref[0]

    # ------------------------------------------------------------------ #
    if tool_name == "save_owner":
        name = _safe_str(inp["name"], "name")
        avail = int(inp["available_minutes"])
        budget = float(inp["budget"])

        if not (10 <= avail <= 480):
            raise ValueError("available_minutes must be between 10 and 480.")
        if budget < 0:
            raise ValueError("budget must be 0 or greater.")

        if owner is None:
            owner_ref[0] = Owner(
                name=name,
                available_time_minutes=avail,
                budget=budget,
            )
        else:
            owner_ref[0].name = name
            owner_ref[0].available_time_minutes = avail
            owner_ref[0].budget = budget
        return f"Owner '{name}' saved ({avail} min, ${budget:.2f} budget)."

    # ------------------------------------------------------------------ #
    if tool_name == "add_pet":
        if owner is None:
            raise ValueError("No owner set. Call save_owner first.")
        name    = _safe_str(inp["name"], "pet name")
        age     = int(inp["age"])
        weight  = float(inp["weight"])
        species = inp["species"]   # already validated by enum in schema

        if not (0 <= age <= 30):
            raise ValueError("age must be between 0 and 30.")
        if not (0.1 <= weight <= 200):
            raise ValueError("weight must be between 0.1 and 200 kg.")

        # Prevent duplicate pet names
        existing = [p.name.lower() for p in owner.pets]
        if name.lower() in existing:
            return f"Pet '{name}' is already registered."

        owner.add_pet(Pet(name=name, age=age, weight=weight, type=species))
        return f"Pet '{name}' ({species}, age {age}, {weight} kg) added."

    # ------------------------------------------------------------------ #
    if tool_name == "add_task":
        if owner is None:
            raise ValueError("No owner set. Call save_owner first.")

        title    = _safe_str(inp["title"], "title")
        duration = int(inp["duration"])
        priority = inp["priority"]      # enum validated by schema
        category = inp["category"]      # enum validated by schema
        cost     = float(inp.get("cost", 0.0))
        pet_name = inp.get("pet_name", "").strip()
        ptime    = _valid_time(inp.get("preferred_time", "08:00"))

        if not (1 <= duration <= 240):
            raise ValueError("duration must be between 1 and 240 minutes.")
        if cost < 0:
            raise ValueError("cost must be 0 or greater.")

        # Resolve pet reference
        pet_obj = None
        if pet_name:
            matches = [p for p in owner.pets if p.name.lower() == pet_name.lower()]
            if not matches:
                registered = ", ".join(p.name for p in owner.pets) or "none"
                raise ValueError(
                    f"Pet '{pet_name}' not found. Registered pets: {registered}."
                )
            pet_obj = matches[0]

        task = Task(
            title=title,
            duration_minutes=duration,
            priority=Priority[priority],
            category=category,
            cost=cost,
            pet=pet_obj,
            preferred_time=ptime,
        )
        owner.add_task(task)
        pet_label = f" for {pet_obj.name}" if pet_obj else ""
        return (
            f"Task '{title}'{pet_label} added "
            f"({duration} min, {priority}, {ptime})."
        )

    # ------------------------------------------------------------------ #
    if tool_name == "generate_schedule":
        if owner is None:
            raise ValueError("No owner set. Call save_owner first.")
        if not owner.tasks:
            raise ValueError("No tasks to schedule. Add tasks first.")

        plan = Scheduler().schedule(owner)

        if not plan.tasks:
            return (
                "No tasks fit within the time or budget constraints. "
                "Try increasing available_minutes or budget."
            )

        lines = [
            f"Schedule ready: {len(plan.tasks)} task(s), "
            f"{plan.total_duration()} min total, ${plan.total_cost():.2f} total cost.",
            "",
        ]
        for t in plan.sort_by_time():
            pet_label = f" [{t.pet.name}]" if t.pet else ""
            cost_label = f" (${t.cost:.2f})" if t.cost > 0 else ""
            lines.append(
                f"  {t.preferred_time} – {t.title}{pet_label} "
                f"| {t.duration_minutes} min | {t.priority.name}{cost_label}"
            )

        conflicts = plan.detect_conflicts()
        if conflicts:
            lines.append("")
            lines.append(f"WARNING: {len(conflicts)} time conflict(s) detected:")
            lines.extend(f"  {c}" for c in conflicts)

        skipped_titles = {t.title for t in plan.tasks}
        skipped = [t for t in owner.tasks if t.title not in skipped_titles]
        if skipped:
            lines.append("")
            lines.append("Skipped (did not fit):")
            lines.extend(f"  – {t.title}" for t in skipped)

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    if tool_name == "list_pets":
        if owner is None or not owner.pets:
            return "No pets registered yet."
        rows = [
            f"  • {p.name} ({p.type}, age {p.age}, {p.weight} kg)"
            for p in owner.pets
        ]
        return "Registered pets:\n" + "\n".join(rows)

    # ------------------------------------------------------------------ #
    if tool_name == "list_tasks":
        if owner is None or not owner.tasks:
            return "No tasks added yet."
        rows = [
            f"  • {t.title} | {t.duration_minutes} min | {t.priority.name} | {t.preferred_time}"
            for t in owner.tasks
        ]
        return f"{len(owner.tasks)} task(s):\n" + "\n".join(rows)

    # ------------------------------------------------------------------ #
    raise ValueError(f"Unknown tool: '{tool_name}'.")


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(
    user_message: str,
    conversation_history: list,
    owner_ref: list,
) -> tuple[str, list]:
    """
    Run one user turn through the agentic loop.

    Parameters
    ----------
    user_message          : the new user message
    conversation_history  : list of prior {role, content} message dicts
    owner_ref             : one-element list wrapping Optional[Owner]
                            (mutated in-place by tools)

    Returns
    -------
    (assistant_reply, updated_conversation_history)
    """
    client = anthropic.Anthropic()

    messages = conversation_history + [{"role": "user", "content": user_message}]
    log.info("AGENT TURN | user=%s", user_message[:120])

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        log.info(
            "API RESP   | stop_reason=%s | iteration=%d/%d",
            response.stop_reason, iteration + 1, MAX_ITERATIONS,
        )

        # Append the full assistant turn to the running message list
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract the final text reply
            reply = next(
                (b.text for b in response.content if b.type == "text"),
                "(No text response.)",
            )
            log.info("AGENT DONE | reply=%s", reply[:120])
            return reply, messages

        # Handle tool calls
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            # stop_reason is something other than end_turn but no tools — bail out
            break

        tool_results = []
        for block in tool_use_blocks:
            result_text = execute_tool(block.name, block.input, owner_ref)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # Guardrail: max iterations hit
    log.warning("GUARDRAIL  | MAX_ITERATIONS (%d) reached", MAX_ITERATIONS)
    fallback = (
        "I've reached the maximum number of steps for this request. "
        "Please try breaking your request into smaller parts."
    )
    return fallback, messages
