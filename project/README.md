# 02225 Distributed Real-Time Systems - Hierarchical Scheduling Project

This project implements a simulator and a compositional schedulability analysis tool for an Advanced Driver-Assistance System (ADAS) modeled using a two-level Hierarchical Scheduling System (HSS) on a multicore platform.

## Project Goals

*   **Model:** Define an ADAS application using components and tasks, mapped onto a heterogeneous multicore architecture.
*   **Simulate:** Create a discrete-event simulator to observe the system's runtime behavior under HSS rules, tracking metrics like response times and deadline misses.
*   **Analyze:** Develop a tool to perform compositional schedulability analysis using the Bounded Delay Resource (BDR) model to determine if tasks meet their deadlines theoretically.
*   **Compare:** Validate the theoretical analysis against the practical simulation results.

## Features

*   **Simulator (`main_simulator.py`, `source/simulator.py`):**
    *   Simulates task execution on multiple cores within an HSS framework.
    *   Supports EDF and RM scheduling policies within components.
    *   Manages resource allocation between hierarchical levels based on component budgets (Q) and periods (P) provided in input files (acting similar to a Periodic Resource Model server).
    *   Tracks task states, deadlines met/missed, and calculates average/maximum response times.
    *   Generates `output/results_simulator.csv` with detailed simulation statistics.
*   **Analysis Tool (`main_analysis.py`, `source/analysis.py`):**
    *   Performs compositional schedulability analysis based on the BDR model.
    *   Calculates Demand Bound Functions (DBF) for EDF and RM workloads.
    *   Calculates Supply Bound Functions (SBF) for BDR interfaces derived from the component Q/P values (using the Half-Half algorithm interpretation: $\alpha = Q/P$, $\Delta = 2(P-Q)$).
    *   Checks schedulability at both the core level (component utilization) and component level (DBF vs. SBF).
    *   Generates `output/results_analysis.csv` indicating the schedulability status of tasks and components.

## System Model Overview

*   **Hardware (`input/architecture.csv`):** A multicore platform where cores have specific performance `speed_factor`s and run either an EDF or RM top-level scheduler.
*   **Software (`input/tasks.csv`, `input/budgets.csv`):** The ADAS system is modeled as `Components` (e.g., `Camera_Sensor`) containing periodic `Tasks`. Tasks have WCETs (adjusted by core speed), periods (assumed deadlines), and potentially RM priorities. Components have internal EDF or RM schedulers and are assigned initial `budget` (Q) and `period` (P) values for resource allocation.
*   **Hierarchy:** Components are statically assigned to cores, and tasks are statically assigned to components, forming a two-level hierarchy on each core.
*   **Resource Allocation:** The simulator directly uses the component Q/P. The analysis tool converts these Q/P values into BDR parameters $(\alpha, \Delta)$ for compositional analysis.

## Theoretical Concepts Applied

This project utilizes key concepts from real-time systems theory, including:

*   Hierarchical Scheduling Systems (HSS)
*   Bounded Delay Resource (BDR) Model for analysis
*   Periodic Resource Model (PRM) for simulation
*   Demand Bound Function (DBF) and Supply Bound Function (SBF)
*   EDF and Rate Monotonic (RM) scheduling algorithms
*   Utilization-based schedulability tests

## Input Files (`input/` folder)

*   **`architecture.csv`:** Core definitions (`core_id`, `speed_factor`, top-level `scheduler`).
*   **`budgets.csv`:** Component definitions (`component_id`, internal `scheduler`, initial `budget` (Q), initial `period` (P), assigned `core_id`).
*   **`tasks.csv`:** Task definitions (`task_name`, nominal `wcet`, `period`, assigned `component_id`, RM `priority` if applicable).

## Output Files (`output/` folder)

*   **`results_simulator.csv`:** Contains detailed results from the simulation run.
    *   `task_name`: Identifier for the task.
    *   `component_id`: Identifier for the component the task belongs to.
    *   `Core_id`: Identifier for the core the task ran on.
    *   `task_schedulable`: True if the task missed zero deadlines during simulation, False otherwise.
    *   `avg_response_time`: Average time from task arrival to completion.
    *   `max_response_time`: Maximum time from task arrival to completion.
    *   `component_schedulable`: True if all tasks within this component were schedulable in the simulation, False otherwise.
    *   `deadlines_missed`: Total count of deadlines missed by this task.
    *   `deadlines_met`: Total count of deadlines met by this task.

*   **`results_analysis.csv`:** Contains results from the theoretical schedulability analysis.
    *   `Task_ID`: Identifier for the task.
    *   `adjusted_WCET`: Task's Worst-Case Execution Time, adjusted for the assigned core's speed factor.
    *   `Priority`: The priority assigned to the RM task. If the task scheduler is EDF it is set to -1.
    *   `Task_Schedulable`: True if the task missed zero deadlines during analysis, False otherwise.
    *   `Component_ID`: Identifier for the component the task belongs to.
    *   `Component_Schedulable`: True if all tasks within this component were schedulable in the simulation, False otherwise.

## How to Run

1.  **Prerequisites:** 
- Python 3 
- `pandas` library (`pip install pandas`).
2.  **Navigate:** Open a terminal in the project's root directory.
3.  **Run Simulator:**
    ```bash
    python main_simulator.py <desired_simulation_time>
    ```

4.  **Run Analysis Tool:**
    ```bash
    python main_analysis.py
    ```
5.  **Check Output:** Result files will be created/updated in the `output/` directory.

### Analysis Tool Terminal Output

In addition to the `results_analysis.csv` file, the analysis tool (`main_analysis.py`) will print a summary to the terminal, indicating:
*   Whether the entire system is considered schedulable based on the analysis.
*   A list of component IDs identified as `Unschedulable components`.
*   A list of component IDs identified as `Schedulable components`.

Example terminal output of unschedulable system:

```bash
System is not completely schedulable.

Unschedulable components:
['Component_1', 'Component_2']

Schedulable components:
['Component_3']
```
## Assumptions and Simplifications

*   **Task Model:** Tasks are treated as periodic. Their periods are also used as their relative deadlines (implicit deadlines).
*   **Independence:** Tasks are independent, with no precedence constraints or shared resource interactions other than the CPU resource managed by the HSS framework.
*   **Overheads:** System overheads like context switching and scheduler execution time are considered negligible.
*   **Static Configuration:** Task-to-component and component-to-core assignments are fixed throughout the simulation and analysis.
*   **Resource Model Interpretation:**
    *   The **simulator** replenishes component resources based directly on the initial budget (Q) and period (P) values provided in `budgets.csv`, behaving like a Periodic Resource Model (PRM) server for each component.
    *   The **analysis tool** interprets these same Q/P values using the BDR (Bounded Delay Resource) model framework. It derives BDR parameters $(\alpha, \Delta)$ via the Half-Half algorithm ($\alpha = Q/P$, $\Delta = 2(P-Q)$) to calculate the Supply Bound Function (SBF) for checking against the component's Demand Bound Function (DBF).
*   **Simulator Deadline Miss Policy:** If a new instance of a task arrives before the previous instance has completed (indicating a deadline miss), the **simulator aborts** the previous instance. The old instance is removed from the ready queue or stopped if currently running, and the new instance is activated.
