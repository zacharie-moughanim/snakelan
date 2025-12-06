from typing import *
import select
import sys, os, time
from socket import socket, gethostbyname
from pynput import keyboard
from local_scanner import get_local_devices, device, str_net_dev
from selector import selector, echoon, echooff
from utils import os_generic_clear, tcp_recv_with_length

debug = False

## Keyboard monitoring

accepted_direction_inputs = ['o', 'k', 'l', 'm']
keyboard_directions_arrow = {keyboard.Key.up : "o", keyboard.Key.down : "l", keyboard.Key.left : "k", keyboard.Key.right : "m"}
direction_change_allowed = False

## Display parameters
clear_cmd = os_generic_clear()

def nothing(key) :
  pass

def send_keyboard_input(server : socket, key) : # TODO re-add this argument : server : socket, instead of a global 
  global direction_change_allowed
  try :
    if direction_change_allowed :
      if debug :
        print(f"{key}, {str(key.char)} received !")
      if key.char in accepted_direction_inputs :
        server.send(str(key.char).encode())
  except AttributeError :
    pass

## Establishing connection with a game server

connection_established : bool = False
choice : str = "s"
addr : str = ""
local_devs : List[device] = []
errmsg : str = ""
while not(connection_established) and choice != "q" :
  server : socket = socket()
  errmsg = ""
  try :
    os.system(clear_cmd)
    if choice == "s" :
      print("Scanning local network for devices...")
      local_devs = get_local_devices()
    print("Who to play with ?")
    addr = local_devs[selector(local_devs, lambda dev : str(dev[0]))][2][0]
    server.connect((addr, 9999))
    connection_established = True
    msg = server.recv(12)
    os.system(clear_cmd)
    if msg.decode() == "game start ?" :
      server.send("game startOK".encode())
    else :
      errmsg = "Distant server is not a snake_lan server"
  except ConnectionRefusedError :
    errmsg = "Connection refused"
  if errmsg != "" :
    server.detach()
    connection_established = False
    input()
    choice = input(f"\n{errmsg}, try another device, rescan or quit ? (T,s,q)\n")
    if choice == "" :
      choice = "t"
    else :
      choice = choice.lower()

if not(connection_established) :
  print("Could not establish connection with game server, quitting")
  quit()

print("Connection established with a snake_lan game server")

## Playing game
os.system(clear_cmd)
print(tcp_recv_with_length(server).decode()) # printing the initial board

try :
  echooff()
  listener = keyboard.Listener(on_press = lambda k : send_keyboard_input(server, k), on_release = nothing)
  listener.start() # Start listening for keyboard inputs
  while True :
    if debug :
      print("\nwaiting for the signal for a move, or \"\game over\"...")
    msg = server.recv(11) # waiting for signal to choose a direction or game over signal
    if msg.decode() == "Game over.." :
      if debug :
        print("Game over received :", msg.decode())
      break

    if msg.decode() == "start moves" :
      if debug :
        print("RECEIVED START MOVES")
      direction_change_allowed = True
    else :
      print(f"Error : unexpected message \"{msg.decode()}\", expected \"start moves\"")
      quit()
    if debug :
      print("WAITING FOR END_MOVES")
    msg = server.recv(9)
    if debug :
      print(msg)
    if msg.decode() != "end moves" :
      print(f"Error : unexpected message \"{msg.decode()}\", expected \"end moves\"")
      quit()
    if debug :
      print("RECEIVED END_MOVES")
    direction_change_allowed = False
    if debug :
      print("\n WAITING FOR THE BOARD : \n")
    os.system(clear_cmd)
    print(tcp_recv_with_length(server).decode()) # printing the actualized board
    if debug :
      print("\n RECEIVED BOARD : \n")
  listener.stop() # Stop listening for keyboard inputs
finally :
  echoon()

## Game ended, waiting for losers list
losers = tcp_recv_with_length(server)
print("Players :", losers.decode(), "lost")