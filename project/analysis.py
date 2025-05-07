import math
from project_lib import *


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

    if t_interval >= delta:
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
    schedulable = False
    
    sorted_tasks = sorted(component._sub_components, key=lambda _task: _task._priority, reverse=False)
    schedulable_tasks = [False] * len(sorted_tasks)

    for i, task in enumerate(sorted_tasks):
        t_interval = 0.0

        while t_interval <= task._period and (schedulable == False):
            dbf_task = dbf_task_RM(sorted_tasks, task, t_interval)

            if dbf_task <= sbf_component(component, t_interval):
                schedulable = True
                schedulable_tasks[i] = True

            t_interval += 1

    return schedulable, schedulable_tasks



"""
    Demand bound function for a component which has EDF as
    scheduling algorithm.

    >   Return:
        (1)
            -   True:   Component is schedulable
            -   False:  Component is not schedulable
"""
def dbf_component_EDF(component : Component):
    schedulable = True

    #   Calculate the hyperperiod of the task set (maximum resource demand
    #   in the task set cycle)
    def calculate_hyperperiod(tasks):
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a

        def lcm(a, b):
            return abs(a * b) // gcd(a, b) if a and b else 0

        hyperperiod = tasks[0]._period
        for i in range(1, len(tasks)):
            hyperperiod = lcm(hyperperiod, tasks[i]._period)

        return float(hyperperiod)
    
    
    task_set = component._sub_components
    hyperperiod = calculate_hyperperiod(task_set)
    
    t_interval = 0.0
    while t_interval <= hyperperiod:
        dbf_edf = 0.0
        for task in task_set:
            dbf_edf += math.floor((t_interval + task._period - task._deadline)/task._period) * task._wcet

        if dbf_edf > sbf_component(component, t_interval):
            schedulable = False
            break

        t_interval += 1
        
    return schedulable


#   [...]
#   Half-half algorithm implemented inside Component class (see project_types.py)


#   ------------------------------------------------------------------------------------------------------
#   ------------------------------------------------------------------------------------------------------


#   This function checks if a task needs to be activated. If a task has met its period, a new
#   job is created for that task, and added to the active jobs list.
def activate_task_jobs():

    for task in tasks.values():
        #   Cast to int to ensure that when working with float time_unit it still catches the period activation
        #   ATTENTION: As of now, this condition only works because of the assumption that time_unit will always be 1
        #   in the context of the exercise
        if jobs.get(task._id) == None and CURRENT_TIME != 0 and int(CURRENT_TIME) % task._period == 0:
            #   Jobs deadline is calculated based on the time when the job is released (current) and the tasks deadline
            new_job = Job(
                task._id,
                CURRENT_TIME + task._period,
                CURRENT_TIME
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
        component_root._deadline = dbf_component_EDF(component_root)
    elif component_root._scheduler == "RM":
        component_root._deadline = dbf_component_RM(component_root)


#   This function handles the highest priority job for each core
#   and updates the job's execution time for simulation
def handle_job(current_job: Job, time_unit: float):
    def update_component(job):
        task = tasks.get(job._task_id)
        component = components.get(task._component_id)

        #   Every time a job is completed, the component's supply
        #   count is updated (in the end, provided supply = deadline and required supply = 0)
        if job == None:
            component._provided_supply += sbf_component(component, CURRENT_TIME)
        else:
            component._required_supply -= \
                (sbf_component(component, CURRENT_TIME) - component._provided_supply)
            
    
    if current_job:
        if current_job._exec_time <= 0.0:
            # Set the task job as completed
            jobs[current_job._task_id] = None
        else:
            # Decrease the remaining execution time on the job
            jobs[current_job._task_id]._exec_time -= time_unit

        update_component(current_job)



