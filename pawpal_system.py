from dataclasses import dataclass, field
from typing import List


@dataclass
class Pet:
    name: str
    age: int
    weight: float
    type: str


@dataclass
class Owner:
    name: str
    available_time_minutes: int


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str   # "low", "medium", "high"
    category: str   # "walk", "feeding", "meds", "enrichment", "grooming"


class Schedule:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def total_duration(self) -> int:
        pass

    def summary(self) -> str:
        pass