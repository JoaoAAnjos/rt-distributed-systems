import pandas as pd
import random
import math

from typing import Dict,List

class Task:
    def __init__(self, id: str, wcet: int, bcet: int, period: int, deadline: int, priority: int):
        self.id = id
        self.wcet = wcet
        self.bcet = bcet
        self.period = period
        self.deadline = deadline
        self.priority = priority
        self.schedulable = True
        # Initialize it as -1 since this will be calculated by the simulator
        self.wcrt = -1

class Job:
    def __init__(self, task_id: str, deadline: int, release_time: int):
        self.task_id = task_id
        self.deadline = deadline
        self.release_time = release_time
        self.exec_time = gen_random_comp_time(self)


# Global variable so it can be accessed when creating the tasks
time_unit = 0
# Global variable for current time
current_time = 0.0
# Global variable for tasks
tasks: Dict[str, Task] = {}
# Global variable for active jobs
jobs: List[Job] = []

"""
Responsible for handling the VSS simulation is run using the information contained on the specified file
"""
def run_vss(file_name: str, sim_time: int, time_unit: float):
    global current_time

    print("Running VSS simulation for " + file_name)

    # Set the global variable for the time_unit
    globals()["time_unit"] = time_unit

    # Create tasks from csv
    initialize_tasks(pd.read_csv(file_name))

    # Initialize jobs
    initialize_jobs()

    # Reset the current time if running more than one simulation
    current_time = 0.0

    while current_time <= sim_time:
        activate_task_jobs()

        # Get the highest priority task at this moment
        current_job = highest_priority_ready_job()

        if current_job:
            
            # Check if job has finished execution
            if current_job.exec_time <= 0:
               
                task = tasks.get(current_job.task_id)

                # Calculate response time 
                response_time = current_time - current_job.release_time

                # If task hasnt been considered unschedulable before, and current time is lesser or equal to the deadline, save WCRT value
                if task.schedulable and current_time <= current_job.deadline:

                    if task.wcrt < response_time:
                        task.wcrt = response_time
                # Else, set as unschedulable and record the WCRT value of when it misses the deadline 
                # (only do this for tasks who aren't sc)
                elif task.schedulable:
                    task.schedulable = False
                    task.wcrt = response_time


                # Set the task job as completed
                jobs.remove(current_job)
        
            # Decrease the remaining execution time on the job
            current_job.exec_time -= time_unit

        current_time += time_unit

    # Append the results to the txt file
    output_results("VSS", file_name)    
    

"""
Initializes the global variable 'tasks' from the csv information
"""
def initialize_tasks(df: pd.DataFrame):
    # Ensure the list is clean if running more than one simulation
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
        
        # Add to dictionary, mapped to its id
        tasks[row["Task"]] = task

        
"""
Initialize the jobs for each task
"""
def initialize_jobs():
    # Ensure the list is clean if running more than one simulation
    jobs.clear()

    for task in tasks.values():
        job = Job(
            task.id,
            task.deadline,
            current_time
        )

        jobs.append(job)


"""
This function checks if a task needs to be activated. If a task has met its period, a new
job is created for that task, and added to the active jobs list.
"""
def activate_task_jobs():

    for task in tasks.values():

        # Cast to int to ensure that when working with float time_unit it still catches the period activation
        # ATTENTION: As of now, this condition only works because of the assumption that time_unit will always be 1 in the context of the exercise
        if current_time != 0 and int(current_time) % task.period == 0:
            job = Job(
                task.id,
                # Jobs deadline is calculated based on the time when the job is released (current) and the tasks deadline
                current_time + task.deadline,
                current_time
            )

            jobs.append(job)


"""
For the jobs that are ready, returns the one with the highest priority (i.e. whose corresponding task has the
highest priority)
"""
def highest_priority_ready_job() -> Job:
    result = None
    max_priority = math.inf

    for j in jobs:

        task = tasks.get(j.task_id)

        # This seems misleading, but a smaller number in this column means a higher priority
        if task.priority < max_priority:
            result = j
            max_priority = task.priority 

    return result


"""
Generates random computation time for a job
"""
def gen_random_comp_time(job : Job) -> float:
    # Get the corresponding task
    task = tasks.get(job.task_id)
    
    return gen_random_comp_time_task(task)
    

"""
Generates random computation time for a task
"""
def gen_random_comp_time_task(task: Task) -> float:
    # Calculate computation time with a random value between bcet and wcet using time_unit intervals
    rd_values = [task.bcet + i * time_unit for i in range(int((task.wcet - task.bcet) // time_unit) + 1)]
    return random.choice(rd_values)


"""
Responsible for handling the RTA simulation is run using the information contained on the specified file
"""
def run_rta(file_name: str):
    print("Running RTA simulation for " + file_name)
    
    # Create tasks from csv
    initialize_tasks(pd.read_csv(file_name))

    # Sort tasks by priority. (Eg: In Rate Monotonic the priority is defined by the period, shorter period = larger priority)
    sorted_tasks_dict = dict(sorted(tasks.items(), key=lambda item: item[1].priority))

    # Extract values to list to iterate by index easier
    sorted_tasks = list(sorted_tasks_dict.values())

    # RTA algorithm
    for i in range(len(sorted_tasks)):

        task = sorted_tasks[i]

        R = 0  
        R_old = 0
        interference = 0

        while True:
            R_old = R
            R = interference + task.wcet

            # Break if unschedulable
            if R > task.deadline:
                task.schedulable = False
                break
                       
            # Calculate interference from higher priority tasks
            interference = 0

            for j in range(i):
                interference += math.ceil(R / sorted_tasks[j].period) * sorted_tasks[j].wcet

            # The task is schedulable and R contains the theoretical wcrt value
            if R <= R_old: 
                break

        task.wcrt = math.ceil(R)

    # Append the results to the txt file
    output_results("RTA", file_name)


"""
Outputs the results of the analysis, or the simulation, into a txt file depending on the results origin (either RTA or VSS),
printing at the end of the results if the task set is schedulable or unschedulable.
"""
def output_results(res_origin: str, app_model: str):
    output_file = "results-" + res_origin + ".txt"

    schedulable_taskset = True

    #Append the results to the txt file
    with open(output_file, "a") as file:
        file.write(res_origin +" Simulation results for application model in " + app_model + "\n\n")

        for key, value in tasks.items():
            file.write("Task_id: "+ key + " | WCRT : " + str(value.wcrt) + " | Deadline: " + 
                       str(value.deadline) + " | Schedulable: "+str(value.schedulable)+"\n")
            
            # Determine if task set is schedulable or unschedulable (a single unschedulable task makes the set unschedulable as a whole)
            if ( schedulable_taskset and (not value.schedulable or value.wcrt == -1)):
                schedulable_taskset = False
            
        
        sched_result = "schedulable" if schedulable_taskset else "unschedulable" 

        file.write("\nAccording to the results, this taskset is " + sched_result + "\n")

        file.write("\n\n")      
