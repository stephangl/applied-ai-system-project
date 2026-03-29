from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Pet:
    name: str
    age: int
    weight: float
    type: str
    tasks: List["Task"] = field(default_factory=list)

    def add_task(self, task: "Task") -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    category: str           # "walk", "feeding", "meds", "enrichment", "grooming"
    cost: float = 0.0
    pet: Optional[Pet] = None       # which pet this task is for
    status: str = "pending"         # "pending" or "completed"
    preferred_time: str = "08:00"   # HH:MM format
    repeat: str = "none"            # "none", "daily", "weekly"
    due_date: date = field(default_factory=date.today)

    def complete(self) -> Optional["Task"]:
        """Mark this task as completed and return the next occurrence if recurring."""
        self.status = "completed"

        intervals = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        if self.repeat not in intervals:
            return None

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            cost=self.cost,
            pet=self.pet,
            preferred_time=self.preferred_time,
            repeat=self.repeat,
            due_date=date.today() + intervals[self.repeat],
        )


@dataclass
class Owner:
    name: str
    available_time_minutes: int
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    budget: float = 0.0

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        """Add a care task to the owner's task pool."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> None:
        """Mark a task complete and re-queue the next occurrence if recurring."""
        next_task = task.complete()
        if next_task:
            self.tasks.append(next_task)


class Schedule:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Append a task to the scheduled plan."""
        self.tasks.append(task)

    def total_duration(self) -> int:
        """Return the sum of all scheduled task durations in minutes."""
        return sum(task.duration_minutes for task in self.tasks)

    def total_cost(self) -> float:
        """Return the total cost of all scheduled tasks."""
        return sum(task.cost for task in self.tasks)

    def sort_by_time(self) -> List[Task]:
        """Return tasks sorted by preferred_time (HH:MM) using a lambda key."""
        return sorted(self.tasks, key=lambda t: tuple(map(int, t.preferred_time.split(":"))))

    def filter_by_status(self, status: str) -> List[Task]:
        """Return only tasks matching the given status ('pending' or 'completed')."""
        return [t for t in self.tasks if t.status == status]

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return only tasks assigned to the given pet name."""
        return [t for t in self.tasks if t.pet and t.pet.name == pet_name]

    def detect_conflicts(self) -> List[str]:
        """Return a list of warning messages for tasks whose time slots overlap."""
        warnings = []

        def to_minutes(hhmm: str) -> int:
            h, m = map(int, hhmm.split(":"))
            return h * 60 + m

        tasks = self.sort_by_time()
        for i, a in enumerate(tasks):
            a_start = to_minutes(a.preferred_time)
            a_end   = a_start + a.duration_minutes
            for b in tasks[i + 1:]:
                b_start = to_minutes(b.preferred_time)
                b_end   = b_start + b.duration_minutes
                if a_start < b_end and b_start < a_end:
                    a_pet = a.pet.name if a.pet else "unassigned"
                    b_pet = b.pet.name if b.pet else "unassigned"
                    warnings.append(
                        f"WARNING: '{a.title}' ({a_pet}, {a.preferred_time}–{a_end % 60:02d} min) "
                        f"overlaps with '{b.title}' ({b_pet}, {b.preferred_time})"
                    )
        return warnings

    def summary(self) -> str:
        """Return a human-readable overview of the scheduled plan."""
        if not self.tasks:
            return "No tasks scheduled."
        lines = ["Scheduled tasks:"]
        for task in self.tasks:
            pet_str  = f" [{task.pet.name}]" if task.pet else ""
            cost_str = f" (${task.cost:.2f})" if task.cost > 0 else ""
            lines.append(
                f"  - {task.title}{pet_str} | {task.duration_minutes} min | "
                f"{task.priority.name.capitalize()}{cost_str}"
            )
        lines.append(f"Total time: {self.total_duration()} min")
        lines.append(f"Total cost: ${self.total_cost():.2f}")
        return "\n".join(lines)


class Scheduler:
    def schedule(self, owner: Owner) -> Schedule:
        """Build a daily plan by fitting the highest-priority tasks within time and budget."""
        sorted_tasks = sorted(
            owner.tasks,
            key=lambda t: (-t.priority.value, tuple(map(int, t.preferred_time.split(":")))),
        )

        plan = Schedule()
        spent_budget = 0.0
        for task in sorted_tasks:
            fits_time   = plan.total_duration() + task.duration_minutes <= owner.available_time_minutes
            fits_budget = spent_budget + task.cost <= owner.budget if owner.budget > 0 else True
            if fits_time and fits_budget:
                plan.add_task(task)
                spent_budget += task.cost

        return plan
