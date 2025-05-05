from project_lib import *
import heapq
import math
import os
import csv
from typing import List, Optional, Tuple
from project_lib import (Core, Component, Task, Job, Resource_paradigm,
                         initialize_data, cores, tasks as global_tasks,
                         components as global_components, CURRENT_TIME)

# --- Simulation Constants ---
SIMULATION_END_TIME = 1000.0  
EPSILON = 1e-9              # For floating point comparisons

# --- Event Definition ---
# Using a tuple: (time, event_type, task_object)
# event_type can be 'TASK_ARRIVAL', 'TASK_COMPLETION', 'SIM_END'

# --- Simulator State ---
event_queue: List[Tuple[int, str, Optional[Task]]] = []
ready_queue: List[Tuple[int, Task]] = [] # Min-heap based on priority
running_task: Optional[Task] = None
sim_cores: dict[str, Core] = {} # Store cores relevant to this sim run
sim_tasks: dict[str, Task] = {} # Store tasks relevant to this sim run

# ------------------------
# --- Helper Functions ---
# ------------------------

"""Retrieves all Task objects associated with a given core_id."""
def get_tasks_for_core(core_id: str) -> List[Task]:
    core_tasks = []
    if core_id not in sim_cores:
        print(f"Warning: Core {core_id} not found during task retrieval.")
        return []
    # Check if core_id is valid
    for comp in global_components.values():
        if comp._core_id == core_id:
            # Check if component has tasks
            if hasattr(comp, '_sub_components'):
                 for child in comp._sub_components:
                     if isinstance(child, Task) and child._id in global_tasks:
                         # Ensure we use the global task object
                         core_tasks.append(global_tasks[child._id])
            else:
                 print(f"Warning: Component {comp._component_id} lacks '_sub_components'. Cannot find its tasks.")
    # If no tasks found, print a warning
    if not core_tasks:
         print(f"Warning: No tasks found associated with {core_id}.")
    return core_tasks

"""Adds an event to the global event queue."""
def schedule_event(time: float, event_type: str, task: Optional[Task] = None):
    if time < SIMULATION_END_TIME + EPSILON:
        heapq.heappush(event_queue, (time, event_type, task))

"""Adds a task to the ready queue (max-heap based on priority)."""
def add_to_ready_queue(task: Task):
    heapq.heappush(ready_queue, (task._priority, task))

"""Gets the highest priority task from the ready queue without removing it."""
def get_highest_priority_ready_task() -> Optional[Task]:
    if ready_queue:
        task = ready_queue[0] # Peek at the smallest element (highest priority)
        return task
    return None

"""Removes and returns the highest priority task from the ready queue."""
def remove_highest_priority_ready_task() -> Optional[Task]:
     if ready_queue:
        task = heapq.heappop(ready_queue)
        return task
     return None

"""Removes a specific task from the ready queue (inefficient)."""
def remove_task_from_ready_queue(task_to_remove: Task):
    global ready_queue
    new_ready_queue = []
    found = False
    while ready_queue:
        priority, task = heapq.heappop(ready_queue)
        if task._id == task_to_remove._id:
            found = True
            # Don't add it back
        else:
            heapq.heappush(new_ready_queue, (priority, task))
    ready_queue = new_ready_queue
    # if not found:
    #     print(f"Warning: Task {task_to_remove._id} not found in ready queue for removal.")

# -----------------------------
# --- Core Simulation Logic ---
# -----------------------------

"""Prepares tasks and schedules initial events for the target core."""
def initialize_simulation_state(target_core_id: str):
    global running_task, event_queue, ready_queue, CURRENT_TIME, sim_tasks, sim_cores

    CURRENT_TIME = 0.0
    running_task = None
    event_queue = []
    ready_queue = []
    heapq.heapify(event_queue)
    heapq.heapify(ready_queue)
    sim_tasks = {}
    sim_cores = {}


    # 1. Find the target core
    if target_core_id not in cores:
        print(f"Error: Target core '{target_core_id}' not found in loaded cores.")
        return False
    target_core = cores[target_core_id]
    sim_cores[target_core_id] = target_core
    print(f"Simulating Core: {target_core_id} (Speed Factor: {target_core._speed_factor})")

    # 2. Get tasks for the core
    core_task_list = get_tasks_for_core(target_core_id)
    if not core_task_list:
        print(f"Error: No tasks found for core '{target_core_id}'. Aborting simulation.")
        return False

    # 3. Prepare tasks (priority, WCET adjustment, add dynamic state)
    print("Preparing tasks:")
    for task in core_task_list:
        sim_tasks[task._id] = task # Keep track of tasks in this sim run

        # Adjust WCET based on core speed
        task._adjusted_wcet = task._wcet / target_core._speed_factor

        # Add dynamic state attributes
        task.state = 'IDLE' # States: IDLE, READY, RUNNING
        task.remaining_wcet = 0.0
        task.arrival_time = 0.0
        task.completion_time = 0.0
        task.absolute_deadline = 0.0
        task.job_count = 0
        # Statistics
        task.response_times = []
        task.deadlines_met = 0
        task.deadlines_missed = 0
        task.last_completion_event_time = -1.0 # To avoid double processing completion

        print(f"  - Task: {task._id}, Period: {task._period}, Prio: {task._priority}, Adj WCET: {task._adjusted_wcet:.4f}")

        # 4. Schedule initial arrival
        schedule_event(0.0, 'TASK_ARRIVAL', task)

    # 5. Schedule simulation end
    schedule_event(SIMULATION_END_TIME, 'SIM_END')

    print("Simulation state initialized.")
    return True

"""Decides which task to run next based on RM priority."""
def make_scheduling_decision():
    global running_task, CURRENT_TIME

    # Find highest priority task in ready queue
    highest_ready = get_highest_priority_ready_task()

    # print(f"DEBUG: Sched Decision at {CURRENT_TIME:.4f}. Running: {running_task._id if running_task else 'None'}. Highest Ready: {highest_ready._id if highest_ready else 'None'}")

    if running_task is None:
        if highest_ready:
            # Start the highest priority ready task
            running_task = remove_highest_priority_ready_task()
            running_task.state = 'RUNNING'
            print(f"{CURRENT_TIME:.4f}: Starting Task {running_task._id} (Rem WCET: {running_task.remaining_wcet:.4f})")
            # Schedule its completion
            completion_time = CURRENT_TIME + running_task.remaining_wcet
            schedule_event(completion_time, 'TASK_COMPLETION', running_task)
        else:
            # Core is idle
             # print(f"{CURRENT_TIME:.4f}: Core is Idle")
            pass
    else: # A task is currently running
        if highest_ready and highest_ready._priority < running_task._priority:
            # Preemption needed
            print(f"{CURRENT_TIME:.4f}: Preempting Task {running_task._id} (Prio {running_task._priority}) by Task {highest_ready._id}")

            # Stop the running task and put it back in the ready queue
            preempted_task = running_task
            preempted_task.state = 'READY'
            # WCET remaining was updated just before this decision
            add_to_ready_queue(preempted_task) # Put it back in ready queue

            # Start the new highest priority task
            running_task = remove_highest_priority_ready_task()
            running_task.state = 'RUNNING'
            print(f"{CURRENT_TIME:.4f}: Starting Task {running_task._id} (Rem WCET: {running_task.remaining_wcet:.4f})")
            completion_time = CURRENT_TIME + running_task.remaining_wcet
            schedule_event(completion_time, 'TASK_COMPLETION', running_task)
        else:
            # Running task continues (no preemption)
            # print(f"{CURRENT_TIME:.4f}: Task {running_task._id} continues.")
            pass


"""Handles a task arrival event."""
def handle_task_arrival(event_time: float, task: Task):
    # print(f"{event_time:.4f}: Task Arrival: {task._id} (Job {task.job_count + 1})")
    global running_task

    previous_job_overran = False
    if task.state != 'IDLE':
        # Deadline miss detection for the previous job
        previous_job_overran = True
        print(f"!!! Overrun: Task {task._id} arrived at {event_time:.4f} but previous job (state={task.state}) active. Deadline MISSED for previous job.")
        task.deadlines_missed += 1

        # --- Abort Policy ---
        # Common approach: Abort it to prioritize the new job.

        if task.state == 'RUNNING':
            # If the overrunning job was the one currently running
            if running_task and running_task._id == task._id:
                print(f"    Aborting currently RUNNING job of Task {task._id}.")
                # A better DES would explicitly remove the specific completion event.
                running_task = None # Make the core available
                # Note: The task object itself still exists, but it's no longer tracked as running.
                # We will reset its state below when the new job starts.
        elif task.state == 'READY':
            # If the overrunning job was preempted and in the ready queue
            print(f"    Removing overdue READY job of Task {task._id} from ready queue.")
            remove_task_from_ready_queue(task) # Remove the old instance

        # Task state will be reset to READY for the new job below.

    # --- Activate the NEW job ---
    task.state = 'READY'
    task.arrival_time = event_time
    task.remaining_wcet = task._adjusted_wcet # New job gets full WCET
    task.absolute_deadline = event_time + task._deadline # New job gets its own deadline
    task.job_count += 1

    # Add the NEW job instance to the ready queue
    add_to_ready_queue(task)

    # Schedule the NEXT arrival of this task
    schedule_event(event_time + task._period, 'TASK_ARRIVAL', task)

    # Trigger scheduling decision (because a new task is ready or core might be free)
    if previous_job_overran and task.state == 'RUNNING':
         # If we just aborted the running task, we definitely need to reschedule
         make_scheduling_decision()
    elif not running_task or task._priority < running_task._priority :
         # If core is idle OR the new task has higher priority than running task
         make_scheduling_decision()

"""Handles a task completion event."""
def handle_task_completion(event_time: float, task: Task):
    global running_task

    # Check if this completion is valid (task must be RUNNING)
    # Also check if we already processed a completion for this exact time (potential float issue)
    if task.state != 'RUNNING' or running_task is None or running_task._id != task._id \
       or abs(event_time - task.last_completion_event_time) < EPSILON:
        # print(f"DEBUG: Ignoring stale/duplicate completion for {task._id} at {event_time:.4f}")
        return # Stale event or already processed

    print(f"{event_time:.4f}: Task Completion: {task._id} (Job {task.job_count})")
    task.last_completion_event_time = event_time # Mark as processed

    task.state = 'IDLE'
    task.completion_time = event_time
    response_time = task.completion_time - task.arrival_time
    task.response_times.append(response_time)

    # Check deadline
    if event_time > task.absolute_deadline + EPSILON:
        task.deadlines_missed += 1
        print(f"!!! Deadline Missed: {task._id} (Job {task.job_count}) finished at {event_time:.4f}, deadline was {task.absolute_deadline:.4f}")
    else:
        task.deadlines_met += 1

    running_task = None # Core becomes free

    # Trigger scheduling decision
    make_scheduling_decision()

"""Executes the RM simulation loop for the specified core."""
def run_simulation(target_core_id: str):
    global CURRENT_TIME, running_task

    if not initialize_simulation_state(target_core_id):
        return

    print("\n--- Starting RM Simulation Loop ---")
    while event_queue:
        # Get next event
        event_time, event_type, event_task = heapq.heappop(event_queue)

        # Check for simulation end condition
        if event_type == 'SIM_END' or event_time > SIMULATION_END_TIME + EPSILON :
            CURRENT_TIME = min(event_time, SIMULATION_END_TIME) # Advance time to end
            print(f"\n--- Simulation End at {CURRENT_TIME:.4f} ---")
            break # Exit loop

        # --- Process time elapsed since last event ---
        if event_time > CURRENT_TIME:
            time_elapsed = event_time - CURRENT_TIME
            if running_task:
                # print(f"DEBUG: Task {running_task._id} ran for {time_elapsed:.4f}. Rem WCET before: {running_task.remaining_wcet:.4f}")
                executable_time = min(time_elapsed, running_task.remaining_wcet)
                running_task.remaining_wcet -= executable_time
                # print(f"DEBUG: Task {running_task._id} Rem WCET after: {running_task.remaining_wcet:.4f}")

                # Check if the running task finished *during* this time slice
                if running_task.remaining_wcet < EPSILON and executable_time < time_elapsed + EPSILON:
                     # Task finished before the scheduled event
                     finish_time = CURRENT_TIME + executable_time
                     print(f"    Task {running_task._id} finished early at {finish_time:.4f}")
                     CURRENT_TIME = finish_time
                     handle_task_completion(CURRENT_TIME, running_task) # running_task becomes None here
                     # Skip processing the original event for this task if it was its completion
                     if event_type == 'TASK_COMPLETION' and event_task._id == task._id:
                          continue # Skip the now redundant completion event

            # Update current time AFTER potentially handling early completion
            CURRENT_TIME = event_time # Advance time to the actual event time

        # --- Process the event ---
        #print(f"Processing Event: T={event_time:.4f}, Type={event_type}, Task={event_task._id if event_task else 'N/A'}")
        if event_type == 'TASK_ARRIVAL':
            handle_task_arrival(CURRENT_TIME, event_task)
        elif event_type == 'TASK_COMPLETION':
            # Only handle if task didn't finish early during time update
             if running_task and running_task._id == event_task._id:
                 if abs(running_task.remaining_wcet) < EPSILON: # Should be zero if completion is accurate
                    handle_task_completion(CURRENT_TIME, event_task)
                 else:
                      # This might happen due to floating point or if preemption occured exactly here
                      print(f"Warning: Completion event for {event_task._id} at {CURRENT_TIME:.4f}, but remaining WCET is {running_task.remaining_wcet:.4f}. Re-evaluating.")
                      make_scheduling_decision() # Re-check who should run
             # else: Completion event might be stale due to preemption or early finish

    print("--- Simulation Loop Finished ---")
    # Final statistics calculation/display happens outside this function

"""Calculates results and saves them to a CSV file."""
def save_results_to_csv(filename="solution.csv"):
    print(f"\n--- Saving Simulation Results to {filename} ---")

    task_results_data = []
    component_schedulability_map = {} # Store schedulability per component

    # --- Calculate task-level results and determine component schedulability ---
    for task_id, task in sim_tasks.items():
        component_id = task._component_id # Get component ID from task object

        jobs_finished = task.deadlines_met + task.deadlines_missed
        avg_response_time = sum(task.response_times) / len(task.response_times) if task.response_times else 0.0
        max_response_time = max(task.response_times) if task.response_times else 0.0

        # Task schedulable: 1 if it ran at least one job and missed none, 0 otherwise
        task_schedulable_flag = 1 if (jobs_finished > 0 and task.deadlines_missed == 0) else 0
        task_ran_and_failed = 1 if (jobs_finished > 0 and task.deadlines_missed > 0) else 0

        # Store task results temporarily
        task_results_data.append({
            'task_name': task._id,
            'component_id': component_id,
            'task_schedulable': task_schedulable_flag,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'ran_and_failed': task_ran_and_failed # Helper flag
        })

        # Update component schedulability: If any task in the component failed, the component is not schedulable
        if component_id not in component_schedulability_map:
             component_schedulability_map[component_id] = True # Assume schedulable until a task fails

        if task_ran_and_failed:
            component_schedulability_map[component_id] = False # Mark component as not schedulable

    # Convert boolean map to 0/1 for CSV
    component_schedulable_numeric = {
        comp_id: 1 if is_schedulable else 0
        for comp_id, is_schedulable in component_schedulability_map.items()
    }

    # --- Prepare rows for CSV including component schedulability ---
    csv_rows = []
    for task_data in sorted(task_results_data, key=lambda x: x['task_name']): # Sort by task name for consistent output
        component_id = task_data['component_id']
        comp_sched_value = component_schedulable_numeric.get(component_id, 0) # Default to 0 if component somehow not in map

        csv_rows.append({
            'task_name': task_data['task_name'],
            'component_id': component_id,
            'task_schedulable': task_data['task_schedulable'],
            'avg_response_time': f"{task_data['avg_response_time']:.4f}", # Format to 4 decimal places
            'max_response_time': f"{task_data['max_response_time']:.4f}", # Format to 4 decimal places
            'component_schedulable': comp_sched_value
        })

    # --- Write to CSV File ---
    header = [
        'task_name',
        'component_id',
        'task_schedulable',
        'avg_response_time',
        'max_response_time',
        'component_schedulable'
    ]

    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)

            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"Successfully saved results to {filename}")

    except IOError:
        print(f"Error: Could not write to file {filename}")
    except Exception as e:
        print(f"An unexpected error occurred while writing CSV: {e}")

# ----------------------
# --- Main Execution ---
# ----------------------


if __name__ == "__main__":
    # Ensure input directory and files exist (create dummies if needed)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input")
    os.makedirs(input_dir, exist_ok=True)

    arch_file = os.path.join(input_dir, "architecture.csv")
    budg_file = os.path.join(input_dir, "budgets.csv")
    task_file = os.path.join(input_dir, "tasks.csv")

    # --- Initialize data using the library ---
    print("Initializing data from CSV files...")
    initialize_data()
    print("Data initialization complete.")
    print(f"Loaded Cores: {list(cores.keys())}")
    print(f"Loaded Tasks: {list(global_tasks.keys())}")

    # --- Run the simulation for a specific core ---
    target_core = "Core_1" # Specify the core ID to simulate
    if target_core in cores:
         if cores[target_core]._scheduler == "RM":
             run_simulation(target_core)
             save_results_to_csv()
         else:
             print(f"Core {target_core} uses {cores[target_core]._scheduler}, not RM. Skipping RM simulation.")
    else:
         print(f"Core {target_core} not found in configuration.")