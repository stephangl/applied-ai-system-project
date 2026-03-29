import streamlit as st
from pawpal_system import Pet, Task, Priority, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialisation (runs once per session) ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# ---------------------------------------------------------------------------

st.title("🐾 PawPal+")

# --- Owner & Pet setup ---
st.subheader("Owner & Pets")

col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input("Available time (min)", min_value=10, max_value=480, value=90)
with col3:
    budget = st.number_input("Budget ($)", min_value=0.0, value=50.0, step=5.0)

st.markdown("**Add a pet**")
pcol1, pcol2, pcol3, pcol4 = st.columns(4)
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    pet_age = st.number_input("Age", min_value=0, max_value=30, value=3)
with pcol3:
    pet_weight = st.number_input("Weight (kg)", min_value=0.1, value=4.5)
with pcol4:
    pet_type = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & add pet"):
    # Create owner only if it doesn't exist yet, otherwise keep existing pets/tasks
    if st.session_state.owner is None:
        st.session_state.owner = Owner(
            name=owner_name,
            available_time_minutes=int(available_minutes),
            budget=budget,
        )
    else:
        # Update time/budget without resetting pets or tasks
        st.session_state.owner.available_time_minutes = int(available_minutes)
        st.session_state.owner.budget = budget

    new_pet = Pet(name=pet_name, age=int(pet_age), weight=float(pet_weight), type=pet_type)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Saved! {pet_name} added to {owner_name}'s pets.")

if st.session_state.owner:
    pet_names = [p.name for p in st.session_state.owner.pets]
    st.caption(f"Registered pets: {', '.join(pet_names) if pet_names else 'none yet'}")

st.divider()

# --- Task management ---
st.subheader("Tasks")

tcol1, tcol2, tcol3, tcol4 = st.columns(4)
with tcol1:
    task_title = st.text_input("Task title", value="Morning walk")
with tcol2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with tcol3:
    priority = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
with tcol4:
    cost = st.number_input("Cost ($)", min_value=0.0, value=0.0, step=5.0)

category = st.selectbox("Category", ["walk", "feeding", "meds", "enrichment", "grooming"])

# Pet selector — only shown if an owner with pets exists
task_pet = None
if st.session_state.owner and st.session_state.owner.pets:
    pet_options = {p.name: p for p in st.session_state.owner.pets}
    selected_pet_name = st.selectbox("For pet", list(pet_options.keys()))
    task_pet = pet_options[selected_pet_name]

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Save an owner first before adding tasks.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority],
            category=category,
            cost=float(cost),
            pet=task_pet,
        )
        st.session_state.owner.add_task(task)
        st.session_state.tasks.append({
            "title": task_title,
            "pet": task_pet.name if task_pet else "-",
            "duration": int(duration),
            "priority": priority,
            "cost": f"${cost:.2f}",
            "category": category,
        })
        st.success(f"Task '{task_title}' added.")

if st.session_state.tasks:
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule generation ---
st.subheader("Generate Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Set up an owner before generating a schedule.")
    elif not st.session_state.owner.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = Scheduler().schedule(st.session_state.owner)
        st.success("Schedule generated!")
        st.text(plan.summary())

        conflicts = plan.detect_conflicts()
        if conflicts:
            st.warning("Scheduling conflicts detected:")
            for msg in conflicts:
                st.warning(msg)
        else:
            st.info("No scheduling conflicts.")
