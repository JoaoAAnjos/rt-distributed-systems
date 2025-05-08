import pandas as pd
import os

from typing import Dict, List, Optional
from enum import Enum, auto

#   ------------------------------------------------------------------------------------
#   Enums 
#   ------------------------------------------------------------------------------------
class Scheduler(Enum):
    EDF = auto()
    RM = auto()

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

            #   Create root component (0 interface)
            self.root_comp = Component(self._core_id, scheduler, 0, 0, self._core_id, False)

        except AssertionError:
            print("Error: Given parameters (Core) \
                  didn't meet the requirements for instance.")
            
#   ------------------------------------------------------------------------------------
#   Component
#   ------------------------------------------------------------------------------------
class Component:
    def __init__(self, component_id: str, scheduler: str, budget: int, period: float, core_id: str):
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
            self._scheduler = Scheduler[scheduler]

            # Tree information (Children and Parent)
            self.parent = None
            self.children: List[Component] = []

            #   Interface definition (Half-half algorithm)
            self._interface = None
            if period > 0.0:
                parameters = [float(budget/period),float(2*(period - budget))]
                self._interface = Resource_paradigm(parameters)

            #   Obtain total resource need by supply bound function for component
            self._required_supply = 0.0

            #   Obtain global provided resource from supply bound function
            self._provided_supply = 0.0

        except AssertionError:
            print("Error: Given parameters (Component) \
                  didn't meet the requirements for instance.")
        pass


    #   Add a child to the component's children
    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    # Returns whether a component is a leaf or not (i.e. is terminal)  
    def is_leaf(self):
        return not self.children

            
#   ------------------------------------------------------------------------------------
#   Task 
#   ------------------------------------------------------------------------------------
class Task:
    def __init__(self, id: str, wcet: float, period: float, component_id: str, priority: int):
        try:
            assert  type(id) == str and \
                    type(wcet) == float and \
                    type(period) == float and \
                    type(component_id) == str

            self._id = id
            self._wcet = wcet
            self._period = period
            self._deadline = period
            self._component_id = component_id
            if priority is None:
                self._priority = -1
            else:
                self._priority = priority

            #   Initially define task as schedulable
            self._schedulable = True

            #   Initialize it as -1 since this will be calculated by the simulator
            self._wcrt = -1

        except AssertionError:
            print("Error: Given parameters (Task) \
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
cores_registry: Dict[str, Core] = {}
#Global variable for components
components_registry: Dict[str, Component] = {}
# Global variable for tasks
tasks_registry: Dict[str, Task] = {}
# Registry of Tasks associated with Component for terminal Components
component_task_registry: Dict[str, List[Task]] = {}

#Global time value for simulator usage
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

        cores_registry[core._core_id] = core

"""
Initializes components and adds them to hierarchy structure
"""
def initialize_components(df: pd.DataFrame):

    for index, row in df.iterrows():
        component = Component(
            row["component_id"],
            row["scheduler"],
            row["budget"],
            row["period"],
            row["core_id"],
            True
        )

        core = cores_registry.get(component._core_id)
        core.root_comp.add_child(component)

        components_registry[component._component_id] = component

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

    tasks_registry[task._id] = task

    component_task_registry.setdefault(task._component_id, []).append(task)
        

"""
Only works under the assumption that both the input folder is named 'input' and the files inside
will be named architecture.csv, budgets.csv and tasks.csv, following the nomenclature on the test
cases given by the teacher. When function has finished executing, all objects from csv data are created, 
added to global resources and organized in an hierarchical structure.
"""
def initialize_csv_data():

    # Get the directory where the Python script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the file
    input_folder = os.path.join(script_dir, "input")

    initialize_cores(pd.read_csv(os.path.join(input_folder, "architecture.csv")))

    initialize_components(pd.read_csv(os.path.join(input_folder, "budgets.csv")))

    initialize_tasks(pd.read_csv(os.path.join(input_folder, "tasks.csv")))