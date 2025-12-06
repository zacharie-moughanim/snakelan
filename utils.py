from typing import *
from enum import Enum
import sys
import socket

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

def bool_of_input(s : str, default : bool = True) -> bool | None :
  """ For an input choice of the form (y/n), (Y/n) or (y/N), returns the associated boolean, with the [default] value in case of empty input """
  if s == "" :
    return default
  else :
    s = s.lower()
    if s == "y" :
      return True
    elif s == "n" :
      return False
    else :
      return None

def os_generic_clear() -> str :
  syspm = sys.platform
  if syspm == 'linux' :
    return "clear"
  elif syspm == 'cygwin' :
    return "clear"  # FIXME not sure this is the clear command
  elif syspm == 'win32' :
    return "cls"
  elif syspm == 'darwin' :
    return "clear"   # FIXME not sure this is the clear command
  else :
    print("Unsupported os, defaulting to \"clear\" to clear console screen, display may be faulty")
    return "clear"

## Network auxiliaries

def tcp_recv_with_length(sckt : socket, size : int = 4, endianness : str = 'big') :
  """ receives a message on TCP socket [sckt], prepended by its length in bytes, the length is supposed to be encoded on [size] bytes according to the [endiannes] """
  n = int.from_bytes(sckt.recv(4), endianness)
  return sckt.recv(n)

def tcp_send_with_length(sckt : socket, msg : bytes, size : int = 4, endianness : str = 'big') :
  """ sends [msg] on TCP socket [sckt], prepended by its length in bytes, the length is encoded on [size] bytes """
  n = len(msg)
  assert (n < 2**32) # to send the length on 4 bytes this must be verified, although we have other problems if we try to send 4 GB over the network for a game of snake
  sckt.send(n.to_bytes(4, endianness)) # TODO check canonical endianness for network communications
  sckt.send(msg)
