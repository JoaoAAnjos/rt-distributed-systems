#   File to implement three functions/processes:
#       1. VSS Simulator
#       2. RTA Analysis
#       3. (previous to both) Response-time generator for tasks


import numpy as np
import random
import sys
import math


computation_times = []
time_unit = 1
data = np.loadtxt(sys.argv[1], delimiter=",", skiprows=1,usecols=range(1, 6))


class Task:
    def __init__(self):
        self.comp_time = 0
        self.deadline = 0
        self.comp_count = 0
        self.jobs = 0
        self.id = ""


#   Set of tasks: defined from 'data'
class TaskSet:
    global data, computation_times
    
    def __init__(self):
        self.task_list = [Task() for _ in range(len(data))]
        self.priority_order = []

        temp_priority = data[:,4]

        for i in range(len(data)):
            self.task_list[i].comp_time = computation_times[i]
            self.task_list[i].deadline = data[i,3]
            self.task_list[i].id = f'T{i + 1}'

        #   Get the priority order (RTA)
        sorted_indices = sorted(range(len(temp_priority)), key=lambda i: temp_priority[i])
        self.priority_order.extend(sorted_indices)



def gen_random_comp():
    global data

    for i in range(len(data)):
        if int(data[i,1]) == int(data[i,0]):
            computation_times.append(int(data[i,1]))
        else:
            computation_times.append(random.randrange(int(data[i,1]),int(data[i,0]),1))

    

def RTA_analysis(set):
    wcrt = []
    interference = 0

    #   RTA algorithm
    for i in range(len(set.priority_order)):
        task = set.priority_order[i]

        ri = set.task_list[task].comp_time / (1 - interference)
        wcrt.append(math.ceil(ri))

        interference += (set.task_list[task].comp_time/set.task_list[task].deadline)
    return wcrt


def VSS_simulator(set):
    b = 4
    #   VSS simulator



if __name__ == '__main__':
    random.seed()
    gen_random_comp()

    #   Set creation
    set1 = TaskSet()

    #   VSS call
    #wcrt_vss = VSS_simulator(set1)
    #print(wcrt_vss)

    #   RTA call
    wcrt_rta = RTA_analysis(set1)
    print(wcrt_rta)
