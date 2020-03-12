#!/usr/bin/env python3

import fileinput
import sys
from itertools import tee, islice

from lemin_vis.map_parser import parse_map_str, Map
from lemin_vis.solution_parser import parse_solution_str, Solution
import lemin_vis.view as view


def extract_map_and_solution(input_data):
    solution_begin = input_data.find('L')

    if solution_begin == -1:
        solution_begin = input_data.find("ERROR")

    i1, i2 = tee(input_data)

    i1 = islice(i1, solution_begin)
    i2 = islice(i2, solution_begin, None)

    map_data = ''.join(i1)
    solution_data = ''.join(i2)

    return (map_data, solution_data)


# read map and solution from standard input
if len(sys.argv) < 2:
    input_data = sys.stdin.read()
else:
    # read map and solution from file specified as arg
    map_solution_filename = sys.argv[1]

    with open(map_solution_filename) as map_file:
        input_data = map_file.read()

try:
    map_data, solution_data = extract_map_and_solution(input_data)
except Exception as ex:
    print("ExtractionError: could not separate map data from solution data")
    sys.exit()

try:
    map = parse_map_str(map_data)
except Exception as ex:
    # if map parsing failed
    map = Map()
    map.error = f"MapParseError: {repr(ex)}"

try:
    solution = parse_solution_str(solution_data, map)
except Exception as ex:
    # if solution parsing failed
    solution = Solution()
    solution.error = f"SolutionParseError: {repr(ex)}"

view.init_and_run(map, solution)
