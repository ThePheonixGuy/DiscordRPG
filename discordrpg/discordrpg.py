#Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
from __main__ import send_cmd_help
#Others
import os

class DiscordRPG:
    """The Discord RPG. I mean, *Thee Discord RPG*"""

    def __init__(self, bot):
        self.bot = bot
        self.players = Player(bot, "data/discordrpg/players.json") #note that the players refered to from here on out will be a collective object of the type Player that handles the player function.
        # this method of referal will be prefered going forward, unless we move forward to using modules (which we might)
        self.settings_path = "data/discordrpg/settings.json"
        self.settings = dataIO.load_json(self.settings_path)

    @commands.command(pass_context = True)
    async def helloworld(self,ctx):
        """This repeats hello world to the user"""

        #Your code will go here
        await self.bot.say("Bye bye World.")

    #this tag below, tells the framework it is a command. pass context is useful, you'll see it used throughout other cogs.
    @commands.command(pass_context = True)
    async def noticeme(self, ctx): #ctx is the passed context
    	"""This tells the user they have been noticed"""
    	author = ctx.message.author

    	await self.bot.say("Yes, senpai? What would you like to tell me?")

    	userresponse = await self.bot.wait_for_message(author = author)
    	#author check param in this is important. it waits for a response from the user who
    	#initiated the command.

    	await self.bot.say("Really... '{}' is all you had to say, {}? Pathetic.".format(userresponse.content, author.mention))

    @commands.command(pass_context=True)
    async def character(self,ctx):
        """Character options menu"""
        #make search to players json file. if not found, then ask for a registration.
        embed = discord.Embed(title = "Character Options Menu", description = "Use the numbers to make a choice.", colour =0xfd0000)
        embed.add_field(name='Options', value = "`1.` Get Character Sheet\n`2.` Change Avatar", inline = False)
        await self.bot.say()

    @commands.group(name="character", pass_context=True)
    async def rpg(self, ctx):
        """General RPG stuff."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @rpg.command(pass_context=True, no_pm = False)
    async def register(self,ctx):
        """Registers and Creates your RPG Character."""
        author = ctx.message.author
        await self.bot.say("Thanks for joining {}! Now, we are going to need some information...".format(author.mention))
        created = await self._createcharacter(ctx)

        if created is not None:
            await self.bot.say("Thank you! Your character Sheet will be dm'ed to you.")
            embed = discord.Embed(title= "{}'s Character".format(author.name), description="CharName" , color=0xff0000)
            embed.add_field(name="Stats", value="fromjson **Race:** but eally really **Level:** long might help", inline = False)
            embed.add_field(name='Health', value='fromjson', inline=True)
            embed.add_field(name='Mana', value='fromjson', inline=True)
            embed.add_field(name='Stamina', value='fromjson', inline=True)
            embed.add_field(name='Gold', value='fromjson', inline=True)
            embed.add_field(name='Character Bio', value = "fromjson long", inline = False)
            embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
            embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')
            await self.bot.say(" ", embed = embed)


    async def _createcharacter(self,ctx):
        completion = "yes"
        return completion


class Player:

	def __init__(self,bot, file_path):
		self.bot = bot
		self.players = dataIO.load_json(file_path)

	def _createplayer(self, charname, race, bio):
		newplayer = {}




def check_folders():
    if not os.path.exists("data/discordrpg"):
        print("Creating data/discordrpg folder...")
        os.makedirs("data/discordrpg")


def check_files():

    f = "data/discordrpg/settings.json"
    if not dataIO.is_valid_json(f):
        print("Creating default RPG's settings.json...")
        dataIO.save_json(f, {})

    f = "data/discordrpg/players.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty players.json...")
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(DiscordRPG(bot))