import random
from typing import Dict


#   Time unit for the simulation (in seconds)
TIME_UNIT = 1.0


#   ------------------------------------------------------------------------------------
#   Task definitions employed in HSS
class Task:
    def __init__(self, id, wcet, period, component_id, priority=-1):
        try:
            assert  type(id) == str and \
                    type(wcet) == float and \
                    type(period) == float and \
                    type(component_id) == str and \
                    type(priority) == int

            self._id = id
            self._wcet = wcet
            self._bcet = 0.0
            self._period = period
            self._deadline = period
            self._component_id = component_id
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
#   Resource Paradigm employed in HSS (only BDR model is valid)
class Resource_paradigm:
    def __init__(self,parameters,model="BDR"):
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
            else:
                inst_valid = False

            #   In case of feasibility for PRM and EDP models, add:
            """
            elif model == "PRM" and len(parameters) == 2:
                self._wcet = parameters[0]
                self._period = parameters[1]
            elif model == "EDP" and len(parameters) == 3:
                self._wcet = parameters[0]
                self._period = parameters[1]
                self._deadline = parameters[2]
            """

            assert all(isinstance(inst,float) for inst in parameters) and inst_valid
                
        except AssertionError:
            print("Error: Given parameters (Resource_paradigm) \
                  didn't meet the requirements for instance.")
        pass


#   ------------------------------------------------------------------------------------
#   Component employed in HSS 
class Component:
    def __init__(self,component_id,scheduler,budget,period,core_id,terminal,children=None):
        try:
            #   Component ID specification
            assert type(component_id) == str
            self._component_id = component_id

            #   Core ID specification
            assert type(core_id) == str
            self._core_id = core_id
            
            #   Scheduler definition (string), can be:
            #   * EDF (Earliest Deadline First)
            #   * RM (Rate-Monotonic)
            assert type(scheduler) == str
            self._scheduler = scheduler

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

            #   Interface definition (Half-half algorithm)
            self._interface = None
            if period > 0.0:
                parameters = [float(budget/period),float(2*(period - budget))]
                self._interface = Resource_paradigm(parameters)

            #   Obtain total resource need by supply bound function for component
            self._required_supply = 0.0

            #   Obtain global provided resource from supply bound function
            self._provided_supply = 0.0

            #   Deadline definition for component's priority (EDF)
            self._deadline = 0.0

            #   Check if component is schedulable
            self._schedulable = self.is_schedulable()

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

    
    #   Schedule children tasks/components following scheduler specification
    def schedule_component(self):
        # Function to apply EDF scheduling at a component level
        def schedule_edf(ready_tasks):
            return sorted(ready_tasks, key=lambda task: task._deadline)

        # Function to apply RM scheduling at a terminal component level
        def schedule_rm(ready_tasks):
            return sorted(ready_tasks, key=lambda task: task._priority)
        
        if self._scheduler == "EDF":
            #   Apply EDF scheduling
            self._sub_components = schedule_edf(self._sub_components)
        elif self._scheduler == "RM":
            #   Apply RM scheduling
            self._sub_components = schedule_rm(self._sub_components)


    #   Compute if component is schedulable. Assume initially schedulable
    #   for empty tasks
    def is_schedulable(self):
        schedulable = True

        if self._is_terminal:               #   Terminal component (set of tasks)
            sumatory = 0.0
            for task in self._sub_components:
                #   Initially calculate by task._wcet instead of WCRT
                sumatory += task._wcet/task._period

            if self._scheduler == "RM":     #   Rate-Monotonic scheduling
                n = len(self._sub_components)
                schedulable = sumatory <= n*(2**(1/n) - 1)
            else:                           #   Earliest Deadline First scheduling
                schedulable = sumatory <= 1.0
        else:
            for component in self._sub_components:
                #   Check if component is schedulable
                if not component.is_schedulable():
                    schedulable = False
                    break
            
        return schedulable


#   ------------------------------------------------------------------------------------
#   Core class employed in HSS
class Core():
    def __init__(self,identifier,speed_factor,children):
        try:
            assert isinstance(identifier,str)
            self._core_id = identifier

            assert isinstance(speed_factor,float) and speed_factor > 0.0
            self._speed_factor = speed_factor

            #   Create root component (0 interface)
            self._root_comp = Component("Component_rt","EDF",0,0,self._core_id,False,children)

        except AssertionError:
            print("Error: Given parameters (Core) \
                  didn't meet the requirements for instance.")
