from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
import discord
import os
import sqlite3
import random
import json
import math
import asyncio
from datetime import datetime, timedelta
from PIL import Image
from typing import List, Tuple, Union

ABS_PATH = os.path.dirname(os.path.abspath(__file__))

# Ensure database directory exists
DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# Ensure database exists
DB_PATH = os.path.join(DATABASE_DIR, "currency.db")
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    balance INTEGER DEFAULT 0,
                    last_roll TEXT
                )''')
    conn.commit()
    conn.close()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

class Card:
    suits = ["H", "D", "C", "S"]

    def __init__(self, suit: str, value: int):
        self.suit = suit
        self.value = value
        self.symbol = self.get_symbol(value)
        self.down = False
        self.image = f"{self.symbol}{self.suit}.png"

    @staticmethod
    def get_symbol(value: int) -> str:
        if value == 11:
            return "J"
        elif value == 12:
            return "Q"
        elif value == 13:
            return "K"
        elif value == 14:
            return "A"
        return str(value)

    def flip(self):
        self.down = not self.down
        return self

def hand_to_images(hand: List[Card]) -> List[Image.Image]:
    return [Image.open(os.path.join(ABS_PATH, 'cards', card.image)) for card in hand]

def center(*hands: Tuple[List[Image.Image]]) -> Image.Image:
    bg = Image.open(os.path.join(ABS_PATH, 'table.png'))
    bg_center_x = bg.size[0] // 2
    bg_center_y = bg.size[1] // 2

    img_w = hands[0][0].size[0]
    img_h = hands[0][0].size[1]

    start_y = bg_center_y - (((len(hands) * img_h) + ((len(hands) - 1) * 15)) // 2)
    for hand in hands:
        start_x = bg_center_x - (((len(hand) * img_w) + ((len(hand) - 1) * 10)) // 2)
        for card in hand:
            bg.alpha_composite(card, (start_x, start_y))
            start_x += img_w + 10
        start_y += img_h + 15
    return bg

def output(name: str, *hands: Tuple[List[Card]]) -> None:
    center(*map(hand_to_images, hands)).save(f'{name}.png')

def calc_hand(hand: List[Card]) -> int:
    non_aces = [c for c in hand if c.symbol != 'A']
    aces = [c for c in hand if c.symbol == 'A']
    total = 0
    for card in non_aces:
        if not card.down:
            if card.symbol in 'JQK':
                total += 10
            else:
                total += card.value
    for card in aces:
        if not card.down:
            if total <= 10:
                total += 11
            else:
                total += 1
    return total

def check_bet(ctx: Context, bet: int) -> None:
    bet = int(bet)
    if bet < 10:
        raise commands.errors.BadArgument()
    user_id = ctx.author.id
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if not result or bet > result[0]:
        raise commands.errors.InsufficientFundsException(result[0] if result else 0, bet)

class Currency(commands.Cog, name="currency"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    async def save_config(self, config):
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    @commands.hybrid_command(
            name="winmultiplier",
            description="Check or set the global win muliplier.",
            usage="<amount>",
            aliases=["winmulti", "wmulti"]
    )
    @commands.has_permissions(administrator=True)
    @app_commands.describe(amount="The amount to set the win multiplier to.")
    async def winmultiplier(self, context: Context, amount: float = None) -> None:
        """
        Check or set the global coin multiplier.

        :param context: The application command context.
        :param amount: The amount to set the coin multiplier to.
        """
        config = await self.load_config()
        if amount is None:
            embed = discord.Embed(
                title="Win Multiplier",
                description=f"The current win multiplier is set to {config['win_multiplier']}.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        else:
            config['win_multiplier'] = amount
            await self.save_config(config)
            embed = discord.Embed(
                title="Win Multiplier",
                description=f"The win multiplier has been set to {amount}.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            
    @commands.hybrid_command(
            name="lossmultiplier",
            description="Check or set the global loss muliplier.",
            usage="<amount>",
            aliases=["lossmulti", "lmulti"]
    )
    @commands.has_permissions(administrator=True)
    @app_commands.describe(amount="The amount to set the loss multiplier to.")
    async def lossmultiplier(self, context: Context, amount: float = None) -> None:
        """
        Check or set the global coin multiplier.

        :param context: The application command context.
        :param amount: The amount to set the coin multiplier to.
        """
        config = await self.load_config()
        if amount is None:
            embed = discord.Embed(
                title="Loss Multiplier",
                description=f"The current loss multiplier is set to {config['loss_multiplier']}.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        else:
            config['loss_multiplier'] = amount
            await self.save_config(config)
            embed = discord.Embed(
                title="Loss Multiplier",
                description=f"The loss multiplier has been set to {amount}.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="roll",
        description="🪙 Roll for a reward!",
        aliases=["r", "dice", "diceroll", "rolldice", "rtd", "rollthedice"]
    )
    async def roll(self, context: Context) -> None:
        """
        This command allows users to roll the dice for a reward.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("SELECT last_roll FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            last_roll_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S") if result[0] else datetime.min
            current_time = datetime.now()
            if (current_time - last_roll_date).total_seconds() >= 1800:  # 0.5 hour in seconds
                # Roll dice
                earnings = random.randint(25, 500)
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (earnings, user_id))
                c.execute("UPDATE users SET last_roll = ? WHERE user_id = ?", (current_time.strftime("%Y-%m-%d %H:%M:%S"), user_id))
                conn.commit()
                embed = discord.Embed(
                    title="🪙 Coin Reward",
                    description=f"You rolled the dice and earned {earnings} coins!",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                time_remaining = timedelta(seconds=3600) - (current_time - last_roll_date)
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                embed = discord.Embed(
                    title="🪙 Coin Reward",
                    description=f"You can roll the dice again in {hours} hours, {minutes} minutes, and {seconds} seconds.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
        else:
            # Automatically register user and roll for them
            await self.register_user_roll(context)

    async def register_user_roll(self, context: Context) -> None:
        """
        This function registers a new user and rolls the dice for them.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("INSERT INTO users (user_id, username, last_roll) VALUES (?, ?, ?)", (user_id, str(context.author), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        #await context.send("You have been registered and can now roll the dice to earn coins.")
        # Roll dice
        earnings = random.randint(25, 250)
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (earnings, user_id))
        c.execute("UPDATE users SET last_roll = ? WHERE user_id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        embed = discord.Embed(
            title="🪙 Coin Reward",
            description=f"You rolled the dice and earned {earnings} coins!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    async def register_user_hol(self, context: Context) -> None:
        """
        This function registers a new user.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, str(context.author)))
        conn.commit()

    @commands.hybrid_command(
        name="highlow",
        description="Play the higher or lower gambling game!",
        aliases=["hol", "higherlower"]
    )
    @app_commands.describe(
        amount="The amount of coins to bet."
    )
    async def higherlower(self, context: Context, amount: int) -> None:
        """
        Play the higher or lower gambling game.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            await self.register_user(context)

        balance = result[0] if result else 0

        if balance <= 0:
            embed = discord.Embed(
            title="Higher or Lower!",
            description=f"You don't have enough coins to play.",
            color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        if amount < 10:
            embed = discord.Embed(
                title="Higher or Lower!",
                description="The minimum bet amount is 10 coins.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        config = await self.load_config()
        def check(reaction, user):
            return user == context.author

        try:
            bet_amount = int(amount)
            if bet_amount > balance:
                embed = discord.Embed(
                    title="Higher or Lower!",
                    description="You don't have enough coins for that bet.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
                return
            
            class holChoice(discord.ui.View):
                def __init__(self, user):
                    super().__init__()
                    self.user = user
                    self.value = None

                @discord.ui.button(label='Higher', style=discord.ButtonStyle.blurple)
                async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user != self.user:
                        return
                    self.value = 'h'
                    self.stop()

                @discord.ui.button(label='Lower', style=discord.ButtonStyle.red)
                async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
                    print(interaction.user)
                    if interaction.user != self.user:
                        return
                    self.value = 'l'
                    self.stop()

            number = random.randint(1, 30)
            buttons = holChoice(context.author)
            embed = discord.Embed(
                title="Higher or Lower!",
                description=f"Guess if the next number will be higher or lower than `{number}` (h/l):",
                color=discord.Color.blue()
            )
            embed.add_field(name="Rules:", value=f"```A random number from 1 to 30 will be generated. You must guess if the next number will be higher or lower than the current number. If you guess correctly, you win {config["win_multiplier"]}x your bet amount. If you guess incorrectly, you lose 55% of your bet amount.```", inline=False)
            embed.add_field(name="Bet Amount:", value=f"`{bet_amount} coins`", inline=True)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            message = await context.send(embed=embed, view=buttons)
            await buttons.wait()
            await message.edit(embed=embed, view=None, content=None)

            try:
                guess = buttons.value
                button_value = ""
                if guess == "h":
                    button_value = "higher"
                else:
                    button_value = "lower"
                next_number = random.randint(2, 29)
                if next_number == number:
                    random.randint(2, 19)
                if (next_number > number and guess == 'h') or (next_number < number and guess == 'l'):
                    winnings = math.floor(bet_amount * config["win_multiplier"])
                    embed = discord.Embed(
                        title="Higher or Lower!",
                        description="Congratulations! You guessed correctly. You won {} coins! 🪙".format(winnings),
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Number:", value=f"First: `{number}` | Next: `{next_number}`", inline=False)
                    embed.add_field(name="Guess:", value=f"You guessed `{button_value}`.", inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await message.edit(embed=embed)
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (winnings, user_id))
                    conn.commit()
                else:
                    losses = math.floor(bet_amount * config["loss_multiplier"])
                    embed = discord.Embed(
                        title="Higher or Lower!",
                        description=f"Sorry, you guessed incorrectly.  You lost {losses} coins.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Number:", value=f"First: `{number}` | Next: `{next_number}`", inline=False)
                    embed.add_field(name="Guess:", value=f"You guessed `{button_value}`.", inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await message.edit(embed=embed)
                    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (losses, user_id))
                    conn.commit()

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Higher or Lower!",
                    description="You took too long to guess. The game has ended.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await message.edit(embed=embed)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Higher or Lower!",
                description="You took too long to respond. The game has ended.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="balance",
        description="Check your current balance.",
        aliases=["bal"]
    )
    async def balance(self, context: Context, user: discord.User = None) -> None:
        """
        This command allows users to check their current balance.

        :param context: The application command context.
        :param user: The user whose balance is to be checked (optional).
        """
        if user is None:
            user = context.author
        
        user_id = user.id
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if result:
            balance = result[0]
            embed = discord.Embed(
                title="🪙 Balance",
                description=f"{user.mention}'s current balance is {balance} coins.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Balance",
                description=f"{user.mention} hasn't registered yet.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
    name="gamble",
    description="Gamble a specified amount of currency.",
    usage="<amount>",
    aliases=["bet"]
    )
    @app_commands.describe(amount="The amount of currency to gamble.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def gamble(self, context: Context, amount: int) -> None:
        """
        This command allows users to gamble a specified amount of currency.

        :param context: The application command context.
        :param amount: The amount of currency to gamble.
        """
        user_id = context.author.id

        # Check if user is registered
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="You are not registered to gamble.",
                color=discord.Color.red()
            )
            embed.add_field(name="How to register", value=f"Use the `roll` command to register yourself in the currency database!", inline=False)
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        balance = user_data[0]

        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Amount",
                description="You can only gamble a positive amount of currency.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        
        if amount < 10:
            embed = discord.Embed(
                title="Invalid Amount",
                description="The minimum amount to gamble is 10 coins.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        if amount > balance:
            embed = discord.Embed(
                title="Insufficient Balance",
                description="You don't have enough currency to gamble.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Perform gamble
        config = await self.load_config()
        result = random.choice(["win", "lose"])
        if result == "win":
            winnings = math.floor(amount * config["win_multiplier"])
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (winnings, user_id))
            conn.commit()
            message = f"🪙 You won {winnings} coins! 🪙"
            color = discord.Color.green()
        else:
            losses = math.floor(amount * config["loss_multiplier"])
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (losses, user_id))
            conn.commit()
            message = f"You lost {losses} coins!"
            color = discord.Color.red()

        embed = discord.Embed(
            title="Gamble Result",
            description=message,
            color=color
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="send",
        description="Send coins to another user.",
        usage="<@user> <amount>",
        aliases=["transfer", "give"]
    )
    @app_commands.describe(amount="The amount of coins to send.")
    async def send(self, context: Context, user: discord.User, amount: int) -> None:
        """
        This command allows users to send coins to another user.

        :param context: The application command context.
        :param user: The user to send coins to.
        :param amount: The amount of coins to send.
        """
        sender_id = context.author.id

        # Check if sender is registered
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (sender_id,))
        sender_data = c.fetchone()
        if not sender_data:
            embed = discord.Embed(
                title="Sender Not Registered",
                description="You are not registered to send coins.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Amount",
                description="You can only send a positive amount of coins.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        if user == context.author:
            embed = discord.Embed(
                title="Invalid User",
                description="You can't send coins to yourself.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Check if sender has enough balance
        c.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
        sender_balance_data = c.fetchone()
        if sender_balance_data is None:
            embed = discord.Embed(
                title="Error",
                description="Failed to retrieve sender balance data.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        sender_balance = sender_balance_data[0]
        if sender_balance < amount:
            embed = discord.Embed(
                title="Insufficient Balance",
                description="You don't have enough coins to send.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        recipient_id = user.id

        # Check if recipient is registered
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (recipient_id,))
        recipient_data = c.fetchone()
        if not recipient_data:
            embed = discord.Embed(
                title="Recipient Not Registered",
                description="The recipient is not registered to receive coins.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Update sender's balance
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        conn.commit()

        # Update recipient's balance
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
        conn.commit()
        embed = discord.Embed(
            title="🪙 Coins Sent",
            description=f"You have sent {amount} coins to {user.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="addcurr",
        description="Add a currency to a user's balance.",
        usage="<@user> <amount>"
    )
    @commands.has_permissions(administrator=True)
    async def addcurr(self, context: Context, user: discord.User, amount: int) -> None:
        """
        This command allows administrators to add currency to a user's balance.

        :param context: The application command context.
        :param user: The user to add currency to.
        :param amount: The amount of currency to add.
        """
        user_id = user.id

        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Currency Added",
            description=f"{amount} coins have been added to {user.display_name}'s balance.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="rmbalance",
        description="Remove a user's balance.",
        usage="<@user> <@amount>",
        aliases=["rmbal", "removebal", "removebalance"]
    )
    @commands.has_permissions(administrator=True)
    async def rmcurr(self, ctx, user: discord.User, amount: int):
        """
        Remove currency from a user's balance.
        
        :param user: The user to remove currency from.
        :param amount: The amount of currency to remove.
        """
        user_id = user.id

        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return
        
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Currency Removed",
            description=f"{amount} coins have been removed from {user.display_name}'s balance.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="resetbalance",
        description="Resets a user's balance.",
        usage="<@user>",
        aliases=["rsbalance", "resetbal", "rsbal"]
    )
    @commands.has_permissions(administrator=True)
    async def resetcurr(self, ctx, user: discord.User):
        """
        Reset a user's balance to 0.
        
        :param user: The user whose balance to reset.
        """
        user_id = user.id

        # Check if user is registered
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return

        # Reset user's balance to 0
        c.execute("UPDATE users SET balance = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Balance Reset",
            description=f"{user.display_name}'s balance has been reset to 0 coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="setbalance",
        description="Set a user's balance.",
        usage="<@user> <@amount>",
        aliases=["setbal"]
    )
    @commands.has_permissions(administrator=True)
    async def setcurr(self, ctx, user: discord.User, amount: int):
        """
        Set a user's balance to a specific amount.
        
        :param user: The user whose balance to set.
        :param amount: The amount of currency to set.
        """
        user_id = user.id

        # Check if user is registered
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user_data = c.fetchone()
        if not user_data:
            embed = discord.Embed(
                title="User Not Registered",
                description="The specified user is not registered.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.send(embed=embed)
            return

        # Update user's balance to the specified amount
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="🪙 Balance Set",
            description=f"{user.display_name}'s balance has been set to {amount} coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="leaderboard",
        description="Displays the top users with the highest balances.",
        aliases=["lb", "top"]
    )
    async def leaderboard(self, context: Context) -> None:
        """
        Display the top users with the highest balances.
        """
        # Fetch top 10 users with the highest balance
        c.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        top_users = c.fetchall()

        if not top_users:
            embed = discord.Embed(
                title="Leaderboard",
                description="No users found in the leaderboard.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Create the leaderboard embed
        embed = discord.Embed(
            title="🪙 Leaderboard - Top 10 Users 🪙",
            description="Here are the top users with the highest balances:",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

        for idx, (user_id, balance) in enumerate(top_users, start=1):
            user = self.bot.get_user(user_id)
            if user:
                embed.add_field(name=f"{idx}. {user.display_name}", value=f"{balance} coins 🪙", inline=False)
            else:
                embed.add_field(name=f"{idx}. User ID: {user_id}", value=f"{balance} coins 🪙", inline=False)

        await context.send(embed=embed)

    # Blackjack
    @commands.command(
    name="blackjack",
    description="Play a simple game of blackjack. Bet must be greater than $0.",
    usage="<bet_amount>"
    )
    @app_commands.describe(bet_amount="The amount you want to bet in blackjack, minimum is 10 coins.")
    async def blackjack(self, context: Context, bet_amount: int) -> None:
        user_id = context.author.id
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            await self.register_user_hol(context)

        balance = result[0] if result else 0

        if balance <= 0:
            embed = discord.Embed(
                title="Blackjack",
                description="You don't have enough coins to play.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        try:
            check_bet(context, bet_amount)
        except commands.errors.BadArgument:
            embed = discord.Embed(
                title="Invalid Bet Amount",
                description="The bet amount must be greater than $0.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return
        except commands.errors.InsufficientFundsException as e:
            embed = discord.Embed(
                title="Insufficient Funds",
                description=f"You don't have enough coins for that bet. Your balance: {e.balance}.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        deck = [Card(suit, num) for num in range(2, 15) for suit in Card.suits]
        random.shuffle(deck)

        player_hand: List[Card] = [deck.pop(), deck.pop()]
        dealer_hand: List[Card] = [deck.pop(), deck.pop().flip()]

        player_score = calc_hand(player_hand)
        dealer_score = calc_hand(dealer_hand)

        async def out_table(**kwargs) -> discord.Message:
            output(context.author.id, dealer_hand, player_hand)
            embed = discord.Embed(**kwargs)
            file = discord.File(f"{context.author.id}.png", filename=f"{context.author.id}.png")
            embed.set_image(url=f"attachment://{context.author.id}.png")
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            return await context.send(file=file, embed=embed)

        def check_reaction(reaction: discord.Reaction, user: Union[discord.Member, discord.User]) -> bool:
            return all((
                str(reaction.emoji) in ("🇸", "🇭"),
                user == context.author,
                user != self.bot.user,
                reaction.message.id == msg.id
            ))

        standing = False

        msg = None
        while True:
            player_score = calc_hand(player_hand)
            dealer_score = calc_hand(dealer_hand)
            config = await self.load_config()
            if player_score == 21:
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet_amount, context.author.id))
                conn.commit()
                result = ("🪙 Blackjack!", 'won')
                break
            elif player_score > 21:
                losses = math.floor(bet_amount * 0.90)
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (losses, context.author.id))
                conn.commit()
                result = ("Player busts", 'lost')
                break

            msg = await out_table(
                title="Your Turn",
                description=f"Your hand: {player_score}\nDealer's hand: {dealer_score}"
            )
            await msg.add_reaction("🇭")
            await msg.add_reaction("🇸")

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60, check=check_reaction)
            except asyncio.TimeoutError:
                if msg:
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                return

            if str(reaction.emoji) == "🇭":
                player_hand.append(deck.pop())
                if msg:
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                continue
            elif str(reaction.emoji) == "🇸":
                standing = True
                break

        if standing:
            dealer_hand[1].flip()
            while (dealer_score := calc_hand(dealer_hand)) < 17:
                dealer_hand.append(deck.pop())
            
            losses = math.floor(bet_amount * 0.9)

            if dealer_score == 21:
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (losses, context.author.id))
                conn.commit()
                result = ('Dealer blackjack', 'lost')
            elif dealer_score > 21:
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet_amount, context.author.id))
                conn.commit()
                result = ("Dealer busts", 'won')
            elif dealer_score == player_score:
                result = ("Tie!", 'kept')
            elif dealer_score > player_score:
                c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (losses, context.author.id))
                conn.commit()
                result = ("You lose!", 'lost')
            else:
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet_amount, context.author.id))
                conn.commit()
                result = ("🪙 You win!", 'won')

        color = discord.Color.red() if result[1] == 'lost' else discord.Color.green() if result[1] == 'won' else discord.Color.blue()
        coin_type = bet_amount
        if result[1] == 'lost':
            coin_type = losses
        if msg:
            try:
                await msg.delete()
            except discord.errors.NotFound:
                pass
        try:
            await out_table(
                title=result[0],
                color=color,
                description=f"**You {result[1]} {coin_type} coins!**\nYour hand: {player_score}\nDealer's hand: {dealer_score}"
            )
            os.remove(f'./{context.author.id}.png')

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Blackjack",
                description="You took too long to respond. The game has ended.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
        title="rates",
        description="View the current win and loss multipliers.",
        aliases=["multipliers", "multi"]
    )
    async def rates(self, context: Context) -> None:
        """
        View the current win and loss multipliers.
        """
        config = await self.load_config()
        embed = discord.Embed(
            title="Rates",
            description=f"Win Multiplier: {config['win_multiplier']}\nLoss Multiplier: {config['loss_multiplier']}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

@commands.Cog.listener()
async def on_disconnect(self):
    conn.close()

async def setup(bot) -> None:
    await bot.add_cog(Currency(bot))
