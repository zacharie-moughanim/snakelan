from snake import *

# continue_game = True

# while continue_game :
#   print("Size of the board ?")
#   size = [11, 21, 31][selector([0, 1, 2], lambda i : [" ⸳ ", " ▪ ", " ■ "][i])]
#   print("\nSpeed of the game ?")
#   timeout = [1., .5, .1][selector([0, 1, 2], lambda i : ["🐢 ", "🐍 ", "🐰 "][i])]
#   initial_snakes = [((int(size/2), int(size/4)), Dir.EAST), ((int(size/2), int(3 * size/4)), Dir.WEST)]
#   game = Game(size, size, 3, initial_snakes[:1], timeout)
#   try :
#     echooff()
#     game.start()
#   finally :
#     echoon()
#   in_cont = None
#   while in_cont is None :
#     in_cont = bool_of_input(input("\rContinue ? (Y/n)\n"))
#   continue_game = in_cont

size = 11
timeout = 3.

initial_snakes = [((int(size/2), int(size/4)), Dir.EAST), ((int(size/2), int(3 * size/4)), Dir.WEST)]
game = OnlineGame(size, size, 3, initial_snakes, timeout)
game.start()

game.end()