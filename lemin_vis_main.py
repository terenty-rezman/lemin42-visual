from lemin_map_parser import read_map_file, Map
from lemin_solution_parser import read_solution_file, Solution
import lemin_view

try:
    map = read_map_file("maps/big.map")
except Exception as ex:
    # if map parsing failed
    map = Map()
    map.error = f"MapParseError: {repr(ex)}"

try:
    solution = read_solution_file('solution3.txt', map)
except Exception as ex:
    # if solution parsing failed
    solution = Solution()
    solution.error = f"SolutionParseError: {repr(ex)}"

lemin_view.init_and_run(map, solution)
