#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <stdio.h>


/// The tasks t_i are stored with a best execution time, a worst
/// execution time, and a priority order for execution. The number
/// of tasks varies between 1 and 20. These are stored in a .txt
/// archive called tasks.txt with format:
///
/// "Task_X BCET_X(float) WCET_X(float) priority_X(uint16_t)"
#define FILE_NAME "tasks.txt"


/// \brief  Sorts the array \param arr_priors so as for the tasks
///         not to have the same priority in the order given.
uint16_t* sort_priorities(uint16_t* arr_priors, uint16_t n_tasks)
{
    int j = 0, t_i = 0, arr_i = 0;
    uint16_t aux_p = 0;
    uint16_t* arr_priors_def = (uint16_t*)malloc(n_tasks * sizeof(uint16_t));
    for(int i = 0; i < n_tasks; i++)
        arr_priors_def[i] = (uint16_t)(i+1);

    
    /// Get correct priority order for tasks
    for(int i = 0; i < n_tasks; i++)
    {
        j = i;
        arr_i = i;
        t_i = i + 1;
        while(j > 0)
        {
            if(arr_priors[j] < arr_priors[j - 1])
            {
                aux_p = arr_priors[j-1];
                arr_priors[j-1] = arr_priors[j];
                arr_priors[j] = aux_p;
                arr_i--;                            /// Update position of task

                /// Get correct task order
                arr_priors_def[arr_i + 1] = arr_priors_def[arr_i];
                arr_priors_def[arr_i] = t_i;
            }

            j--;
        }
    }

    return arr_priors_def;
}


/// \brief  Generates an array with random priorities between tasks
/// \return An array[n_tasks] with the priority order set for the tasks
uint16_t* gen_priorities(uint16_t n_tasks)
{
    uint16_t* arr_prs = (uint16_t*)malloc(n_tasks * sizeof(uint16_t));
    float r_num = 0.0;

    for(uint16_t i = 0; i < n_tasks; i++)
    {
        r_num = (float)rand() / (float)RAND_MAX;
        if(r_num < (1/n_tasks)) r_num = 1/n_tasks;
        r_num = r_num*n_tasks;

        arr_prs[i] = (uint16_t)r_num;
    }

    /// Sort tasks for possible errors
    arr_prs = sort_priorities(arr_prs,n_tasks);

    return arr_prs;
}


/// \brief  Generates the computational time for each task t_i
/// \return Array[n_tasks] with times for BCET and WCET (between 0.1 and 1.6)
float** gen_comp_time(uint16_t n_tasks)
{
    float** arr_cis = (float**)malloc(2 * sizeof(float*));
    for (int i = 0; i < 2; i++)
        arr_cis[i] = (float*)malloc(n_tasks * sizeof(float));

    float random_n = 0.0;
    
    for(uint16_t i = 0; i < n_tasks; i++)
    {
        random_n = (float)rand() / (float)RAND_MAX;     /// Between 0.0 and 1.0
        arr_cis[0][i] = 0.1 + random_n;                 /// Best case
        arr_cis[1][i] = arr_cis[0][i] + 0.5*random_n;   /// Worst case
    }
    return arr_cis;
}


int main()
{
    srand(time(NULL));      /// Initialize seed

    /// Tasks amount generation (between 1 and 20)
    float n_tis = (float)rand() / (float)RAND_MAX;
    int int_tis = 0;
    if(n_tis < 0.05) n_tis = 0.05;
    n_tis = n_tis*20;
    int_tis = (int)n_tis;


    /// Obtention of arrays for tasks data
    float** comp_times = gen_comp_time(int_tis);
    uint16_t* priorities = gen_priorities(int_tis);
    

    /// File handling
    FILE* file = fopen(FILE_NAME, "a+");    /// Open for addition
    if (file == NULL)
    {
        perror("Error opening the file");
        return 1;
    }

    for (int i = 0; i < int_tis; i++)
        fprintf(file, "%d %.2f %.2f %d\n", (i+1),
                comp_times[0][i], comp_times[1][i], priorities[i]);

    fprintf(file, "---\n");

    fclose(file);
    printf("File Updated!\n");

    return 0;
}