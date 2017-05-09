#Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
from __main__ import send_cmd_help
#Others
import os
from copy import deepcopy, copy
try:
    import validators
    validatorsAvail = True
except:
    validatorsAvail = False


class DiscordRPG:
    """The Discord RPG. I mean, *Thee Discord RPG*"""

    def __init__(self, bot):
        self.bot = bot
        self.player = Player(bot, "data/discordrpg/players.json", "data/discordrpg/inventories.json") #note that the players refered to from here on out will be a collective object of the type Player that handles the player function.
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

    

    @commands.group(name="rpg", pass_context=True)
    async def rpg(self, ctx):
        """General RPG stuff."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @rpg.command(pass_context=True)
    async def character(self,ctx):
        """Character options menu"""
        author = ctx.message.author
        current_player = {}
        player_exists = await self.player.check_player(author.id)
        if player_exists:
            current_player = await self.player.get_player_records(author.id)
        else:
            await self.bot.say("You have not yet joined the RPG. Please signup using `{}rpg register`".format(ctx.prefix))
            return

        print(current_player)

        embed = discord.Embed(title = "Options for {}".format("fromjson charname"), description = "Use the numbers to make a choice.", colour =0xfd0000)
        embed.add_field(name='Options', value = "`1.` Get Character Sheet\n`2.` Change Avatar", inline = False)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')
        await self.bot.say("", embed = embed)

        response = await self.bot.wait_for_message(author = author)
        if '1' in response.content:
            # Return the character sheet
            embed = await self.player.getCharacterSheet(author)
            await self.bot.say("  ", embed = embed)
        elif '2' in response.content:
            # Grab url, validate it and save to the players profile in players.json
            await self.bot.say("Please provide me with a url only, to use as an image for your character sheet.") #TODO extract and validate, maybe see if attachements can be pulled.
            avatarurl = await self.bot.wait_for_message(author = author)

            if validators.url(avatarurl.content):
                await self.bot.say("Seeting your image to the following image: {}".format(avatarurl.content))
                # do the magic of sending to self.player.setAvatar(author.id,url)
            else:
                await self.bot.say("Not a valid URL. Try again.")
        else:
            await self.bot.say("Invalid response. Please try again.")

    @rpg.command(pass_context=True, no_pm = False)
    async def register(self,ctx):
        """Registers and Creates your RPG Character."""
        author = ctx.message.author
        await self.bot.say("Thanks for joining {}! Now, we are going to need some information...".format(author.mention))
        await self.player._createplayer(ctx)


        

        


class Player:

    def __init__(self,bot, player_path, invent_path):
        self.bot = bot
        self.playerRoster = dataIO.load_json(player_path)
        self.playerInventories = dataIO.load_json(invent_path)

    async def check_player(self, userID):
        try:
            if userID in self.playerRoster:
                return True
            else:
                return False
        except:
            return False

    async def check_inventory(self, userID):
        try:
            if userID in self.playerInventories:
                return True
            else:
                return False
        except:
            return False

    async def get_player_records(self, userID):
        if self.check_player(userID):
            return deepcopy(self.playerRoster[userID])
        else:
            return False

    async def get_player_invent(self, userID):
        if self.check_player(userID):
            return deepcopy(self.playerInventories[userID])
        else:
            return False


    async def _createplayer(self, ctx):
        #order = charname, race, hometown, bio. stats to be inferred from race.
        author = ctx.message.author
        newplayer = {}
        race = ""
        charname = ""
        bio = ""
        hometownid = ctx.message.server.id
        hometownname = ctx.message.server.name
        completion = "yes" # TODO. retrieve requisite info. add it to dictionary and pass to _createplayer method.

        embed = discord.Embed(title = "Pick a Class".format("fromjson charname"), description = "Let's start off by finding what class your character is.", colour =0xff0000)
        embed.add_field(name='Class', value = "Choose from the following Classes:", inline = False)
        embed.add_field(name ='Warrior', value = 'The Melee Class. Specialising in close quarters combat, the warrior is lethal with a selecton of weapons.\nType `1` to select this class.', inline = False)
        embed.add_field(name ='Rogue', value = 'Specialising in ranged combat and steath, the Rogue is Death from a Distance, with a touch of magic to make life easier\nType `2` to select this class.', inline = False)
        embed.add_field(name ='Sorcerer', value = "Nothing above their power, the arcane arts allow the Sorcerers to bend any element to their will\nType `3` to select this class.", inline = False)
        embed.set_thumbnail(url = 'http://unrealitymag.com/wp-content/uploads/2011/11/torchlight1.jpg')
        await self.bot.say(' ', embed = embed)
        raceChoice = await self.bot.wait_for_message(author = author)
        if '1' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Warrior's name?")
            race = "Warrior"
        elif '2' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Rogue's name?")
            race = "Rogue"
        elif '3' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Sorcerers's name?")
            race = "Sorcerer"

        charname = await self.bot.wait_for_message(author = author)
        charname = charname.content 
        await self.bot.say("Great, welcome to {}, {}".format("*player.town*", charname))

        newplayer['User'] = author.name
        newplayer['HomeTownName'] = hometownname
        newplayer['HomeTownID'] = hometownid
        newplayer['CharName'] = charname
        newplayer['Race'] = race
        newplayer['Level'] = 1
        newplayer['BaseStats'] = {'HP': 50, 'Mana': 10, 'Stamina': 30}
        newplayer['Gold'] = 100
        newplayer['CurrLocX'] = 0
        newplayer['CurrLocY'] = 0

        if await self.check_player(author.id):
            self.playerRoster[author.id] = newplayer
        else:
            self.playerRoster[author.id] = {}
            self.playerRoster[author.id] = newplayer

        has_invent = await self.check_inventory(author.id)
        if not has_invent:
            self.playerInventories[author.id] = {}


        self.saveplayers()
        self.saveinventories()

        return completion

    async def getCharacterSheet(self, user):
        author = user

        #TODO DEEPCOPY from playerRoster of the specific user.

        embed = discord.Embed(title= "CharName", description="Currently (location goes here)" , color=0xff0000) #TODO will require a location provider. Part of map Class.
        embed.add_field(name='Character Bio', value = "fromjson Hailing from *{}*, *{}* is a {}. {}".format("player.hometown","CharName", "player.race", "player.bio"), inline = False) #TODO replace with vals
        embed.add_field(name='Race', value='fromjson', inline=True)
        embed.add_field(name='Level', value='fromjson', inline=True)
        embed.add_field(name='Health', value='fromjson', inline=True)
        embed.add_field(name='Mana', value='fromjson', inline=True)
        embed.add_field(name='Stamina', value='fromjson', inline=True)
        embed.add_field(name='Gold', value='fromjson', inline=True)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')

        await self.bot.say(" ", embed = embed)

    async def setProfileAvatar(self, userID, url):
        #check it for keyerror. try catch is easier. but the check for a registered profile needs to come before this.
        self.playerRoster[userID]['avatar'] = url

    def saveplayers(self):
        f = "data/discordrpg/players.json"
        dataIO.save_json(f, self.playerRoster)

    def saveinventories(self):
        f = "data/discordrpg/inventories.json"
        dataIO.save_json(f, self.playerInventories)




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

    f = "data/discordrpg/inventories.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty inventories.json...")
        dataIO.save_json(f, {})

    f = "data/discordrpg/towns.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty towns.json...")
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    if validatorsAvail:
        bot.add_cog(DiscordRPG(bot))
    else:
        raise RuntimeError("You need to run pip3 install validators")
    