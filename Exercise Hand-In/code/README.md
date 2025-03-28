# VSS and RTA Simulators

This repository contains two simulators for analyzing real-time task scheduling:
1. **Very Simple Simulator (VSS)**: Simulates fixed-priority preemptive scheduling and calculates worst-case response times (WCRT) for tasks.
2. **Response-Time Analysis (RTA)**: Performs a theoretical analysis to calculate worst-case response times (WCRT) for tasks based on their priorities and execution times.

Both simulators take as input a CSV file containing task definitions and output the results to text files.

## Table of Contents
1. [Requirements](#requirements)
2. [File Structure](#file-structure)
3. [Running the Simulators](#running-the-simulators)
   - [Running VSS](#running-vss)
   - [Running RTA](#running-rta)
4. [Input CSV Format](#input-csv-format)
5. [Output Files](#output-files)
6. [Example](#example)

## Requirements
- Python 3.x
- Required Python libraries:
  - `pandas`
  - `random`
  - `math`

You can install the required libraries using pip:
```bash
pip install pandas
```

## File Structure

The project consists of the following files:

- **exercise.py**: Contains the core logic for both the VSS and RTA simulators. This includes task and job initialization, simulation loops, and response-time calculations.

- **vss_main.py**: The main script to run the VSS simulator. It handles user input for CSV files, simulation time, and time unit, and then executes the VSS simulation.

- **rta_main.py**: The main script to run the RTA simulator. It handles user input for CSV files and executes the RTA analysis.

- **results-VSS.txt**: The output file where the VSS simulation results (worst-case response times for each task) are saved.

- **results-RTA.txt**: The output file where the RTA analysis results (worst-case response times for each task) are saved.

## Running the Simulators
### Running VSS

1. Open a terminal or command prompt.

2. Navigate to the directory containing the `vss_main.py` file.

3. Run the VSS simulator by executing the following command:
```bash
 python vss_main.py
```

4. Follow the prompts:

- Specify the CSV file(s): Enter the name(s) of the CSV file(s) containing the task definitions. If multiple files are provided, separate them with commas (`,`).

- Input the desired simulation time: Enter the total simulation time (a positive integer).

- Input the desired time unit: Enter the time unit (a positive float or integer).

The results will be saved in `results-VSS.txt`.

### Running RTA

1. Open a terminal or command prompt.

2. Navigate to the directory containing the `rta_main.py` file.

3. Run the RTA simulator by executing the following command:
```bash
python rta_main.py
```
4. Follow the prompts:

- Specify the CSV file(s): Enter the name(s) of the CSV file(s) containing the task definitions. If multiple files are provided, separate them with commas (`,`).

The results will be saved in `results-RTA.txt`.

## Input CSV Format

The CSV file should contain the following columns in the specified order:

1. **Task**: Task identifier (`string`).

2. **BCET**: Best-case execution time (`integer`).

3. **WCET**: Worst-case execution time (`integer`).

4. **Period**: Task period (`integer`).

5. **Deadline**: Task deadline (`integer`).

6. **Priority**: Task priority (`integer`).

Example CSV (`tasks.csv`):
````
Task,BCET,WCET,Period,Deadline,Priority
T1,1,3,10,10,1
T2,2,4,20,20,2
T3,1,2,30,30,3
````

## Output Files

- **results-VSS.txt**: Contains the worst-case response times (WCRT) observed during the VSS simulation for each task.
- **results-RTA.txt**: Contains the worst-case response times (WCRT) calculated by the RTA analysis for each task.

**Note**: In both outputs, a WCRT of `-1` means the task cannot meet its deadline under the given scheduling constraints.

Example output (`results-VSS.txt`):
````
VSS Simulation results for application model in tasks.csv

Task_id: T1 | WCRT : 3.0 | Deadline: 10 | Schedulable: True
Task_id: T2 | WCRT : 4.0 | Deadline: 20 | Schedulable: True
Task_id: T3 | WCRT : 4.0 | Deadline: 30 | Schedulable: True

According to the results, this taskset is unschedulable
````
Example output (`results-RTA.txt`):
````
RTA Simulation results for application model in tasks.csv

Task_id: T1 | WCRT : 4 | Deadline: 10 | Schedulable: True
Task_id: T2 | WCRT : 5 | Deadline: 4 | Schedulable: False
Task_id: T3 | WCRT : 6 | Deadline: 20 | Schedulable: True

According to the results, this taskset is unschedulable
````


## Example
### Running VSS

1. Place a CSV file (e.g., `tasks.csv`) in the same directory as the `vss_main.py` file.

2. Run the VSS simulator by executing:
````bash
    python vss_main.py
````
3. Input the CSV file name, simulation time, and time unit:
````
Specify the csv file(s) that contain the application model: tasks.csv
Input the desired simulation time: 1000
Input the desired time unit: 1.0
````
4. Check the results in `results-VSS.txt`.

### Running RTA

1. Place a CSV file (e.g., tasks.csv) in the same directory as the code.

2.  Run the RTA simulator by executing:
````bash
python rta_main.py
````
3. Input the CSV file name:
````
Specify the csv file(s) that contain the application model: tasks.csv
````
4. Check the results in `results-RTA.txt`.

## Notes

- Ensure the CSV file follows the required format.

- For VSS, the simulation time and time unit determine the granularity of the simulation.

- For RTA, the analysis is deterministic and does not depend on simulation time or time unit.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.