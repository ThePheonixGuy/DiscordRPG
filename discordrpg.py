import discord
from discord.ext import commands

class DiscordRPG:
    """The Discord RPG. I mean, *Thee Discord RPG*"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context = True)
    async def helloworld(self,ctx):
        """This repeats hello world to the user"""

        #Your code will go here
        await self.bot.say("Hello World!")

def setup(bot):
    bot.add_cog(DiscordRPG(bot))