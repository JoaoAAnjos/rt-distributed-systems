#   File to implement three functions/processes:
#       1. VSS Simulator
#       2. RTA Analysis
#       3. (previous to both) Response-time generator for tasks


import numpy as np
import random
import sys


computation_times = []
time_unit = 1
data = np.loadtxt(sys.argv[1], delimiter=",", skiprows=1)


class Task:
    def __init__(self):
        self.comp_time = 0
        self.deadline = 0
        self.comp_count = 0
        self.jobs = 0


#   Set of tasks: defined from 'data'
class TaskSet:
    global data, computation_times
    
    def __init__(self, data):
        self.task_list = [Task() for _ in range(len(data))]

        for i in range(len(data)):
            self.task_list[i].comp_time = computation_times[i]
            self.task_list[i].deadline = data[i,4]



def gen_random_comp():
    global data

    for i in len(data):
        computation_times.append(random.randrange(data[i,1],data[i,2],1))
    

def RTA_analysis(set):
    wcrt = []

    #   RTA algorithm
    for task in set:
        

    return wcrt


def VSS_simulator(set):
    b = 4
    #   VSS simulator



if __name__ == '__main__':
    set1 = TaskSet()

