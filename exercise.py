import pandas as pd
import random
import math

from typing import Dict,List

class SimulationLogger:
    def __init__(self, log_file="simulation_log.txt"):
        self.log_file = log_file
        with open(self.log_file, 'w') as f:
            f.write("=== Simulation Debug Log ===\n\n")

    def log(self, message):
        with open(self.log_file, 'a') as f:
            f.write(message + "\n")

    def log_time_step(self, current_time):
        self.log(f"\n=== Time: {current_time:.2f} ===")

    def log_ready_jobs(self, ready_jobs, tasks, current_time):
        self.log(f"\nReady jobs at {current_time:.2f}:")
        for j in ready_jobs:
            self.log(
                f"  Task {j.task_id} (Prio={tasks[j.task_id].priority}): "
                f"ET_left={j.exec_time:.2f}"
            )

    def log_job_execution(self, current_job, tasks):
        self.log(
            f"\nExecuting: Task {current_job.task_id} "
            f"(Prio={tasks[current_job.task_id].priority})"
        )
        self.log(f"  Remaining ET: {current_job.exec_time:.2f}")

    def log_job_completion(self, current_job, current_time, deadline_met, wcrt):
        response_time = current_time - current_job.release_time
        if deadline_met:
            wcrt_str = f"{wcrt:.2f}" if wcrt is not None else "N/A"
            self.log(
                f"  COMPLETED ON TIME: RT={response_time:.2f}, "
                f"WCRT={wcrt_str}"
            )
        else:
            self.log(
                f"  DEADLINE MISSED! (Deadline={current_job.abs_deadline:.2f}, "
                f"Completion={current_time:.2f})"
            )

    def log_new_job(self, task_id, release_time):
        self.log(f"  NEW JOB ACTIVATED: Task {task_id} at {release_time:.2f}")
        
class Task:
    def __init__(self, id: str, wcet: int, bcet: int, period: int, deadline: int, priority: int):
        self.id = id
        self.wcet = wcet
        self.bcet = bcet
        self.period = period
        self.deadline = deadline
        self.priority = priority
        self.schedulable = True
        #initialize it as -1 since this will be calculated by the simulator
        self.wcrt = -1

class Job:
    def __init__(self, task_id: str, release_time: float):
        self.task_id = task_id
        self.release_time = release_time
        self.is_ready = True
        self.exec_time = 0
        self.abs_deadline = 0


#global variable so it can be accessed when creating the tasks
time_unit = 0
#global variable for current time
current_time = 0.0
#global variable for tasks
tasks: Dict[str, Task] = {}
#global variable for jobs
jobs: List[Job] = []
# Create a debugger instance
logger = SimulationLogger()

"""
Responsible for handling the VSS simulation is run using the information contained on the specified file
"""
def run_vss(file_name: str, sim_time: int, time_unit: float):
    global current_time

    print("Running VSS simulation for " + file_name)

    #set the global variable for the time_unit
    globals()["time_unit"] = time_unit

    #create tasks from csv
    initialize_tasks(pd.read_csv(file_name))

    #initialize jobs
    initialize_jobs()

    #reset the current time if running more than one simulation
    current_time = 0.0

    while current_time <= sim_time:
        logger.log_time_step(current_time)
        
        activate_task_jobs()
        
        ready_jobs = [j for j in jobs if j.is_ready and j.release_time <= current_time]
        logger.log_ready_jobs(ready_jobs, tasks, current_time)
        
        if ready_jobs:
            current_job = min(ready_jobs, key=lambda j: tasks[j.task_id].priority)
            logger.log_job_execution(current_job, tasks)
            
            current_job.exec_time -= time_unit
            
            if current_job.exec_time <= 0:
                response_time = current_time - current_job.release_time
                task = tasks[current_job.task_id]
                deadline_met = current_time <= current_job.abs_deadline
                
                if task.schedulable and deadline_met:
                    task.wcrt = max(task.wcrt, response_time)
                elif task.schedulable:
                    task.schedulable = False
                    task.wcrt = response_time
                    
                logger.log_job_completion(
                    current_job, current_time, deadline_met, task.wcrt
                )
                current_job.is_ready = False
            
        current_time += time_unit

    # Final schedulability check
    for task in tasks.values():
        task.schedulable = (task.wcrt != -1) and (task.wcrt <= task.deadline)

    output_results("VSS", file_name)
    

"""
Initializes the global variable 'tasks' from the csv information
"""
def initialize_tasks(df: pd.DataFrame):
    #ensure the list is clean if running more than one simulation
    tasks.clear()

    for index, row in df.iterrows():
        task = Task(
            row["Task"],
            row["WCET"],
            row["BCET"],
            row["Period"],
            row["Deadline"],
            row["Priority"]    
        )
        
        #add to dictionary, mapped to its id
        tasks[row["Task"]] = task

        
"""
Initialize the jobs for each task
"""
def initialize_jobs():
    #ensure the list is clean if running more than one simulation
    jobs.clear()
    for task in tasks.values():
        # Only create the first job for each task
        job = Job(task.id, 0)  # First release at time 0
        job.abs_deadline = task.deadline  # Relative deadline
        job.exec_time = gen_random_comp_time_task(task)
        jobs.append(job)


"""
This function checks if a task needs to be activated. If a job has been executed inside its deadline, 
it needs to be activated again when its period is reached, so it can be executed again. In the context of
this code, this is achieved by setting the is_ready flag inside the task's job to True, so it can be picked
up when assembling the ready jobs list. Only jobs that have been executed inside their deadline need this,
as jobs who have not still need to finish their execution, so they still have the flag is_ready set to true
"""
def activate_task_jobs():
    for job in list(jobs):
        if not job.is_ready:
            task = tasks[job.task_id]
            # Reactivate at next period if current time matches activation point
            if abs(current_time - (job.release_time + task.period)) < 1e-6:
                logger.log_new_job(task.id, current_time)
                new_job = Job(task.id, current_time)
                new_job.abs_deadline = current_time + task.deadline
                new_job.exec_time = gen_random_comp_time_task(task)
                jobs.append(new_job)

"""
Generates random computation time for a job
"""
def gen_random_comp_time(job : Job) -> float:
    #get the corresponding task
    task = tasks.get(job.task_id)
    
    return gen_random_comp_time_task(task)
    

"""
Generates random computation time for a task
"""
def gen_random_comp_time_task(task: Task) -> float:
    #calculate computation time with a random value between bcet and wcet using time_unit intervals
    rd_values = [task.bcet + i * time_unit for i in range(int((task.wcet - task.bcet) // time_unit) + 1)]
    return random.choice(rd_values)

"""
Responsible for handling the RTA simulation is run using the information contained on the specified file
"""
def run_rta(file_name: str):
    print("Running RTA simulation for " + file_name)
    
    #create tasks from csv
    initialize_tasks(pd.read_csv(file_name))

    #sort tasks by priority. (Eg: In Rate Monotonic the priority is defined by the period, shorter period = larger priority)
    sorted_tasks_dict = dict(sorted(tasks.items(), key=lambda item: item[1].priority))

    #Extract values to list to iterate by index easier
    sorted_tasks = list(sorted_tasks_dict.values())

    #RTA algorithm
    for i in range(len(sorted_tasks)):

        task = sorted_tasks[i]

        R = 0  
        R_old = 0
        interference = 0

        while True:
            R_old = R
            R = interference + task.wcet

            #Break if unschedulable
            if R > task.deadline:
                task.schedulable = False
                break
                       
            #Calculate interference from higher priority tasks
            interference = 0

            for j in range(i): 
                interference += math.ceil(R / sorted_tasks[j].period) * sorted_tasks[j].wcet

            #The task is schedulable and R contains the theoretical wcrt value
            if R <= R_old: 
                break

        task.wcrt = math.ceil(R)

    #append the results to the txt file
    output_results("RTA", file_name)

"""
Outputs the results of the analysis, or the simulation, into a txt file depending on the results origin (either RTA or VSS),
printing at the end of the results if the task set is schedulable or unschedulable.
"""
def output_results(res_origin: str, app_model: str):
    output_file = "results-" + res_origin + ".txt"

    schedulable_taskset = True

    #append the results to the txt file
    with open(output_file, "a") as file:
        file.write(res_origin +" Simulation results for application model in " + app_model + "\n\n")

        for key, value in tasks.items():
            file.write("Task_id: "+ key + " | WCRT : " + str(value.wcrt) + " | Deadline: " + 
                       str(value.deadline) + " | Schedulable: "+str(value.schedulable)+"\n")
            if ( schedulable_taskset and (not value.schedulable or value.wcrt == -1)):
                schedulable_taskset = False
            
        
        sched_result = "schedulable" if schedulable_taskset else "unschedulable" 

        file.write("\nAccording to the results, this taskset is " + sched_result + "\n")

        file.write("\n\n")      
