from dataclasses import dataclass


def mix(x, y, a):
    """
        linear blend between two values,
        'a' in [0 1]
    """
    return x*(1 - a) + y*a


@dataclass
class Rect():
    top: int
    left: int
    bottom: int
    right: int


class Ant:
    def __init__(self, start_room):
        self.steps = dict()

        self.start_room = start_room
        self.current_room = start_room
        self.next_room = start_room

        self.x = start_room.coords.x
        self.y = start_room.coords.y

    def set_step(self, step):
        if int(step) not in self.steps:
            return

        self.compute_position(step)

    def compute_position(self, step):
        integer_step = int(step)
        self.current_room = self.steps[integer_step]

        next_step = integer_step + 1

        self.next_room = self.steps[next_step] if next_step in self.steps else self.current_room

        blend_coef = step - integer_step

        # linear interpolation between room coordinates
        self.x = mix(self.current_room.coords.x,
                     self.next_room.coords.x, blend_coef)
        self.y = mix(self.current_room.coords.y,
                     self.next_room.coords.y, blend_coef)


class Solution:
    def __init__(self):
        self.ants: dict = {}
        self.number_of_steps: int = 0
        self.error: str = None
        self.rect: Rect = None

    def set_step(self, step):
        """
            move all ants to the rooms they should be on given step,
            if step is intermideate value e.g. 1.5
            ants position is interpolated between rooms on steps e.g. [1 2]
        """
        for ant in self.ants.values():
            ant.set_step(step)


def read_solution_file(filename, map):
    solution = Solution()

    # create ants
    for i in range(map.number_of_ants):
        ant_id = str(i+1)  # ant numbers start with 1 not 0
        solution.ants[ant_id] = Ant(map.start_room)

    # parse solution file
    with open(filename) as solution_file:
        solution_step = 1

        for line in solution_file:
            # eliminate trailing \n
            line = line.strip()

            ants_per_line = line.split(' ')
            for ant_state in ants_per_line:
                # separate ant name from room
                separated_data = ant_state.split('-')

                # [1:] to discard "L" in ant name like "L1"
                ant_id = separated_data[0][1:]

                room_name = separated_data[1]

                solution.ants[ant_id].steps[solution_step] = map.rooms[room_name]

            solution_step += 1

        solution.number_of_steps = solution_step

    # additional processing for visualization
    # add initial step to each ant where they start from start room
    ants_add_initial_step(solution, map)

    solution.rect = find_solution_rect(solution, map)

    return solution


def ants_add_initial_step(solution, map):
    for ant in solution.ants.values():
        first_step = min(ant.steps.keys())
        zero_step = first_step - 1
        ant.steps[zero_step] = map.start_room


def find_solution_rect(solution, rect):
    "find rect that encloses all solution rooms"
    top = float('+inf')
    left = float('+inf')
    bottom = float('-inf')
    right = float('-inf')

    for ant in solution.ants.values():
        for room in ant.steps.values():
            if room.coords.y < top:
                top = room.coords.y
            elif room.coords.y > bottom:
                bottom = room.coords.y

            if room.coords.x < left:
                left = room.coords.x
            elif room.coords.x > right:
                right = room.coords.x

    return Rect(top, left, bottom, right)
