"""
Solution to UBC CPEN 513 Assignment 2.
Implements Simulated Annealing.
Uses Tkinter for GUI.
"""

import os
from tkinter import *
from enum import Enum
from queue import PriorityQueue

# Constants
FILE_PATH = "../benchmarks/cm151a.txt"  # Path to the file with info about the circuit to place

# Global variables
num_cells_to_place = 0  # Number of cells in the circuit to be placed
num_cell_connections = 0  # Number of connections to be routed, summed across all cells/nets
grid_width = 0  # Width of the placement grid
grid_height = 0  # Height of the placement grid
cell_dict = {}  # Dictionary of all cells, key is cell ID
net_dict = {}  # Dictionary of all nets, ket is net ID
placement_grid = None


class Site:
    """
    A placement site/slot for a cell to inhabit
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.canvas_id = -1  # ID of corresponding rectangle in Tkinter canvas
        pass


class Cell:
    """
    A single cell
    """
    def __init__(self, cell_id):
        self.id = cell_id
        pass


class Net:
    """
    A collection of cells to be connected during routing
    """
    def __init__(self, net_id: int, num_cells: int):
        self.id = net_id
        self.num_cells = num_cells
        self.source = None
        self.sinks = []
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

    # Read input file
    script_path = os.path.dirname(__file__)
    true_path = os.path.join(script_path, FILE_PATH)
    routing_file = open(true_path, "r")

    # Setup the routing grid/array
    create_placement_grid(routing_file)

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
            rectangle_colour = "blue"
            rectangle_coords = (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
            (placement_grid[x][y]).canvas_id = routing_canvas.create_rectangle(rectangle_coords, fill=rectangle_colour)

    # Event bindings and Tkinter start
    routing_canvas.focus_set()
    routing_canvas.bind("<Key>", lambda event: key_handler(routing_canvas, event))
    root.mainloop()


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
        algorithm_to_completion(routing_canvas)
    elif str.isdigit(e_char):
        algorithm_multistep(routing_canvas, int(e_char))
    else:
        pass


def algorithm_to_completion(routing_canvas):
    """
    Execute Simulated Annealing to completion.
    :param routing_canvas: Tkinter canvas
    :return: void
    """

    pass


def algorithm_multistep(routing_canvas, n):
    """
    Perform multiple iterations of SA
    :param routing_canvas: Tkinter canvas
    :param n: Number of iterations
    :return: void
    """
    pass


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
    for _ in range(grid_width):
        placement_grid.append([])
    # Populate grid with sites
    for cell_x, column in enumerate(placement_grid):
        for cell_y in range(grid_height):
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

        print(net_tokens)
        num_cells_in_net = int(net_tokens[0])

        # Create new net
        new_net = Net(line_num, num_cells_in_net)
        net_dict[line_num] = new_net

        # Add cells to net
        source_id = int(net_tokens[1])  # Add source cell first
        new_net.source = cell_dict[source_id]
        for sink_idx in range(2, num_cells_in_net):
            sink_id = int(net_tokens[sink_idx])
            new_net.sinks.append(cell_dict[sink_id])

    return placement_grid


if __name__ == "__main__":
    main()
