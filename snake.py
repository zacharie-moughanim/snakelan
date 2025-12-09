from typing import *
from utils import *
from enum import Enum
from socket import gethostbyname, gethostbyaddr, socket, MSG_DONTWAIT
from pynput import keyboard
from selector import selector, echoon, echooff
import _thread
from threading import Thread, Lock
import time, os, random

## Types

snake_board = list[list[tuple[Cell, int | None]]]

## Keyboard monitoring

keyboard_directions = ({'z' : Dir.NORTH, 'q' : Dir.WEST, 's' : Dir.SOUTH, 'd' : Dir.EAST}, {'o' : Dir.NORTH, 'k' : Dir.WEST, 'l' : Dir.SOUTH, 'm' : Dir.EAST}) # separate dictionaries for zqsd and oklm keys, they are separate for local games
keyboard_directions_all = {
    keyboard.Key.up : Dir.NORTH, keyboard.Key.down : Dir.SOUTH, keyboard.Key.left : Dir.WEST, keyboard.Key.right : Dir.EAST,
    "z" : Dir.NORTH, "q" : Dir.WEST, "s" : Dir.SOUTH, "d" : Dir.EAST,
    "o" : Dir.NORTH, "k" : Dir.WEST, "l" : Dir.SOUTH, "m" : Dir.EAST
  } # concatenated dictionaries for zqsd, oklm and ↑←↓→ keys


def nothing(key) :
  pass

def update_local(game, key) :
  global direction_change_allowed
  if direction_change_allowed :
    try :
      if key.char in keyboard_directions[0] :
        game.snakes[0].change_direction(keyboard_directions[0][key.char])
      elif key.char in keyboard_directions[1] :
        game.snakes[1].change_direction(keyboard_directions[1][key.char])
    except AttributeError :
      pass

def listening_moves(game : "Game", sclient : socket, lock : Lock) -> None :
  """ listen moves from [sclient] while [lock] is acquired and performs the updates in the second snake's direction in [game] """
  while lock.locked() : # while the main thread acquired the lock, we listen for move command from the client + FIXME find a way to remove active waiting
    try :
      msg = sclient.recv(1, MSG_DONTWAIT)
      distant_move = msg.decode()
      if distant_move in keyboard_directions_all.keys() :
        if debug :
          print("Received command :", distant_move, "from distant adversary")
        # print(distant_move)
        game.snakes[1].change_direction(keyboard_directions_all[distant_move])
      else :
        if debug :
          print("Received unrecognized move :", distant_move, "from distant adversary")
    except BlockingIOError :
      pass
  
## Display parameters

clear_cmd = os_generic_clear()

direction_change_allowed = False # needs to be a global because used in [update_local], called on key events and modified via an instance of Game FIXME test to pass a mutable parameter instead

## Classes

debug = False

class Snake : # FIXME : when pressing quickly z then d (or a rotation of the same thing), loses automatically + some issues with the displaying of the snake when passing through themselve
  id : int
  x_hd : int
  y_hd : int
  x_tl : int
  y_tl : int
  already_played : bool # indicates whether we already moved this round
  dir : Dir # current direction, the last direction key pressed by the user
  dirs : list[Dir] # a list of the directions of each cell composing the snake, 0 is the tail, -1 is the head

  def __init__(self, id : int, grid : snake_board, x : int, y : int, initial_snake_length : int, dir : Dir = Dir.EAST) : # for now, [dir] can only be [EAST] or [WEST]
    """ [id] a unique identifier, [game] the game where the snake belongs, [(x, y)] the initial position of the snake's head, [dir] the initial direction of the snake """
    assert (dir == Dir.EAST or dir == Dir.WEST)
    assert (x + 1 >= initial_snake_length) # not enough length to place the snake on the grid
    # print(f"Initializing {id} at ({x}, {y}), dir : {dir} of length {initial_snake_length}")
    self.id = id
    self.already_played = False
    self.x_hd = x
    self.x_tl = x
    self.y_hd = y
    if dir == Dir.EAST :
      self.y_tl = y - 2
    if dir == Dir.WEST :
      self.y_tl = y + 2
    self.dir = dir
    self.dirs = [dir for i in range(initial_snake_length - 1)]
    step = 1
    if dir == Dir.EAST :
      for i_y in range(self.y_tl, self.y_hd + 1) :
        grid[x][i_y] = (Cell.SNAKE, id)
    elif dir == Dir.WEST :
      for i_y in range(self.y_tl, self.y_hd - 1, -1) :
        grid[x][i_y] = (Cell.SNAKE, id)

  def __repr__(self) :
    return f"id : {self.id}, head at : ({self.x_hd}, {self.y_hd}), tail at : ({self.x_tl}, {self.y_tl}), dirs : {self.dirs}, dir : {self.dir}, length : {len(self.dirs)}"

  def change_direction(self, dir : Dir) -> str :
    if not(is_opposite_direction(self.dir, dir)) :
      self.dir = dir

  def move_head(self) -> None :
    """ moves the head to the next position, given the direction """
    new_x_hd, new_y_hd = next_coordinates(self.x_hd, self.y_hd, self.dir)
    self.x_hd = new_x_hd
    self.y_hd = new_y_hd
    self.dirs.append(self.dir)

  def move_tail(self, grid : snake_board) -> None :
    """ moves the tail to the next position and make the previous position of the tail empty, given the direction """
    new_x_tl, new_y_tl = next_coordinates(self.x_tl, self.y_tl, self.dirs[0])
    type_cell, id_snake = grid[self.x_tl][self.y_tl]
    if type_cell == Cell.SNAKE and id_snake == self.id :
      grid[self.x_tl][self.y_tl] = (Cell.EMPTY, None)
    self.x_tl = new_x_tl
    self.y_tl = new_y_tl
    self.dirs.pop(0)

  def move(self, grid : snake_board, other_snakes : list['Snake']) -> tuple[list[int], bool] :
    """ Moves the snake to the next cell, according to the direction.
      returns the list of snakes which we detected lost and a boolean indicating whether we ate an apple """
    self.move_head()

    height = len(grid)
    width = len(grid[0])

    if not(0 <= self.x_hd < height and 0 <= self.y_hd < width) :
      # The snake goes out of bound, beyond our restricted yet humble and true world, maybe they had dreams of a better future outside the walls of their prison
      self.move_tail(grid)
      self.already_played = True
      return ([self.id], False)
    
    type_cell, other_id = grid[self.x_hd][self.y_hd]
    match type_cell :
      case Cell.EMPTY :
        self.move_tail(grid)
        grid[self.x_hd][self.y_hd] = (Cell.SNAKE, self.id)
        self.already_played = True
        return ([], False)
      case Cell.APPLE :
        grid[self.x_hd][self.y_hd] = (Cell.SNAKE, self.id)
        self.already_played = True
        return ([], True)
      case Cell.WALL :
        self.move_tail(grid)
        self.already_played = True
        return ([self.id], False)
      case Cell.SNAKE :
        self.move_tail(grid)
        assert (other_id != None)
        other : Snake = other_snakes[other_id]
        # print(f"I ({self})...\nmay hit {other}")
        if other.has_already_played() :
          if other.is_head(self.x_hd, self.y_hd) :
            # head to head, both lost
            self.already_played = True
            return ([self.id, other_id], False)
          else :
            self.already_played = True
            return ([self.id], False)
        else :
          if other.is_tail(self.x_hd, self.y_hd) :
            if other.is_next_apple(grid) :
              self.already_played = True
              return ([self.id], False)
            else :
              # head to tail, but the tail is gonna move forward, so pixel perfect dodge
              self.already_played = True
              return ([], False)
          else :
            self.already_played = True
            return ([self.id], False)

  def is_tail(self, x : int, y : int) :
    """ checks if [(x, y)] is our tail """
    return x == self.x_tl and y == self.y_tl

  def is_head(self, x : int, y : int) :
    """ checks if [(x, y)] is our head """
    return x == self.x_hd and y == self.y_hd
  
  def is_next_apple(self, grid : snake_board) :
    """ checks if we are going to eat an apple after moving """
    next_x, next_y = next_coordinates(self.x_hd, self.y_hd, self.dir)
    type_cell, _ =  grid[next_x][next_y]
    return type_cell == Cell.APPLE
    
  def has_already_played(self) :
    return self.already_played

  def end_of_round(self) :
    self.already_played = False

class Game : # FIXME still buggy, it appears we can just go back (pressing q when we're going from left to right) without losing, and cf fixme of Snake class
  grid : snake_board # each cell, if it's a snake, contains the id of the snake as well, otherwise, the additional information is None
  width : int
  height : int
  snakes : List[Snake] # snake[i].id is always equal to i
  snake_colors : tuple[str, str, str, str, str] # The symbol with which we print the snake
  state : State
  losers : List[int]
  timeout : float
  emoji_mode : bool
  def __init__(self, width : int, height : int, initial_snake_length : int, initial_snakes : list[tuple[tuple[int, int], Dir]], timeout : float = 1., emoji_mode : bool = True) :
    """ initiates a game.
      [width] [height] : dimension of the board
      [initial_snake_length] : ...
      [initial_snakes] : a list of initial coordinates of the heads and directions of the snakes. We assume snakes don't overlap at the beginning and provides valid coordinates;
      [timeout] : the time between two actualization of the board. 1 second by default.
      [emoji_mode] : if [True], printing the game elements with emoji, otherwise, print using ascii and unicode characters
     """
    n_snakes = len(initial_snakes)
    assert (n_snakes < 5) # for now, only a maximum of 5 snakes is allowed (because of the colors)
    self.width = width
    self.height = height
    self.state = State.NOT_STARTED
    self.losers = []
    self.timeout = timeout
    self.n_snakes = n_snakes
    self.emoji_mode = emoji_mode
    if self.emoji_mode :
      self.snake_color = ("⬜", "🟩", "🟥", "🟧", "🟦")
    else :
      self.snake_color = ("#", "%", "$", "€", "&")
    self.grid = [[(Cell.EMPTY, None) for i in range(width)] for i in range(height)]
    self.snakes = []
    # placing apples :
    self.grid[int(height/2)][int(width/2)] = (Cell.APPLE, None)
    # placing snakes :
    self.snakes = [Snake(i, self.grid, snake_data[0][0], snake_data[0][1], initial_snake_length, snake_data[1]) for (i, snake_data) in enumerate(initial_snakes)]
  def __str__(self) :
    first_line = "┌"             # first and last line for a frame of the form : 
    last_line = "└"              # ┌──────────────────┐
    for i in range(self.width) : # │                  │
      if self.emoji_mode :       # │                  │
        first_line += "─"        # │                  │
        last_line += "─"         # │                  │
      first_line += "─"          # │                  │
      last_line += "─"           # │                  │
    first_line += "┐"            # │                  │
    last_line += "┘"             # └──────────────────┘
    res = ""
    res += first_line
    res += "\n"
    for i in range(self.height) :
      line = "│"
      for j in range(self.width) :
        type_cell, id = self.grid[i][j]
        match type_cell :
          case Cell.EMPTY :
            if self.emoji_mode :
              line += "  "
            else :
              line += " "
          case Cell.APPLE :
            if self.emoji_mode :
              line += "🍎"
            else :
              line += "O"
          case Cell.SNAKE :
            line += self.snake_color[id]
          case Cell.WALL :
            if self.emoji_mode :
              line += "🧱"
            else :
              line += "▆"
      res += (line + "│\n")
    res += last_line
    return res
  def change_parameters(self, width : int | None = None, height : int | None = None, initial_snake_length : int | None = None, initial_snakes : list[tuple[tuple[int, int], Dir]] | None = None, timeout : float | None = None, emoji_mode : bool | None = None) :
    """ Changes parameters of the game. See Game for details about the parameters. """
    if width is not None :
      self.width = width
    if height is not None :
      self.height = height
    assert (initial_snakes is not None and initial_snake_length is not None) # FIXME find a way to restore previous inital positions
    if initial_snakes is not None :
      # resets board to initial positions, according to [initial_snakes]
      self.grid = [[(Cell.EMPTY, None) for i in range(self.width)] for i in range(self.height)]
      # placing apples :
      self.grid[int(self.height/2)][int(self.width/2)] = (Cell.APPLE, None)
      # placing snakes :
      self.snakes = [Snake(i, self.grid, snake_data[0][0], snake_data[0][1], initial_snake_length, snake_data[1]) for i, snake_data in enumerate(initial_snakes)]
    if timeout is not None :
      self.timeout = timeout
    if emoji_mode is not None :
      self.emoji_mode = emoji_mode
  def update_directions(self) -> None :
    global direction_change_allowed
    direction_change_allowed = True
    time.sleep(self.timeout)
    direction_change_allowed = False
  def play_round(self) -> bool :
    """ plays a round, returns True if the game can be continued, False if it is finished """
    self.update_directions()
    # Moving snakes. (at the beginning, all [already_played] must be [False])
    losers = []
    apple_ate = False
    for snake in self.snakes :
      new_losers, new_apple_ate = snake.move(self.grid, self.snakes)
      losers.extend(new_losers)
      apple_ate = apple_ate or new_apple_ate
    # Adds an apple if necessary
    if apple_ate :
      x_rd = random.randrange(self.height)
      y_rd = random.randrange(self.width)
      while (self.grid[x_rd][y_rd][0] != Cell.EMPTY) :
        x_rd = random.randrange(self.height)
        y_rd = random.randrange(self.width)
      self.grid[x_rd][y_rd] = (Cell.APPLE, None)
    # Ends the round, reset the snake's [already_played] booleans for a new round, prints the losers if there was some. 
    for snake in self.snakes :
      snake.end_of_round()
    if losers != [] :
      print(join(losers, ", ", " and "), " lost")
      self.losers = losers
    return losers == []
  def start(self, display : bool = True, clear : bool = True) -> None :
    os.system(clear_cmd)
    print(self)
    listener = keyboard.Listener(on_press = lambda k : update_local(self, k), on_release = nothing)
    listener.start()
    while self.play_round() :
      if display :
        os.system(clear_cmd)
        print(self)
    listener.stop()

class OnlineGame(Game) :
  connected_to_adversary : bool
  server_up : bool
  server : socket
  sclient : socket
  def __init__(self, width : int, height : int, initial_snake_length : int, initial_snakes : list[tuple[tuple[int, int], Dir]], timeout : float = 1.) :
    """ Initiates an online game. For now, allow only two players. See [Game] for more information. """
    n_snakes = len(initial_snakes)
    if n_snakes != 2 :
      raise ValueError("For now, an online game can only be between two players.")
    self.connected_to_adversary = False
    self.server_up = False
    super().__init__(width, height, initial_snake_length, initial_snakes, timeout)
  def update_directions(self) -> None :
    global direction_change_allowed
    if debug :
      print("sending start moves")
    self.sclient.send("start moves".encode()) # nb of bytes : 11
    if debug :
      print("start moves was received by client")
    end_listening_lock = _thread.allocate_lock()
    listening_distant = Thread(target = listening_moves, args = (self, self.sclient, end_listening_lock))
    end_listening_lock.acquire() # shouldn't not be blocking
    listening_distant.start()
    direction_change_allowed = True
    time.sleep(self.timeout)
    end_listening_lock.release()
    # thread must have finished now, due to the release of th elock
    if debug :
      print("sending end moves")
    self.sclient.send("end moves".encode()) # nb of bytes : 9
    if debug :
      print("end moves was received by client")
    direction_change_allowed = False
  def play_round(self) -> bool :
    """ plays a round, returns True if the game can be continued, False if it is finished """
    self.update_directions()
    # Moving snakes. (at the beginning, all [already_played] must be [False])
    losers = []
    apple_ate = False
    for snake in self.snakes :
      new_losers, new_apple_ate = snake.move(self.grid, self.snakes)
      losers.extend(new_losers)
      apple_ate = apple_ate or new_apple_ate
    # Adds an apple if necessary
    if apple_ate :
      x_rd = random.randrange(self.height)
      y_rd = random.randrange(self.width)
      while (self.grid[x_rd][y_rd][0] != Cell.EMPTY) :
        x_rd = random.randrange(self.height)
        y_rd = random.randrange(self.width)
      self.grid[x_rd][y_rd] = (Cell.APPLE, None)
    # Ends the round, reset the snake's [already_played] booleans for a new round, prints the losers if there was some. 
    for snake in self.snakes :
      snake.end_of_round()
    if losers != [] :
      self.losers = losers
    return losers == []
  def connect_to_adversary(self) -> None :
    """ Connect to an adversary, must be called before calling [start]. Will loop until an adversary is found. """
    if self.connected_to_adversary :
      print("Close the first connection, by calling the [end] method, before starting another one.")
    else :
      # Waiting for an adversary
      adversary_found : bool | None = False
      if not(self.server_up) :
        self.server = socket()
        self.server.bind(('0.0.0.0', 9999))
        self.server.listen()
      while not(self.connected_to_adversary) :
        print("Waiting for an adversary to connect...")
        adversary_selected = None
        (sclient, adclient) = self.server.accept()
        while adversary_selected is None : # until user decided whether to engage
          print(gethostbyaddr(adclient[0])[0], end = " ")
          adversary_selected = bool_of_input(input("wants to play, start a game with them ? (y/n) "), None)
        if adversary_selected :
          # Adversary selected by user, trying to engage a game
          try :
            if debug :
              print("sending game start ?")
            sclient.send("game start ?".encode()) # nb of bytes : 12
            if debug :
              print("game start ? received by client, now waiting for game startOK confirmation")
            donnees = sclient.recv(12)
            if debug :
              print(donnees.decode())
              time.sleep(2)
            if donnees.decode() == "game startOK" :
              self.sclient = sclient
            else :
              print("Did not respond to the game invitiation")
              adversary_selected = False
          except ConnectionResetError :
            print("This one is not worth it, they just left ! How rude !")
            adversary_selected = False
          print("Connection established", end = "")
          self.connected_to_adversary = True
          for i in range(3) :
            print(".", end = "", flush = True)
            time.sleep(.3)
  def start(self, display : bool = True, clear : bool = True) -> None :
    """ Starts an online game with the adversary connected via [self.sclient] """
    if not(self.connected_to_adversary) :
      print("You must be connected to an adverary to start a game")
    else :
      os.system(clear_cmd)
      print(self)
      if debug :
        print("sending self for the first time : ")
      tcp_send_with_length(self.sclient, str(self).encode())
      if debug :
        print("(first ever) self received by client")
      listener = keyboard.Listener(on_press = lambda k : update_local(self, k), on_release = nothing)
      listener.start()
      while self.play_round() :
        if not(debug) :
          os.system(clear_cmd)
        if display :
          if debug :
            print("sending self : ")
          print(self)
          tcp_send_with_length(self.sclient, str(self).encode()) 
          if debug :
            print("self received by client")
      listener.stop()
      os.system(clear_cmd)
      print(self)
      print(join(self.losers, ", ", " and "), "lost")
      if debug :
        print("sending self for the last time : ")
      tcp_send_with_length(self.sclient, str(self).encode()) 
      if debug :
        print("self received by client (for the last time)")
      if debug :
        print("Sending Game over...")
      self.sclient.send("Game over..".encode()) # nb of bytes : 11 /!\ must be the same number of bytes as moves start (11)
      if debug :
        print("client received Game over, now sending losers...")
      tcp_send_with_length(self.sclient, join(self.losers, sep = ";").encode()) # TODO replace this by a while loop, ending by a character indicating the end of losers
      if debug :
        print("client received losers")
  def end(self) -> bool :
    """ Ends a game : close connection with distant adversary, but keep server up. Returns [True] if we were able to close the socket, [False] if it was not connected. """
    if self.connected_to_adversary :
      self.sclient.close()
      self.connected_to_adversary = False
      return True
    else :
      return False
  def close_server(self) -> bool :
    """ Disconnect the server. Returns [True] if we were able to close the socket, [False] if it was not connected. """
    if self.server_up :
      self.server.close()
      self.server_up = False
      return True
    else :
      return False
  def send_to_adversary(self, data : bytes) -> None :
    """ Sends [data] to the current adversary. Raise a [ValueError] if we were not connected to an adversary beforehand. """
    if self.connected_to_adversary :
      self.sclient.send(data)
    else :
      raise ValueError("You must connect to an adversary before sending them data")
  def recv_from_adversary(self, n : int, flags : int = 0) -> bytes :
    """ Receives [n] bytes from the current adversary. Raise a [ValueError] if we were not connected to an adversary beforehand. """
    if self.connected_to_adversary :
      return self.sclient.recv(n, flags) # TODO check if flags = 0 is te correct default value for [recv]
    else :
      raise ValueError("You must connect to an adversary before receiving data from them")