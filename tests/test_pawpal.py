from pawpal_system import Pet, Task, Priority


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
