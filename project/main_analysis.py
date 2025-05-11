from source.analysis import dbf_component_EDF, dbf_component_RM
from source.project_lib import cores_registry, initialize_data, Scheduler
import os


ANALYSIS_OUTPUT = "output/results_analysis.csv"


"""
    Analyse the entire cores and components distribution

    >   Return:
        (1)
            -   True:   System is schedulable
            -   False:  System is not schedulable
        (2)
            -   Array of unschedulable components if false
"""
def analyse_system():
    system_schedulable = True
    unschedulable_components = []
    schedulable_components = []
    
    initialize_data()

    #   Clear and initialize CSV results file
    with open(ANALYSIS_OUTPUT, "w") as f:
        f.write("Task_ID,WCET,Priority,Task_Schedulable,Component_ID,Component_Schedulable\n")
        f.write("=========================================================================\n")

    #   Make a copy of cores registry
    cores_register = cores_registry.copy()

    #   Check if cores are schedulable
    for core in cores_register.values():
        if not core.simple_scheduler():
            system_schedulable = False

            for component in core.root_comp.children:
                unschedulable_components.append(component._component_id)

            #   Remove core from cores
            del cores_registry[core._core_id]

    #   Check if components are schedulable
    for core in cores_registry.values():
        for component in core.root_comp.children:
            sorted_tasks = []
            if component._scheduler == Scheduler.RM:
                sorted_tasks = sorted(component.children, \
                                      key=lambda _task: _task._priority, reverse=False)
                schedulable, schedulable_tasks = dbf_component_RM(component)
            elif component._scheduler == Scheduler.EDF:
                sorted_tasks = component.children
                schedulable, schedulable_tasks = dbf_component_EDF(component)

            #   Write results to CSV file
            write_results(sorted_tasks,schedulable_tasks,component,schedulable)

            if not schedulable:
                system_schedulable = False
                unschedulable_components.append(component._component_id)
            else:
                schedulable_components.append(component._component_id)

    return system_schedulable, unschedulable_components, schedulable_components



"""
    Write results to CSV file. Receive the sorted tasks, schedulable tasks,
    component and schedulable status of the component.

    >   Return:
        -   None
"""
def write_results(sorted_tasks,schedulable_tasks,component,schedulable):
    with open(ANALYSIS_OUTPUT, "a") as f:
        for i, task in enumerate(sorted_tasks):
            f.write(f"{task._id},{task._wcet:.4f},{task._priority},{schedulable_tasks[i]},"
                    f"{component._component_id},{schedulable}\n")


#   ------------------------------------------------------------------------------------
#   Main function

if __name__ == "__main__":
    #   Analyse the entire components distribution
    schedulable, unschedulable_components, schedulable_components = analyse_system()

    #   Print results
    if schedulable:
        print("\nSystem is completely schedulable. All cores' components are schedulable.")
    else:
        print("\nSystem is not completely schedulable.")
        print("\nUnschedulable components:\n", unschedulable_components)

    if schedulable_components:
        print("\nSchedulable components:\n", schedulable_components)

