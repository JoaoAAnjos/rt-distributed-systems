from source.project_lib import *
import heapq
import sys
import math

from enum import Enum, auto
from typing import List, Optional, Callable, Any
from source.project_lib import (Core, Component, Task, cores_registry, 
                         tasks_registry, components_registry, CURRENT_TIME)

# --- Simulation Constants ---
SIMULATION_END_TIME = 0.0  
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
        self.wcet = task._wcet
        self.absolute_deadline = CURRENT_TIME + task._deadline
        self.period = task._period
        self.component_id = task._component_id
        self.schedulable = True
        
        self.state = TaskState.IDLE
        self.arrival_time = CURRENT_TIME
        self.exec_time = self.wcet
        self.exec_count = 0
        self.completion_times = []
        self.response_times = []
        self.deadlines_met = 0
        self.deadlines_missed = 0

    def __lt__(self, other):
        #   ATTENTION: You should only compare two tasks that belong to the same component
        #   (i.e, that have the same scheduler) or else this logic is wrong
        component = components_registry.get(self.component_id)

        if component._scheduler == Scheduler.RM:
            return self.period < other.period
        elif component._scheduler == Scheduler.EDF:
            return self.absolute_deadline < other.absolute_deadline


class Event:

    def __init__(self, time: float, event_type: EventType, data: Any):
        self.time = time
        self.type = event_type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

#   ------------------------------------------------------------------------------------
#   Global variables
#   ------------------------------------------------------------------------------------

#   Queue holding the events for simulation. This is a priority queue (min-heap based on event.time)
event_queue: List[Event] = []
#   Registry of Tasks associated with Component for terminal Components
component_task_exec_registry: Dict[str, List[TaskExecution]] = {}
#   The queue of ready tasks for each terminal Component
ready_queues: Dict[str, List[TaskExecution]] = {}
#   The root core
core: Core = None
#   The TaskExecution currently running.
running_task: Optional[TaskExecution] = None

#  --------------------------------------------------------------------------------------
#  Helper Functions
#  --------------------------------------------------------------------------------------

"""
    Gets the highest priority component, with a non-empty ready queue.
"""
def get_highest_priority_component() -> Component:
    def traverse(node: Component):
        nonlocal result
        priority_attr = None

        #   Decides which property should be evaluated based on scheduler 
        if node._scheduler == Scheduler.RM:
            priority_attr = '_period'
        elif node._scheduler == Scheduler.EDF:
            priority_attr = 'next_replenish_time'

        if priority_attr is None:
            print(f"Error: Target component '{node._component_id}' has an uncovered scheduler.")
            return
        
        #   If it's a leaf node
        if node.is_leaf():
            #   Check if it meets the conditions to be picked
            if ((ready_queues.get(node._component_id) or \
            (running_task is not None and running_task.component_id == node._component_id)) and \
            get_node_available_resources(node) > 0.0):

                result = node
            return
            
        #   Find child with highest priority
        next_node = min(node.children, key=lambda x: getattr(x, priority_attr))
        traverse(next_node)
        
        #   If we didn't find a valid leaf in that branch, try other children
        if result is None:
            for child in sorted(node.children, key=lambda x: getattr(x, priority_attr)):
                #   Already checked this one
                if child != next_node:
                    traverse(child)
        
    result = None
    traverse(core.root_comp)
    return result 


"""
    Adds a task to a component's ready queue.
"""
def add_to_component_ready_queue(component: Component, task_exec: TaskExecution):
    heapq.heappush(ready_queues.get(component._component_id), task_exec)


"""
    Removes an element from a component's ready queue.
"""
def remove_from_component_ready_queue(component: Component, task_exec: TaskExecution):
    ready_queue = ready_queues.get(component._component_id)

    if ready_queue:
        ready_queue.remove(task_exec)
        #   This is necessary because removing an arbitrary task from the ready_queue breaks
        #   the heapify and needs to be redone.
        heapq.heapify(ready_queue)


"""
    Gets the highest priority task from the ready queue without removing it.
"""
def peek_highest_priority_ready_task(ready_queue: List[TaskExecution]) -> Optional[TaskExecution]:
    if ready_queue:
        #   Peek at the smallest element (highest priority)
        return ready_queue[0]
    return None


"""
    Removes and returns the highest priority task from the ready queue.
"""
def pop_highest_priority_ready_task(ready_queue: List[TaskExecution]) -> Optional[TaskExecution]:
     if ready_queue:
        task = heapq.heappop(ready_queue)
        return task
     return None


"""
    Adds an event to the event queue.
"""
def schedule_event(event: Event):
    if event.time < SIMULATION_END_TIME:
        heapq.heappush(event_queue, event)


"""
    Peeks at the next event on the event queue.
"""
def peek_next_event() -> Optional[Event]:
    if event_queue:
        return event_queue[0]
    
    return None


"""
    Removes and returns the next event from the event queue.
"""
def get_next_event() -> Optional[Event]:
    if event_queue:
        return heapq.heappop(event_queue)
    
    return None


"""
    Iterates through the component tree hierarchy downwards, applying an operation on every node.
"""
def apply_action_on_tree(node: Component, action: Callable[[Component], None]):
    action(node)
    
    for child in node.children:
        apply_action_on_tree(child, action)


"""
    Calculates the available resources for a node and returns it.
"""
def get_node_available_resources(node: Component) -> float:
    def traverse(node: Component):
        nonlocal result

        if node == core.root_comp:
            return
        
        #   Gets the lowest possible budget value in the tree, by checking the budget
        #   available from parents
        if node.current_budget < result:
            result = node.current_budget

        traverse(node._parent)

    result = sys.float_info.max
    traverse(node)
    return result


"""
    Iterates through the component tree hierarchy, finding the node that fits the condition.
    The condition is given as a callable that returns bool to allow more complex checks.
"""
def filter_tree_node(node: Component, action: Callable[[Component], bool]) -> Component:
    if action(node):
        return node
    else:
        for child in node.children:
            filter_tree_node(child, action)


"""
    Sets up the TaskExecution objects in the registry for simulator execution.
"""
def initialize_taskexecs_registry(component: Component):
    #   Check if the component has tasks as children
    if component.is_leaf():

        component_tasks = component_task_registry.get(component._component_id)

        component_taskexecs = []

        for task in component_tasks:
            task_exec = TaskExecution(task)
            component_taskexecs.append(task_exec)

            #   Schedule the task arrival event
            schedule_event(Event(0.0, EventType.TASK_ARRIVAL, task_exec))

        component_task_exec_registry[component._component_id] = component_taskexecs


"""
    Initializes the ready queue for a component, heapifying it.
"""
def initialize_ready_queue(component: Component):
    #   Check if the component has tasks as children
    if component.is_leaf():
        ready_queue = []
        heapq.heapify(ready_queue)

        ready_queues[component._component_id] = ready_queue


"""
    Sets initial budget and schedules initial event for budget replenish.
"""
def set_initial_remaining_budgets(component: Component):

    component.current_budget = component._budget
    component.next_replenish_time = component._period

    if (component != core.root_comp):
        schedule_event(Event(component._period, EventType.BUDGET_REPLENISH, component))


"""
    Reduces a component's current budget and its respective parent component's budget
    by a given value.
"""
def reduce_current_hierarchy_budget(component: Component, value: float):

    if component != core.root_comp:
        component.current_budget -= value
        reduce_current_hierarchy_budget(component._parent, value)


# -----------------------------
# --- Core Simulation Logic ---
# -----------------------------

"""
    Executes the RM simulation loop for the specified core.
"""
def run_simulation(target_core_id: str, maxSimTime: float):
    global CURRENT_TIME, SIMULATION_END_TIME, running_task

    SIMULATION_END_TIME = maxSimTime

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
    #   Final statistics calculation/display happens outside this function


"""
    Prepares tasks and schedules initial events for the target core.
"""
def initialize_simulation_state(target_core_id: str):
    global CURRENT_TIME, running_task, core
    
    #   Reset variables
    CURRENT_TIME = 0.0
    event_queue.clear()
    component_task_exec_registry.clear()
    ready_queues.clear()
    running_task = None

    #   Heapify event_queue
    heapq.heapify(event_queue)

    #   Find the target core and setup root node information
    if target_core_id not in cores_registry:
        print(f"Error: Target core '{target_core_id}' not found in loaded cores.")
        return False
    
    core = cores_registry[target_core_id]

    #   Setup component task execution registry. This also initializes TaskExecution objects and
    #   their respective task_arrival events, as the simulator has synchronous start
    apply_action_on_tree(core.root_comp, initialize_taskexecs_registry)
    
    #   Setup component ready queues
    apply_action_on_tree(core.root_comp, initialize_ready_queue)

    #   Set component initial remaining budgets
    apply_action_on_tree(core.root_comp, set_initial_remaining_budgets)  

    print("Simulation state initialized.")
    return True


"""
    Processes the passed time between current time and what should be the next event.
"""
def process_idle_time(elapsed_time: float):
    global CURRENT_TIME, running_task

    if running_task is None:
        return
    
    #   Temporary variable so we can change current time for processing idle without changing 
    #   the global variable. This is done because CURRENT_TIME is updated on the main simulation
    #   loop and should not be updated here. The reason is because new events might pop up in
    #   this idle time processing, and the CURRENT_TIME after being changed here would be incorrect.
    #   Although it would be updated to the correct value when the event is popped out of the queue
    #   back on the main loop, we should avoid any unecessary changes to the variable that might
    #   lead to bugs and incorrect results.
    current_time = CURRENT_TIME

    #   Get component to which current running task belongs
    component = components_registry.get(running_task.component_id)

    available_budget = get_node_available_resources(component)

    #   Get the lowest budget in the running component hierarchy. This tells us how much available
    #   resources we have to run the task
    execution_slice = min(running_task.exec_time, available_budget, elapsed_time)

    #   Update task and component based on the available execution_slice
    running_task.exec_time -= execution_slice
    reduce_current_hierarchy_budget(component, execution_slice)

    #   Update current time
    current_time += execution_slice

    if math.isclose(running_task.exec_time, 0.0) or running_task.exec_time < 0.0:

        schedule_event(Event(current_time, EventType.TASK_COMPLETION, running_task))

    elif math.isclose(available_budget - execution_slice, 0.0) or \
    available_budget - execution_slice < 0.0:
        running_task.state = TaskState.READY
        add_to_component_ready_queue(component, running_task)
        
        running_task = None

        make_scheduling_decision()

        process_idle_time(elapsed_time - execution_slice)



"""
    Handles the current event from the event queue.
"""
def handle_event(event: Event):
    if event.type == EventType.BUDGET_REPLENISH:
        handle_budget_replenish(event)
    elif event.type == EventType.TASK_ARRIVAL:
        handle_task_arrival(event)
    elif event.type == EventType.TASK_COMPLETION:
        handle_task_completion(event)


"""
    Decides which task should be running at current time, according to schedulers and priorities.
"""
def make_scheduling_decision():
    global running_task, CURRENT_TIME

    highest_ready = None
    component = get_highest_priority_component()

    if component is not None:
        ready_queue = ready_queues.get(component._component_id)

        highest_ready = peek_highest_priority_ready_task(ready_queue)

    if running_task is None and highest_ready:
        #   Start the highest priority ready task
        running_task = pop_highest_priority_ready_task(ready_queue)
        running_task.state = TaskState.RUNNING
    else: #     A task is currently running
        if (highest_ready and \
        (component._component_id != running_task.component_id or \
        (component._component_id == running_task.component_id and highest_ready < running_task))):

            #   Stop the running task and put it back in the ready queue
            preempted_task = running_task
            preempted_task.state = TaskState.READY
            add_to_component_ready_queue(components_registry.get(preempted_task.component_id), \
                                         preempted_task)

            #   Start the new highest priority task
            running_task = pop_highest_priority_ready_task(ready_queue)
            running_task.state = TaskState.RUNNING


"""
    Handles Component budget being replenished event.
"""
def handle_budget_replenish(event: Event):
    try:
        assert type(event.data) == Component
        #   Dynamic variables to avoid changing original Component class
        event.data.current_budget = event.data._budget
        event.data.next_replenish_time = CURRENT_TIME + event.data._period

        schedule_event(Event(event.data.next_replenish_time, EventType.BUDGET_REPLENISH, event.data))
    except AssertionError:
            print("Error: Event data was not of type Component as expected")
    pass
    

"""
    Handles a task arrival event.
"""
def handle_task_arrival(event: Event):
    global running_task

    assert type(event.data) == TaskExecution 
    task = event.data
    component = components_registry.get(task.component_id)

    if task.state != TaskState.IDLE:
        #   Deadline miss detection for the previous job
        task.deadlines_missed += 1
        task.schedulable = False

        # --- Abort Policy ---
        #   Approach: Abort it to prioritize the new job.

        if task.state == TaskState.RUNNING:
            #   If the overrunning job was the one currently running
            if running_task and running_task.id == task.id:
                print(f"    Aborting currently RUNNING job of Task {task.id}.")
                running_task = None # Make the core available
                #   Note: The task object itself still exists, but it's no longer tracked as running.
                #   We will reset its state below when the new job starts.
            else:
                print(f" Task detected as running is not actually running_task TASK_ID: {task.id}")
        elif task.state == TaskState.READY:
            print(f"    Removing From ready queue TASK {task.id}.")
            #   If the overrunning job was preempted and in the ready queue
            remove_from_component_ready_queue(component, task) # Remove the old instance

        #   Task state will be reset to READY for the new job below.

    # --- Activate the NEW job ---
    task.state = TaskState.READY
    task.arrival_time = event.time
    task.exec_time = task.wcet

    #   New job gets its own deadline. Under assumption period = deadline.
    task.absolute_deadline = event.time + task.period
    task.exec_count += 1

    #   Add the NEW job instance to the ready queue
    add_to_component_ready_queue(component, task)

    #   Schedule the NEXT arrival of this task
    schedule_event(Event(event.time + task.period, EventType.TASK_ARRIVAL, task))
    

"""
    Handles a task completion event.
"""
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