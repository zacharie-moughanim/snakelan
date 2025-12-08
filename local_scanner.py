## Typing
from typing import Dict, Tuple, List, Any
device = Tuple[str, List[str], List[str]]
address = str

## Imports
import socket
from selector import echooff, echoon
from pynput import keyboard

## Pretty printing

def join(t : list[Any], sep : str = ", ", last_sep : str | None = None) -> str :
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

def str_net_dev(dev : device) :
  res : List[str] = ["Name : " + dev[0]]
  if dev[1] != [] :
    res.append("alias.es : " + join(dev[1], last_sep = "and"))
  res.append("address : " + join(dev[2], last_sep = "and"))
  return join(res)
  return f"Name : {dev[0]}, alias(es) : {join(dev[1])}, address : {join(dev[2])}"

def next_address(addr : tuple[int, int, int, int]) -> tuple[int, int, int, int] :
  """ returns the next address of [addr] """
  assert(0 <= addr[0] <= 255)
  assert(0 <= addr[1] <= 255)
  assert(0 <= addr[2] <= 255)
  assert(0 <= addr[3] <= 255)
  if addr[3] < 255 :
    return (addr[0], addr[1], addr[2], addr[3] + 1)
  elif addr[2] < 255 :
    return (addr[0], addr[1], addr[2] + 1, 0)
  elif addr[1] < 255 :
    return (addr[0], addr[1] + 1, 0, 0)
  elif addr[0] < 255 :
    return (addr[0] + 1, 0, 0, 0)
  else :
    raise ValueError("Trying to increment maximum IPv4 address")

## Main

def get_local_devices(lower_address : tuple[int, int, int, int] = (192, 168, 0, 1), upper_address : tuple[int, int, int, int] = (192, 168, 255, 255)) -> list[device] :
  """ Scans local IPv4 addresses within [lower_address] (included) and [upper_address] (excluded). Press Ctrl+C while searching to interrupt the search. Default search : 192.168.*.*. """
  local_devs : list[device] = []
  try :
    echooff()
    addr = lower_address
    while addr != upper_address :
      try :
        print(f"\r{addr[0]}.{addr[1]}.{addr[2]}.{addr[3]}         ", sep = "", end = "")
        dev : device = socket.gethostbyaddr(f"{addr[0]}.{addr[1]}.{addr[2]}.{addr[3]}")
        print("\n", len(local_devs), " | ", str_net_dev(dev), sep = "")
        local_devs.append(dev)
      except socket.herror :
        pass
      addr = next_address(addr)
  except KeyboardInterrupt :
    echoon()
    pass
  finally :
    echoon()
  return local_devs
  
