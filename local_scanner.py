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

## Main

def get_local_devices(ranges : Tuple[range, range, range, range] = ([192], [168], range(255), range(255))) -> list[device] :
  """ Scans local IPv4 addresses within [ranges]. press Ctrl+C while searching to interrupt the search. Default search : 192.168.*.*. """
  local_devs : list[device] = []
  try :
    echooff()
    for i in ranges[0] :
      for j in ranges[1] :
        for k in ranges[2] :
          for l in ranges[3] :
            try :
              print(f"\r{i}.{j}.{k}.{l}         ", sep = "", end = "")
              dev : device = socket.gethostbyaddr(f"{i}.{j}.{k}.{l}")
              print("\n", len(local_devs), " | ", str_net_dev(dev), sep = "")
              local_devs.append(dev)
            except socket.herror :
              pass
  except KeyboardInterrupt :
    echoon()
    pass
  finally :
    echoon()
  return local_devs
  
