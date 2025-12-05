## Typing
from typing import Dict, Tuple, List, Any
device = Tuple[str, List[str], List[str]]

## Imports
import socket
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

## Main

def get_local_devices() -> list[device] :
  local_devs : list[device] = []
  try :
    for i in range(255) :
      for j in range(255) :
        try :
          print(f"\r", sep = "", end = "")
          dev : device = socket.gethostbyaddr(f"192.168.{i}.{j}")
          print(len(local_devs), "|", str_net_dev(dev))
          local_devs.append(dev)
        except socket.herror :
          pass
  except KeyboardInterrupt :
    pass
  return local_devs
  
