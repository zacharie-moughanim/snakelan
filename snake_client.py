import select
import sys, os, time
from socket import socket, gethostbyname
from pynput import keyboard
from local_scanner import get_local_devices, device, str_net_dev
from selector import selector

def select_local_server() -> device :
  local_devs = get_local_devices()
  return local_devs[selector(local_devs, lambda dev : str(dev[0]))]

keyboard_directions_arrow = {keyboard.Key.up : "z", keyboard.Key.down : "s", keyboard.Key.left : "q", keyboard.Key.right : "d"}

server = socket()
addr = select_local_server()[2][0]
server.connect((addr, 9999))

msg, a = server.recvfrom(1024)
os.system("clear")
print(msg.decode())

timeout_msg = server.recv(4) # timeout to make a move
print(f"\nThe timeout for a move is set to : {int.from_bytes(timeout_msg)}\n")

timeout = int.from_bytes(timeout_msg)

while True :
  print("\nwaiting for the signal for a move, or \"\\ngame over\"\n")
  msg = server.recv(64) # waiting for signal to choose a direction
  if msg.decode() == "\ngame over\n" :
    print("Game over received")
    break
  print(msg.decode())

  print("START LISTENING")
  # The event listener will be running in this block
  with keyboard.Events() as events:
    # Block at most one second
    event = events.get(float(timeout))
    if event is None:
      print('You did not press a key within one second')
      server.send("n".encode())
    else:
      if event.key in keyboard_directions_arrow :
        server.send(keyboard_directions_arrow[event.key].encode())
      else :
        server.send("n".encode())

  msg = server.recv(64)
  while msg.decode() != "round over\n" :
    # while we did not receive the end of round signal, we print the messages received
    print(msg.decode())
    print("\n waiting for error messages and stuff (like \"round over\") \n")
    msg = server.recv(64)
  print("\n waiting for the board \n")
  os.system('clear')
  print(server.recv(1024).decode()) # printing the actualized board
