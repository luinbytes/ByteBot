from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
import discord
import os
import json
import sqlite3
from PIL import ImageColor

DATABASE_DIR = "database"
ABS_PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATABASE_DIR, "currency.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

class Market(commands.Cog, name="market"):
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
            name="initmarket",
            description="Initialize the market",
            usage="initmarket",
    )
    @commands.has_permissions(administrator=True)
    async def init_market(self, context: Context) -> None:
        guild = self.bot.get_guild(context.guild.id)
        existing_roles = guild.roles
        colour_roles_exist = False

        for role in existing_roles:
            if role.name.startswith("Colour_"):
                colour_roles_exist = True
                break

        if colour_roles_exist:
            embed = discord.Embed(
                title="Market",
                description="Market already initialized.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
        else:
            colours = ["Red", "Orange", "Yellow", "Green", "Blue", "Indigo", "Violet"]
            for colour in colours:
                await guild.create_role(name=f"Colour_{colour}", color=discord.Colour.from_rgb(*ImageColor.getrgb(colour)))

            embed = discord.Embed(
                title="Market",
                description="Market initialized.",
                color=discord.Colour.green()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)

    @commands.hybrid_command(
            name="shop",
            description="View the shop",
            usage="shop",
            aliases=["market", "store"]
    )
    async def shop(self, context: Context) -> None:
        config = await self.load_config()
        guild = self.bot.get_guild(context.guild.id)
        existing_roles = guild.roles
        colour_roles = []

        for role in existing_roles:
            if role.name.startswith("Colour_"):
                colour_roles.append(role)

        embed = discord.Embed(
            title="🪙 Market",
            color=discord.Colour.blue()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)

        for role in colour_roles:
            role_name = role.name.split("_")[1]
            embed.add_field(name=f"{role_name} role", value=f"Price: `{config['market_colour_pricing']}`", inline=True)

        await context.send(embed=embed)

    @commands.command(
    name="buy",
    description="Buy something from the market",
    usage="buy <item>",
    aliases=["purchase"]
    )
    async def buy(self, context: Context, *, item: str) -> None:
        config = await self.load_config()
        guild = self.bot.get_guild(context.guild.id)
        member = context.author
        existing_roles = member.roles
        colour_roles = []

        for role in existing_roles:
            if role.name.startswith("Colour_"):
                colour_roles.append(role)

        target_role = discord.utils.get(guild.roles, name=f"Colour_{item.split(' ')[0].capitalize()}")
        if target_role is None:
            embed = discord.Embed(
            title="Market",
            description="Invalid colour role.",
            color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        if target_role in colour_roles:
            embed = discord.Embed(
                title="Market",
                description="You already have this colour role.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Check if the user has enough money
        user_id = str(member.id)
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        if result is None:
            embed = discord.Embed(
                title="Market",
                description="You don't have enough money to buy this colour role.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        balance = result[0]
        price = config.get("market_colour_pricing", 0)
        if balance < price:
            embed = discord.Embed(
                title="Market",
                description="You don't have enough money to buy this colour role.",
                color=discord.Colour.red()
            )
            embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
            await context.send(embed=embed)
            return

        # Deduct the amount from the user's balance
        new_balance = balance - price
        c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
        conn.commit()

        for role in colour_roles:
            await member.remove_roles(role)

        await member.add_roles(target_role)

        embed = discord.Embed(
            title="Market",
            description=f"You have successfully bought the {item} colour role.",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="setcolourprice",
        description="Set the price of colour roles",
        usage="setprice <price>",
        aliases=["setcolourpricing", "setcolourcost"]
    )
    @commands.is_owner()
    async def set_colour_price(self, context: Context, price: int) -> None:
        config = await self.load_config()
        config["market_colour_pricing"] = price
        await self.save_config(config)

        embed = discord.Embed(
            title="Market",
            description=f"Colour role pricing set to `{price}`.",
            color=discord.Colour.green()
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

@commands.Cog.listener()
async def on_disconnect(self):
    conn.close()

async def setup(bot) -> None:
    await bot.add_cog(Market(bot))