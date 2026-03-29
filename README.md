# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors


## Smart Scheduler

The scheduler selects and orders tasks greedily by priority, fitting them within the owner's time and budget constraints. Key features built on top of the core logic:

- **Priority-based scheduling** — tasks are sorted high → low priority, with `preferred_time` (HH:MM) as a tiebreaker so earlier tasks fill slots first.
- **Multi-pet support** — an owner can register multiple pets; each task is linked to a specific pet and labelled in the schedule output.
- **Budget enforcement** — tasks with a cost are only included if the remaining budget allows it; a $0 budget disables the check.
- **Recurring tasks** — tasks marked `repeat="daily"` or `repeat="weekly"` automatically generate the next occurrence (via `timedelta`) when completed, keeping the task pool up to date.
- **Sorting and filtering** — the schedule can be sorted chronologically by `preferred_time` and filtered by status (`pending`/`completed`) or by pet name.
- **Conflict detection** — after scheduling, overlapping time slots are detected using interval overlap logic and returned as human-readable warnings, without crashing the program.

## Testing PawPal+

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | What is verified |
|---|---|
| **Task completion** | Calling `complete()` changes status from `pending` to `completed` |
| **Pet task tracking** | Adding tasks to a pet correctly increases the pet's task count |
| **Sorting** | `sort_by_time()` returns tasks in strict chronological order (HH:MM), including 5-task scrambled input |
| **Filtering** | `filter_by_status()` and `filter_by_pet()` return only matching tasks |
| **Recurring tasks** | Daily/weekly tasks produce a new instance with the correct `due_date` on completion; all attributes are preserved |
| **Non-recurring tasks** | `complete()` returns `None` for `repeat="none"` tasks |
| **Owner re-queuing** | `Owner.complete_task()` appends the next occurrence back into the task pool |
| **Conflict detection** | Overlapping time slots and exact duplicate times are flagged with a warning message |
| **No false conflicts** | Sequential tasks that touch but do not overlap produce no warnings |

### Confidence level

★★★★☆ (4/5)

Core scheduling logic, recurrence, sorting, filtering, and conflict detection are all covered with both happy-path and edge-case tests (14 passing). One star held back because the greedy scheduler has no tests for budget-only or time-only exclusion scenarios, and the Streamlit UI layer has no automated tests.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
