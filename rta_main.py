import exercise as ex

#RTA

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

