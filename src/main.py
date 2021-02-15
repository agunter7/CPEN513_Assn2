"""
Solution to UBC CPEN 513 Assignment 2.
Implements Simulated Annealing.
Uses Tkinter for GUI.
"""

import os
import random
from tkinter import *
from math import exp, sqrt

# Constants
FILE_PATH = "../benchmarks/cm151a.txt"  # Path to the file with info about the circuit to place
COOLING_FACTOR = 0.9
INITIAL_TEMP_COEFFICIENT = 50


# Global variables
num_cells_to_place = 0  # Number of cells in the circuit to be placed
num_cell_connections = 0  # Number of connections to be routed, summed across all cells/nets
grid_width = 0  # Width of the placement grid
grid_height = 0  # Height of the placement grid
cell_dict = {}  # Dictionary of all cells, key is cell ID
net_dict = {}  # Dictionary of all nets, key is net ID
placement_grid = []
cell_queue = []
placement_done = False  # Is the placement complete?
# Simulated Annealing variables
sa_temp = -1  # SA temperature
sa_initial_temp = -1  # Starting SA temperature
iters_per_temp = -1  # Number of iterations to perform at each temperature
iters_this_temp = 0  # Number of iterations performed at the current temperature
accepted_moves_this_temp = 0  # Number of moves accepted at the current temperature
current_cost = 0  # The estimated cost of the current placement


class Site:
    """
    A placement site/slot for a cell to inhabit
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.canvas_id = -1  # ID of corresponding rectangle in Tkinter canvas
        self.canvas_centre = (-1, -1)
        self.isOccupied = False
        self.occupant = None
        pass


class Cell:
    """
    A single cell
    """
    def __init__(self, cell_id):
        self.id = cell_id
        self.isPlaced = False
        self.site = None
        self.nets = []  # Nets this cell is a part of
        pass


class Line:
    """
    A wrapper class for Tkinter lines
    """
    def __init__(self, source: Cell, sink: Cell, canvas_id: int):
        self.source = source
        self.sink = sink
        self.canvas_id = canvas_id


class Net:
    """
    A collection of cells to be connected during routing
    """
    def __init__(self, net_id: int, num_cells: int):
        self.id = net_id
        self.num_cells = num_cells
        self.source = None
        self.sinks = []
        self.lines = []
        pass


def main():
    """
    Top-level main function
    :return: void
    """
    global FILE_PATH
    global num_cells_to_place
    global num_cell_connections
    global grid_width
    global grid_height
    global placement_grid

    random.seed(0)  # Set random seed

    # Read input file
    script_path = os.path.dirname(__file__)
    true_path = os.path.join(script_path, FILE_PATH)
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
    Perform an initial placement prior to SA
    :param routing_canvas: Tkinter canvas
    """
    global placement_grid
    global current_cost
    global sa_temp
    global INITIAL_TEMP_COEFFICIENT
    global num_cells_to_place
    global iters_per_temp
    global sa_initial_temp

    # Check if there are enough sites for the requisite number of cells
    if num_cells_to_place > (grid_width*grid_height):
        print("ERROR: Not enough space to place this circuit!")
        exit()

    free_sites = []
    for x in range(grid_width):
        for y in range(grid_height):
            free_sites.append((x, y))
    random.shuffle(free_sites)

    for net in net_dict.values():
        # Place the net's source
        place_x, place_y = free_sites.pop()
        placement_site = placement_grid[place_y][place_x]
        placement_site.occupant = net.source
        net.source.site = placement_site
        placement_site.isOccupied = True
        net.source.isPlaced = True

        # Place the net's sinks
        for sink in net.sinks:
            place_x, place_y = free_sites.pop()
            placement_site = placement_grid[place_y][place_x]
            placement_site.occupant = sink
            sink.site = placement_site
            placement_site.isOccupied = True
            sink.isPlaced = True

        # Draw net on canvas
        draw_net(routing_canvas, net)

    # Find the initial cost
    current_cost = calculate_total_cost()

    # Set the initial annealing temperature as 20*std_dev of cost of 50 swaps
    initial_cost_list = []
    for _ in range(50):
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
    mean_sample_cost = sample_cost_sum/50
    std_dev = 0
    for cost in initial_cost_list:
        std_dev += (cost-mean_sample_cost)**2
    std_dev /= 50-1
    std_dev = sqrt(std_dev)
    sa_initial_temp = 20*std_dev
    sa_temp = sa_initial_temp

    # Set the number of iterations at a given temperature
    iters_per_temp = INITIAL_TEMP_COEFFICIENT * (num_cells_to_place**(4/3))


def draw_net(routing_canvas, net):
    """
    Draw a net on the canvas from scratch
    """

    # Check that net is fully placed
    if not net.source.isPlaced:
        return
    for sink in net.sinks:
        if not sink.isPlaced:
            return

    # Draw line between cells
    for sink in net.sinks:
        line_id = draw_line(routing_canvas, net.source, sink)
        new_line = Line(net.source, sink, line_id)
        net.lines.append(new_line)


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

    line_id = routing_canvas.create_line(source_x, source_y, sink_x, sink_y, fill='red', width=1)

    return line_id


def redraw_line(routing_canvas, line: Line):
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
    if e_char == 'a':
        pass
    elif e_char == 'd':
        pass
    elif e_char == '0':
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

    pass


def sa_multistep(routing_canvas, n):
    """
    Perform multiple iterations of SA
    :param routing_canvas: Tkinter canvas
    :param n: Number of iterations
    :return: void
    """

    for _ in range(n):
        sa_step(routing_canvas)


def sa_step(routing_canvas):
    """
    Perform a single iteration of SA
    :param routing_canvas: Tkinter canvas
    :return: void
    """
    global placement_done
    global iters_this_temp
    global sa_temp
    global accepted_moves_this_temp
    global sa_initial_temp

    if placement_done:
        print("Placement done!")
        return

    # Choose move randomly
    cell_a, target_x, target_y = pick_random_move()

    # Check if target site is occupied by a cell
    target_site = placement_grid[target_y][target_x]
    cell_b = None
    if target_site.isOccupied:
        cell_b = target_site.occupant

        if cell_b is None:
            print("Shite")

        # Calculate theoretical delta
        delta = get_swap_delta(cell_a, cell_b)
    else:
        # Calculate theoretical delta
        delta = get_move_delta(cell_a, target_x, target_y)

    # Generate random decision boundary
    decision_value = random.random()
    decision_boundary = exp(-1*delta/sa_temp)

    # Check if move will be taken
    if decision_value < decision_boundary:
        if target_site.isOccupied:
            swap(routing_canvas, cell_a, cell_b, delta)
        else:
            move(routing_canvas, cell_a, target_x, target_y, delta)
        accepted_moves_this_temp += 1

    # Check for temperature update
    iters_this_temp += 1
    if iters_this_temp >= iters_per_temp:
        # Reduce temperature
        sa_temp *= COOLING_FACTOR
        iters_this_temp = 0
        if accepted_moves_this_temp == 0 and sa_temp/sa_initial_temp < 0.05:
            placement_done = True
        accepted_moves_this_temp = 0


def move(routing_canvas: Canvas, cell: Cell, x: int, y:int, delta: float):
    global current_cost

    # Move the cell
    old_site = cell.site
    cell.site = placement_grid[y][x]
    cell.site.isOccupied = True
    cell.site.occupant = cell
    old_site.isOccupied = False
    old_site.occupant = None

    # Redraw lines connected to the cell
    for net in cell.nets:
        for line in net.lines:
            if line.source is cell or line.sink is cell:
                redraw_line(routing_canvas, line)

    # Update total cost
    current_cost += delta


def swap(routing_canvas: Canvas, cell_a: Cell, cell_b: Cell, delta: float):
    global current_cost

    # Swap the cells
    temp_site = cell_a.site
    cell_a.site = cell_b.site
    cell_b.site = temp_site
    cell_a.site.occupant = cell_a
    cell_b.site.occupant = cell_b

    # Redraw lines connected to either cell
    for net_a in cell_a.nets:
        for line in net_a.lines:
            if line.source is cell_a or line.sink is cell_a:
                redraw_line(routing_canvas, line)
    for net_b in cell_b.nets:
        for line in net_b.lines:
            if line.source is cell_b or line.sink is cell_b:
                redraw_line(routing_canvas, line)

    # Update total cost
    current_cost += delta


def get_move_delta(cell: Cell, x: int, y: int):
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


def get_swap_delta(cell_a: Cell, cell_b: Cell):
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


def hpwl(net: Net):
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
    return (rightmost_x-leftmost_x) + (lowest_y-highest_y)


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


def add_text(routing_canvas: Canvas, cell: Cell) -> int:
    """
    Add text for the routing value of a cell to the canvas.
    To be used when adding a cell to the wavefront.
    :param routing_canvas: Tkinter canvas
    :param cell: Cell
    :return: int - Tkinter ID for added text
    """
    pass


def cleanup_candidates(routing_canvas):
    """
    Cleanup the canvas
    :param routing_canvas: Tkinter canvas
    :return: void
    """
    pass


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
    main()
