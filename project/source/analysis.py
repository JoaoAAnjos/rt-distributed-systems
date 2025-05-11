import math
from source.project_lib import *


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
    schedulable = True
    
    sorted_tasks = sorted(component.children, key=lambda _task: _task._priority, reverse=False)
    schedulable_tasks = [False] * len(sorted_tasks)

    for i, task in enumerate(sorted_tasks):
        t_interval = 0.0

        while t_interval <= task._period and (schedulable_tasks[i] == False):
            dbf_task = dbf_task_RM(sorted_tasks, task, t_interval)

            if dbf_task <= sbf_component(component, t_interval):
                schedulable_tasks[i] = True

            t_interval += 1

    for i in range(len(schedulable_tasks)):
        if schedulable_tasks[i] == False:
            schedulable = False
            break

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
    
    
    task_set = component.children
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
        
    schedulable_tasks = [schedulable] * len(component.children)
    return schedulable, schedulable_tasks


#   [...]
#   Half-half algorithm implemented inside Component class (see project_types.py)


#   ------------------------------------------------------------------------------------------------------
#   ------------------------------------------------------------------------------------------------------