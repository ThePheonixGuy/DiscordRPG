#Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
from __main__ import send_cmd_help
#Others
import os
from copy import deepcopy, copy
import datetime
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
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.map = Map(bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")
        self.settings_path = "data/discordrpg/settings.json"
        self.settings = dataIO.load_json(self.settings_path) 

    @commands.group(name='rpgset', pass_context = True)
    async def rpgset(self,ctx):
        """Settings for the RPG on this server"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @rpgset.command(pass_context=True) 
    async def townname(self,ctx, *, name):
        """Allows you to set a name for this server's Home Town"""
        author = ctx.message.author
        sid = ctx.message.server
        townExists = await self.town.check_town(sid)
        if not townExists:
            await self.bot.say("Oops. Your town is still in piles of rubble. Please ask an admin or moderator of this channel to get your town started with `{}rpg signup`".format(ctx.prefix))
            return
        await self.town.set_town_name(ctx,name)

    @rpgset.command(pass_context=True) 
    async def townavatar(self,ctx, *, name):
        """Allows you to set a name for this server's Home Town"""
        author = ctx.message.author
        sid = ctx.message.server
        townExists = await self.town.check_town(sid)
        if not townExists:
            await self.bot.say("Oops. Your town is still in piles of rubble. Please ask an admin or moderator of this channel to get your town started with `{}rpg signup`".format(ctx.prefix))
            return

        await self.bot.say("Please provide me with a url only, to use as an image for your character sheet.")
        #TODOLATER allow attachment grabbing. its possible, but im lazy
        
        avatarurl = await self.bot.wait_for_message(author = author)

        if validators.url(avatarurl.content):
            await self.town.set_town_avatar(sid, avatarurl.content)
            #TODO do the magic of sending to self.player.setAvatar(author.id,url)
            #TODO set up avatar saving
        else:
            await self.bot.say("Not a valid URL. Try again.")

    @commands.group(name="rpg", pass_context=True)
    async def rpg(self, ctx):
        """General RPG stuff."""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @rpg.command(pass_context=True)
    @checks.admin_or_permissions(manage_server=True)
    async def signup(self,ctx):
        """Allows an admin or moderator to signup this server into the RPG"""
        author = ctx.message.author
        await self.bot.say("Hey there, {}. Thanks for signing up your server. Please provide a name for your new town!".format(author.mention))
        response = await self.bot.wait_for_message(author = author)
        townName = response.content
        await self.bot.say("{}? Alright, if you say so. Gimme a second to get things set up, I'll get back to you.".format(townName))

        await self.town.create_town(ctx, townName)

    @rpg.command(pass_context=True)
    async def character(self,ctx):
        """Character options menu"""
        author = ctx.message.author
        sid = ctx.message.server
        current_player = {}
        player_exists = await self.player.check_player(author.id)
        if player_exists:
            current_player = await self.player.get_player_records(author.id)
        else:
            await self.bot.say("You have not yet joined the RPG. Please signup using `{}rpg register`".format(ctx.prefix))
            return

        embed = discord.Embed(title = "Options for {}".format("fromjson charname"), description = "Use the numbers to make a choice.", colour =0xfd0000)
        embed.add_field(name='Options', value = "`1.` Get Character Sheet\n`2.` Change Avatar\n`3.` Change Bio", inline = False)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')
        await self.bot.say("", embed = embed)

        response = await self.bot.wait_for_message(author = author)
        if '1' in response.content:
            # Return the character sheet
            await self.player.getCharacterSheet(author)
        elif '2' in response.content:
            # Grab url, validate it and save to the players profile in players.json
            await self.bot.say("Please provide me with a url only, to use as an image for your character sheet.")
            #TODOLATER allow attachment grabbing. its possible, but im lazy
            avatarurl = await self.bot.wait_for_message(author = author)

            if validators.url(avatarurl.content):
                await self.player.setProfileAvatar(author.id, avatarurl.content)
            else:
                await self.bot.say("Not a valid URL. Try again.")
        elif '3' in response.content:
            self.player.setBio(ctx, author.id)
        else:
            await self.bot.say("Invalid response. Please try again.")

    @rpg.command(pass_context=True, no_pm = False)
    async def register(self,ctx):
        """Registers and Creates your RPG Character."""
        author = ctx.message.author
        sid = ctx.message.server.id

        townExists = await self.town.check_town(sid)
        if not townExists:
            await self.bot.say("Oops. Your town is still in piles of rubble. Please ask an admin or moderator of this channel to get your town started with `{}rpg signup`".format(ctx.prefix))
            return

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

    def __init__(self, bot, player_path, invent_path):
        self.bot = bot
        self.playerRoster = dataIO.load_json(player_path)
        self.playerInventories = dataIO.load_json(invent_path)
        self.monster = Monster(bot, "data/discordrpg/monsters.json")
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.map = Map(bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")

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
        town_record = await self.town.get_town_records(hometownid)
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

        await self.bot.say("Great, welcome to {}, {}".format(town_record['Town_Name'], charname))

        newplayer['User'] = author.name
        newplayer['HomeTownID'] = hometownid
        newplayer['CharName'] = charname
        newplayer['Race'] = race
        newplayer['Level'] = 1
        newplayer['Gold'] = 100
        newplayer['CurrLocX'] = 0
        newplayer['CurrLocY'] = 0
        newplayer['Bio'] = bio.content
        if 'W' in race:
            newplayer['BaseStats'] = {'HP': 50, 'Mana': 10, 'Stamina': 30}
            newplayer['Avatar'] = "https://s-media-cache-ak0.pinimg.com/736x/77/02/6b/77026b08f33fb0b4a35434553c4fccc8.jpg"
        elif 'R' in race:
            newplayer['BaseStats'] = {'HP': 40, 'Mana': 15, 'Stamina': 20}
            newplayer['Avatar'] = "https://s-media-cache-ak0.pinimg.com/736x/8c/2b/da/8c2bdafd9c5c5b2ec38b81741aa5e879.jpg"
        elif 'S' in race:
            newplayer['BaseStats'] = {'HP': 35, 'Mana': 30, 'Stamina': 15}
            newplayer['Avatar'] = "https://s-media-cache-ak0.pinimg.com/originals/c3/e5/25/c3e525a719eaa6ae0df486baa672391c.jpg"
        else:
            await self.bot.say("Sorry... there seems to be an issue with your class. Please try again.")
            return
        
        if await self.check_player(author.id):
            self.playerRoster[author.id] = newplayer
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
        townID = char_profile['HomeTownID']
        char_town = await self.town.get_town_records(townID)
        current_loc = "***req loc_provider from class Map***"
        embed = discord.Embed(title= "{}".format(char_profile['CharName']), description=current_loc , color=0xff0000) #TODO will require a location provider. Part of map Class.
        embed.add_field(name='Bio', value = "Hailing from **{}**, *{}* is a {}. In his own words, '*{}*' ".format(char_town['Town_Name'],char_profile['CharName'], char_profile['Race'], char_profile['Bio']), inline = False) #TODO replace with vals
        embed.add_field(name='Race', value=char_profile['Race'], inline=True)
        embed.add_field(name='Level', value=char_profile['Level'], inline=True)
        embed.add_field(name='Health', value=char_profile['BaseStats']['HP'], inline=True)
        embed.add_field(name='Mana', value=char_profile['BaseStats']['Mana'], inline=True)
        embed.add_field(name='Stamina', value=char_profile['BaseStats']['Stamina'], inline=True)
        embed.add_field(name='Gold', value=char_profile['Gold'], inline=True)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = char_profile['Avatar'])

        await self.bot.say(" ", embed = embed)

    async def setProfileAvatar(self, userID, url):
        #TODO check it for keyerror. use check method.
        if check_player(userID): 
            self.playerRoster[userID]['Avatar'] = url
            self.saveplayers()
            await self.bot.say("Done!")
        else:
            await self.bot.say("You might not be registered with the RPG. Please try registering first.")

    async def setBio(self, ctx, userID):
        author = ctx.message.author
        current_player = self.get_player_records(userID)
        if current_player == None:
            await self.bot.say("No current records for you, {}. Please use `{}rpg register to enter the game".format(author.mention, ctx.prefix))
            return

        await self.bot.say("Please provide me with a new Bio.")

        new_bio = await self.bot.wait_for_message(author = author)

        current_player['Bio'] = new_bio.content

        self.playerRoster[userID] = current_player

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

class Town:

    def __init__(self,bot,towns_path):
        self.bot = bot
        self.known_towns = dataIO.load_json(towns_path)

    async def check_town(self, townID):
        try:
            if townID in self.known_towns:
                return True
            else:
                return False
        except:
            return False

    async def get_town_records(self, townID):
        if await self.check_town(townID):
            return deepcopy(self.known_towns[townID])
        else:
            return None

    async def get_town_sheet(self, townID):

        town_record = await self.get_town_records(townID)

        embed = discord.Embed(title= "{}".format(town_record['Town_Name']), description="The humble {} was rebuilt from the rubble at {}".format("fromjson","fromjson") , color=0xff0000) #TODO will require a location provider. Part of map Class.
        embed.add_field(name='Bio', value = "fromjson Hailing from *{}*, *{}* is a {}. {}".format("player.hometown","CharName", "player.race", "player.bio"), inline = False) #TODO replace with vals
        embed.add_field(name='Race', value='fromjson', inline=True)
        embed.add_field(name='Level', value='fromjson', inline=True)
        embed.add_field(name='Health', value='fromjson', inline=True)
        embed.add_field(name='Mana', value='fromjson', inline=True)
        embed.add_field(name='Stamina', value='fromjson', inline=True)
        embed.add_field(name='Gold', value='fromjson', inline=True)
        embed.set_author(name='{}'.format(author.name), icon_url = '{}'.format(author.avatar_url))
        embed.set_thumbnail(url = 'https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')

        await self.bot.say(" ", embed = embed)

    

    async def create_town(self, ctx, townName):
        newTown = {}
        sid = ctx.message.server.id
        if sid in self.known_towns:
            await self.bot.say("This guild is already signed up. If you would like to change something, please try {}rpgset".format(ctx.prefix))
        else:
            newTown['Town_Name'] = townName
            newTown['Created_At'] = str(datetime.datetime.now())
            newTown['Level'] = 1
            newTown['Avatar'] = "http://orig09.deviantart.net/2440/f/2013/249/7/a/fantasy_rpg_town_by_e_mendoza-d6lb9td.jpg"
            newTown['Buildings'] = {}
            newTown['Loc_X'] = 1 #TODO be replaced by the map provider.
            newTown['Loc_Y'] = 1 #TODO be replaced by the map provider.
            self.known_towns[sid] = newTown


        await self.bot.say("Thank you for signing your guild up! Details for this town are to follow.") #TODO town embed card.

        self.savetowns()

    async def set_town_avatar(self, townID, url):
        if check_town(townID):
            self.known_towns[townID]['Avatar'] = url
            await self.bot.say("Done!")
        else:
            await self.bot.say("Your town might not be signed up with the RPG. Please try signup first.")
        self.savetowns()


    async def set_town_name(self,ctx, name):
        sid = ctx.message.server.id
        #TODO make a hollow container to a method of the town class when town customization becomes a thing.
        if sid not in self.known_towns:
            await self.bot.say("This town has never actually been created before, but I'll go ahead and establish your great wonder with the name {}".format(name))
            await self.create_town(ctx, name)
            return

        self.known_towns[sid]['Town_Name'] = name

        await self.bot.say("The Town Name for this guild is now {}".format(self.known_towns[sid]['Town_Name']))

        self.savetowns()

    def savetowns(self):
        f = "data/discordrpg/towns.json"
        dataIO.save_json(f, self.known_towns)


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

    f = "data/discordrpg/map.json"
    if not dataIO.is_valid_json(f):
        print("Creating empty towns.json...")
        dataIO.save_json(f, {})

    f = "data/discordrpg/tiletypes.json"
    if not dataIO.is_valid_json(f):
        raise RuntimeError("Data file tiletypes.json is either missing from the data folder or corrupt. Please redownload it and place it in your bot's data/discordrpg/ folder")

    f = "data/discordrpg/monsters.json"
    if not dataIO.is_valid_json(f):
        raise RuntimeError("Data file monsters.json is either missing from the data folder or corrupt. Please redownload it and place it in your bot's data/discordrpg/ folder")



def setup(bot):
    check_folders()
    check_files()
    if validatorsAvail:
        bot.add_cog(DiscordRPG(bot))
    else:
        raise RuntimeError("You need to run pip3 install validators")

