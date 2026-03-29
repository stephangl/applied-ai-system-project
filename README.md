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


## Features

### Greedy Priority Scheduler
Tasks are sorted by priority (HIGH → MEDIUM → LOW) and added to the schedule one by one as long as they fit within the owner's available time and budget. Within the same priority level, tasks with an earlier `preferred_time` are selected first. This approach is fast and predictable — the owner always knows why a task was included or skipped.

### Chronological Sorting
`Schedule.sort_by_time()` sorts scheduled tasks by their `preferred_time` field (HH:MM format) using a lambda that converts the time string into a `(hours, minutes)` integer tuple. This ensures `"09:30"` correctly sorts before `"13:00"`, avoiding the wrong order that plain alphabetical string comparison would produce. The Streamlit UI always displays the final plan in this sorted order.

### Conflict Detection
After a schedule is built, `Schedule.detect_conflicts()` checks every pair of tasks for time-slot overlap using the interval overlap condition: two tasks conflict if `a_start < b_end AND b_start < a_end`. Start and end times are derived from `preferred_time` and `duration_minutes`. Conflicts are returned as human-readable warning strings rather than exceptions, so the app stays running and the owner can adjust task times manually.

### Daily Recurrence
Tasks with `repeat="daily"` or `repeat="weekly"` automatically regenerate when completed. Calling `task.complete()` marks the original as `"completed"` and returns a new `Task` instance with the same attributes and a `due_date` of `date.today() + timedelta(days=1)` (or `timedelta(weeks=1)`). `Owner.complete_task()` handles re-queuing this new instance back into the owner's task pool. Non-recurring tasks return `None` from `complete()` and are not re-queued.

### Filtering
`Schedule.filter_by_status(status)` and `Schedule.filter_by_pet(pet_name)` return filtered subsets of the scheduled tasks using list comprehensions. These are used in the UI to separate pending from completed tasks and to show per-pet views of the plan.

### Multi-pet Support
An owner can register any number of pets via `Owner.add_pet()`. Each task carries an optional reference to the pet it belongs to, which is used for filtering, conflict labelling, and display in the schedule table.

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

📸 Demo

<a href="/ai110/ai110-module2show-pawpal-starter/demo.png" target="_blank"><img src='/course_images/ai110/ai110-module2show-pawpal-starter/demo.png' width='600'/></a>