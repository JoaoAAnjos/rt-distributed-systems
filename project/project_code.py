from project_types import Component,Core,Task,Job
import math


#   Constant representing last time some resource was
#   provided for component/s:
time_supply = 0.0


#   Return the Supply Bound Function for a component's
#   BDR resource paradigm.
#   >   Parameters:
#       - component: component instance
#       - time: float number that represents time since
#         last resource 
def sbf_component(component : Component, act_time : float):
    global time_supply

    delta = component._interface._part_delay
    alfa = component._interface._av_factor

    if (act_time - time_supply) > delta:
        return float(alfa*(act_time - (delta + time_supply)))
    else:
        return 0.0
    


#   Definition of the supply bound function for a task set following
#   RM algorithm under the worst case computation time
def sbf_task_RM(component : Component):
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
#   RM algorithm under the worst case computation time
def sbf_task_EDF(component : Component, time_interval : float):
    if component._scheduler == "RM" or (not component._is_terminal):
        return
    
    task_set = list(component._sub_components.values())
    total_supply = 0.0

    for task in task_set:
        total_supply += math.floor(time_interval / task._period) * task._wcet
        
    return total_supply


#   [...]
#   Half-half algorithm implemented inside Component class (see project_types.py)


#   ------------------------------------------------------------------------------------------------------
#   ------------------------------------------------------------------------------------------------------

#   Here below, define simulator and algorithm employed for the simulation.
#   Also define time unit, etcetera.


TIME_UNIT = 1.0