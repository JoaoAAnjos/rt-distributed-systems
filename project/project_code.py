from project_types import Component, Core, Task, Job, TIME_UNIT
from typing import Dict
import math
import csv



"""
Return the Supply Bound Function for a component's
BDR resource paradigm.
>   Parameters:
    - component: component instance
    - time: float number that represents time since
      last resource
"""
def sbf_component(component : Component, t_interval : float):
    delta = component._interface._part_delay
    alfa = component._interface._av_factor
    ret_value = 0.0

    if t_interval > delta:
        ret_value = float(alfa*(t_interval - delta))
    
    return ret_value
    


"""
    Demand bound function for a task set following
    RM algorithm

    >   Return:
        -   Total demand bound function value
"""
def dbf_task_RM(sorted_tasks, task : Task, t_interval : float):
    dbf_value = task._wcet
    for hp_task in sorted_tasks:
        if hp_task._priority < task._priority:
            dbf_value += math.ceil(t_interval / hp_task._period) * hp_task._wcet

    #   Return the total amount of resource demanded by the task
    return dbf_value



"""
    Demand bound function for a component which has RM as
    scheduling algorithm.

    >   Return:
        (1)
            -   True:   Component is schedulable
            -   False:  Component is not schedulable
        (2)
            -   Array of schedulable/unschedulable tasks
"""
def dbf_component_RM(component : Component):
    schedulable = True
    
    sorted_tasks = sorted(component._sub_components, key=lambda _task: _task._priority, reverse=True)
    schedulable_tasks = [True] * len(sorted_tasks)

    for i, task in enumerate(sorted_tasks):
        t_interval = 0.0

        while t_interval <= task._period and schedulable:
            dbf_task = dbf_task_RM(sorted_tasks, task, t_interval)

            if dbf_task > sbf_component(component, t_interval):
                schedulable = False
                schedulable_tasks[i] = False
                break

            t_interval += TIME_UNIT

    return schedulable, schedulable_tasks



"""
    Demand bound function for a component which has EDF as
    scheduling algorithm.

    >   Return:
        (1)
            -   True:   Component is schedulable
            -   False:  Component is not schedulable
"""
def dbf_task_EDF(component : Component):
    schedulable = True

    #   Calculate the hyperperiod of the task set (maximum resource demand
    #   in the task set cycle)
    def calculate_hyperperiod(tasks):
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a

        def lcm(a, b):
            if a == 0 or b == 0:
                return 0
            return abs(a * b) // gcd(a, b)

        hyperperiod = tasks[0]._deadline
        for i in range(1, len(tasks)):
            hyperperiod = lcm(hyperperiod, tasks[i]._deadline)

        return float(hyperperiod)
    
    task_set = list(component._sub_components.values())
    hyperperiod = calculate_hyperperiod(task_set)
    
    t_interval = 0.0
    while t_interval <= hyperperiod:
        dbf_edf = 0.0
        for task in task_set:
            dbf_edf += math.ceil((t_interval + task._period - task._deadline)/task._period) * task._wcet

        if dbf_edf > sbf_component(component, t_interval):
            schedulable = False
            break

        t_interval += TIME_UNIT
        
    return schedulable


#   [...]
#   Half-half algorithm implemented inside Component class (see project_types.py)


#   ------------------------------------------------------------------------------------------------------
#   ------------------------------------------------------------------------------------------------------

#   Here below, define simulator and algorithm employed for the simulation.
#   Also define time unit, etcetera.


# Global variable for tasks
tasks: Dict[str, Task] = {}

# Global variable for active jobs
jobs: Dict[str, Job] = {}

# Global variable for components
components: Dict[str, Component] = {}

# Global variable for current time
current_time = 0.0


#   Initialize the jobs for each task
def initialize_jobs():
    # Ensure the list is clean if running more than one simulation
    jobs.clear()

    for task in tasks.values():
        job = Job(
            task._id,
            task._period,
            current_time
        )

        jobs.append(job)


#   This function checks if a task needs to be activated. If a task has met its period, a new
#   job is created for that task, and added to the active jobs list.
def activate_task_jobs():

    for task in tasks.values():
        #   Cast to int to ensure that when working with float time_unit it still catches the period activation
        #   ATTENTION: As of now, this condition only works because of the assumption that time_unit will always be 1
        #   in the context of the exercise
        if jobs.get(task._id) == None and current_time != 0 and int(current_time) % task._period == 0:
            #   Jobs deadline is calculated based on the time when the job is released (current) and the tasks deadline
            new_job = Job(
                task._id,
                current_time + task._period,
                current_time
            )
            jobs[task._id] = new_job



#   For the jobs that are ready, returns the one with the highest priority (i.e. whose corresponding
#   task has the highest priority)
def highest_priority_ready_job(component_root : Component) -> Job:
    result = None

    if component_root._is_terminal:
        for task in component_root._sub_components:
            if jobs.get(task._id) != None:
                result = jobs.get(task._id)
    else:
        component_hp = None

        for component in component_root._sub_components:
            #   Check if the component is still being computed
            if component._required_supply > 0.0:
                component_hp = component
        
        if component_hp != None:
            result = highest_priority_ready_job(component_hp)

    return result



#   This function is used to schedule and rearrange components
#   and tasks by priority for the simulation following the scheduler
#   type specifications
def schedule_components(component_root : Component):
    if not component_root._is_terminal:
        for component in component_root._sub_components:
            schedule_components(component)

    #   Rearrange children by scheduler
    component_root.schedule_component()

    #   Compute deadline by supply bound function
    if component_root._scheduler == "EDF":
        component_root._deadline = sbf_task_EDF(component_root)
    elif component_root._scheduler == "RM":
        component_root._deadline = sbf_task_RM(component_root)



def run_simulation(sim_time: float,time_unit: float):
    #   Set global simulation time to zero
    global current_time

    global TIME_UNIT
    TIME_UNIT = time_unit

    #   Obtain simulation structure
    core_instances = initialize_simulation()

    #   Schedule components and tasks by priority
    for core in core_instances:
        schedule_components(core._root_comp)

        if not core._root_comp.is_schedulable():
            print(f"Error: Tasks from core {core._core_id} not schedulable")
            core_instances.remove(core)


    #   Exit simulation if no cores are schedulable
    if not core_instances:
        print("Core list is empty. Aborting simulation.")
        exit(1)

    # Initialize jobs
    initialize_jobs()

    # Reset the current time if running more than one simulation
    current_time = 0.0

    while current_time <= sim_time:
        activate_task_jobs()

        # Get the highest priority jobs for each core
        for core in core_instances:
            current_job = highest_priority_ready_job(core._root_comp)
            handle_job(current_job)

        current_time += time_unit


#   This function handles the highest priority job for each core
#   and updates the job's execution time for simulation
def handle_job(current_job: Job, time_unit: float):
    def update_component(job):
        task = tasks.get(job._task_id)
        component = components.get(task._component_id)

        #   Every time a job is completed, the component's supply
        #   count is updated (in the end, provided supply = deadline and required supply = 0)
        if job == None:
            component._provided_supply += sbf_component(component, current_time)
        else:
            component._required_supply -= \
                (sbf_component(component, current_time) - component._provided_supply)
            
    
    if current_job:
        if current_job._exec_time <= 0.0:
            # Set the task job as completed
            jobs[current_job._task_id] = None
        else:
            # Decrease the remaining execution time on the job
            jobs[current_job._task_id]._exec_time -= time_unit

        update_component(current_job)



# Function to initialize parameters for the simulation (CSV files)
def initialize_simulation():
    def read_data(file_path):
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the first row (header)
            for row in reader:
                yield row

    core_instances = []
    components_instances = []

    #   Children of Core component
    for row in read_data("/home/caio_iriarte/rt-distributed-systems/project/budgets.csv"):
        components_instances.append( \
        Component(row[0],row[1],float(row[2]),float(row[3]),row[4],True))

        #   Add component to dictionary, mapped to its id
        components[row[0]] = components_instances[-1]

    #   Children of terminal components
    for row in read_data("/home/caio_iriarte/rt-distributed-systems/project/tasks.csv"):
        task_id = row[3]

        #   Add task to corresponding component
        for component in components_instances:
            if component._component_id == task_id:
                task = Task(row[0],float(row[1]),float(row[2]),row[3],row[5])

                # Add task to dictionary, mapped to its id
                tasks[row[0]] = task
                component.add_child(task)

    #   Core ID and speed factor specifications
    for row in read_data("/home/caio_iriarte/rt-distributed-systems/project/architecture.csv"):
        core_inst = Core(row[0],float(row[1]))

        #   Add component instances to core instance
        for component in components_instances:
            if component._core_id == row[0]:
                core_inst._root_comp.add_child(component)
        
        core_instances.append(core_inst)

    return core_instances