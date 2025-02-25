#!bin/bash
gcc -g -o task_gen task_gen.c       #   C compilation
./task_gen
#taskset -c 0 ./task_gen             #   Assure execution by only one core