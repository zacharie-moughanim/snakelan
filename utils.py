from typing import *
from enum import Enum

class Cell(Enum) :
  EMPTY = 0
  WALL = 1
  APPLE = 2
  SNAKE = 3

class Dir(Enum) :
  NORTH = 0
  SOUTH = 1
  EAST = 2
  WEST = 3

def dir_of_string(s : str) -> Dir :
  match s :
    case "N" :
      return Dir.NORTH
    case "NORTH" :
      return Dir.NORTH
    case "S" :
      return Dir.SOUTH
    case "SOUTH" :
      return Dir.SOUTH
    case "E" :
      return Dir.EAST
    case "EAST" :
      return Dir.EAST
    case "W" :
      return Dir.WEST
    case "WEST" :
      return Dir.WEST
    case _ :
      print("Dir.of_string(s) : s must be NORTH, SOUTH, EAST, WEST or first letters of one of them")
      assert(False)

def is_opposite_direction(dir1 : Dir, dir2 : Dir) :
  match dir1, dir2 :
    case Dir.NORTH, Dir.SOUTH :
      return True
    case Dir.WEST, Dir.EAST :
      return True
    case Dir.SOUTH, Dir.NORTH :
      return True
    case Dir.EAST, Dir.WEST :
      return True
    case _ :
      return False

class State(Enum) :
  NOT_STARTED = 0
  ONGOING = 1
  ENDED = 2

def next_coordinates(x : int, y : int, dir : Dir) -> tuple[int, int] :
  """ returns the cell adjacent to [(x, y)], following the direction [dir] """
  match dir :
    case Dir.NORTH :
      return (x - 1, y)
    case Dir.SOUTH :
      return (x + 1, y)
    case Dir.WEST :
      return (x, y - 1)
    case Dir.EAST :
      return (x, y + 1)

def look_around(grid : list[list[Any]], x : int, y : int) -> list[Any] :
  """ given [grid] a matrix, returns a list of each adjacent case to [(x, y)] in the order : [N, S, E, O], None if at a border """
  res = [None, None, None, None]
  width = len(grid)
  height = len(grid[0])
  if 0 < x :
    res[0] = grid[x - 1][y]
  if x < width :
    res[1] = grid[x + 1][y]
  if 0 < y :
    res[2] = grid[x][y - 1]
  if y < height :
    res[3] = grid[x][y + 1]
  return res

def join(t : list[Any], sep : str, last_sep : str | None = None) -> str :
  """ [join [Person 1, Person 2, Person 3] ", " " and "] returns the string "Person 1, Person2 and Person3", [last_sep] is set to [sep] by default """
  res = ""
  if last_sep is None :
    last_sep = sep
  for i, x in enumerate(t) :
    if i == 0 :
      res += str(x)
    elif i == len(t) - 1 :
      res += (last_sep + str(x))
    else :
      res += (sep + str(x))
  return res