from pawpal_system import Owner, Pet, Task, Priority, Scheduler
from datetime import date

# --- Pets ---
mochi = Pet(name="Mochi", age=3, weight=4.5, type="dog")
luna  = Pet(name="Luna",  age=6, weight=3.2, type="cat")

# --- Owner ---
jordan = Owner(
    name="Jordan",
    available_time_minutes=90,
    budget=60.0,
)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Tasks for Mochi ---
jordan.add_task(Task("Morning walk",    duration_minutes=20, priority=Priority.HIGH,   category="walk",        pet=mochi))
jordan.add_task(Task("Mochi feeding",   duration_minutes=10, priority=Priority.HIGH,   category="feeding",     pet=mochi))
jordan.add_task(Task("Vet visit",       duration_minutes=45, priority=Priority.MEDIUM, category="meds",        pet=mochi, cost=40.0))

# --- Tasks for Luna ---
jordan.add_task(Task("Luna feeding",    duration_minutes=10, priority=Priority.HIGH,   category="feeding",     pet=luna))
jordan.add_task(Task("Grooming",        duration_minutes=20, priority=Priority.MEDIUM, category="grooming",    pet=luna, cost=15.0))
jordan.add_task(Task("Enrichment play", duration_minutes=15, priority=Priority.LOW,    category="enrichment",  pet=luna))

# --- Generate schedule ---
plan = Scheduler().schedule(jordan)

# --- Output ---
print(f"=== PawPal+ Daily Schedule — {date.today()} ===")
print(f"Owner : {jordan.name}")
print(f"Pets  : {', '.join(p.name for p in jordan.pets)}")
print(f"Time budget  : {jordan.available_time_minutes} min")
print(f"Money budget : ${jordan.budget:.2f}")
print()
print(plan.summary())
