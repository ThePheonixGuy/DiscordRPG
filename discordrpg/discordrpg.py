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
        self.player = Player(bot, "data/discordrpg/players.json", "data/discordrpg/inventories.json")
        self.monster = Monster(bot, "data/discordrpg/monsters.json")
        self.map = Map(bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")
        self.settings_path = "data/discordrpg/settings.json"
        self.settings = dataIO.load_json(self.settings_path)  

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

        embed = discord.Embed(title = "Options for {}".format("fromjson charname"), description = "Use the numbers to make a choice.", colour =0xfd0000)
        embed.add_field(name='Options', value = "`1.` Get Character Sheet\n`2.` Change Avatar", inline = False)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')
        await self.bot.say("", embed = embed)

        response = await self.bot.wait_for_message(author = author)
        if '1' in response.content:
            # Return the character sheet
            await self.player.getCharacterSheet(author)
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

        player_exists = await self.player.check_player(author.id)
        if player_exists:
            await self.bot.say("You are already regsitered. You can use `{}rpg character` to do things.".format(ctx.prefix))
            return
        
        await self.bot.say("Thanks for joining {}! We are going to need some information...".format(author.mention))
        await self.player._createplayer(ctx)

    @rpg.command(pass_context=True, no_pm = False)
    async def monsters(self,ctx):
        """Lets you see all current monsters. *Testing command*"""
        await self.monster.get_all_monsters(ctx)


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
        if await self.check_player(userID):
            return deepcopy(self.playerRoster[userID])
        else:
            return None

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
        embed.add_field(name ='Warrior', value = 'The Melee Class. Specialising in close quarters combat, the warrior is lethal with a selecton of weapons.\n*Type `1` to select this class.*', inline = False)
        embed.add_field(name ='Rogue', value = 'Specialising in ranged combat and steath, the Rogue is Death from a Distance, with a touch of magic to make life easier\n*Type `2` to select this class.*', inline = False)
        embed.add_field(name ='Sorcerer', value = "Nothing above their power, the arcane arts allow the Sorcerers to bend any element to their will\n*Type `3` to select this class.*", inline = False)
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

        await self.bot.say("Please provide a short backstory about yourself, {}".format(charname))
        bio = await self.bot.wait_for_message(author = author)

        await self.bot.say("Great, welcome to {}, {}".format("*fromjson settings player.town*", charname))

        newplayer['User'] = author.name
        newplayer['HomeTownName'] = hometownname
        newplayer['HomeTownID'] = hometownid
        newplayer['CharName'] = charname
        newplayer['Race'] = race
        newplayer['Level'] = 1
        newplayer['Gold'] = 100
        newplayer['CurrLocX'] = 0
        newplayer['CurrLocY'] = 0
        newplayer['Bio'] = bio
        if 'W' in race:
            newplayer['BaseStats'] = {'HP': 50, 'Mana': 10, 'Stamina': 30}
        elif 'R' in race:
            newplayer['BaseStats'] = {'HP': 40, 'Mana': 15, 'Stamina': 20}
        elif 'S' in race:
            newplayer['BaseStats'] = {'HP': 35, 'Mana': 30, 'Stamina': 15}
        else:
            await self.bot.say("Sorry... there seems to be an issue with your class. Please try again.")
            return
        

        if await self.check_player(author.id):
            self.playerRoster[author.id] = newplayers
        else:
            self.playerRoster[author.id] = {}
            self.playerRoster[author.id] = newplayer

        has_invent = await self.check_inventory(author.id)
        if not has_invent:
            self.playerInventories[author.id] = {}

        await self.getCharacterSheet(author)

        self.saveplayers()
        self.saveinventories()

        return completion

    async def getCharacterSheet(self, user):
        author = user

        char_profile = await self.get_player_records(user.id)
        print(char_profile)

        embed = discord.Embed(title= "{}".format(char_profile['CharName']), description="will need to be a mapProvider, from passing currloc variables" , color=0xff0000) #TODO will require a location provider. Part of map Class.
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
        self.saveplayers()

    def saveplayers(self):
        f = "data/discordrpg/players.json"
        dataIO.save_json(f, self.playerRoster)

    def saveinventories(self):
        f = "data/discordrpg/inventories.json"
        dataIO.save_json(f, self.playerInventories)


class  Monster:
    def __init__(self,bot,monster_path):
        self.bot = bot
        self.npcmonsters = dataIO.load_json(monster_path)

    async def get_all_monsters(self, ctx):
        await self.bot.say(self.npcmonsters)

    async def monster_info(self,bot,monsterID):
        pass

class  Map:
    def __init__(self,bot, tile_path, map_path):
        self.bot = bot
        self.fieldmap = dataIO.load_json(map_path)
        self.tiletypes = dataIO.load_json(tile_path)

    async def map_generator(self, user, loc_x, loc_y):
        # Takes a co-ordinat x and y. Needs to check if the x value exists in the dict.
        # the dict is layed out as follows:
        # row to coloumn basis. One x co-ord, with every Discovered Y co-ord as a value of that x co-ord key.
        # thus a call to a specific tile location will look like:
        # self.fieldmap[x_co_ord][y_co_ord]

        # You need to check the passed location co-rds to see if theyre in the dict. Use try except blocks, i will do the x co-ord for you, or use an "if key not in dict" structure.
        # If it exists, return.
        # If not, add it to the dict. 
        # decide a random tile to occur from titletypes.json (will add the import later) and add it to the dict at that location  such that self.fieldmap[x][y] = {tile details} 
        # ^^this needs to be a function of distance from home town and user lvl, compared to the tile difficulty. remember monster spawning will be automated off this so you dont have to account for it.
        # Save the decided tile to the dict. Save the dict to a file. Thus the thing will continually generate as new distances are explored. 
        
        try:
            if loc_x  in self.fieldmap:
                if loc_y in self.fieldmap[loc_x]:
                    return
                else:
                    # code to select a tile goes here
                    return
            else:
                self.fieldmap[loc_x] = {}
                self.map_generator(user, loc_x, loc_y)
                return
        except:
            await self.bot.say("This error must not appear when the game is published to mainserver.")

    def savemap(self):
        f = "data/discordrpg/map.json"
        dataIO.save_json(f, self.fieldmap)



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

