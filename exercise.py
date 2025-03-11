#   File to implement three functions/processes:
#       1. VSS Simulator
#       2. RTA Analysis
#       3. (previous to both) Response-time generator for tasks


import numpy as np
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
        #initialize computation time with a random value between bcet and wcet using time_unit intervals
        rd_values = [bcet + i * time_unit for i in range(int((wcet - bcet) // time_unit) + 1)]
        self.comp_time = random.choice(rd_values)

class Job:
    def __init__(self, task_id: str, comp_time: int):
        self.task_id = task_id
        self.exec_time = comp_time
        self.release_time = 0
        self.is_ready = True
    
#   Set of tasks: defined from 'data'
class TaskSet:
    global data, computation_times
    
    def __init__(self):
        self.task_list = [Task() for _ in range(len(data))]
        self.priority_order = []

        temp_priority = data[:,4]

        for i in range(len(data)):
            self.task_list[i].comp_time = computation_times[i]
            self.task_list[i].deadline = data[i,4]
            self.task_list[i].id = i + 1

        #   Get the priority order (RTA)
        sorted_indices = sorted(range(len(temp_priority)), key=lambda i: temp_priority[i])
        self.priority_order.extend(sorted_indices)

#global variable so it can be accessed when creating the tasks
time_unit = 0
#global variable for current time
current_time = 0.0
#global variable for tasks
tasks: Dict[str, Task] = {}
#global variable for jobs
jobs: List[Job] = []

computation_times = []

"""
This line will trigger an error with non-numeric values, so we cannot use this due to the first column of the csv (string).
I had to comment the rest of the code that was not related to the simulator because I was getting a lot of errors related to this
line when running the code, and I did not have the time to fix it (and all the other code is referencing it). 
This line I know it will cause errors because of the column with strings, but the rest of the code is probably ok, I just
commented it so I could test the simulator without these compilation errors.

I don't think that the simulator is working 100% correctly at the moment, but I haven't been able to figure out whats wrong.
However, I believe this implementation should be correct for the most part, and only needs small changes to work ok.

UPDATE: uncommented this since I realized this will actually work, but I had to change data is loaded into here, or else it will have
conflicts when launching vss_main, since it takes no sys args. This is just a temp solution, and the code itself is still broken by
my changes, but I won't change anything else until further discussion
"""
data = None

"""
Responsible for handling the simulation is run using the information contained on the specified file
"""
def run_vss(file_name: str, sim_time: int, time_unit: float):
    global current_time

    print("Running simulation for " + file_name)

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

    #output the results to the txt file
    with open("results.txt", "w") as file:
        file.write("Simulation results for application model in " + file_name + "\n")

        for key, value in tasks.items():
            file.write(key + ": " + str(value.wcrt) + "\n")

        file.write("\n\n")

    print("Simulation complete. Results have been outputed to results.txt")
    

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
            task.id,
            task.comp_time
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
                
                a = current_time
                b = 2
                #cast to int to ensure that when working with float time_unit it still catches the period activation
                if int(current_time)%task.period == 0:
                    #activate task job. Reset the values relevant for job execution
                    job.is_ready = True
                    job.exec_time = task.comp_time
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

def gen_random_comp():
    global data

    for i in range(len(data)):
        if int(data[i,1]) == int(data[i,0]):
            computation_times.append(int(data[i,1]))
        else:
            #Switched the values here compared to main because you are starting at WCET and stoping at BECT which outputs an error
            computation_times.append(random.randrange(int(data[i,0]),int(data[i,1]),1))
    

def RTA_analysis(set):
    wcrt = []
    interference = 0

    #   RTA algorithm
    for i in range(len(set.priority_order)):
        task = set.priority_order[i]
        ri = set.task_list[task].comp_time / (1 - interference)

        if ri > set.task_list[task].deadline:
            wcrt.append(math.ceil(-1.0))
            return wcrt
        
        wcrt.append(math.ceil(ri))
        interference += (set.task_list[task].comp_time/set.task_list[task].deadline)
    return wcrt

def run_RTA(input):
    global data
    data = input
    random.seed()
    gen_random_comp()

    #   Set creation
    set1 = TaskSet()

    #   RTA call
    wcrt_rta = RTA_analysis(set1)
    print(wcrt_rta)
