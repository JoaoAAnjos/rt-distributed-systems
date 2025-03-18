import exercise as ex

#VSS start
print("""
===========================================
      Very Simple Simulator (VSS) 
===========================================
      
The simulator takes as input the application model consisting of a set of hypothetical tasks stored 
in a csv file and the simulation time. The output is a list of worst-case response times (WCRT) 
observed during the simulation for each task.

This simulator expects the csv file to contain 6 columns, in the following order:
-Task identifier
-Best case execution time (BCET)
-Worst case execution time (WCET)
-Period
-Deadline
-Priority
      
If the csv file passed to the simulator differs from these specifications the simulator's output will be
incorrect. The simulator allows more than one csv file to be passed, and it will run a simulation for the
data contained in each file. When asked to specify the csv file, you can pass more than one by inserting
the files names separated by commas (,). The files should be located in the simulator's root folder,
and the file termination should be specified in the name (.csv).
      
After defining the csv file(s) that will feed the simulation, you will be asked to input the simulation time.
Keep in mind this is not a real time measure, but a theoretical time amount, used to define the number of cycles
the simulator's logic will go through. Afterwards, you will be asked to input the desired time unit. This should
be a numeric value, and not a standard time unit like seconds or miliseconds. If a float number is inputed, the
separator should be (.)
      
The simulator will apply its logic for (simulation time / time unit) amount of times.

If multiple csv files were passed, the same simulation time and time unit will be used for each simulation.
      
The simulator will print the results to a txt file called 'results-VSS' 
(this can be improved, for example, by adding a column to the CSV)
""")

#clean results.txt file
with open("results-VSS.txt", "w") as file:
    pass

#ask for csv file(s) containing the model and store the data
csv_input = input("Specify the csv file(s) that contain the application model:")
csv_files = [file_name.strip() for file_name in csv_input.split(",")]

#ask for simulation time and store it
sim_time = int(input("Input the desired simulation time:"))

#ask for time unit value and store it
time_unit = float(input("Input the desired time unit:"))

#run the simulation(s)
for file_name in csv_files:
    ex.run_vss(file_name, sim_time, time_unit)

#simulation complete
print("Simulation(s) complete. Results have been outputed to results-VSS.txt")
