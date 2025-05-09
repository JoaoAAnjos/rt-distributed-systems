from project_lib import *
import heapq
import os
import csv

from enum import Enum, auto
from typing import List, Optional, Callable, Any
from project_lib import (Core, Component, Task, initialize_csv_data, cores_registry, 
                         tasks_registry, components_registry, CURRENT_TIME)

# --- Simulation Constants ---
SIMULATION_END_TIME = 1000.0  
EPSILON = 1e-9              # For floating point comparisons

#   --------------------
#   Enums
#   --------------------

class TaskState(Enum):
    IDLE = auto()
    READY = auto()
    RUNNING = auto()

class EventType(Enum):
    TASK_ARRIVAL = auto()
    TASK_COMPLETION = auto()
    BUDGET_REPLENISH = auto()

#   ------------------------------------------------------------------------------------
#   Classes
#   ------------------------------------------------------------------------------------

class TaskExecution:

    def __init__(self, task: Task):
        self.id = task._id
        self.wcet = task._wcet / core._speed_factor
        self.absolute_deadline = CURRENT_TIME + task._deadline
        self.period = task._period
        self.component_id = task._component_id
        
        self.state = TaskState.READY
        self.arrival_time = CURRENT_TIME
        self.exec_time = self.wcet
        self.exec_count = 0
        self.completion_times = []
        self.response_times = []
        self.deadlines_met = 0
        self.deadlines_missed = 0

class Event:

    def __init__(self, time: float, event_type: EventType, data: Any):
        self.time = time
        self.type = event_type
        self.data = data

#   ------------------------------------------------------------------------------------
#   Global variables
#   ------------------------------------------------------------------------------------

# Queue holding the events for simulation. This is a priority queue (min-heap based on event.time)
event_queue: List[Event] = []
# Registry of Tasks associated with Component for terminal Components
component_task_exec_registry: Dict[str, List[TaskExecution]] = {}
# The queue of ready tasks for each terminal Component
ready_queues: Dict[str, List[TaskExecution]] = {}
# The root core
core: Core = None
# The TaskExecution currently running.
running_task: Optional[TaskExecution] = None

#  --------------------------------------------------------------------------------------
#  Helper Functions
#  --------------------------------------------------------------------------------------

"""Gets the highest priority component, with a non-empty ready queue"""
def get_highest_priority_component() -> Component:
    def traverse(node: Component):
        nonlocal result
        priority_attr = None

        #Decides which property should be evaluated based on scheduler 
        if node._scheduler == Scheduler.RM:
            priority_attr = 'period'
        elif node._scheduler == Scheduler.EDF:
            priority_attr = 'next_replenish_time'

        if priority_attr is None:
            print(f"Error: Target component '{node._component_id}' has an uncovered scheduler.")
            return
        
        # If it's a leaf node
        if node.is_leaf():
            # Check if it's better than our current best candidate
            if (ready_queues.get(node._component_id) and 
                node.current_budget > 0 and
                (result is None or getattr(node, priority_attr) < getattr(result, priority_attr))):
                result = node
            return
            
        # Find child with highest priority
        next_node = min(node.children, key=lambda x: getattr(x, priority_attr))
        traverse(next_node)
        
        # If we didn't find a valid leaf in that branch, try other children
        if result is None or getattr(node, priority_attr) < getattr(result, priority_attr):
            for child in sorted(node.children, key=lambda x: getattr(x, priority_attr)):
                if child != next_node:  # Already checked this one
                    traverse(child)
        
    result = None
    traverse(core.root_comp)
    return result 


"""Adds a task to a component's ready queue"""
def add_to_component_ready_queue(component: Component, task_exec: TaskExecution):
    priority = None
    
    if component._scheduler == Scheduler.RM:
        priority = task_exec.period
    elif component._scheduler == Scheduler.EDF:
        priority = task_exec.absolute_deadline

    if priority is None:
        print(f"Error: Target component '{component._component_id}' has an uncovered scheduler.")
        return

    heapq.heappush(ready_queues.get(component._component_id), (priority, task_exec))


"""Removes an element from a component's ready queue"""
def remove_from_component_ready_queue(component: Component, task_exec: TaskExecution):
    ready_queues.get(component._component_id, task_exec)


"""Gets the highest priority task from the ready queue without removing it."""
def get_highest_priority_ready_task(ready_queue: List[TaskExecution]) -> Optional[TaskExecution]:
    if ready_queue:
        task = ready_queue[0] # Peek at the smallest element (highest priority)
        return task
    return None


"""Removes and returns the highest priority task from the ready queue."""
def pop_highest_priority_ready_task(ready_queue: List[TaskExecution]) -> Optional[TaskExecution]:
     if ready_queue:
        task = heapq.heappop(ready_queue)
        return task
     return None


"""Adds an event to the event queue"""
def schedule_event(event: Event):
    if event.time < SIMULATION_END_TIME:
        heapq.heappush(event_queue, (event.time, event))

"""Peeks at the next event on the event queue"""
def peek_next_event() -> Optional[Event]:
    if event_queue:
        return event_queue[0]
    
    return None

"""Removes and returns the next event from the event queue"""
def get_next_event() -> Optional[Event]:
    if event_queue:
        return heapq.heappop(event_queue)
    
    return None


"""Iterates through the component tree hierarchy, applying an operation on every node"""
def apply_action_on_tree(node: Component, action: Callable[[Component], None]):
    action(node)
    
    for child in node.children:
        apply_action_on_tree(child, action)


"""Iterates through the component tree hierarchy, finding the node that fits the condition.
    The condition is given as a callable that returns bool to allow more complex checks"""
def filter_tree_node(node: Component, action: Callable[[Component], bool]) -> Component:
    if action(node):
        return node
    else:
        for child in node.children:
            filter_tree_node(child, action)


"""Sets up the TaskExecution objects in the registry for simulator execution"""
def initialize_taskexecs_registry(component: Component):

    if component.is_leaf():
        component_tasks = component_task_registry.get(component._component_id)

        component_taskexecs = []

        for task in component_tasks:
            task_exec = TaskExecution(task)

            component_taskexecs.append(task_exec)

            schedule_event(Event(0.0, EventType.TASK_ARRIVAL, task_exec))

        component_task_exec_registry[component._component_id] = component_taskexecs


"""Initializes the ready queue for a component, heapifying it"""
def initialize_ready_queue(component: Component):

    if component.is_leaf():
        ready_queue = []
        heapq.heapify(ready_queue)

        ready_queues[component._component_id] = ready_queue


"""Sets initial budget and schedules initial event for budget replenish"""
def set_initial_remaining_budgets(component: Component):

    component.current_budget = component.budget
    component.next_replenish_time = component.period

    schedule_event(Event(component.period, EventType.BUDGET_REPLENISH, component))

# -----------------------------
# --- Core Simulation Logic ---
# -----------------------------

"""Executes the RM simulation loop for the specified core."""
def run_simulation(target_core_id: str, maxSimTime: float):
    global CURRENT_TIME, running_task

    if not initialize_simulation_state(target_core_id):
        return

    print("\n--- Starting RM Simulation Loop ---")
    while event_queue and CURRENT_TIME < maxSimTime:
        next_event = peek_next_event()
        time_to_next_event = next_event.time

        if time_to_next_event > CURRENT_TIME:
            elapsed_time = time_to_next_event - CURRENT_TIME
            process_idle_time(elapsed_time)

        next_event = get_next_event()
        CURRENT_TIME = next_event.time
        handle_event(next_event)

        make_scheduling_decision()

    CURRENT_TIME = min(CURRENT_TIME, SIMULATION_END_TIME)
    print(f"\n--- Simulation End at {CURRENT_TIME:.4f} ---")
    # Final statistics calculation/display happens outside this function


"""Prepares tasks and schedules initial events for the target core."""
def initialize_simulation_state(target_core_id: str):
    global CURRENT_TIME, running_task, core
    
    #Reset variables
    CURRENT_TIME = 0.0
    event_queue.clear()
    component_task_exec_registry.clear()
    ready_queues.clear()
    running_task = None

    #Heapify event_queue
    heapq.heapify(event_queue)

    # Find the target core and setup root node information
    if target_core_id not in cores_registry:
        print(f"Error: Target core '{target_core_id}' not found in loaded cores.")
        return False
    
    core = cores_registry[target_core_id]

    #Setup component task execution registry. This also initializes TaskExecution objects and
    #their respective task_arrival events, as the simulator has synchronous start
    apply_action_on_tree(core.root_comp, initialize_taskexecs_registry)
    
    #Setup component ready queues
    apply_action_on_tree(core.root_comp, initialize_ready_queue)

    #Set component initial remaining budgets
    apply_action_on_tree(core.root_comp, set_initial_remaining_budgets)  

    print("Simulation state initialized.")
    return True

"""Processes the passed time between current time and what should be the next event"""
def process_idle_time(elapsed_time: float):

    if running_task is None:
        return
    
    #Get component to which current running task belongs
    component = components_registry.get(running_task.component_id)

    execution_slice = min(running_task.exec_time, component.current_budget, elapsed_time)

    #Update task and component based on the available execution_slice
    running_task.exec_time -= execution_slice
    component.current_budget -= execution_slice

    #Update current time
    CURRENT_TIME += execution_slice

    if running_task.exec_time <= 0:
        schedule_event(Event(CURRENT_TIME, EventType.TASK_COMPLETION, running_task))
    elif component.current_budget <= 0:
        running_task.state = TaskState.READY
        add_to_component_ready_queue(component, running_task)
        
        running_task = None

        make_scheduling_decision()

        process_idle_time(elapsed_time - execution_slice)



"""Handles the current event from the event queue"""
def handle_event(event: Event):
    if event.type == EventType.BUDGET_REPLENISH:
        handle_budget_replenish(event)
    elif event.type == EventType.TASK_ARRIVAL:
        handle_task_arrival(event)
    elif event.type == EventType.TASK_COMPLETION:
        handle_task_completion(event)


"""Decides which task should be running at current time, according to schedulers and priorities."""
def make_scheduling_decision():
    global running_task, CURRENT_TIME

    component = get_highest_priority_component()
    ready_queue = ready_queues.get(component._component_id)

    highest_ready = get_highest_priority_ready_task(ready_queue)

    if running_task is None:
        if highest_ready:
            # Start the highest priority ready task
            running_task = pop_highest_priority_ready_task()
            running_task.state = TaskState.RUNNING
        else:
            running_task = None
    else: # A task is currently running
        if highest_ready and highest_ready != running_task:

            # Stop the running task and put it back in the ready queue
            preempted_task = running_task
            preempted_task.state = TaskState.READY
            # WCET remaining was updated just before this  TODO Review this comment
            add_to_component_ready_queue(component, preempted_task)

            # Start the new highest priority task
            running_task = pop_highest_priority_ready_task()
            running_task.state = TaskState.RUNNING


"""Handles Component budget being replenished event"""
def handle_budget_replenish(event: Event):
    try:
        assert type(event.data) == Component
        #Dynamic variables to avoid changing original Component class
        event.data.current_budget = event.data.budget
        event.data.next_replenish_time = CURRENT_TIME + event.data.period

        schedule_event(Event(event.data.next_replenish_time, EventType.BUDGET_REPLENISH, event.data))

        #TODO A BUDGET REPLENISH HAS TO FORCE A RECALCULATION OF THE CURRENT TASK TO BE RUN

    except AssertionError:
            print("Error: Event data was not of type Component as expected")
    pass
    

"""Handles a task arrival event."""
def handle_task_arrival(event: Event):
    global running_task

    assert type(event.data) == TaskExecution 
    task = event.data
    component = components_registry.get(task.component_id)

    if task.state != TaskState.IDLE:
        # Deadline miss detection for the previous job
        task.deadlines_missed += 1

        # --- Abort Policy ---
        # Approach: Abort it to prioritize the new job.

        if task.state == TaskState.RUNNING:
            # If the overrunning job was the one currently running
            if running_task and running_task._id == task.id:
                print(f"    Aborting currently RUNNING job of Task {task._id}.")
                running_task = None # Make the core available
                # Note: The task object itself still exists, but it's no longer tracked as running.
                # We will reset its state below when the new job starts.
        elif task.state == TaskState.READY:
            # If the overrunning job was preempted and in the ready queue
            remove_from_component_ready_queue(component, task) # Remove the old instance

        # Task state will be reset to READY for the new job below.

    # --- Activate the NEW job ---
    task.state = TaskState.READY
    task.arrival_time = event.time
    task.exec_time = task.wcet
    task.absolute_deadline = event.time + task.period # New job gets its own deadline. Under assumption period = deadline.
    task.exec_count += 1

    # Add the NEW job instance to the ready queue
    add_to_component_ready_queue(component, task)

    # Schedule the NEXT arrival of this task
    schedule_event(Event(event.time + task.period, EventType.TASK_ARRIVAL, task))
    

"""Handles a task completion event."""
def handle_task_completion(event: Event):
    global running_task

    assert type(event.data) == TaskExecution 
    task = event.data

    task.state = TaskState.IDLE
    response_time = event.time - task.arrival_time
    task.completion_times.append(event.time)
    task.response_times.append(response_time)
    task.deadlines_met += 1

    if running_task == task:
        running_task = None # Core becomes free


#   ------------------------------------------------------------------------------------
#   Simulation Results Output
#   ------------------------------------------------------------------------------------

#TODO REVIEW AT END OF SIMULATOR CODE
"""Calculates results and saves them to a CSV file."""
def save_results_to_csv(filename="results_simulator.csv"):
    return


# ----------------------
# --- Main Execution ---
# ----------------------

#TODO REVIEW AT END OF OTHER CODE
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
    initialize_csv_data()
    print("Data initialization complete.")
    print(f"Loaded Cores: {list(cores.keys())}")
    print(f"Loaded Tasks: {list(tasks_registry.keys())}")

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