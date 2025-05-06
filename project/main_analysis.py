from analysis import dbf_component_EDF, dbf_component_RM
from project_lib import cores, initialize_data



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

    #   Check if cores are schedulable
    for core in cores.values():
        if not core.simple_scheduler():
            system_schedulable = False

            for component in core.root_comp._sub_components:
                unschedulable_components.append(component._component_id)

            #   Remove core from cores
            del cores[core._core_id]

    #   Check if components are schedulable
    for core in cores.values():
        for component in core.root_comp._sub_components:
            if component._scheduler == "RM":
                schedulable, _ = dbf_component_RM(component)
            elif component._scheduler == "EDF":
                schedulable = dbf_component_EDF(component)

            if not schedulable:
                system_schedulable = False
                unschedulable_components.append(component._component_id)
            else:
                schedulable_components.append(component._component_id)

    return system_schedulable, unschedulable_components, schedulable_components


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
        print("Unschedulable components:\n", unschedulable_components)

    if schedulable_components:
        print("Schedulable components:\n", schedulable_components)

