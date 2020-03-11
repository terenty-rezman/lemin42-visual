#!/usr/bin/env python3

import fileinput
import sys

from lemin_vis.map_parser import parse_map_str, Map
from lemin_vis.solution_parser import read_solution_file, Solution
import lemin_vis.view as view

map_data_str = ''
solution_data_str = ''

# read map and solution from standard input to strings
if len(sys.argv) < 3:
    is_reading_solution = False

    for line in fileinput.input():
        if not is_reading_solution and line.startswith('L'):
            solution_data_str += line
            is_reading_solution = True

        if is_reading_solution:
            solution_data_str += line
        else:
            map_data_str += line
else:
    # read map and solution from standard import
    map_filename = sys.argv[1]
    solution_filename = sys.argv[2]

    with open(map_filename) as map_file:
        map_data_str = map_file.read()

    with open(solution_filename) as solution_file:
        solution_data_str = solution_file.read()

try:
    map = parse_map_str(map_data_str)
except Exception as ex:
    # if map parsing failed
    map = Map()
    map.error = f"MapParseError: {repr(ex)}"

try:
    solution = read_solution_file(solution_data_str, map)
except Exception as ex:
    # if solution parsing failed
    solution = Solution()
    solution.error = f"SolutionParseError: {repr(ex)}"

view.init_and_run(map, solution)
