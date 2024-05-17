from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
import discord
import os
import sqlite3
import random
import math
import asyncio
from datetime import datetime, timedelta

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

class Currency(commands.Cog, name="currency"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="roll",
        description="Roll for a reward!",
        aliases=["r"]
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
            if (current_time - last_roll_date).total_seconds() >= 3600:  # 1 hour in seconds
                # Roll dice
                earnings = random.randint(5, 250)
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (earnings, user_id))
                c.execute("UPDATE users SET last_roll = ? WHERE user_id = ?", (current_time.strftime("%Y-%m-%d %H:%M:%S"), user_id))
                conn.commit()
                embed = discord.Embed(
                    title="Coin Reward",
                    description=f"You rolled the dice and earned {earnings} coins.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                time_remaining = timedelta(seconds=3600) - (current_time - last_roll_date)
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                embed = discord.Embed(
                    title="Coin Reward",
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
        earnings = random.randint(1, 100)
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (earnings, user_id))
        c.execute("UPDATE users SET last_roll = ? WHERE user_id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
        conn.commit()
        embed = discord.Embed(
            title="Daily Reward",
            description=f"You rolled the dice and earned {earnings} coins.",
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
    async def higherlower(self, context: Context) -> None:
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

        embed = discord.Embed(
            title="Higher or Lower!",
            description=f"You currently have {balance} coins.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Betting open.", value="Please enter a bet amount...", inline=True)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)


        def check(message):
            return message.author == context.author and message.channel == context.channel and message.content.isdigit()

        try:
            message = await self.bot.wait_for('message', timeout=30.0, check=check)
            bet_amount = int(message.content)
            if bet_amount > balance:
                embed = discord.Embed(
                    title="Higher or Lower!",
                    description="You don't have enough coins for that bet.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
                return

            number = random.randint(1, 20)
            embed = discord.Embed(
                title="Higher or Lower!",
                description=f"Guess if the next number will be higher or lower than {number} (h/l):",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

            def higher_lower_check(message):
                return message.author == context.author and message.channel == context.channel and message.content.lower() in ['h', 'l']

            try:
                guess_message = await self.bot.wait_for('message', timeout=30.0, check=higher_lower_check)
                guess = guess_message.content.lower()

                next_number = random.randint(1, 20)
                embed = discord.Embed(
                    title="Higher or Lower!",
                    description=f"The next number is: {next_number}",
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)

                if (next_number > number and guess == 'h') or (next_number < number and guess == 'l'):
                    winnings = math.floor(bet_amount * 1.2)
                    embed = discord.Embed(
                        title="Higher or Lower!",
                        description="Congratulations! You guessed correctly. You won {} coins.".format(winnings),
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (winnings, user_id))
                    conn.commit()
                else:
                    embed = discord.Embed(
                        title="Higher or Lower!",
                        description=f"Sorry, you guessed incorrectly. The correct number was {number}. You lost {bet_amount} coins.",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (bet_amount, user_id))
                    conn.commit()

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="Higher or Lower!",
                    description="You took too long to guess. The game has ended.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)

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
                title="Balance",
                description=f"{user.name}'s current balance is {balance} coins.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Balance",
                description=f"{user.name} hasn't registered yet.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
    name="gamble",
    description="Gamble a specified amount of currency.",
    usage="<amount>",
    aliases=["bet"]
    )
    @app_commands.describe(amount="The amount of currency to gamble. All winnings are 1.3x the amount.")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
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
        result = random.choice(["win", "lose"])
        if result == "win":
            winnings = math.floor(amount * 1.3)
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (winnings, user_id))
            conn.commit()
            message = f"You won {winnings} coins!"
            color = discord.Color.green()
        else:
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            message = f"You lost {amount} coins!"
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
            title="Coins Sent",
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

        # Check if user is registered
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

        # Update user's balance
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="Currency Added",
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

        # Update user's balance
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()

        embed = discord.Embed(
            title="Currency Removed",
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
            title="Balance Reset",
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
            title="Balance Set",
            description=f"{user.display_name}'s balance has been set to {amount} coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

@commands.Cog.listener()
async def on_disconnect(self, member):
    conn.close()

async def setup(bot) -> None:
    await bot.add_cog(Currency(bot))
