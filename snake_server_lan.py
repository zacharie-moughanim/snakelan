from snake import *# TODO replace * by the needed functions
from threading import Thread, Lock
import _thread
from utils import os_generic_clear
from selector import echooff, echoon
import os

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
  game_start_type = None
  while game_start_type is None :
    game_start_type = input("\rContinue, change parameters with the same adversary, play with another adversary or quit ? (c/p/a/q)\n") # FIXME when received restart 
    game_start_type = game_start_type.lower()
    if game_start_type not in ["c", "p", "a", "q"] :
      game_start_type = None
  if game_start_type == "a" or game_start_type == "q" :
    game.send_to_adversary((0).to_bytes()) # signaling to the client we want to stop the game, should stop thread in client
    # lock_restart_signal.release()
    # check_restart_signal.join() # shouldn't be blocking since we released the lock
  else : # then [game_start_type] is either c or p, we want a rematch with the same adversary
    game.send_to_adversary((1).to_bytes()) # signaling to the client we want a rematch
    # check_restart_signal.join()
  adversary_wants_rematch = int.from_bytes(game.recv_from_adversary(1))
  assert((adversary_wants_rematch == 0) or (adversary_wants_rematch == 1))
  continue_game = (game_start_type != "q")
  if adversary_wants_rematch == 0 and (game_start_type == "c" or game_start_type == "p") :
    print("Adversary declined the rematch, quitting")
    continue_game = False
  if game_start_type == "a" or game_start_type == "q" :
    game.end()