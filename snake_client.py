from typing import *
import sys, os, time
from socket import socket, gethostbyname
from pynput import keyboard
from local_scanner import get_local_devices, device, str_net_dev
from selector import selector, echoon, echooff
from threading import *
from utils import os_generic_clear, tcp_recv_with_length, bool_of_input

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

## Network auxiliaries

def action_on_recv(sckt : socket, n : int, on_recv) -> bytes :
  """ Tries to receive [n] bytes from [sckt]. If and when received, calls [on_recv] with the data received as argument. Useful with threading. """
  on_recv(sckt.recv(n))
  time.sleep(1)

## Establishing connection with a game server

ip_scan_start : Tuple[int, int, int, int] = (192, 168, 0, 1)
ip_scan_end : Tuple[int, int, int, int] = (192, 168, 255, 255)
if len(sys.argv) > 2 :
  ip_scan_start = tuple([int(x) for x in sys.argv[1].split('.')]) # TODO improve selection of address to scan, add a window at the beginning of the game
  ip_scan_end = tuple([int(x) for x in sys.argv[2].split('.')]) # TODO also allow to enter the name of the device rather than the IPv4 address
  # print("from", ip_scan_start, "until", ip_scan_end)
  # time.sleep(2)
else :
  print("To specify which address range to scan : python snake_client.py <min_address> <max_address>")

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
      local_devs = get_local_devices(tuple(ip_scan_start), tuple(ip_scan_end))
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
    choice = input(f"\n{errmsg}, try another device, rescan or quit ? (t,s,q)\n")
    choice = choice.lower()

if not(connection_established) :
  print("Could not establish connection with game server, quitting")
  quit()

print("Connection established with a snake_lan game server")

## Playing game

def process_restart_signal(data : bytes) -> None :
  if int.from_bytes(data) == 1 :
    print("Adversary wants a rematch !")
  elif int.from_bytes(data) == 0 :
    print("Adversary ended the game")
    quit() # TODO this only stops the thread trying to receive info, find a way to stop main thread too : look in the case where we receive this message but are still waiting for inputs on our end.
  else :
    print("Unexpected rematch message received from server :", int.from_bytes())

continue_game = True

while continue_game :
  os.system(clear_cmd)
  print(tcp_recv_with_length(server).decode()) # printing the initial board

  try :
    echooff()
    listener = keyboard.Listener(on_press = lambda k : send_keyboard_input(server, k), on_release = nothing)
    listener.start() # Start listening for keyboard inputs
    while True :
      if debug :
        print("\nwaiting for the signal for a move, or \"game over\"...")
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
  # check_restart_signal = Thread(target = lambda : action_on_recv(server, 1, process_restart_signal))
  # check_restart_signal.start()
  restart = None
  while restart is None :
    restart = bool_of_input(input("\rRematch ? (y/n)\n"), None)
  if not(restart) :
    server.send((0).to_bytes()) # signaling to the server we want to stop the game
    print("Goodbye")
    continue_game = False
  else :
    server.send((1).to_bytes()) # signaling to the server we want a rematch
    print("Waiting for the server's answer for a rematch...")
    adversary_wants_rematch = int.from_bytes(server.recv(1))
    assert(adversary_wants_rematch == 0 or adversary_wants_rematch == 1)
    if adversary_wants_rematch == 0 :
      print("Adversary declined rematch, quitting")
      continue_game = False
    else :
      continue_game = True

# TODO add possibility for client to restart a game with another server without quitting and re-running 