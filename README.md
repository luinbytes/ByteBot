# ByteBot

ByteBot is a Discord bot written in Python that provides a variety of fun and interactive features.

## Features

- **8ball:** Ask the bot any question and receive a random answer.
- **Random Fact:** Get a random fact to learn something new.
- **Coin Flip:** Make a coin flip and bet on the outcome.
- **Rock Paper Scissors:** Play the classic game of Rock Paper Scissors against the bot.
- **Slap:** Slap another user with a funny GIF.

## Installation

1. Clone the repository:
git clone https://github.com/luinbytes/ByteBot.git

2. Install the required dependencies:
pip install -r requirements.txt

3. Create a Discord bot account and obtain your bot token.

4. Create a file named `.env` in the root directory of the project and add the following line, replacing `YOUR_BOT_TOKEN` with your actual bot token:
TOKEN=YOUR_BOT_TOKEN

5. Run the bot:
python main.py

## Usage

Once the bot is running, you can interact with it using the following commands:

### Fun
- `!8ball <question>`: Ask any question to the bot.
- `!randomfact`: Get a random fact.
- `!coinflip`: Make a coin flip, but give your bet before.
- `!rps`: Play the rock paper scissors game against the bot.
- `!slap <user>`: Slap someone.

### General
- `!help`: List all commands the bot has loaded.
- `!botinfo`: Get some useful (or not) information about the bot.
- `!serverinfo`: Get some useful (or not) information about the server.
- `!ping`: Check if the bot is alive.
- `!invite`: Get the invite link of the bot to be able to invite it.
- `!server`: Get the invite link of the discord server of the bot for some support.

### Images
- `!cat`: Spawns a random cat! Big thanks to The Cat API!

### Memes
- `!memerandom`: Grabs a random meme from meme-api.com

### Moderation
- `!kick`: Kick a user out of the server.
- `!nick`: Change the nickname of a user on a server.
- `!ban`: Bans a user from the server.
- `!warning`: Manage warnings of a user on a server.
- `!purge`: Deletes a user selected amount of messages from the current channel.
- `!hackban`: Bans a user without the user having to be in the server.
- `!archive`: Archives in a text file the last messages with a chosen limit of messages.

### Owner
- `!sync`: Synchronizes the slash commands.
- `!unsync`: Unsynchronizes the slash commands.
- `!load`: Load a cog
- `!unload`: Unloads a cog.
- `!reload`: Reloads a cog.
- `!shutdown`: Make the bot shutdown.
- `!say`: The bot will say anything you want.
- `!embed`: The bot will say anything you want, but within embeds.

### Utilities
- `!bitcoin`: Get the current price of bitcoin.
- `!userinfo`: Get information about a user
- `!avatar`: Get the avatar of a user

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` file for more information.

## License

This project is licensed under the GNU General Public License version 3. See the `LICENSE` file for more information.
