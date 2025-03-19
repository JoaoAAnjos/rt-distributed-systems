#   File to implement three functions/processes:
#       1. VSS Simulator
#       2. RTA Analysis
#       3. (previous to both) Response-time generator for tasks
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
        #initialize it as -1 since this will be calculated by the simulator
        self.wcrt = -1

class Job:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.release_time = 0
        self.is_ready = True
        self.exec_time = gen_random_comp_time(self)


#global variable so it can be accessed when creating the tasks
time_unit = 0
#global variable for current time
current_time = 0.0
#global variable for tasks
tasks: Dict[str, Task] = {}
#global variable for jobs
jobs: List[Job] = []

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

    #I've done the loop only with the first condition the teacher suggested because I still do not
    #understand completely the second part of the loop. Please get some clarification from the TA's
    while current_time <= sim_time:
        activate_task_jobs()

        current_job = highest_priority_ready_job()

        if current_job:
            #set the release time if it hasn't been set yet
            if current_job.release_time == 0:
                current_job.release_time = current_time
            
            #check if job has finished execution
            if current_job.exec_time <= 0:
                #calculate response time and save it if its the worst observed
                response_time = current_time - current_job.release_time
                task = tasks.get(current_job.task_id)
                
                if task.wcrt < response_time:
                    task.wcrt = response_time
                
                #set the task as completed
                current_job.is_ready = False

            #decrease the remaining execution time on the job
            current_job.exec_time -= time_unit
        
        current_time += time_unit

    #append the results to the txt file
    with open("results-VSS.txt", "a") as file:
        file.write("VSS Simulation results for application model in " + file_name + "\n")

        for key, value in tasks.items():
            file.write(key + ": " + str(value.wcrt) + "\n")

        file.write("\n\n")    
    

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
    jobs.clear

    for task in tasks.values():
        job = Job(
            task.id
        )

        jobs.append(job)


"""
This function checks if a task needs to be activated. If a job has been executed inside its deadline, 
it needs to be activated again when its period is reached, so it can be executed again. In the context of
this code, this is achieved by setting the is_ready flag inside the task's job to True, so it can be picked
up when assembling the ready jobs list. Only jobs that have been executed inside their deadline need this,
as jobs who have not still need to finish their execution, so they still have the flag is_ready set to true
(at least I think so, maybe confirm with TA's).
"""
def activate_task_jobs():
    for job in jobs:

        if not job.is_ready:

            #grab corresponding task
            task = tasks.get(job.task_id)

            if task:
                
                #cast to int to ensure that when working with float time_unit it still catches the period activation
                if int(current_time)%task.period == 0:
                    #activate task job. Reset the values relevant for job execution
                    job.is_ready = True
                    job.exec_time = gen_random_comp_time(job)
                    job.release_time = 0
            else:
                print("Corresponding Task for the job was not found. Something is wrong in the simulators execution.")


"""
For the jobs that are ready, returns the one with the highest priority (i.e. whose corresponding task has the
highest priority)
"""
def highest_priority_ready_job() -> Job:
    result = None
    max_priority = 0

    for j in jobs:

        if j.is_ready:
            task = tasks.get(j.task_id)

            if task.priority > max_priority:
                result = j
                max_priority = task.priority 

    return result

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

    #sort tasks by priority. In Rate Monotonic the priority is defined by the period (shorter period = larger priority)
    #Question for the TA's: how to account for other priorities
    sorted_tasks_dict = dict(sorted(tasks.items(), key=lambda item: item[1].period))

    #Extract values to list to iterate by index easier
    sorted_tasks = list(sorted_tasks_dict.values())

     #   RTA algorithm
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
                R = -1
                break
                       
            #Calculate interference from higher priority tasks
            interference = 0

            for j in range(i): 
                interference += math.ceil(R / sorted_tasks[j].period) * sorted_tasks[j].wcet

            #The task is schedulable and R contains the theoretical wcrt value
            if R == R_old: 
                break

        task.wcrt = math.ceil(R)

    #append the results to the txt file
    with open("results-RTA.txt", "a") as file:
        file.write("RTA Simulation results for application model in " + file_name + "\n")

        for key, value in tasks.items():
            file.write(key + ": " + str(value.wcrt) + "\n")

        file.write("\n\n")    
