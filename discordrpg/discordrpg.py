#Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
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