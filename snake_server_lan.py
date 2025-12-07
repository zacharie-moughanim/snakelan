from snake import *# TODO replace * by the needed functions
from threading import Thread, Lock
import _thread
from utils import os_generic_clear
from selector import echooff, echoon
import os

adversary_wants_rematch : int = 0
""" 0 : adversary not decided yet, 1 : adversary decided they want a rematch, 2 : adversary decided they want to stop the game """

def process_restart_signal(data : bytes, game : OnlineGame) -> None :
  global adversary_wants_rematch
  if int.from_bytes(data) == 1 :
    adversary_wants_rematch = 1
    print("Adversary wants a rematch !")
  else :
    adversary_wants_rematch = 2
    print("Adversary ended the game")
    print("end try in secondary thread resulted in :", game.end())
    quit() # TODO this only stops the thread trying to receive info, find a way to stop main thread too : look in the case where we receive this message but are still waiting for inputs on our end.

def action_on_recv_from_adversary(game : Game, n : int, on_recv, lock : Lock) -> bytes :
  """ Tries to receive [n] bytes from the adversary of the [game] of which we are the , until [lock] is released. If and when received, calls [on_recv] with the data received as argument. Useful with threading. """
  while lock.locked() : # FIXME find a way to remove active waiting
    try :
      on_recv(game.recv_from_adversary(n, MSG_DONTWAIT))
    except BlockingIOError :
      pass

clear_cmd = os_generic_clear()

continue_game : str | None = True
game_start_type = "a"
game : Game

while continue_game :
  if game_start_type == "p" or game_start_type == "a" :
    os.system(clear_cmd)
    print("Size of the board ?")
    size = [11, 21, 31][selector([0, 1, 2], lambda i : [" ⸳ ", " ▪ ", " ■ "][i])]
    print("\nSpeed of the game ?")
    timeout = [1., .5, .1][selector([0, 1, 2], lambda i : ["🐢 ", "🐍 ", "🐰 "][i])]
    initial_snakes = [((int(size/2), int(size/4)), Dir.EAST), ((int(size/2), int(3 * size/4)), Dir.WEST)]
    if game_start_type == "a" :
      game = OnlineGame(size, size, 3, initial_snakes, timeout)
      os.system(clear_cmd)
      game.connect_to_adversary()
      os.system(clear_cmd)
    elif game_start_type == "p" :
      game.change_parameters(size, size, 3, initial_snakes, timeout)
  if game_start_type == "c" :
    game.change_parameters(initial_snake_length = 3, initial_snakes = initial_snakes)
  
  try :
    echooff()
    game.start()
  finally :
    echoon()
  lock_restart_signal = _thread.allocate_lock()
  lock_restart_signal.acquire() # shouldn't be blocking
  check_restart_signal = Thread(target = lambda : action_on_recv_from_adversary(game, 1, lambda data : process_restart_signal(data, game), lock_restart_signal))
  check_restart_signal.start()
  game_start_type = None
  adversary_wants_rematch = 0
  while game_start_type is None :
    game_start_type = input("\rContinue, change parameters with the same adversary, play with another adversary or quit ? (c/p/a/q)\n") # FIXME when received restart 
    game_start_type = game_start_type.lower()
    if game_start_type not in ["c", "p", "a", "q"] :
      game_start_type = None
  if game_start_type == "a" or game_start_type == "q" :
    if adversary_wants_rematch == 0 : # if the adversary did not decide yet if they wanted a rematch or not
      game.send_to_adversary((0).to_bytes()) # signaling to the client we want to stop the game, should stop thread in client
      lock_restart_signal.release()
      # check_restart_signal.join() # shouldn't be blocking since we released the lock
    print("end try in main thread resulted in :", game.end()) # TODO the case of "a" is still faulty
  else : # then [game_start_type] is either c or p, we want a rematch with the same adversary
    if adversary_wants_rematch == 0 :
      game.send_to_adversary((1).to_bytes()) # signaling to the client we want a rematch
      check_restart_signal.join()
      assert((adversary_wants_rematch == 1) or (adversary_wants_rematch == 2))
    if adversary_wants_rematch == 2 :
      quit() # if the adversary ended the game while we wanted a rematch, we quit FIXME maybe in the future it might be better to propose alternatives (a/q) at this point
  continue_game = (game_start_type != "q")