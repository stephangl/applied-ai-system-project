# Model Card — PawPal+ AI Agent

**Model used:** claude-haiku-4-5 (Anthropic) via the Claude API  
**Task:** Conversational pet care scheduling assistant using tool-calling

---

## Limitations and Biases

The system requires users to specify exact numeric values (minutes, kilograms, age) — if a user says "a couple of hours" instead of "120 minutes," the agent may guess or ask for clarification rather than inferring correctly.

---

## Potential Misuse and Prevention

The agent could theoretically be prompted to act outside its intended scope (e.g., generating unrelated content through prompt injection in a task title). This is prevented by a scope guardrail baked into the system prompt.

---

## What Surprised Me While Testing

The agent recovered from its own tool errors more gracefully than expected — when given an invalid pet name in `add_task`, Claude would read the error message returned by `execute_tool()` and automatically call `list_pets` to check what was registered before retrying. I also did not expect how sensitive the output was to conversation history format: omitting the full `response.content` block (and passing only the text) caused tool result IDs to mismatch, silently breaking multi-step turns.

---

## Collaboration with AI During This Project

**Helpful suggestion:** When asked how to structure the tool executor, the AI suggested separating input validation from the dispatch logic. This made it easy to return clear error messages to Claude without risking partial writes to the owner object.

**Flawed suggestion:** When setting up the Streamlit chat tab, the AI initially suggested calling `st.rerun()` inside the same `if` block that submitted the user message. This caused an infinite rerun loop on every interaction because the condition was still true after the rerun.
