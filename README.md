# SnakeLan

It's a game of snake, playable on lan.

For the lan game, someone needs to run `snake_server_lan.py` on their device, and someone on the same local network need to run `snake_client.py` then, the client needs to select the device with which they want to start a game.
The server chooses the parameters of the game and can either close the connection after a game, or ask the client if they want a replay.
When the client is scanning for local networks, they can choose to stop the search at any moment by pressing Ctrl+C and start selecting a server if the adversary they wanted is already printed by the local scanner. <!-- TODO change this command for sth less extreme -->

## Dependencies

You first need to install the `pynput` library.

To run a local game, you need : `snake_local.py` <- `snake.py` <- `utils.py`.

To run a lan server, you need : `snake_server_lan.py` <- `snake.py` <- `utils.py`.

To run a lan client, you need : `snake_client.py` <- `utils`, `selector`, `local_scanner`.

## Platform supported

Linux