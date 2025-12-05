from typing import Any
from pynput import keyboard
import subprocess

choice = 0
choice_confirmed = False
n = 0

def echooff():
    subprocess.run(['stty', '-echo'], check=True)
def echoon():
    subprocess.run(['stty', 'echo'], check=True)

def print_selection(i_choice, choices, str_of_choice) :
  for i, x in enumerate(choices) :
    if i == i_choice :
      left_par = '>'
      right_par = '<'
    else :
      left_par = ' '
      right_par = ' '
    print(left_par + str_of_choice(x) + right_par + "  ", end = "", flush = True)

def nothing(key) :
  pass

def on_press(key):
  global choice, choice_confirmed
  try :
    if key == keyboard.Key.enter :
      choice_confirmed = True
      return False
    # key.char raise [AttributeError] on e.g. enter, thus we test if the key is enter beforehand
    elif key == keyboard.Key.left :
      if 0 < choice :
        choice -= 1
      return False
    elif key == keyboard.Key.right :
      if choice < n - 1 :
        choice += 1
      return False
  except AttributeError :
    pass


def selector(choices : list[Any], str_of_choice = str) -> Any :
  global choice, choice_confirmed, n
  n = len(choices)
  choice = 0
  choice_confirmed = False
  print("Choose :")
  try :
    echooff()
    while not(choice_confirmed) :
      print(end = "\r")
      print_selection(choice, choices, str_of_choice)
      with keyboard.Listener(on_press = on_press, on_release = nothing) as listener :
        listener.join()
  finally :
    echoon()
  return choice
