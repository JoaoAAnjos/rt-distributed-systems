from source.simulator import initialize_csv_data, run_simulation
from source.simulator import component_task_exec_registry, components_registry
from source.simulator import tasks_registry, cores_registry
import os
import csv


RESULTS_CSV_FILENAME = "output/results_simulator.csv"

#   ------------------------------------------------------------------------------------
#   Simulation Results Output
#   ------------------------------------------------------------------------------------

"""
    Cleans the results CSV file for a new run.
"""
def delete_results_csv_file(filename=RESULTS_CSV_FILENAME):
    file_exists = os.path.isfile(filename)

    if file_exists:
        os.remove(filename)

"""
    Calculates results and saves them to a CSV file.
"""
def save_results_to_csv(filename=RESULTS_CSV_FILENAME):
    #   Determine if the file exists to decide whether to write a header
    file_exists = os.path.isfile(filename)

    rows_to_write = []

    #   Iterate through components to determine component_schedulable
    #   This requires iterating tasks per component first
    component_schedulability_map = {}
    for comp_id, task_exec_list in component_task_exec_registry.items():
        #   Should not happen if initialized correctly
        if not task_exec_list:
            component_schedulability_map[comp_id] = True # Or False, depends on definition
            continue
        
        all_tasks_in_comp_schedulable = True
        for task_exec in task_exec_list:
            #   A task is considered schedulable by the simulator if it missed no deadlines
            #   or if a more lenient definition is used (e.g. some missed deadlines are acceptable
            #   for soft tasks). For this implementation, assumed schedulable = 0 deadlines missed.
            if task_exec.deadlines_missed > 0:
                all_tasks_in_comp_schedulable = False
                break
        component_schedulability_map[comp_id] = all_tasks_in_comp_schedulable

    #   Now prepare rows for CSV
    for comp_id, task_exec_list in component_task_exec_registry.items():
        #   Get the original Component object
        component_obj = components_registry.get(comp_id)
        if not component_obj:
            print(f"Warning: Component {comp_id} not found in components_registry during results saving.")
            continue

        #   Ensure this component actually ran on the target_core_id for which run_simulation was called
        #   This check is a bit indirect here, as components are assigned to cores, and
        #   component_task_exec_registry is global. A better way might be to pass the core's tasks
        #   directly.
        #   For now, we assume component_task_exec_registry is populated relevant to the last
        #   run_simulation call.
        #   If component_obj._core_id != target_core_id: --> This check assumes Component class has 
        #   _core_id --> continue

        for task_exec in task_exec_list:
            #   Get original Task object for its name
            task_obj = tasks_registry.get(task_exec.id)
            if not task_obj:
                print(f"Warning: Task {task_exec.id} not found in tasks_registry during results saving.")
                #   Fallback to ID
                task_name = task_exec.id
            else:
                task_name = task_obj._id

            task_schedulable_by_sim = True if task_exec.deadlines_missed == 0 else False
            
            avg_response_time = 0.0
            max_response_time = 0.0
            if task_exec.response_times:
                avg_response_time = sum(task_exec.response_times) / len(task_exec.response_times)
                max_response_time = max(task_exec.response_times)

            component_schedulable = True if component_schedulability_map.get(comp_id, False) else False
            core_obj = cores_registry.get(component_obj._core_id)

            rows_to_write.append({
                'task_name': task_name,
                'component_id': comp_id,

                #   Use the core_id for which simulation was run
                'Core_id': core_obj._core_id,
                'task_schedulable': task_schedulable_by_sim,
                'avg_response_time': f"{avg_response_time:.4f}",
                'max_response_time': f"{max_response_time:.4f}",
                'component_schedulable': component_schedulable,
                'deadlines_missed': task_exec.deadlines_missed,
                'deadlines_met': task_exec.deadlines_met
            })

    if not rows_to_write:
        print(f"No results to write for core {core_obj._core_id}.")
        return

    try:
        with open(filename, 'a' if file_exists else 'w', newline='') as csvfile:
            fieldnames = [
                'task_name', 'component_id', 'Core_id', 'task_schedulable',
                'avg_response_time', 'max_response_time', 'component_schedulable',
                'deadlines_missed', 'deadlines_met'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            
            for row in rows_to_write:
                writer.writerow(row)
        print(f"Results for core {core_obj._core_id}\
              {'appended to ' if file_exists else 'written to '}{filename}")
    except IOError:
        print(f"Error: Could not write to file {filename}")



# --------------------------------------------------------------------------------------
# -------------------------- Main Execution for ADAS Simulator -------------------------
# --------------------------------------------------------------------------------------


if __name__ == "__main__":
    # --- Initialize data using the library ---
    print("Initializing data from CSV files...")
    initialize_csv_data()
    print("Data initialization complete.")

    #delete the results csv file from previous run
    delete_results_csv_file()

    #ask for simulation time and store it
    #sim_time = int(input("Input the desired simulation time: "))

    for core in cores_registry:
        run_simulation(core, 100000.0)
        save_results_to_csv()