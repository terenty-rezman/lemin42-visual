import itertools
from dataclasses import dataclass
from collections import namedtuple
from enum import Enum

Coords = namedtuple("Coords", "x y")
RoomType = Enum("RoomType", "start end")


@dataclass
class Room:
    name: str
    coords: Coords
    type: RoomType


@dataclass
class Link:
    from_: Room  # 'from' is a keyword in python
    to_: Room    # underscore for consistency


class Map:
    def __init__(self):
        self.number_of_ants: int = 0
        self.rooms: dict = {}
        self.links: list = []
        self.start_room: Room = None
        self.end_room: Room = None
        self.error: str = None


def read_map_file(filename):
    map = Map()

    with open(filename) as map_file:
        # read 1st line: number of ants
        map.number_of_ants = int(map_file.readline())

        # read "room" lines until first "link" line is encountered
        map_file_iter = iter(map_file)
        room_type = None

        for room_line in map_file_iter:
            # eliminate trailing "\n"
            room_line = room_line.strip()

            # ignore comment lines
            if is_comment_line(room_line):
                continue

            # first "link" line read -> put it back and proceed to reading "link" rooms
            if is_link_line(room_line):
                # "put link line back to iterator"
                map_file_iter = itertools.chain((room_line,), map_file_iter)
                break

            # ##start or ##end room
            if is_command_line(room_line):
                room_type = parse_command_line(room_line)
                continue

            # create room and add to collection
            room = parse_room_line(room_line, room_type)
            map.rooms[room.name] = room

            # store start and end rooms
            if room_type == RoomType.start:
                map.start_room = room
            if room_type == RoomType.end:
                map.end_room = RoomType.end

            room_type = None

        # read link lines
        for link_line in map_file_iter:
            # eliminate trailing "\n"
            link_line = link_line.strip()

            # ignore comment lines
            if is_comment_line(link_line):
                continue

            # create link and add to collection
            link = parse_link_line(link_line, map.rooms)
            map.links.append(link)

    return map


def is_comment_line(line):
    return True if line[0] == '#' and line[1] != '#' else False


def is_link_line(line):
    return True if '-' in line else False


def is_command_line(line):
    return True if line.startswith('##') else False


def parse_command_line(line):
    type_str = line[2:]
    if type_str == 'start':
        return RoomType.start
    elif type_str == 'end':
        return RoomType.end

    return None


def parse_room_line(line, room_type):
    data = line.split(' ')
    room_name = str(data[0])
    x = int(data[1])
    y = int(data[2])

    return Room(room_name, Coords(x, y), room_type)


def parse_link_line(line, rooms):
    data = line.split('-')
    from_room_name = str(data[0])
    to_room_name = str(data[1])

    return Link(rooms[from_room_name], rooms[to_room_name])
