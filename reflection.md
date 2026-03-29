# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design includes 
- Owner (name, available_time_minutes)
- Pet (name, age, weight, type of pet)
- Task (title, duration_minutes, priority, category)
- Schedule (list of tasks) - add_task(task), total_duration(), summary()

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, Claude identified some missing relationship. Owenr and Schedule were not connected. Pet had no influence on task or schedule. Pet data was stored but never used. Priority was used as a string and instead changed to enum. Low = 1, Medium = 2, High = 3. Also introduced a budget, this way we know if can keep track of costs and the owner can decide the schedule appropriately

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
It checks for conflicts, and preferred time, also computes the dutation. The constraints that mattered most I decided where priority and conflicts.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Tasks are picked on by one from a sorted list and added if they fit, but it can leave time on the table. This is reasonable since a pet owner just needs something fast and transparent instead of optimizing every single specific time block.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used it for refactoring, helping me craft my finalized UML diagram and brainstorming.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

There was no logic to consider if an owner had more than one pet in the UML diagram it constructed. So I had to manually mention that edge case. Once implemented it redesigned the diagram to implement the new change.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
Task completetion,sorting, filtering
- Why were these tests important?
These are vital to the app - ex. Task completion is a core logic to change tasks status. Sorting returns tasks
in strict chronologigal order, and filtering to return only mathing tasks

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
I would say pretty confident as the core logic covers both happy paths and edge cases. If I had more time I would test to see if two tasks of equal priortiy and identical preferred times then which one would take precedence? Also checking if the owner has days where they are strictly unavailable.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I was satisfied with the final UML diagram after some reiterations with AI.

**b. What you would improve**
I would improve on the UI, it seems a little overwhelming and not very user friendly.

- If you had another iteration, what would you improve or redesign?
I would improve on some edge cases, the ones implemented are sufficient but does not cover everything.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I think constantly double checking its work and asking it to pause and consider the changes its makign and what effects it may have. It tends to just follow whatever the user prompts.
