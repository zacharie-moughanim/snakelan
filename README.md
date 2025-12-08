# SnakeLan

It's a game of snake, playable on lan.

## Dependencies

You first need to install the `pynput` library.

To run a local game, you need : `snake_local.py` <- `snake.py` <- `utils.py`.

To run a lan server, you need : `snake_server_lan.py` <- `snake.py` <- `utils.py`.

To run a lan client, you need : `snake_client.py` <- `utils.py`, `selector.py`, `local_scanner`.

## Usage

### Server

For the lan game, someone needs to run `snake_server_lan.py` on their device, and someone on the same local network need to run `snake_client.py <min_address> <max_address>`.
The server chooses the parameters of the game.

After a game, they can either close the connection or ask the client if they want to replay.

### Client

The client scans address within `min_address` and `max_address` if none is provided, defaulting to `192.168.0.1` to `192.168.255.255`.
Then, the client needs to select the device with which they want to start a game.
When the client is scanning for local networks, they can choose to stop the search at any moment by pressing Ctrl+C and start selecting a server if the adversary they wanted is already printed by the local scanner. <!-- TODO change this command for sth less extreme --

## Platform supported

Linux WARNING pynput appear to not work in classic terminal. Although for some reason it works with vscode integrated terminal.
Windows, Windows/Cygwin, MacOS TODO for these, must find equivalent for `tty -/+echo` and `clear`.