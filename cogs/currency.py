from discord.ext import commands
from discord.ext.commands import Context
import discord
import os
import sqlite3
import random
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
        description="Roll for a daily reward!",
    )
    async def roll(self, context: Context) -> None:
        """
        This command allows users to roll the dice for a daily reward.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("SELECT last_roll FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            last_roll_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S") if result[0] else datetime.min
            current_time = datetime.now()
            if (current_time - last_roll_date).total_seconds() >= 10800:  # 3 hours in seconds
                # Roll dice
                earnings = random.randint(5, 250)
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (earnings, user_id))
                c.execute("UPDATE users SET last_roll = ? WHERE user_id = ?", (current_time.strftime("%Y-%m-%d %H:%M:%S"), user_id))
                conn.commit()
                embed = discord.Embed(
                    title="Daily Reward",
                    description=f"You rolled the dice and earned {earnings} coins.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
            else:
                time_remaining = timedelta(seconds=10800) - (current_time - last_roll_date)
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                embed = discord.Embed(
                    title="Daily Reward",
                    description=f"You can roll the dice again in {hours} hours, {minutes} minutes, and {seconds} seconds.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=embed)
        else:
            # Automatically register user and roll for them
            await self.register_user(context)

    async def register_user(self, context: Context) -> None:
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

    @commands.hybrid_command(
        name="balance",
        description="Check your current balance.",
    )
    async def balance(self, context: Context) -> None:
        """
        This command allows users to check their current balance.

        :param context: The application command context.
        """
        user_id = context.author.id
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        if result:
            balance = result[0]
            embed = discord.Embed(
                title="Balance",
                description=f"Your current balance is {balance} coins.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Balance",
                description=f"You haven't registered yet. Use the `{context.prefix}roll` command to start earning coins!",
                color=discord.Color.red()
            )
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="send",
        description="Send coins to another user.",
        usage="<@user> <amount>",
    )
    async def send(self, context: Context, user: discord.User, amount: int) -> None:
        """
        This command allows users to send coins to another user.

        :param context: The application command context.
        :param user: The user to send coins to.
        :param amount: The amount of coins to send.
        """
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

        sender_id = context.author.id
        recipient_id = user.id

        # Check if sender has enough balance
        c.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
        sender_balance = c.fetchone()[0]
        if sender_balance < amount:
            embed = discord.Embed(
                title="Insufficient Balance",
                description="You don't have enough coins to send.",
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
            description=f"You have sent {amount} coins to {user.display_name}.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

@commands.Cog.listener()
async def on_disconnect(self, member):
    conn.close()

async def setup(bot) -> None:
    await bot.add_cog(Currency(bot))
