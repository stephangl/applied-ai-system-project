# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_scheduler.py

# Run a single test
pytest tests/test_scheduler.py::test_function_name
```

## Project Overview

**PawPal+** is a Module 2 student project — a Streamlit pet care planning assistant. The student designs and implements the scheduling system from scratch; `app.py` is an intentional scaffold/placeholder.

## Architecture

- `app.py` — Streamlit UI entry point. Currently shows demo inputs only. The "Generate schedule" button is a stub; the student must wire it to their scheduler.
- Students are expected to create their own modules for domain classes (`Pet`, `Owner`, `Task`) and a `Scheduler` class, then import them into `app.py`.
- `st.session_state` is used to persist tasks between Streamlit reruns.

## What needs to be implemented

The core system the student must build:
1. **Domain classes** — `Task` (title, duration, priority), `Pet`, `Owner`
2. **Scheduler** — constraint-based daily plan generation (time budget, priority ordering)
3. **Plan output** — display results and explain why each task was chosen
4. **Tests** — pytest tests for scheduling logic (e.g., priority ordering, time constraints)

The student should follow a design-first workflow: UML → class stubs → logic → tests → UI integration.
