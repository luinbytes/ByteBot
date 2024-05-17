import platform

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.context_menu_user = app_commands.ContextMenu(
            name="Grab ID", callback=self.grab_id
        )
        self.bot.tree.add_command(self.context_menu_user)
        self.context_menu_message = app_commands.ContextMenu(
            name="Remove spoilers", callback=self.remove_spoilers
        )
        self.bot.tree.add_command(self.context_menu_message)

    # Message context menu command
    async def remove_spoilers(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        """
        Removes the spoilers from the message. This command requires the MESSAGE_CONTENT intent to work properly.

        :param interaction: The application command interaction.
        :param message: The message that is being interacted with.
        """
        spoiler_attachment = None
        for attachment in message.attachments:
            if attachment.is_spoiler():
                spoiler_attachment = attachment
                break
        embed = discord.Embed(
            title="Message without spoilers",
            description=message.content.replace("||", ""),
            color=0xBEBEFE,
        )
        if spoiler_attachment is not None:
            embed.set_image(url=attachment.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # User context menu command
    async def grab_id(
        self, interaction: discord.Interaction, user: discord.User) -> None:
        """
        Grabs the ID of the user.

        :param interaction: The application command interaction.
        :param user: The user that is being interacted with.
        """
        embed = discord.Embed(
            description=f"The ID of {user.mention} is `{user.id}`.",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar) # type: ignore
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded or show commands in a specific category.",
    )
    async def help(self, context: Context, category: str = None) -> None:
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available categories:", color=0xBEBEFE
        )
        embed.add_field(name=f"Use {prefix}help <category> to see commands", value="", inline=False)
        for cog_name in self.bot.cogs:
            if cog_name == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            embed.add_field(name="", value=cog_name.capitalize(), inline=False)
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        
        if category:
            category_lower = category.lower()
            cog = self.bot.get_cog(category_lower)
            if cog:
                commands = cog.get_commands()
                data = []
                for command in commands:
                    description = command.description.partition("\n")[0]
                    data.append(f"{prefix}{command.name} - {description}")
                help_text = "\n".join(data)
                category_embed = discord.Embed(
                    title=f"{category.capitalize()} Commands",
                    description=f"```{help_text}```",
                    color=0xBEBEFE
                )
                category_embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                await context.send(embed=category_embed)
            else:
                await context.send("Invalid category. Please use !help to see available categories.")
        else:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="botinfo",
        description="Get some useful (or not) information about the bot.",
    )
    async def botinfo(self, context: Context) -> None:
        """
        Get some useful (or not) information about the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            description="Made by @0x6c75",
            color=0xBEBEFE,
        )
        embed.set_author(name="Bot Information")
        embed.add_field(name="Owner:", value="@0x6c75", inline=True)
        embed.add_field(
            name="Python Version:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Discord.py Version:",
            value=f"{discord.__version__}",
            inline=True,
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {self.bot.config['prefix']} for normal commands",
            inline=False,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        description="Get some useful (or not) information about the server.",
    )
    async def serverinfo(self, context: Context) -> None:
        """
        Get some useful (or not) information about the server.

        :param context: The hybrid command context.
        """
        roles = [role.name for role in context.guild.roles]
        num_roles = len(roles)
        if num_roles > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying [50/{num_roles}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**", description=f"{context.guild}", color=0xBEBEFE
        )
        if context.guild.icon is not None:
            embed.set_thumbnail(url=context.guild.icon.url)
        embed.add_field(name="Server ID", value=context.guild.id)
        embed.add_field(name="Member Count", value=context.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(context.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(context.guild.roles)})", value=roles)
        embed.add_field(name="Created At", value=f"{context.guild.created_at}")
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="Check if the bot is alive.",
    )
    async def ping(self, context: Context) -> None:
        """
        Check if the bot is alive.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="Get the invite link of the bot to be able to invite it.",
    )
    async def invite(self, context: Context) -> None:
        """
        Get the invite link of the bot to be able to invite it.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title=f"Invite {self.bot.config['bot_name']}",
            description=f"Invite me by clicking [here]({self.bot.config['invite_link']}).",
            color=0xD75BF4,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

    @commands.hybrid_command(
        name="server",
        description="Get the invite link of the discord server of the bot for some support.",
    )
    async def server(self, context: Context) -> None:
        """
        Get the invite link of the discord server of the bot for some support.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title=f"Support Server for {self.bot.config['bot_name']}",
            description=f"Join the support server for the bot by clicking [here](https://discord.gg/qvXZggKKnJ).",
            color=0xD75BF4,
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        try:
            await context.author.send(embed=embed)
            await context.send("I sent you a private message!")
        except discord.Forbidden:
            await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(General(bot))
