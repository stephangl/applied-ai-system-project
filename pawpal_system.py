from dataclasses import dataclass, field
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
    pet: Optional[Pet] = None   # which pet this task is for
    status: str = "pending"     # "pending" or "completed"

    def complete(self) -> None:
        """Mark this task as completed."""
        self.status = "completed"


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
        sorted_tasks = sorted(owner.tasks, key=lambda t: t.priority.value, reverse=True)

        plan = Schedule()
        spent_budget = 0.0
        for task in sorted_tasks:
            fits_time   = plan.total_duration() + task.duration_minutes <= owner.available_time_minutes
            fits_budget = spent_budget + task.cost <= owner.budget if owner.budget > 0 else True
            if fits_time and fits_budget:
                plan.add_task(task)
                spent_budget += task.cost

        return plan
