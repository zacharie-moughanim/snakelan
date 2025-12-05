from typing import *
from utils import *
from enum import Enum
from socket import gethostbyname, socket
from pynput import keyboard
from selector import selector, echoon, echooff
import time, os, random

## Types

snake_board = list[list[tuple[Cell, int | None]]]

## Game parameters
width = 11
height = 11
n_snakes = 2
initial_snake_length = 3
initial_snakes = [((int(height/2), int(width/4)), Dir.EAST), ((int(height/2), int(3 * width/4)), Dir.WEST)]
emoji_mode = True
keyboard_directions = ({'z' : Dir.NORTH, 'q' : Dir.WEST, 's' : Dir.SOUTH, 'd' : Dir.EAST}, {'o' : Dir.NORTH, 'k' : Dir.WEST, 'l' : Dir.SOUTH, 'm' : Dir.EAST})
keyboard_directions_arrow = {keyboard.Key.up : Dir.NORTH, keyboard.Key.down : Dir.SOUTH, keyboard.Key.left : Dir.WEST, keyboard.Key.right : Dir.EAST}
online = True

## Classes

def nothing(key) :
  pass

def update_local(key) :
  global game
  try :
    if key.char in keyboard_directions[0] :
      game.snakes[0].change_direction(keyboard_directions[0][key.char])
    elif key.char in keyboard_directions[1] :
      game.snakes[1].change_direction(keyboard_directions[1][key.char])
  except AttributeError :
    pass

class Snake :
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
    errmsg = ""
    if is_opposite_direction(self.dir, dir) :
      errmsg = f"{self.id} : Cannot change to opposite direction"
      print(errmsg)
    else :
      self.dir = dir
    return errmsg

  def move_head(self) -> None :
    """ moves the head to the next position, given the direction """
    new_x_hd, new_y_hd = next_coordinates(self.x_hd, self.y_hd, self.dir)
    self.x_hd = new_x_hd
    self.y_hd = new_y_hd
    self.dirs.append(self.dir)

  def move_tail(self, grid : snake_board) -> None :
    """ moves the tail to the next position and make the previous position of the tail empty, given the direction """
    new_x_tl, new_y_tl = next_coordinates(self.x_tl, self.y_tl, self.dirs[0])
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

class Game :
  grid : snake_board # each cell, if it's a snake, contains the id of the snake as well, otherwise, the additional information is None
  width : int
  height : int
  snakes : list[Snake] # snake[i].id is always equal to i
  snake_colors : tuple[str, str, str, str, str]
  state : State
  loser : int
  timeout : float
  def __init__(self, width : int, height : int, initial_snake_length : int, initial_snakes : list[tuple[tuple[int, int], Dir]], timeout : float = 1.) :
    """ initiates a game.
      [width] [height] : dimension of the board
      [initial_snakes] : a list of initial coordinates of the heads and directions of the snakes. We assume snakes don't overlap at the beginning and provides valid coordinates;
     """
    assert (n_snakes < 5) # for now, only a maximum of 5 snakes is allowed
    self.width = width
    self.height = height
    self.state = State.NOT_STARTED
    self.loser = -1
    self.timeout = timeout
    self.n_snakes = n_snakes
    if emoji_mode :
      self.snake_color = ("⬜", "🟩", "🟥", "🟧", "🟦")
    else :
      self.snake_color = ("#", "%", "$", "€", "&")
    self.grid = [[(Cell.EMPTY, None) for i in range(width)] for i in range(height)]
    self.snakes = []
    # placing apples :
    self.grid[int(height/2)][int(width/2)] = (Cell.APPLE, None)
    # placing snakes :
    id_cnt = 0
    for snake_data in initial_snakes :
      self.snakes.append(Snake(id_cnt, self.grid, snake_data[0][0], snake_data[0][1], initial_snake_length, snake_data[1]))
      id_cnt += 1
  def __str__(self) :
    first_line = "┌"             # first and last line for a frame of the form : 
    last_line = "└"              # ┌──────────────────┐
    for i in range(self.width) : # │                  │
      if emoji_mode :            # │                  │
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
            if emoji_mode :
              line += "  "
            else :
              line += " "
          case Cell.APPLE :
            if emoji_mode :
              line += "🍎"
            else :
              line += "O"
          case Cell.SNAKE :
            line += self.snake_color[id]
          case Cell.WALL :
            if emoji_mode :
              line += "🧱"
            else :
              line += "▆"
      res += (line + "│\n")
    res += last_line
    return res
  def update_directions(self) -> None :
    time.sleep(self.timeout)

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
    return losers == []
  def start(self, display : bool = True, clear : bool = True) -> None :
    os.system("clear")
    print(self)
    listener = keyboard.Listener(on_press = update_local, on_release = nothing)
    listener.start()
    while self.play_round() :
      if display :
        os.system("clear")
        print(self)
    listener.stop()

class onlineGame(Game) :
  sclient : socket
  def update_directions(self) -> None :
    global snake_to_move
    if online :
      assert len(self.snakes) == 2, "For now, we only allow 2 snakes for an online game."
      # Change direction for player 0 (local)
      print(f"Waiting for your move (up/down/left/right)...")
      with keyboard.Events() as events:
        event = events.get(float(self.timeout))
        if event is None:
            print('You did not press a key within one second')
        else:
          print(f"you pressed {event}")
          if event.key in keyboard_directions_arrow :
            if event.key in keyboard_directions_arrow :
              print(event.key, keyboard_directions_arrow[event.key])
              self.snakes[0].change_direction(keyboard_directions_arrow[event.key])
            else :
              print("New direction must be up, down, left or right")
          else :
            print("New direction must be up, down, left or right")
      print("The end !")
      # Change direction for player 1 (distant)
      print("waiting for adversary's move")
      self.sclient.send("Waiting for your move (z/s/q/d)...".encode())
      adv_move = self.sclient.recv(4) # waits for the adversary's move
      adv_cmd = adv_move.decode()
      if adv_cmd != "n" :
        if adv_cmd in keyboard_directions :
          errmsg = self.snakes[1].change_direction(keyboard_directions[adv_cmd])
          if errmsg != "" :
            self.sclient.send(errmsg.encode())
        else :
          self.sclient.send("New direction must be z, q, s or d".encode())
    else :
      for (i_snake, snake) in enumerate(self.snakes) :
        print(f"Change directions of {i_snake} ?")
        i, o, e = select.select( [sys.stdin], [], [], self.timeout)
        if i :
          cmd = sys.stdin.readline().strip()
          if cmd in keyboard_directions :
            print(cmd, keyboard_directions[cmd])
            snake.change_direction(keyboard_directions[cmd])
          else :
            print("Invalid direction")
  def play_round(self) -> bool :
    """ plays a round, returns True if the game can be continued, False if it is finished """
    self.update_directions()
    # At the beginning, all [already_played] must be [False].
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
    # Ends the round, reset the snake's already_played booleans for a new round, prints the losers if there was some. 
    for snake in self.snakes :
      snake.end_of_round()
    if losers != [] :
      losers_pp = (join(losers, ", ", " and ") + " lost")
      print(losers_pp)
      self.sclient.send((losers_pp+"\n").encode())
      time.sleep(5) # Demander à yaëlle comment faire ça de manière moins dégueulasse
    self.sclient.send("round over\n".encode())
    return losers == []
  def start(self, display : bool = True, clear : bool = True) -> None :
    if online :
      server : socket = socket()
      server.bind(('0.0.0.0', 9999))
      server.listen()

      (self.sclient, adclient) = server.accept() # Attend qu'un adversaire se connecte
      print("@: ", adclient)
      self.sclient.send((str(self)+"\n").encode())
      time.sleep(1)
      self.sclient.send(self.timeout.to_bytes())
      print(f"Timeout : {self.timeout}")
    os.system('clear')
    print(game)
    while True :
      is_end = not(self.play_round())
      if display :
        os.system("clear")
        print(self)
        if online :
          self.sclient.send((str(self)+"\n").encode())
      if is_end :
        time.sleep(1)
        self.sclient.send("\ngame over\n".encode())
        break
    if online :
      print("Closing connection...")
      self.sclient.close()

## Running a game :

continue_game = True

while continue_game :
  timeout = [1., .5, .1][selector([0, 1, 2], lambda i : ["🐢", "🐍", "🐰"][i])]
  game = Game(width, height, initial_snake_length, initial_snakes[:1], timeout)
  try :
    echooff()
    game.start()
  finally :
    echoon()
  in_cont = "x"
  while in_cont not in ["y", "n", ""] :
    in_cont = input("\rContinue ? (Y/n)")
    if in_cont == "n":
      continue_game = False