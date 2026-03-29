from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Priority, Schedule


def test_task_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=20, priority=Priority.HIGH, category="walk")
    assert task.status == "pending"
    task.complete()
    assert task.status == "completed"


def test_add_task_to_pet_increases_task_count():
    pet = Pet(name="Mochi", age=3, weight=4.5, type="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding"))
    assert len(pet.tasks) == 1
    pet.add_task(Task(title="Grooming", duration_minutes=15, priority=Priority.MEDIUM, category="grooming"))
    assert len(pet.tasks) == 2


def test_sort_by_time_orders_tasks_chronologically():
    schedule = Schedule()
    schedule.add_task(Task("Evening walk",  duration_minutes=20, priority=Priority.LOW,  category="walk",    preferred_time="18:00"))
    schedule.add_task(Task("Meds",          duration_minutes=5,  priority=Priority.HIGH, category="meds",    preferred_time="07:00"))
    schedule.add_task(Task("Afternoon play",duration_minutes=15, priority=Priority.LOW,  category="enrichment", preferred_time="13:30"))

    sorted_tasks = schedule.sort_by_time()
    assert [t.preferred_time for t in sorted_tasks] == ["07:00", "13:30", "18:00"]


def test_filter_by_status_returns_only_matching_tasks():
    schedule = Schedule()
    t1 = Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding")
    t2 = Task("Walk",    duration_minutes=20, priority=Priority.HIGH, category="walk")
    t1.complete()
    schedule.add_task(t1)
    schedule.add_task(t2)

    assert schedule.filter_by_status("completed") == [t1]
    assert schedule.filter_by_status("pending")   == [t2]


def test_filter_by_pet_returns_only_that_pets_tasks():
    mochi = Pet(name="Mochi", age=3, weight=4.5, type="dog")
    luna  = Pet(name="Luna",  age=6, weight=3.2, type="cat")

    schedule = Schedule()
    schedule.add_task(Task("Walk",    duration_minutes=20, priority=Priority.HIGH, category="walk",    pet=mochi))
    schedule.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", pet=luna))
    schedule.add_task(Task("Meds",    duration_minutes=5,  priority=Priority.HIGH, category="meds",    pet=mochi))

    mochi_tasks = schedule.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 2
    assert all(t.pet.name == "Mochi" for t in mochi_tasks)


def test_daily_task_creates_next_occurrence_on_complete():
    task = Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", repeat="daily")
    next_task = task.complete()

    assert task.status == "completed"
    assert next_task is not None
    assert next_task.status == "pending"
    assert next_task.due_date == date.today() + timedelta(days=1)


def test_weekly_task_creates_next_occurrence_on_complete():
    task = Task("Grooming", duration_minutes=30, priority=Priority.MEDIUM, category="grooming", repeat="weekly")
    next_task = task.complete()

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_detect_conflicts_returns_warning_for_overlapping_tasks():
    schedule = Schedule()
    schedule.add_task(Task("Walk",    duration_minutes=30, priority=Priority.HIGH, category="walk",    preferred_time="08:00"))
    schedule.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", preferred_time="08:15"))

    conflicts = schedule.detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]


def test_detect_conflicts_returns_no_warnings_for_sequential_tasks():
    schedule = Schedule()
    schedule.add_task(Task("Walk",    duration_minutes=20, priority=Priority.HIGH, category="walk",    preferred_time="08:00"))
    schedule.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", preferred_time="08:30"))

    assert schedule.detect_conflicts() == []


def test_sort_by_time_five_scrambled_tasks():
    """Verify chronological order is correct across five out-of-order tasks."""
    schedule = Schedule()
    schedule.add_task(Task("Lunch",         duration_minutes=10, priority=Priority.LOW,    category="feeding",     preferred_time="12:00"))
    schedule.add_task(Task("Night meds",    duration_minutes=5,  priority=Priority.HIGH,   category="meds",        preferred_time="21:00"))
    schedule.add_task(Task("Morning walk",  duration_minutes=20, priority=Priority.HIGH,   category="walk",        preferred_time="07:30"))
    schedule.add_task(Task("Afternoon play",duration_minutes=15, priority=Priority.MEDIUM, category="enrichment",  preferred_time="15:45"))
    schedule.add_task(Task("Breakfast",     duration_minutes=10, priority=Priority.HIGH,   category="feeding",     preferred_time="08:00"))

    sorted_times = [t.preferred_time for t in schedule.sort_by_time()]
    assert sorted_times == ["07:30", "08:00", "12:00", "15:45", "21:00"]


def test_daily_recurrence_preserves_task_attributes():
    """Confirm the next occurrence keeps the same title, priority, and category as the original."""
    task = Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding",
                repeat="daily", preferred_time="07:00")
    next_task = task.complete()

    assert next_task.title           == task.title
    assert next_task.priority        == task.priority
    assert next_task.category        == task.category
    assert next_task.preferred_time  == task.preferred_time
    assert next_task.due_date        == date.today() + timedelta(days=1)
    assert next_task.status          == "pending"


def test_detect_conflicts_flags_exact_duplicate_times():
    """Two tasks with identical preferred_time should always conflict."""
    schedule = Schedule()
    schedule.add_task(Task("Walk",    duration_minutes=20, priority=Priority.HIGH, category="walk",    preferred_time="09:00"))
    schedule.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", preferred_time="09:00"))

    conflicts = schedule.detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]


def test_non_recurring_task_returns_none_on_complete():
    task = Task("Vet visit", duration_minutes=45, priority=Priority.HIGH, category="meds", repeat="none")
    assert task.complete() is None


def test_complete_task_requeues_next_occurrence_on_owner():
    owner = Owner(name="Jordan", available_time_minutes=60)
    task = Task("Feeding", duration_minutes=10, priority=Priority.HIGH, category="feeding", repeat="daily")
    owner.add_task(task)

    owner.complete_task(task)

    pending = [t for t in owner.tasks if t.status == "pending"]
    assert len(pending) == 1
    assert pending[0].due_date == date.today() + timedelta(days=1)
