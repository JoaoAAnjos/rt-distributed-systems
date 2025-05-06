import pandas as pd
import os

from typing import Dict,List

#   ------------------------------------------------------------------------------------
#   Core class 
#   ------------------------------------------------------------------------------------
class Core:
    def __init__(self, identifier: str, speed_factor: float, scheduler: str):
        try:
            assert isinstance(identifier,str)
            self._core_id = identifier

            assert isinstance(speed_factor,float) and speed_factor > 0.0
            self._speed_factor = speed_factor

            assert isinstance(scheduler, str)
            self._scheduler = scheduler

            #   Create root component (0 interface)
            self.root_comp = Component(False, self._core_id, self._scheduler, 0, 0, self._core_id)

            cores[self._core_id] = self

        except AssertionError:
            print("Error: Given parameters (Core) \
                  didn't meet the requirements for instance.")
            

    """
        Function to check if the children components from a core are schedulable
        (RM and EDF algorithms).
        
        >   Return:
            -   True:   Core subcomponents are schedulable
            -   False:  Core subcomponents are not schedulable
    """
    def simple_scheduler(self):
        utilization = 0.0
        
        for component in self.root_comp._sub_components:
            utilization += component._budget / component._period
        
        #   Check if the utilization is less than the limit for scheduler
        if self._scheduler == "RM":
            n = len(self.root_comp._sub_components)
            return utilization <= n*(2**(1/n) - 1)
        elif self._scheduler == "EDF":
            return utilization <= 1.0

            
#   ------------------------------------------------------------------------------------
#   Component
#   ------------------------------------------------------------------------------------
class Component:
    def __init__(self, terminal: bool, component_id: str, scheduler: str, budget: int, \
                 period: int, core_id: str, priority: int = -1):
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

            #   Budget definition (integer)
            assert type(budget) == int and budget >= 0
            self._budget = budget

            #   Period definition (integer)
            assert type(period) == int and period >= 0
            self._period = period

            #   Boolean variable which indicates the component is terminal
            #   (considered then a set of tasks) or not
            assert type(terminal) == bool
            self._is_terminal = terminal

            #   Interface definition (Half-half algorithm)
            self._interface = None
            if period > 0.0:
                parameters = [float(budget/period),float(2*(period - budget))]
                self._interface = Resource_paradigm(parameters)

            #   Obtain total resource need by supply bound function for component
            self._required_supply = 0.0

            #   Obtain global provided resource from supply bound function
            self._provided_supply = 0.0

            components[self._component_id] = self

            #   Initialize subcomponents list
            self._sub_components = []

            #   Define component's priority (needed for RM algorithm)
            self._priority = priority

        except AssertionError:
            print("Error: Given parameters (Component) \
                  didn't meet the requirements for instance.")
        pass


    """
        Add a child to the component's children (Task or Component)
    """
    def add_child(self,child):
        if self._is_terminal:
            assert isinstance(child,Task), "If terminal, child must be Task"
        else:
            assert isinstance(child,Component), "If terminal, child must be Component"

        self._sub_components.append(child)

            
#   ------------------------------------------------------------------------------------
#   Task 
#   ------------------------------------------------------------------------------------
class Task:
    def __init__(self, id: str, wcet: int, period: int, component_id: str, priority: int = -1):
        try:
            assert  type(id) == str and \
                    type(wcet) == int and \
                    type(period) == int and \
                    type(component_id) == str

            self._id = id
            self._wcet = wcet
            self._period = period
            self._deadline = period
            self._component_id = component_id
            
            #   Priority definition (needed for RM algorithm)
            self._priority = priority

            #   Initially define task as schedulable
            self._schedulable = True

            #   Initialize it as -1 since this will be calculated by the simulator
            self._wcrt = -1

            tasks[self._id] = self

        except AssertionError:
            print("Error: Given parameters (Task) \
                  didn't meet the requirements for instance.")

#   ------------------------------------------------------------------------------------
#   Job 
#   ------------------------------------------------------------------------------------
class Job:
    def __init__(self, task_id, deadline, release_time):
        try:
            assert  type(task_id) == int and \
                    type(deadline) == int and \
                    type(release_time) == int
            
            self._task_id = task_id
            self._deadline = deadline
            self._release_time = release_time
            self._exec_time = 0##################

            jobs.append(self)

        except AssertionError:
            print("Error: Given parameters (Job) \
                  didn't meet the requirements for instance.")


#   ------------------------------------------------------------------------------------
#   Resource Paradigm employed in HSS (only BDR model is valid)
#   ------------------------------------------------------------------------------------
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

            assert all(isinstance(inst,float) for inst in parameters) and inst_valid
                
        except AssertionError:
            print("Error: Given parameters (Resource_paradigm) \
                  didn't meet the requirements for instance.")
        pass


#   ------------------------------------------------------------------------------------
#   Global Resources for Simulator and Analysis Tool execution
#   ------------------------------------------------------------------------------------

# Global variable for cores
cores: Dict[str, Core] = {}
#Global variable for components
components: Dict[str, Component] = {}
# Global variable for tasks
tasks: Dict[str, Task] = {}
# Global variable for active jobs
jobs: List[Job] = []

CURRENT_TIME = 0.0

#   ------------------------------------------------------------------------------------
#   Library functions
#   ------------------------------------------------------------------------------------

"""
Initializes cores
"""
def initialize_cores(df: pd.DataFrame):

    for index, row in df.iterrows():
        core = Core(
            row["core_id"],
            row["speed_factor"],
            row["scheduler"]
        )

"""
Initializes components and adds them to hierarchy structure
"""
def initialize_components(df: pd.DataFrame):

    for index, row in df.iterrows():
        component = Component(
            True,
            row["component_id"],
            row["scheduler"],
            row["budget"],
            row["period"],
            row["core_id"],
            row["priority"]
        )

        core = cores.get(row["core_id"])
        core.root_comp.add_child(component)

"""
Initializes tasks and adds them to hierarchy structure
"""
def initialize_tasks(df: pd.DataFrame):

    for index, row in df.iterrows():
        task = Task(
            row["task_name"],
            row["wcet"],
            row["period"],
            row["component_id"],
            row["priority"]
        )

        component = components.get(row["component_id"])
        component.add_child(task)

"""
Initialize jobs for each task
"""
def initialize_jobs():

    for task in tasks.values():
        job = Job(
            task._id,
            task._period,
            CURRENT_TIME
        )

        jobs.append(job)

"""
Only works under the assumption that both the input folder is named 'input' and the files inside
will be named architecture.csv, budgets.csv and tasks.csv, following the nomenclature on the test
cases given by the teacher. When function has finished executing, all objects are created, added to
global resources and organized in an hierarchical structure.
"""
def initialize_data():

    # Get the directory where the Python script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the file
    input_folder = os.path.join(script_dir, "input")

    initialize_cores(pd.read_csv(os.path.join(input_folder, "architecture.csv")))

    initialize_components(pd.read_csv(os.path.join(input_folder, "budgets.csv")))

    initialize_tasks(pd.read_csv(os.path.join(input_folder, "tasks.csv")))