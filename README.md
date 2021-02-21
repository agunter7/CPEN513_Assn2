# CPEN 513 Assignment 2
CPEN 513 CAD Algorithms for Integrated Circuits Assignment 2: Simulated Annealing

# Usage
Run src/main.py with a Python 3.9 interpreter

A placement window should be displayed upon running the file.

Press a number key to begin annealing. 
'0' will run annealing to completion, reporting runtime since '0' was pressed.
'1' will perform a single annealing iteration.
'2' through '9' will perform 10^n iterations, where n='n' (i.e. the pressed key)

At the end of annealing, a plot summarizing the changes to total cost throughout the run will be displayed.

Logs to the console will be made periodically during the anneal and at anneal completion.

GUI updates occur if and only if an annealing temperature update happens or if a computation sequence completes.
GUI may freeze, but the program will continue running. Check the console for continued logs as evidence of this.