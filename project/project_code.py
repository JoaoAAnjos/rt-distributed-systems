import math

from typing import Dict,List
from project_lib import *

#   Return the Supply Bound Function for a component's
#   BDR resource paradigm.
#   >   Parameters:
#       - component: component instance
#       - time: float number that represents time since
#         last resource 
def sbf_component(component : Component, act_time : float):
    delta = component._interface._part_delay
    alfa = component._interface._av_factor
    ret_value = 0.0

    if act_time > delta:
        ret_value = float(alfa*(act_time - delta))
    
    return ret_value
    


#   Definition of the demand bound function for a task set following
#   RM algorithm under the worst case computation time
def dbf_task_RM(component : Component):
    if component._scheduler == "EDF" or (not component._is_terminal):
        return

    # Sort tasks by priority. (Eg: In Rate Monotonic the priority is defined by the period,
    # shorter period = larger priority)
    sorted_tasks_dict = dict(sorted(component._sub_components.items(), key=lambda item: item[1]._priority))

    # Extract values to list to iterate by index easier
    sorted_tasks = list(sorted_tasks_dict.values())

    #   Calculate the total utilization of the task set
    total_supply = 0.0

    # RTA algorithm
    for task in sorted_tasks:
        R = 0  
        R_old = 0
        interference = 0

        while True:
            R_old = R
            R = interference + task._wcet

            # Break if unschedulable
            if R > task._period:
                task._schedulable = False
                break
                       
            # Calculate interference from higher priority tasks
            interference = 0
            for hp_task in sorted_tasks:
                if hp_task._priority < task._priority: # Assuming lower period means higher priority value
                    interference += math.ceil(R / hp_task._period) * hp_task._wcet

            # The task is schedulable and R contains the theoretical wcrt value
            if R <= R_old:
                task._wcrt = math.ceil(R)
                total_supply += task._wcrt
                break

    #   Return the total amount of resource employed by the task set
    return total_supply



#   Definition of the supply bound function for a task set following
#   EDF algorithm under the worst case computation time
def dbf_task_EDF(component : Component):
    if component._scheduler == "RM" or (not component._is_terminal):
        return

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
    total_supply = 0.0

    for task in task_set:
        total_supply += math.floor(hyperperiod / task._period) * task._wcet
        
    return total_supply


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
        component_root._deadline = dbf_task_EDF(component_root)
    elif component_root._scheduler == "RM":
        component_root._deadline = dbf_task_RM(component_root)


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



