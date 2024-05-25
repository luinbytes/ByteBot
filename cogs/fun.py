import random

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context


class Choice(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value = None

    @discord.ui.button(label="Heads", style=discord.ButtonStyle.blurple)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.value = "heads"
        self.stop()

    @discord.ui.button(label="Tails", style=discord.ButtonStyle.blurple)
    async def cancel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        self.value = "tails"
        self.stop()

class RockPaperScissors(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Scissors", description="You choose scissors.", emoji="✂"
            ),
            discord.SelectOption(
                label="Rock", description="You choose rock.", emoji="🪨"
            ),
            discord.SelectOption(
                label="Paper", description="You choose paper.", emoji="🧻"
            ),
        ]
        super().__init__(
            placeholder="Choose...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        choices = {
            "rock": 0,
            "paper": 1,
            "scissors": 2,
        }
        user_choice = self.values[0].lower()
        user_choice_index = choices[user_choice]

        bot_choice = random.choice(list(choices.keys()))
        bot_choice_index = choices[bot_choice]

        result_embed = discord.Embed(color=0xBEBEFE)
        result_embed.set_author(
            name=interaction.user.name, icon_url=interaction.user.display_avatar.url
        )

        winner = (3 + user_choice_index - bot_choice_index) % 3
        if winner == 0:
            result_embed.description = f"**That's a draw!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = 0xF59E42
        elif winner == 1:
            result_embed.description = f"**You won!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = 0x57F287
        else:
            result_embed.description = f"**You lost!**\nYou've chosen {user_choice} and I've chosen {bot_choice}."
            result_embed.colour = 0xE02B2B

        await interaction.response.edit_message(
            embed=result_embed, content=None, view=None
        )


class RockPaperScissorsView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.add_item(RockPaperScissors())


class Fun(commands.Cog, name="fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        description="Ask any question to the bot.",
        usage="8ball <question>",
        aliases=["ask", "eightball"]
    )
    @app_commands.describe(question="The question you want to ask.")
    async def eight_ball(self, context: Context, *, question: str) -> None:
        """
        Ask any question to the bot.

        :param context: The hybrid command context.
        :param question: The question that should be asked by the user.
        """
        answers = [
            "It is certain.",
            "It is decidedly so.",
            "You may rely on it.",
            "Without a doubt.",
            "Yes - definitely.",
            "As I see, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again later.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        embed = discord.Embed(
            title="**My Answer:**",
            description=f"{random.choice(answers)}",
            color=0xBEBEFE,
        )
        embed.set_footer(text=f"The question was: {question}")
        await context.send(embed=embed)

    @commands.hybrid_command(
            name="randomfact", 
            description="Get a random fact.",
            usage="randomfact"
    )
    async def randomfact(self, context: Context) -> None:
        """
        Get a random fact.

        :param context: The hybrid command context.
        """
        # This will prevent your bot from stopping everything when doing a web request - see: https://discordpy.readthedocs.io/en/stable/faq.html#how-do-i-make-a-web-request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://uselessfacts.jsph.pl/random.json?language=en"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    embed = discord.Embed(description=data["text"], color=0xD75BF4)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                await context.send(embed=embed)

    @commands.hybrid_command(
        name="coinflip", 
        description="Make a coin flip, but give your bet before.",
        usage="coinflip",
        aliases=["coin", "flip"]
    )
    async def coinflip(self, context: Context) -> None:
        """
        Make a coin flip, but give your bet before.

        :param context: The hybrid command context.
        """
        buttons = Choice()
        embed = discord.Embed(description="What is your bet?", color=0xBEBEFE)
        message = await context.send(embed=embed, view=buttons)
        await buttons.wait()  # We wait for the user to click a button.
        result = random.choice(["heads", "tails"])
        if buttons.value == result:
            embed = discord.Embed(
                description=f"Correct! You guessed `{buttons.value}` and I flipped the coin to `{result}`.",
                color=0xBEBEFE,
            )
        else:
            embed = discord.Embed(
                description=f"Woops! You guessed `{buttons.value}` and I flipped the coin to `{result}`, better luck next time!",
                color=0xE02B2B,
            )
        await message.edit(embed=embed, view=None, content=None)

    @commands.hybrid_command(
        name="rps", 
        description="Play the rock paper scissors game against the bot.",
        usage="rps",
        aliases=["rockpaperscissors"]
    )
    async def rock_paper_scissors(self, context: Context) -> None:
        """
        Play the rock paper scissors game against the bot.

        :param context: The hybrid command context.
        """
        view = RockPaperScissorsView()
        await context.send("Please make your choice", view=view)

    @commands.hybrid_command(
        name="catslap", 
        description="Cat-Slap someone.",
        usage="catslap <@user>",
        aliases=["slapcat", "catsmack"]
    )
    @app_commands.describe(
        user="The user to slap."
    )
    async def slap(self, context: Context, user: discord.Member = None) -> None:
        """
        Cat-Slap someone.

        :param context: The hybrid command context.
        :param user: The user to slap.
        """
        slap_array = [
            "https://media1.tenor.com/m/W2QqtV4k6ykAAAAd/orange-cat-cat-hitting-cat.gif",
            "https://media1.tenor.com/m/bblihRQawfsAAAAC/kitty-slap-kat-slap.gif",
            "https://media1.tenor.com/m/KjImwF1A5dYAAAAC/cat-kitty.gif",
            "https://media1.tenor.com/m/_7kB0uF03_sAAAAd/cat-slap-slap-cat.gif",
            "https://media1.tenor.com/m/ucAVz13QYXsAAAAd/cats-slap-cat.gif"
        ]

        slap_messages = [
            f"<@{context.author.id}> Slapped <@{user.id}>, ouch!",
            f"<@{context.author.id}> Slapped <@{user.id}>, wtheck...",
            f"<@{context.author.id}> Slapped <@{user.id}>, wtflip!!!",
            f"<@{context.author.id}> Slapped <@{user.id}>, get some ice..."
        ]

        embed = discord.Embed()
        embed.set_image(url=random.choice(slap_array))
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)
        await context.send(random.choice(slap_messages))

    @commands.hybrid_command(
        name="randommeme",
        description="Grabs a random meme from meme-api.com",
        aliases=["meme", "rmeme"],
        usage="randommeme"
    )
    @app_commands.describe(

    )
    async def randommeme(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://meme-api.com/gimme/"
            ) as request:
                # print(request.status)
                if request.status == 200:
                    data = await request.json()
                    title = data.get("title", "No title available")
                    author = data.get("author", "No author available")
                    url = data.get("url", "")

                    embed = discord.Embed(title="Random Meme", \
                        color=0xD75BF4,
                        description=f"[View Image]({url})"
                    )
                    embed.set_image(url=url)
                    embed.add_field(name="Title", value=title, inline=False)
                    embed.add_field(name="Author", value=author, inline=False)
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )

    @commands.hybrid_command(
        name="kanye",
        description="Get a random Kanye West quote.",
        aliases=["kanyewest", "kanyequote"],
        usage="kanye"
    )
    @app_commands.describe(

    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def kanye(self, context: Context) -> None:
        kanyarray = [
            "https://media1.tenor.com/m/-OpJG9GeK3EAAAAC/kanye-west-stare.gif",
            "https://media1.tenor.com/m/sPKTQ1DZpEYAAAAC/kanye-west-shrug.gif",
            "https://media1.tenor.com/m/4qlYLATKhZoAAAAd/kanye-west.gif",
            "https://media1.tenor.com/m/pXbU7RAcQ4MAAAAd/kawaii-kanye-west.gif",
            "https://media1.tenor.com/m/0i0GFBYak7YAAAAd/fadsfantasy.gif",
            "https://media1.tenor.com/m/m_iZNYP99PYAAAAd/luluca-epic-seven.gif",
            "https://media1.tenor.com/m/1HTrLTSaWrcAAAAC/ye.gif",
            "https://media1.tenor.com/m/Qo4mu6AXcuQAAAAC/kanye-west-moneybot.gif",
            "https://media1.tenor.com/m/tso5-09N8voAAAAd/kanye-haircut.gif",
            "https://media1.tenor.com/m/TLnxLfZh_HIAAAAC/ilikeit-janye.gif",
            "https://media1.tenor.com/m/5GndSOFS1xYAAAAd/sus-kanye.gif",
            "https://media1.tenor.com/m/5ovvk6FeZ2YAAAAd/bongocatsolana-bongosolana.gif"
        ]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.kanye.rest/"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    quote = data.get("quote", "No quote available")
                    embed = discord.Embed(
                        title="Kanye West Quote",
                        description=quote,
                        color=0xD75BF4
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    embed.set_image(url=random.choice(kanyarray))
                    await context.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                    await context.send(embed=embed)

    @commands.hybrid_command(
        name="chucknorris",
        description="Get a random Chuck Norris fact.",
        aliases=["norrisfact", "norris", "chuck"],
        usage="chucknorris"
    )
    @app_commands.describe(

    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def chuck_norris(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.chucknorris.io/jokes/random"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    embed = discord.Embed(
                        title="Chuck Norris Fact",
                        description=data["value"],
                        color=0xD75BF4
                    )
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                    await context.send(embed=embed)

    @commands.hybrid_command(
        name="trump",
        description="Get a random Trump quote.",
        aliases=["trumpquote"],
        usage="trump"
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def trump(self, context: Context) -> None:
        trumparray = [
            "https://media1.tenor.com/m/P_wiMZbNoxUAAAAd/trump-meme.gif",
            "https://media1.tenor.com/m/mFQjditE1_YAAAAC/yes-thumbs.gif",
            "https://media1.tenor.com/m/AfmmAJ1nCZwAAAAC/trumpwinning-trump.gif",
            "https://media1.tenor.com/m/mZRs8QkX0p8AAAAC/donald-trump-liv-golf.gif",
            "https://media1.tenor.com/m/3wIbTPz_2PMAAAAd/trump-laugh.gif",
            "https://media1.tenor.com/m/feOregL8nIgAAAAd/trump.gif",
            "https://media1.tenor.com/m/NxtLvCgo_kAAAAAC/trucker-for-trump-truckers.gif",
            "https://media1.tenor.com/m/d8BcwLcNuF8AAAAC/trump-excited.gif"
        ]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.whatdoestrumpthink.com/api/v1/quotes/random"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    quote = data.get("message", "No quote available")
                    embed = discord.Embed(
                        title="Trump Quote",
                        description=quote,
                        color=0xD75BF4
                    )
                    embed.set_image(url=random.choice(trumparray))
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                    await context.send(embed=embed)

    @commands.hybrid_command(
        name="action",
        description="Perform a variety of actions on a user.",
        usage="<action> <@user>",
        aliases=["performaction", "perform"]
    )
    @app_commands.describe(
        user="The user to perform the action on.",
        action="The action to perform on the user."
    )
    async def perform_action(self, context: Context, action: str, user: discord.Member = None) -> None:
        """
        Perform a variety of actions on a user.
    
        :param context: The hybrid command context.
        :param action: The action to perform on the user.
        :param user: The user to perform the action on.
        """
        action_phrases = {
            "angry": ["is angry at", "is angry"],
            "bite": ["bites", "bites"],
            "blush": ["is blushing at", "is blushing"],
            "comfy": ["is feeling comfy because of", "is feeling comfy"],
            "cry": ["is crying because of", "is crying"],
            "cuddle": ["cuddles with", "cuddles with"],
            "dance": ["is dancing with", "is dancing"],
            "fluff": ["fluffs up at", "fluffs up"],
            "hug": ["hugs", "hugs"],
            "kiss": ["kisses", "kisses"],
            "lay": ["lays down with", "is laying down"],
            "lick": ["licks", "licks themselves"],
            "pat": ["pats", "pats themselves"],
            "poke": ["pokes", "pokes themselves"],
            "pout": ["is pouting at", "is pouting"],
            "slap": ["slaps", "slaps themselves"],
            "smile": ["smiles at", "is smiling"],
            "tail": ["wags tail at", "is wagging their tail"],
            "tickle": ["tickles", "tickles themselves"],
            "eevee": ["transforms into Eevee at", "transforms into Eevee"],
            "neko": ["transforms into Neko at", "transforms into Neko"]
        }
    
        if action not in action_phrases.keys():
            return await context.send("Invalid action! Please use `listactions` to see all available actions.")
    
        if user:
            dynamic_description = f"{context.author.mention} {action_phrases[action][0]} {user.mention}!"
        else:
            dynamic_description = f"{context.author.mention} {action_phrases[action][1]}!"
    
        base_url = "https://purrbot.site/api"
        endpoint = f"/img/sfw/{action}/gif"
    
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url + endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    embed = discord.Embed(
                        title="",
                        description=dynamic_description,
                        color=0xD75BF4
                    )
                    embed.set_image(url=data["link"])
                    embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
                    await context.send(embed=embed)

    @commands.hybrid_command(
        name="listactions",
        description="List all the available actions that can be performed.",
        aliases=["actions", "actionlist"],
        usage="listactions"
    )
    @app_commands.describe(

    )
    async def list_actions(self, context: Context) -> None:
        """
        List all the available actions that can be performed.

        :param context: The hybrid command context.
        """
        actions = [
            "angry", "bite", "blush", "comfy", "cry", "cuddle", "dance", "fluff", "hug", "kiss", "lay", "lick", "pat", "poke", "pout", "slap", "smile", "tail", "tickle", "eevee", "neko"
        ]
        embed = discord.Embed(
            title="Available Actions",
            description=", ".join(actions),
            color=0xD75BF4
        )
        embed.set_footer(text=f"Requested by {context.author.name}", icon_url=context.author.avatar)
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="insult",
        description="Generate a random insult.",
        usage="insult <@user>"
    )
    @app_commands.describe(
        user="The user to insult."
    )
    async def insult(self, context: Context, user: discord.Member = None) -> None:
        """
        Generate a random insult.

        :param context: The hybrid command context.
        :param user: The user to insult.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://evilinsult.com/generate_insult.php?lang=en&type=json"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    insult = data.get("insult", "No insult available")
                    if user is None:
                        await context.send(insult)
                    else:
                        await context.send(f"{user.mention}, {insult}")
                else:
                    embed = discord.Embed(
                        title="Error!",
                        description="There is something wrong with the API, please try again later",
                        color=0xE02B2B,
                    )
                    await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))
