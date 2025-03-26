import exercise as ex

#RTA start
print("""
==========================
      RTA Algorithm
==========================
      
This tools takes as input an application model consisting of a set of hypothetical tasks stored
in a csv file. The output is a list of worst-case response times (WCRT) calculated through
a response time analysis algorithm, based on the tasks priority.
      
This tool expects the csv file to contain 6 columns, in the following order:
-Task identifier
-Best case execution time (BCET)
-Worst case execution time (WCET)
-Period
-Deadline
-Priority
      
If the csv file passed to the tool differs from these specifications the tool's output will be
incorrect. The tool allows more than one csv file to be passed, and it will run the analysis for the
data contained in each file. When asked to specify the csv file, you can pass more than one by inserting
the files names separated by commas (,). The files should be located in the simulator's root folder,
and the file termination should be specified in the name (.csv).
      
The simulator will print the results to a txt file called 'results-RTA'.
""")

#clean results.txt file
with open("results-RTA.txt", "w") as file:
    pass

#ask for csv file(s) containing the model and store the data
csv_input = input("Specify the csv file(s) that contain the application model: ")
csv_files = [file_name.strip() for file_name in csv_input.split(",")]

#run the simulation(s)
for file_name in csv_files:
    ex.run_rta(file_name)

#simulation complete
print("Simulation(s) complete. Results have been outputed to results-RTA.txt")

