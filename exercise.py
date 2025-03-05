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


def gen_random_comp():
    global data

    for i in len(data):
        computation_times.append(random.randrange(data[i,2],data[i,3],1))
    

def RTA_analysis():
    a = 2
    #   RTA algorithm


def VSS_simulator():
    b = 4
    #   VSS simulator