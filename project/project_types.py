import random
from typing import Dict,List

TIME_UNIT = 1


#   ------------------------------------------------------------------------------------
#   Task definition employed in HSS
class Task:
    def __init__(self, id, wcet, bcet, period, deadline, priority):
        try:
            assert  type(id) == str and \
                    type(wcet) == int and \
                    type(bcet) == int and \
                    type(period) == int and \
                    type(deadline) == int and \
                    type(priority) == int

            self._id = id
            self._wcet = wcet
            self._bcet = bcet
            self._period = period
            self._deadline = deadline
            self._priority = priority

            #   Initially define task as schedulable
            self._schedulable = True

            #   Initialize it as -1 since this will be calculated by the simulator
            self._wcrt = -1

        except AssertionError:
            print("Error: Given parameters (Task) \
                  didn't meet the requirements for instance.")
            

#   Generates random computation time for a task
def gen_random_comp_time_task(task: Task) -> float:
    #   Calculate computation time with a random value between bcet and wcet
    #   using time_unit intervals
    rd_values = [task._bcet + i * TIME_UNIT for i in \
                 range(int((task._wcet - task._bcet) // TIME_UNIT) + 1)]
    return random.choice(rd_values)


#   ------------------------------------------------------------------------------------

# Global variable for tasks
tasks: Dict[str, Task] = {}


#   Job definition employed in HSS
class Job:
    def __init__(self, task_id, deadline, release_time):
        try:
            assert  type(task_id) == int and \
                    type(deadline) == int and \
                    type(release_time) == int
            
            self._task_id = task_id
            self._deadline = deadline
            self._release_time = release_time
            self._exec_time = gen_random_comp_time(self)

        except AssertionError:
            print("Error: Given parameters (Job) \
                  didn't meet the requirements for instance.")


#   Generates random computation time for a job
def gen_random_comp_time(job : Job) -> float:
    #   Get the corresponding task
    task = tasks.get(job._task_id)
    
    return gen_random_comp_time_task(task)


#   ------------------------------------------------------------------------------------
#   Component employed in HSS 
class Component:
    def __init__(self,scheduler,terminal,interface,children=None):
        try:
            #   Scheduler definition (string)
            assert type(scheduler) == str
            self._scheduler = scheduler

            #   Interface definition (integer)
            assert type(interface) == int
            self._interface = interface

            #   Boolean variable which indicates the component is terminal
            #   (considered then a set of tasks) or not
            assert type(terminal) == bool
            self._is_terminal = terminal

            #   Store children of component
            if children is None:
                children = []

            if terminal:
                assert all(isinstance(inst, Task) for inst in children)
            else:
                assert all(isinstance(inst, Component) for inst in children)
            self._sub_components = children

            #   Check if component is schedulable
            self._schedulable = None
            self.is_schedulable()

        except AssertionError:
            print("Error: Given parameters (Component) \
                  didn't meet the requirements for instance.")
        pass


    #   Add a child to the component's children (Task or Component)
    def add_child(self,child):
        if self._is_terminal:
            assert isinstance(child,Task), "If terminal, child must be Task"
        else:
            assert isinstance(child,Component), "If terminal, child must be Component"

        self._sub_components.append(child)


    #   Compute if component is schedulable. Assume initially schedulable
    #   for empty tasks
    def is_schedulable(self):
        if all(inst._schedulable for inst in self._sub_components):
            self._schedulable = True
        else:
            self._schedulable = False

        return self._schedulable


#   ------------------------------------------------------------------------------------
#   Resource Paradigm employed in HSS
class Resource_paradigm:
    def __init__(self,model,parameters):
        try:
            #   Model definition:
            #   * Bounded-Delay Resource (BDR)
            #   * Periodic Resource Model (PRM)
            #   * Explicit Deadline Periodic (EDP)
            assert isinstance(model,str)
            self._model = model

            inst_valid = True

            if model == "BDR" and len(parameters) == 2:
                self._av_factor = parameters[0]
                self._part_delay = parameters[1]
            elif model == "PRM" and len(parameters) == 2:
                self._wcet = parameters[0]
                self._period = parameters[1]
            elif model == "EDP" and len(parameters) == 3:
                self._wcet = parameters[0]
                self._period = parameters[1]
                self._deadline = parameters[2]
            else:
                inst_valid = False

            assert all(isinstance(inst,float) for inst in parameters) and inst_valid
                
        except AssertionError:
            print("Error: Given parameters (Resource_paradigm) \
                  didn't meet the requirements for instance.")
        pass


#   ------------------------------------------------------------------------------------
#   Scheduling unit employed in HSS
class Scheduling_unit:
    def __init__(self,root_comp,res_paradigm):
        try:
            #   Define root component (and sequence of components/tasks)
            assert isinstance(root_comp,Component)
            self._root_comp = root_comp

            #   Define resource supply:
            #   * Bounded-Delay Resource (BDR)
            #   * Periodic Resource Model (PRM)
            #   * Explicit Deadline Periodic (EDP)
            assert isinstance(res_paradigm,Resource_paradigm)
            self._res_paradigm = res_paradigm
            
        except AssertionError:
            print("Error: Given parameters (Scheduling_unit) \
                  didn't meet the requirements for instance.")
        pass

    
    #   Check if unit is schedulable
    def is_schedulable(self):
        return self._root_comp.is_schedulable()
    
