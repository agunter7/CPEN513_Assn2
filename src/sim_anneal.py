"""
Solution to UBC CPEN 513 Assignment 2.
Implements Simulated Annealing.
Uses Tkinter for GUI.
"""

import os
import random
import time
import matplotlib.pyplot as plt
from tkinter import *
from math import exp, sqrt

# Constants
file_name = ""
FILE_DIR = "../benchmarks/"

# Hyperparameters
cooling_factor = 0.8  # Coefficient for rate of anneal cooling
initial_temp_factor = 10  # Coefficient for anneal initial temperature
moves_per_temp_factor = 75  # Coefficient for number of moves to be performed at each temperature
TEMP_EXIT_RATIO = 0.002  # Ratio for determining exit condition based on temperature
COST_EXIT_RATIO = 0.005  # Ratio for determining exit condition based on cost
MOVE_SAMPLE_SIZE = 50  # Initial number of moves to be performed to determine cost variance of moves
hyperparam_string = str(cooling_factor) + "-" + str(initial_temp_factor) + "-" + str(moves_per_temp_factor) + "-"

# Global variables
num_cells_to_place = 0  # Number of cells in the circuit to be placed
num_cell_connections = 0  # Number of connections to be routed, summed across all cells/nets
grid_width = 0  # Width of the placement grid
grid_height = 0  # Height of the placement grid
cell_dict = {}  # Dictionary of all cells, key is cell ID
net_dict = {}  # Dictionary of all nets, key is net ID
placement_grid = []  # 2D list of sites for placement
placement_done = False  # Is the placement complete?
cost_history = []  # History of costs at each temperature
iter_history = []  # History of cumulative iterations performed at each temperature
temperature_history = []  # History of exact temperature values
root = None  # Tkinter root
unique_line_list = []  # List of unique lines across multiple nets
# Simulated Annealing variables
sa_temp = -1  # SA temperature
sa_initial_temp = -1  # Starting SA temperature
iters_per_temp = -1  # Number of iterations to perform at each temperature
iters_this_temp = 0  # Number of iterations performed at the current temperature
current_cost = 0  # The estimated cost of the current placement
prev_temp_cost = 0  # Cost at the end of exploring the previous temperature
total_iters = 0  # Cumulative number of iterations performed throughout program run


class Site:
    """
    A placement site/slot for a cell to inhabit
    """
    def __init__(self, x: int, y: int):
        self.x = x  # x location
        self.y = y  # y location
        self.canvas_id = -1  # ID of corresponding rectangle in Tkinter canvas
        self.canvas_centre = (-1, -1)  # Geometric centre of Tkinter rectangle
        self.isOccupied = False  # Is the site occupied by a cell?
        self.occupant = None  # Reference to occupant cell
        pass


class Cell:
    """
    A single cell
    """
    def __init__(self, cell_id):
        self.id = cell_id  # Identifier
        self.isPlaced = False  # Has this cell been placed into a site?
        self.site = None  # Reference to the site this cell occupies
        self.nets = []  # Nets this cell is a part of
        pass


class Line:
    """
    A wrapper class for Tkinter lines
    """
    def __init__(self, source: Cell, sink: Cell, canvas_id: int):
        self.source = source  # Reference to source cell
        self.sink = sink  # Reference to sink cell
        self.canvas_id = canvas_id  # Tkinter ID of line


class Net:
    """
    A collection of cells to be connected during routing
    """
    def __init__(self, net_id: int, num_cells: int):
        self.id = net_id  # Identifier
        self.num_cells = num_cells  # Number of cells in this net
        self.source = None  # Reference to source cell
        self.sinks = []  # References to sink cells
        self.lines = []  # References to Lines in this net
        pass


def reset_globals():
    """
    Reset (most) global variables.
    Used for repeated calls to this script from a parent script.
    """
    global num_cells_to_place
    global num_cell_connections
    global grid_width
    global grid_height
    global cell_dict
    global net_dict
    global placement_grid
    global placement_done
    global cost_history
    global iter_history
    global temperature_history
    global root
    global unique_line_list
    global sa_temp
    global sa_initial_temp
    global iters_per_temp
    global iters_this_temp
    global current_cost
    global prev_temp_cost
    global total_iters

    num_cells_to_place = 0
    num_cell_connections = 0
    grid_width = 0
    grid_height = 0
    cell_dict = {}
    net_dict = {}
    placement_grid = []
    placement_done = False
    cost_history = []
    iter_history = []
    temperature_history = []
    root = None
    unique_line_list = []
    sa_temp = -1
    sa_initial_temp = -1
    iters_per_temp = -1
    iters_this_temp = -1
    current_cost = 0
    prev_temp_cost = 0
    total_iters = 0


def quick_anneal(f_name, cool_fact, init_temp_fact, move_p_t_fact):
    """
    Perform an anneal without a GUI. Automatically exits after saving data.
    For experimentation.
    """
    global FILE_DIR
    global file_name
    global num_cells_to_place
    global num_cell_connections
    global grid_width
    global grid_height
    global placement_grid
    global cooling_factor
    global initial_temp_factor
    global moves_per_temp_factor
    global hyperparam_string

    reset_globals()

    random.seed(0)  # Set random seed

    file_name = f_name
    cooling_factor = cool_fact
    initial_temp_factor = init_temp_fact
    moves_per_temp_factor = move_p_t_fact
    hyperparam_string = str(cooling_factor) + "-" + str(initial_temp_factor) + "-" + str(moves_per_temp_factor) + "-"

    print("Running: " + file_name + "-" + str(cooling_factor) + "-" + str(initial_temp_factor) + "-" +
          str(moves_per_temp_factor))

    file_path = FILE_DIR + f_name
    script_path = os.path.dirname(__file__)
    true_path = os.path.join(script_path, file_path)
    routing_file = open(true_path, "r")

    # Setup the routing grid/array
    placement_grid = create_placement_grid(routing_file)

    # Perform initial placement
    initial_placement(None)

    sa_to_completion(None)

    
def anneal():
    """
    Perform anneal with a GUI.
    :return: void
    """
    global FILE_DIR
    global file_name
    global num_cells_to_place
    global num_cell_connections
    global grid_width
    global grid_height
    global placement_grid
    global root

    random.seed(0)  # Set random seed

    # Determine file to open
    file_path = FILE_DIR + file_name
    script_path = os.path.dirname(__file__)
    true_path = os.path.join(script_path, file_path)
    routing_file = open(true_path, "r")

    # Setup the routing grid/array
    placement_grid = create_placement_grid(routing_file)

    # Create routing canvas in Tkinter
    root = Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    site_length = 15
    routing_canvas = Canvas(root, bg='white', width=grid_width*site_length, height=grid_height*site_length)
    routing_canvas.grid(column=0, row=0, sticky=(N, W, E, S))
    for x in range(grid_width):
        for y in range(grid_height):
            # Add a rectangle to the canvas
            top_left_x = site_length * x
            top_left_y = site_length * y
            bottom_right_x = top_left_x + site_length
            bottom_right_y = top_left_y + site_length
            rectangle_colour = "white"
            rectangle_coords = (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
            site = placement_grid[y][x]
            site.canvas_id = routing_canvas.create_rectangle(rectangle_coords, fill=rectangle_colour)
            site.canvas_centre = ((top_left_x+bottom_right_x)/2, (top_left_y+bottom_right_y)/2)

    # Perform initial placement
    initial_placement(routing_canvas)

    # Event bindings and Tkinter start
    routing_canvas.focus_set()
    routing_canvas.bind("<Key>", lambda event: key_handler(routing_canvas, event))
    root.mainloop()


def initial_placement(routing_canvas):
    """
    Perform an initial placement prior to Simulated Annealing
    :param routing_canvas: Tkinter canvas
    """
    global placement_grid
    global current_cost
    global sa_temp
    global moves_per_temp_factor
    global num_cells_to_place
    global iters_per_temp
    global sa_initial_temp
    global cost_history
    global iter_history

    # Check if there are enough sites for the requisite number of cells
    if num_cells_to_place > (grid_width*grid_height):
        print("ERROR: Not enough space to place this circuit!")
        exit()

    # Get a list of all sites to place cells into
    free_sites = []
    for x in range(grid_width):
        for y in range(grid_height):
            free_sites.append((x, y))
    random.shuffle(free_sites)  # Randomize order to avoid undesired initial placement structure

    for net in net_dict.values():
        # Place the net's source
        if not net.source.isPlaced:
            place_x, place_y = free_sites.pop()
            placement_site = placement_grid[place_y][place_x]
            placement_site.occupant = net.source
            net.source.site = placement_site
            placement_site.isOccupied = True
            net.source.isPlaced = True

        # Place the net's sinks
        for sink in net.sinks:
            if not sink.isPlaced:
                place_x, place_y = free_sites.pop()
                placement_site = placement_grid[place_y][place_x]
                placement_site.occupant = sink
                sink.site = placement_site
                placement_site.isOccupied = True
                sink.isPlaced = True

        # Draw net on canvas
        if routing_canvas is not None:
            draw_net(routing_canvas, net)

    # Find the initial cost
    current_cost = calculate_total_cost()

    # Set the initial annealing temperature based on a sample of moves
    initial_cost_list = []
    for _ in range(MOVE_SAMPLE_SIZE):
        cell_a, target_x, target_y = pick_random_move()
        # Check if target site is occupied by a cell
        target_site = placement_grid[target_y][target_x]
        if target_site.isOccupied:
            cell_b = target_site.occupant
            initial_cost_list.append(get_swap_delta(cell_a, cell_b))
        else:
            initial_cost_list.append(get_move_delta(cell_a, target_x, target_y))
    sample_cost_sum = 0
    for cost in initial_cost_list:
        sample_cost_sum += cost
    mean_sample_cost = sample_cost_sum/MOVE_SAMPLE_SIZE
    std_dev = 0
    for cost in initial_cost_list:
        std_dev += (cost-mean_sample_cost)**2
    std_dev /= MOVE_SAMPLE_SIZE-1
    std_dev = sqrt(std_dev)
    sa_initial_temp = initial_temp_factor * std_dev
    print("Initial temperature: " + str(sa_initial_temp))
    sa_temp = sa_initial_temp

    # Store for plotting
    cost_history.append(current_cost)
    iter_history.append(total_iters)
    temperature_history.append(sa_temp)

    # Set the number of iterations at a given temperature
    iters_per_temp = moves_per_temp_factor * (num_cells_to_place ** (4 / 3))


def draw_net(routing_canvas, net):
    """
    Draw a net on the canvas from scratch
    """
    global unique_line_list

    # Check that net is fully placed
    if not net.source.isPlaced:
        return
    for sink in net.sinks:
        if not sink.isPlaced:
            return

    # Draw line between cells
    for sink in net.sinks:
        if routing_canvas is not None:
            line_id = draw_line(routing_canvas, net.source, sink)
            new_line = Line(net.source, sink, line_id)
        else:
            new_line = Line(net.source, sink, -1)
        net.lines.append(new_line)
        unique_line_list.append(new_line)


def draw_line(routing_canvas, source: Cell, sink: Cell):
    """
    Draws a line between two placed cells
    """

    # Get line coordinates
    source_centre = source.site.canvas_centre
    source_x = source_centre[0]
    source_y = source_centre[1]
    sink_centre = sink.site.canvas_centre
    sink_x = sink_centre[0]
    sink_y = sink_centre[1]

    # Draw the line
    line_id = routing_canvas.create_line(source_x, source_y, sink_x, sink_y, fill='red', width=0.01)

    return line_id


def redraw_line(routing_canvas, line: Line):
    """
    Redraw an existing line.
    Used when the line's source or sink has moved since last draw.
    """
    source_centre = line.source.site.canvas_centre
    source_x = source_centre[0]
    source_y = source_centre[1]
    sink_centre = line.sink.site.canvas_centre
    sink_x = sink_centre[0]
    sink_y = sink_centre[1]
    routing_canvas.coords(line.canvas_id, source_x, source_y, sink_x, sink_y)


def key_handler(routing_canvas, event):
    """
    Accepts a key event and makes an appropriate decision.
    :param routing_canvas: Tkinter canvas
    :param event: Key event
    :return: void
    """

    e_char = event.char
    if e_char == '0':
        sa_to_completion(routing_canvas)
    elif str.isdigit(e_char):
        sa_multistep(routing_canvas, int(e_char))
    else:
        pass


def sa_to_completion(routing_canvas):
    """
    Execute Simulated Annealing to completion.
    :param routing_canvas: Tkinter canvas
    :return: void
    """

    start = time.time()  # Record time taken for full placement
    while not placement_done:
        sa_step(routing_canvas)
    end = time.time()
    elapsed = end - start
    print("Took " + str(elapsed))

    # Write results to file
    outfile_name = hyperparam_string + str(file_name[:-4]) + ".csv"
    with open(outfile_name, "w") as f:
        for iters in iter_history:
            f.write(str(iters) + ",")
        f.write("\n")
        for cost in cost_history:
            f.write(str(cost) + ",")
        f.write("\n")
        for temp in temperature_history:
            f.write(str(temp) + ", ")
        f.write("\n")
        f.write(str(elapsed))


def sa_multistep(routing_canvas, n):
    """
    Perform multiple iterations of SA
    :param routing_canvas: Tkinter canvas
    :param n: Number of iterations
    :return: void
    """

    if n != 1:
        # Use an exponential series to make keyboard usage easier
        # E.g. user types '2', perform 10^2=100 steps, type '6' to perform 10^10=1,000,000 steps
        steps = 10**n
    else:
        # Special rule when user types '1', just progress through a single step for fine-grain observation
        steps = n

    # Perform the SA steps
    for _ in range(steps):
        if placement_done:
            break
        sa_step(routing_canvas)

    # Redraw lines on GUI to reflect current state of anneal
    if routing_canvas is not None:
        redraw_all_lines(routing_canvas)


def sa_step(routing_canvas):
    """
    Perform a single iteration of SA
    :param routing_canvas: Tkinter canvas
    :return: void
    """
    global placement_done
    global iters_this_temp
    global sa_temp
    global sa_initial_temp
    global current_cost
    global total_iters
    global prev_temp_cost
    global root

    # Choose move randomly
    cell_a, target_x, target_y = pick_random_move()

    # Check if target site is occupied by a cell
    target_site = placement_grid[target_y][target_x]
    cell_b = None
    if target_site.isOccupied:
        cell_b = target_site.occupant
        # Calculate theoretical cost difference
        delta = get_swap_delta(cell_a, cell_b)
    else:
        # Calculate theoretical cost difference
        delta = get_move_delta(cell_a, target_x, target_y)

    # Generate random decision boundary
    decision_value = random.random()
    decision_boundary = exp(-1*delta/sa_temp)

    # Check if move will be taken
    if decision_value < decision_boundary:
        if target_site.isOccupied:
            swap(cell_a, cell_b, delta)
        else:
            move(cell_a, target_x, target_y, delta)

    # Check for temperature update
    iters_this_temp += 1
    if iters_this_temp >= iters_per_temp:
        if routing_canvas is not None:
            redraw_all_lines(routing_canvas)
        if root is not None:
            root.update_idletasks()  # Update the Tkinter GUI

        # Reduce temperature
        sa_temp *= cooling_factor
        total_iters += iters_this_temp
        iters_this_temp = 0

        # Heartbeat
        print("Temperature: " + str(sa_temp) + "; Cost: " + str(current_cost) + "; Iterations: " + str(total_iters))

        # Store data for plot
        cost_history.append(current_cost)
        iter_history.append(total_iters)
        temperature_history.append(sa_temp)

        if (prev_temp_cost-current_cost)/current_cost < COST_EXIT_RATIO and \
                sa_temp/sa_initial_temp < TEMP_EXIT_RATIO:
            # Placement is complete
            placement_done = True
            # Plot cost history and save data
            plt.plot(iter_history, cost_history, '.', color="black")
            plt.xlabel("Sim. Anneal. Iterations")
            plt.ylabel("HPWL Cost")
            outplot_name = hyperparam_string + str(file_name[:-4]) + ".png"
            plt.savefig(outplot_name)
            plt.show()
            print("Final cost: " + str(current_cost))
            print("Total iterations: " + str(total_iters))

        prev_temp_cost = current_cost  # Note the cost at this temp for the next temp's calculations


def redraw_all_lines(routing_canvas: Canvas):
    """
    Redraw all of the lines in the GUI from scratch.
    """
    global unique_line_list

    for line in unique_line_list:
        redraw_line(routing_canvas, line)


def move(cell: Cell, x: int, y: int, delta: float):
    """
    Move a cell to an empty site
    """
    global current_cost
    global sa_temp

    # Move the cell
    old_site = cell.site
    cell.site = placement_grid[y][x]
    cell.site.isOccupied = True
    cell.site.occupant = cell
    old_site.isOccupied = False
    old_site.occupant = None

    # Update total cost
    current_cost += delta


def swap(cell_a: Cell, cell_b: Cell, delta: float):
    """
    Swap the locations (occupied sites) of two cells
    """
    global current_cost

    # Swap the cells
    temp_site = cell_a.site
    cell_a.site = cell_b.site
    cell_b.site = temp_site
    cell_a.site.occupant = cell_a
    cell_b.site.occupant = cell_b

    # Update total cost
    current_cost += delta


def get_move_delta(cell: Cell, x: int, y: int) -> float:
    """
    Calculate the cost difference that would be incurred by moving a cell to an unoccpied site
    :return: float - The cost difference
    """
    # Get the initial cost sum of all the nets the cell is in
    starting_cost = 0
    for net in cell.nets:
        starting_cost += hpwl(net)

    # Perform a temporary move
    temp_site = cell.site
    cell.site = placement_grid[y][x]

    # Calculate new cost
    final_cost = 0
    for net in cell.nets:
        final_cost += hpwl(net)

    # Reverse the temporary move
    cell.site = temp_site

    return final_cost - starting_cost


def get_swap_delta(cell_a: Cell, cell_b: Cell) -> float:
    """
    Calculate the cost difference that would be incurred by swapping two cells
    :return: float - The cost difference
    """
    # Get the initial cost sum of all nets the target cells are found in
    starting_cost = 0
    unique_net_list = []  # cell_a and cell_b could share nets, need to avoid double entries
    for net_a in cell_a.nets:
        unique_net_list.append(net_a)
    for net_b in cell_b.nets:
        if net_b not in unique_net_list:
            unique_net_list.append(net_b)
    for unique_net in unique_net_list:
        starting_cost += hpwl(unique_net)

    # Perform a temporary swap
    temp_site = cell_b.site
    cell_b.site = cell_a.site
    cell_a.site = temp_site

    # Calculate new cost
    final_cost = 0
    for unique_net in unique_net_list:
        final_cost += hpwl(unique_net)

    # Reverse the temporary swap
    cell_a.site = cell_b.site
    cell_b.site = temp_site

    return final_cost - starting_cost


def hpwl(net: Net) -> float:
    """
    Calculate the Half-Perimeter Wire Length of a net
    :param net: Net to calculate HPWL for
    :return: int - HPWL
    """
    # Find net's bounding box
    source = net.source
    leftmost_x = source.site.x
    rightmost_x = leftmost_x
    lowest_y = source.site.y
    highest_y = lowest_y
    for sink in net.sinks:
        sink_site = sink.site
        site_x = sink_site.x
        site_y = sink_site.y
        if site_x < leftmost_x:
            leftmost_x = site_x
        elif site_x > rightmost_x:
            rightmost_x = site_x
        if site_y > lowest_y:  # Recall that y values increase going "down" the grid
            lowest_y = site_y
        elif site_y < highest_y:
            highest_y = site_y

    # Calculate HPWL from bounding box
    return float((rightmost_x-leftmost_x) + (lowest_y-highest_y))


def pick_random_move():
    """
    Pick a random cell and a random spot to move that cell to
    :return: (Cell,int,int) - cell,x,y
    """
    cell_idx = random.randrange(num_cells_to_place)
    cell = cell_dict[cell_idx]
    target_y = random.randrange(grid_height)
    target_x = random.randrange(grid_width)

    # Ensure target is not the cell's current location
    if target_x == cell.site.x and target_y == cell.site.y:
        return pick_random_move()
    else:
        return cell, target_x, target_y


def pick_random_cell_pair():
    """
    Pick a random pair of cells
    :return: Cell 2-tuple
    """
    cell_a_idx = random.randrange(num_cells_to_place)
    cell_b_idx = random.randrange(num_cells_to_place)

    if cell_a_idx != cell_b_idx:
        cell_a = cell_dict[cell_a_idx]
        cell_b = cell_dict[cell_b_idx]
        return cell_a, cell_b
    else:
        return pick_random_cell_pair()


def create_placement_grid(routing_file) -> list[list[Site]]:
    """
    Create the 2D placement grid
    :param routing_file: Path to the file with circuit info
    :return: list[list[Cell]] - Routing grid
    """
    global num_cells_to_place
    global num_cell_connections
    global grid_width
    global grid_height
    global cell_dict
    global net_dict
    global placement_grid

    grid_line = routing_file.readline()
    # Create the routing grid
    num_cells_to_place = int(grid_line.split(' ')[0])
    num_cell_connections = int(grid_line.split(' ')[1])
    grid_height = int(grid_line.split(' ')[2])
    grid_width = int(grid_line.split(' ')[3])
    placement_grid = []
    # Create grid in column-major order
    for _ in range(grid_height):
        placement_grid.append([])
    # Populate grid with sites
    for cell_x, column in enumerate(placement_grid):
        for cell_y in range(grid_width):
            column.append(Site(x=cell_x, y=cell_y))

    # Keep a cell dictionary
    for cell_id in range(num_cells_to_place):
        cell_dict[cell_id] = Cell(cell_id)

    # Create nets
    new_net_id = -1
    for line_num, line in enumerate(routing_file):
        net_tokens = line.split(' ')
        new_net_id += 1

        if len(net_tokens) < 2:
            # Invalid line
            new_net_id += -1
            continue

        num_cells_in_net = int(net_tokens[0])

        # Create new net
        new_net = Net(line_num, num_cells_in_net)
        net_dict[line_num] = new_net

        # Add cells to net
        source_id = int(net_tokens[1])  # Add source cell first
        source_cell = cell_dict[source_id]
        new_net.source = source_cell
        source_cell.nets.append(new_net)
        for sink_idx in range(2, num_cells_in_net+1):
            sink_id = int(net_tokens[sink_idx])
            sink_cell = cell_dict[sink_id]
            new_net.sinks.append(sink_cell)
            sink_cell.nets.append(new_net)

    return placement_grid


def calculate_total_cost():
    """
    Calculate, from scratch, the total estimated cost of the circuit as currently placed.
    Estimation done with HPWL
    :return: int - HPWL cost for all nets
    """
    total_cost = 0
    for net in net_dict.values():
        total_cost += hpwl(net)
    return total_cost


if __name__ == "__main__":
    anneal()
