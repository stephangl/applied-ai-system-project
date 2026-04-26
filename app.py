from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from pawpal_system import Pet, Task, Priority, Owner, Scheduler
from agent import run_agent

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session state initialisation (runs once per session) ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # {role, content} list sent to Claude API

if "chat_display" not in st.session_state:
    st.session_state.chat_display = []   # {role, text} list for rendering in UI

# ---------------------------------------------------------------------------

st.title("PawPal+")

tab1, tab2 = st.tabs(["Schedule Builder", "Chat Assistant"])

# ===========================================================================
# TAB 1 – existing form-based UI (unchanged)
# ===========================================================================
with tab1:

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
        if st.session_state.owner is None:
            st.session_state.owner = Owner(
                name=owner_name,
                available_time_minutes=int(available_minutes),
                budget=budget,
            )
        else:
            st.session_state.owner.available_time_minutes = int(available_minutes)
            st.session_state.owner.budget = budget

        new_pet = Pet(name=pet_name, age=int(pet_age), weight=float(pet_weight), type=pet_type)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"{pet_name} added to {owner_name}'s pets.")

    if st.session_state.owner:
        pet_names = [p.name for p in st.session_state.owner.pets]
        st.caption(f"Registered pets: {', '.join(pet_names) if pet_names else 'none yet'}")

    st.divider()

    # --- Task management ---
    st.subheader("Tasks")

    tcol1, tcol2, tcol3, tcol4, tcol5 = st.columns(5)
    with tcol1:
        task_title = st.text_input("Task title", value="Morning walk")
    with tcol2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with tcol3:
        priority = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
    with tcol4:
        cost = st.number_input("Cost ($)", min_value=0.0, value=0.0, step=5.0)
    with tcol5:
        preferred_time = st.text_input("Time (HH:MM)", value="08:00")

    category = st.selectbox("Category", ["walk", "feeding", "meds", "enrichment", "grooming"])

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
                preferred_time=preferred_time,
            )
            st.session_state.owner.add_task(task)
            st.session_state.tasks.append({
                "Title":    task_title,
                "Pet":      task_pet.name if task_pet else "-",
                "Time":     preferred_time,
                "Duration": f"{int(duration)} min",
                "Priority": priority,
                "Cost":     f"${cost:.2f}",
                "Category": category,
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
            owner = st.session_state.owner
            plan  = Scheduler().schedule(owner)

            if not plan.tasks:
                st.error("No tasks fit within your time or budget. Try increasing your available time or budget.")
            else:
                st.success(
                    f"Schedule ready — {len(plan.tasks)} task(s) planned, "
                    f"{plan.total_duration()} min total, ${plan.total_cost():.2f} estimated cost."
                )

                sorted_tasks = plan.sort_by_time()
                st.markdown("#### Daily Plan (sorted by time)")
                st.table([
                    {
                        "Time":     t.preferred_time,
                        "Task":     t.title,
                        "Pet":      t.pet.name if t.pet else "-",
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": t.priority.name.capitalize(),
                        "Cost":     f"${t.cost:.2f}" if t.cost > 0 else "-",
                    }
                    for t in sorted_tasks
                ])

                scheduled_titles = {t.title for t in plan.tasks}
                skipped = [t for t in owner.tasks if t.title not in scheduled_titles]
                if skipped:
                    st.markdown("#### Skipped Tasks")
                    st.caption("These tasks did not fit within your time or budget constraints.")
                    st.table([
                        {
                            "Task":     t.title,
                            "Pet":      t.pet.name if t.pet else "-",
                            "Duration": f"{t.duration_minutes} min",
                            "Cost":     f"${t.cost:.2f}" if t.cost > 0 else "-",
                            "Priority": t.priority.name.capitalize(),
                        }
                        for t in skipped
                    ])

                st.markdown("#### Conflict Check")
                conflicts = plan.detect_conflicts()
                if conflicts:
                    st.warning(
                        f"{len(conflicts)} scheduling conflict(s) found. "
                        "Two tasks are overlapping — adjust the start time of one to fix this."
                    )
                    for msg in conflicts:
                        st.warning(msg)
                else:
                    st.success("No time conflicts — your schedule is clear.")

# ===========================================================================
# TAB 2 – Chat assistant (AI agent)
# ===========================================================================
with tab2:
    st.subheader("Chat with PawPal+ Assistant")
    st.caption(
        "Describe your pets and schedule in plain language. "
        "The assistant will set up your owner profile, add pets and tasks, "
        "and generate your daily plan."
    )

    # --- Show current state so the user can see what the agent has set up ---
    if st.session_state.owner:
        owner = st.session_state.owner
        pet_list = ", ".join(p.name for p in owner.pets) or "none"
        st.info(
            f"Current state — Owner: **{owner.name}** | "
            f"Time: {owner.available_time_minutes} min | "
            f"Budget: ${owner.budget:.2f} | "
            f"Pets: {pet_list} | "
            f"Tasks: {len(owner.tasks)}"
        )

    st.divider()

    # --- Render conversation history ---
    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])

    # --- Chat input ---
    user_input = st.chat_input("e.g. I have 90 minutes and a $30 budget, my dog Mochi needs a walk and feeding")

    if user_input:
        # Show user message immediately
        st.session_state.chat_display.append({"role": "user", "text": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run the agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # owner_ref: one-element list so the agent can mutate it
                owner_ref = [st.session_state.owner]

                reply, updated_history = run_agent(
                    user_message=user_input,
                    conversation_history=st.session_state.chat_history,
                    owner_ref=owner_ref,
                )

                # Persist the (possibly new/updated) owner back to session state
                st.session_state.owner = owner_ref[0]

                # Sync the tasks display list from the owner's task pool
                if st.session_state.owner:
                    st.session_state.tasks = [
                        {
                            "Title":    t.title,
                            "Pet":      t.pet.name if t.pet else "-",
                            "Time":     t.preferred_time,
                            "Duration": f"{t.duration_minutes} min",
                            "Priority": t.priority.name,
                            "Cost":     f"${t.cost:.2f}",
                            "Category": t.category,
                        }
                        for t in st.session_state.owner.tasks
                    ]

            st.markdown(reply)

        # Save updated history and display
        st.session_state.chat_history = updated_history
        st.session_state.chat_display.append({"role": "assistant", "text": reply})

        # Rerun so the state banner at the top refreshes
        st.rerun()

    # --- Reset button ---
    if st.session_state.chat_display:
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.session_state.chat_display = []
            st.rerun()
