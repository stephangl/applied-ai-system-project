# PawPal+ System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER (browser)                             │
│                                                                     │
│   Tab 1: Schedule Builder          Tab 2: Chat Assistant            │
│   ┌──────────────────────┐         ┌─────────────────────────┐      │
│   │  Forms (Owner / Pet  │         │  st.chat_input          │      │
│   │  / Task / Generate)  │         │  st.chat_message        │      │
│   └──────────┬───────────┘         └────────────┬────────────┘      │
└──────────────│──────────────────────────────────│───────────────────┘
               │ direct Python calls              │ user message text
               ▼                                  ▼
┌──────────────────────────┐     ┌────────────────────────────────────┐
│        app.py            │     │             agent.py               │
│  (Streamlit UI layer)    │     │         (Agent loop)               │
│                          │     │                                    │
│  • Renders both tabs     │     │  1. Appends user msg to history    │
│  • Owns session_state    │◄────│  2. Calls Claude API (Haiku)       │
│    (owner, tasks,        │     │  3. Receives tool_use blocks       │
│     chat_history)        │     │  4. Calls execute_tool()           │
│  • Syncs owner_ref back  │     │  5. Appends tool_result to msgs    │
│    after each agent turn │     │  6. Loops until end_turn           │
└──────────────┬───────────┘     └──────────┬─────────────────────────┘
               │                            │
               │ imports                    │ calls
               ▼                            ▼
┌──────────────────────────┐     ┌────────────────────────────────────┐
│      pawpal_system.py    │     │         Tool Executor              │
│   (Domain model)         │◄────│      (inside agent.py)             │
│                          │     │                                    │
│  • Owner                 │     │  save_owner   → Owner(...)         │
│  • Pet                   │     │  add_pet      → owner.add_pet()    │
│  • Task / Priority       │     │  add_task     → owner.add_task()   │
│  • Schedule              │     │  list_pets    → owner.pets         │
│  • Scheduler             │     │  list_tasks   → owner.tasks        │
└──────────────────────────┘     │  generate_schedule → Scheduler()   │
                                 └──────────────┬─────────────────────┘
                                                │ HTTPS
                                                ▼
                                 ┌────────────────────────────────────┐
                                 │       Anthropic API                │
                                 │    (claude-haiku-4-5)              │
                                 │                                    │
                                 │  Receives: system prompt,          │
                                 │            tool schemas,           │
                                 │            conversation history    │
                                 │  Returns:  tool_use | end_turn     │
                                 └────────────────────────────────────┘
```

---

## Data Flow (one chat turn)

```
User types message
       │
       ▼
app.py appends to chat_display, calls run_agent()
       │
       ▼
agent.py builds messages list  ──────────────────────────────────────┐
       │                                                             │
       ▼                                                             │
Claude API  ──► stop_reason = "tool_use"                             │
       │              │                                              │
       │              ▼                                              │
       │        execute_tool()   ◄── guardrails applied here         │
       │              │               (validation, length, range)    │
       │              ▼                                              │
       │        pawpal_system.py mutates owner_ref                   │
       │              │                                              │
       │        tool_result appended to messages ────────────────────┘
       │                         (loop back to Claude)
       │
       ▼
Claude API  ──► stop_reason = "end_turn"
       │
       ▼
reply text returned to app.py
       │
       ▼
app.py stores owner_ref[0] → st.session_state.owner
app.py renders reply in st.chat_message("assistant")
app.py calls st.rerun() → UI refreshes state banner
```

---

## Where Humans and Tests Check AI Results

```
┌─────────────────────────────────────────────────────────────────────┐
│                   HUMAN OVERSIGHT POINTS                            │
│                                                                     │
│  1. State banner (Tab 2 top)                                        │
│     Shows owner name, time budget, pet count, task count after      │
│     every agent turn. Human can verify the agent set things up      │
│     correctly before generating a schedule.                         │
│                                                                     │
│  2. Schedule Builder tab (Tab 1)                                    │
│     Fully independent form UI reflects the same session state.      │
│     Human can inspect / correct any data the agent wrote by         │
│     switching tabs and comparing.                                   │
│                                                                     │
│  3. Agent reply text                                                │
│     Claude confirms every tool call in plain language               │
│     (e.g. "I've added Mochi as a dog"). Human reads and             │
│     can flag if it's wrong before the next step.                    │
│                                                                     │
│  4. pawpal_agent.log                                                │
│     Every tool call, input, and result is logged with timestamps.   │
│     Reviewer can audit the full trace offline.                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   AUTOMATED TEST CHECKPOINTS                        │
│                                                                     │
│  tests/test_pawpal.py  (existing, 13 tests)                         │
│  ├── test_task_complete_changes_status                              │
│  ├── test_sort_by_time_orders_tasks_chronologically                 │
│  ├── test_detect_conflicts_*  (2 tests)                             │
│  ├── test_filter_by_*  (2 tests)                                    │
│  └── test_daily/weekly_recurrence_*  (3 tests)                      │
│                                                                     │
│  These run against pawpal_system.py directly — they verify that     │
│  the domain logic the agent relies on is correct, independently     │
│  of what the AI does.                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Guardrails Summary

| Guardrail | Where | What it prevents |
|---|---|---|
| `MAX_ITERATIONS = 10` | `agent.py` | Runaway tool-call loops |
| Input range checks | `execute_tool()` | Invalid durations, ages, budgets |
| `_safe_str()` | `execute_tool()` | Control characters, oversized strings |
| `_valid_time()` | `execute_tool()` | Malformed HH:MM times |
| Duplicate pet guard | `add_pet` tool | Same pet added twice |
| Enum validation | Tool JSON schema | Invalid priority / category / species |
| Scope system prompt | Claude API call | Off-topic responses |
| Structured logging | `pawpal_agent.log` | Silent failures, audit trail |

---

## Setup Steps

```bash
# 1. Clone / open the project
cd applied-ai-system-project

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies (now includes anthropic)
pip install -r requirements.txt

# 4. Add your Anthropic API key to the .env file
# Open .env and replace the placeholder value:
#   ANTHROPIC_API_KEY=sk-ant-...
# The app loads this automatically via python-dotenv — never commit .env

# 5. Run the app
streamlit run app.py

# 6. Run the test suite
pytest

# 7. View agent logs (generated at runtime)
tail -f pawpal_agent.log
```
