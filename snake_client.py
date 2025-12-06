from typing import *
import select
import sys, os, time
from socket import socket, gethostbyname
from pynput import keyboard
from local_scanner import get_local_devices, device, str_net_dev
from selector import selector, echoon, echooff
from utils import os_generic_clear

## Keyboard monitoring

accepted_direction_inputs = ['o', 'k', 'l', 'm']
keyboard_directions_arrow = {keyboard.Key.up : "o", keyboard.Key.down : "l", keyboard.Key.left : "k", keyboard.Key.right : "m"}
direction_change_allowed = False

## Display parameters
clear_cmd = os_generic_clear()

def nothing(key) :
  pass

def send_keyboard_input(key) : # server : socket, 
  global direction_change_allowed, server
  try :
    if direction_change_allowed :
      print(f"{key}, {str(key.char)} received !")
      if key.char in accepted_direction_inputs :
        server.send(str(key.char).encode())
      # if key.char == 'o' :
      #   server.send("o".encode())
      # elif key.char == 'k' :
      #   server.send("k".encode())
      # elif key.char == 'l' :
      #   server.send("l".encode())
      # elif key.char == 'm' :
      #   server.send("m".encode())
  except AttributeError :
    pass

## Network auxiliaries

def tcp_recv_with_length(sckt : socket, size : int = 4, endianness : str = 'big') :
  """ receives a message on TCP socket [sckt], prepended by its length in bytes, the length is supposed to be encoded on [size] bytes according to the [endiannes] """
  n = int.from_bytes(sckt.recv(4), endianness)
  return sckt.recv(n)

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

print(tcp_recv_with_length(server).decode()) # printing the initial board

try :
  echooff()
  listener = keyboard.Listener(on_press = send_keyboard_input, on_release = nothing)
  listener.start() # Start listening for keyboard inputs
  while True :
    print("\nwaiting for the signal for a move, or \"\game over\"...")
    msg = server.recv(11) # waiting for signal to choose a direction or game over signal
    if msg.decode() == "Game over.." :
      print("Game over received :", msg.decode())
      break

    if msg.decode() == "start moves" :
      print("START MOVES RECEIVED")
      direction_change_allowed = True
    else :
      print(f"Error : unexpected message \"{msg.decode()}\"")
      quit()

    print("WAITING FOR END_MOVES")
    msg = server.recv(9)
    print(msg)
    if msg.decode() != "end moves" :
      print("Receive something different than \"end moves\" when expected :", msg.decode())
      quit()
    print("RECEIVED END_MOVES")
    direction_change_allowed = False
    print("\n WAITING FOR THE BOARD : \n")
    # os.system(clear_cmd)
    print(tcp_recv_with_length(server).decode()) # printing the actualized board
    print("\n END BOARD : \n")
  listener.stop() # Stop listening for keyboard inputs
except UnicodeDecodeError :
  print("UnicodeDecodeError detected")
  quit()
finally :
  echoon()

## Game ended, waiting for losers list
losers = tcp_recv_with_length(server)
print("Players :", losers.decode(), "lost")