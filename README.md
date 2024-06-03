# ByteBot

ByteBot is a Discord bot written in Python that provides a variety of fun and interactive features.

## Features

ByteBot has a variety of commands grouped into several categories:

### General
- `!help`: List all commands the bot has loaded or show commands in a specific category.
- `!botinfo`: Get some useful (or not) information about the bot.
- `!serverinfo`: Get some useful (or not) information about the server.
- `!ping`: Check if the bot is alive.
- `!invite`: Get the invite link of the bot to be able to invite it.
- `!server`: Get the invite link of the discord server of the bot for some support.

### Utilities
- `!bitcoin`: Get the current price of bitcoin.
- `!userinfo`: Get information about a user
- `!avatar`: Get the avatar of a user
- `!joinedat`: Get the date a user joined the server.
- `!userid`: Get the ID of a user.
- `!listaliases`: List all available aliases for a command.
- `!prefix`: Get the current prefix for the server.
- `!setwelcomechannel`: Set the welcome channel for the server.
- `!removewelcomechannel`: Remove the welcome channel for the server.

### Market
- `!initmarket`: Initialize the market
- `!shop`: View the shop
- `!buy`: Buy something from the market
- `!setcolourprice`: Set the price of colour roles

### Music
- `!play`: Play a song.
- `!stop`: Stop the music.
- `!pause`: Pause the music.
- `!skip`: Skip the current song.
- `!volume`: Change the volume.
- `!nowplaying`: View the current song.
- `!queue`: View the queue.

### SteamTools
- `!steaminfo`: Scrape info from a users steam account via their steamID.
- `!steamid64`: Convert a vanity URL into a SteamID64.
- `!setbanchannel`: Set the channel to post ban notifications.
- `!tracksteam`: Track a steam user for bans.
- `!untracksteam`: Untrack a steam user for bans.
- `!tracking`: List all tracked steam users for bans.
- `!faceit`: Get a players FACEIT profile.

### Owner
- `!sync`: Synchonizes the slash commands.
- `!unsync`: Unsynchonizes the slash commands.
- `!load`: Load a cog
- `!unload`: Unloads a cog.
- `!reload`: Reloads a cog.
- `!shutdown`: Make the bot shutdown.
- `!say`: The bot will say anything you want.
- `!embed`: The bot will say anything you want, but within embeds.
- `!winmultiplier`: Check or set the global win muliplier.
- `!lossmultiplier`: Check or set the global loss muliplier.
- `!addcurr`: Add a currency to a user's balance.
- `!rmbalance`: Remove a user's balance.
- `!resetbalance`: Resets a user's balance.
- `!setbalance`: Set a user's balance.
- `!setcolourroleprice`: Set the price of a colour role.

### Moderation
- `!kick`: Kick a user out of the server.
- `!nick`: Change the nickname of a user on a server.
- `!ban`: Bans a user from the server.
- `!warning`: Manage warnings of a user on a server.
- `!purge`: Deletes a user selected amount of messages from the current channel.
- `!hackban`: Bans a user without the user having to be in the server.
- `!archive`: Archives in a text file the last messages with a chosen limit of messages.
- `!autorole`: Sets the role to grant users on server join.
- `!starboard`: Sets the starboard channel for the server.
- `!sbreactionamount`: Sets the minimum amount of reactions needed to pin a message to the starboard.
- `!verifystarboard`: Verifies the starboard channel for the server.
- `!setprefix`: Sets the prefix for the server.

### Fun
- `!8ball`: Ask any question to the bot.
- `!randomfact`: Get a random fact.
- `!coinflip`: Make a coin flip, but give your bet before.
- `!rps`: Play the rock paper scissors game against the bot.
- `!catslap`: Cat-Slap someone.
- `!randommeme`: Grabs a random meme from meme-api.com
- `!kanye`: Get a random Kanye West quote.
- `!chucknorris`: Get a random Chuck Norris fact.
- `!trump`: Get a random Trump quote.
- `!action`: Perform a variety of actions on a user.
- `!listactions`: List all the available actions that can be performed.
- `!insult`: Generate a random insult.

### Images
- `!cat`: Spawns a random cat! Big thanks to The Cat API!

### Currency
- `!roll`: 🪙 Roll for a reward!
- `!highlow`: Play the higher or lower gambling game!
- `!balance`: Check your current balance.
- `!gamble`: Gamble a specified amount of currency.
- `!send`: Send coins to another user.
- `!leaderboard`: Displays the top users with the highest balances.
- `!blackjack`: Play a simple game of blackjack. Bet must be greater than $0.
- `!rates`: View the current win and loss multipliers.

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

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` file for more information.

## License

This project is licensed under the GNU General Public License version 3. See the `LICENSE` file for more information.