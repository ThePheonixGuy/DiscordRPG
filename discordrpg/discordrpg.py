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
import math
try:
    import validators
    validatorsAvail = True
except:
    validatorsAvail = False


class DiscordRPG:
    """The Discord RPG. I mean, *Thee Discord RPG*"""

    def __init__(self, bot):
        self.bot = bot
        self.playerPath = "data/discordrpg/players.json"
        self.inventoryPath = "data/discordrpg/inventories.json"
        self.monsterPath = "data/discordrpg/monsters.json"
        self.townPath = "data/discordrpg/towns.json"
        self.tilePath = "data/discordrpg/tiletypes.json"
        self.mapPath = "data/discordrpg/map.json"
        self.player = Player(bot, self.playerPath, self.inventoryPath)
        self.monster = Monster(bot, self.monsterPath)
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.map = Map(self.player, bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")
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
        await self.town.set_town_name(ctx,name)

    @rpgset.command(pass_context=True) 
    async def townavatar(self,ctx, *, avatarurl):
        """Allows you to set a new Avatar picture for this server's Home Town"""
        #TODOLATER allow attachment grabbing. its possible, but im lazy
        author = ctx.message.author
        sid = ctx.message.server.id
        if validators.url(avatarurl):
            await self.town.set_town_avatar(sid, avatarurl)
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
        await self.town.create_town(ctx)

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
            await self.bot.say("You have not yet joined the RPG. Please register using `{}rpg register`".format(ctx.prefix))
            return

        embed = discord.Embed(title = "Options for {}".format(current_player['CharName']), description = "Use the numbers to make a choice.", colour =0xfd0000)
        embed.add_field(name='Options', value = "`1.` Get Character Sheet\n`2.` Change Avatar\n`3.` Change Bio\n`4.` View Home Town", inline = False)
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
            await self.player.setBio(ctx, author.id)
        elif '4' in response.content:
            self.town.savetowns()
            await self.town.reload_town_records()
            await self.town.get_town_sheet(current_player['HomeTownID'])
             #TODO


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
    async def viewtown(self,ctx):
        """View the details of the guild's town you are currently in"""
        sid = ctx.message.server.id
        await self.town.get_town_sheet(sid)
        #TODO make a part of Character, Select based on userID, show hometown.

    @rpg.command(pass_context=True, no_pm = False)
    async def viewmonster(self,ctx, *, monsterID):
        """Testing Stub. Please do not use."""
        await self.monster.getMonsterSheet(monsterID)

    @rpg.command(pass_context=True, no_pm = False)
    async def viewtile(self,ctx, locX: int, locY: int):
        """Testing sub. Please do not use."""
        user = ctx.message.author
        await self.map.map_provider(user, locX , locY)

    @rpg.command(pass_context=True, no_pm = False)
    async def viewplayer(self, ctx, user: discord.Member):
        """Allows you to see the character sheet of another player in the game."""

        hasProfile = await self.player.check_player(user.id)

        if hasProfile:
            await self.player.getCharacterSheet(user)
        else:
            await self.bot.say("That player does not yet exist. Perhaps consider asking them to join using `{}rpg register`?".format(ctx.prefix))

    @rpg.command(pass_context=True, no_pm = False)
    async def play(self,ctx):
        """Runs a session of DiscordRPG"""
        #from this point onwards, CTX cannot be used for resources like server ID's. 
        # Needs to be pulled from the existing resources, in the dicts.
        await self.bot.say("This is still under construction. Any bugs are please to be reported using `;;contact` followed by the error given. Thanks for testing out DiscordRPG!")
        userDO = ctx.message.author
        await self.reload_town_records()
        current_player = await self.player.get_player_records(userDO.id)
        player_town = await self.town.get_town_records(current_player['HomeTownID'])
        print(player_town)
        if 'Never' in current_player['Last_Played']:
            await self.bot.say("Thank you for signing up. Welcome to your next grand adventure")
            await self.first_adventure_town(ctx, current_player, player_town)


    async def first_adventure_town(self, ctx, current_player, player_town):
        #TODONOW create embed intro story.
        #TODO description, and options fromjson
        user = ctx.message.author
        header = ["Awakening", "First, nothing. Then, just white pain. You wake up on the cold, hard stones. Dazed and Confused, you wonder how it is you ended up here. Opening your eyes to the eye-shattering sunlight, you sit yourself up and take a look around. Doesn't look like much, a simple town you think to yourself. You stand up and decide to have a look around."]

        option = ["Take a look around."]

        em1 = await self.embed_builder(ctx, current_player, header, option)

        await self.bot.say("", embed = em1)

        valid = False
        while not valid:
            response = await self.bot.wait_for_message(timeout = 600, author = user)
            if response is None:
                valid = True
                await self.logout(ctx)
                return
            if await self.exit_check(response.content):
                await self.bot.say("Are you sure you wish to end the session here? You will return to this same adventure. Say `yes` to confirm")

                response = await self.bot.wait_for_message(timeout = 600, author = user)

                if response is None:
                    valid = True
                    await self.logout(ctx)
                    return
                elif 'y' in response.content.lower():
                    valid = True
                    await self.bot.say("Logged you out.")
                    return
            elif '1' in response.content:
                #TODONOW continue gameplay here
                await self.bot.say("Yuu wanna hava looksee ye? Well, I 'avnt gotten that far yet!")
                return
            else:
                await self.bot.say("No correct response detected. Please try again.")
                continue



    async def reload_town_records(self):
        self.town = Town(self.bot, "data/discordrpg/towns.json")

    async def exit_check(self, text):
        text = text.lower()
        if 'exit' in text:
            return True
        else:
            return False

    async def logout(self, ctx):
        await self.bot.say("You took too long, so I logged you out.")

    async def embed_builder(self,ctx, user, header, option):
        value = ""
        count = 1
        for item in option:
            value = "`{}.`{}\n".format(count,item)
            count +=1
        em = discord.Embed(title = "{}".format(header[0]), description = "{}".format(header[1]), colour =0xfd0000)
        em.add_field(name='Use the numbers to Indicate your Choice.', value = value, inline = False)
        em.set_author(name='{}'.format(user["CharName"]))
        em.set_thumbnail(url = user['Avatar'])
        em.set_footer(text = "Say Exit to logout from this session.")
        return em

    async def generic_adventure(self, ctx, current_player, player_town):
        option = []
        em1 = discord.Embed(title = "{}".format(option[0]), description = "{}".format(option[1]), colour =0xfd0000)
        em1.add_field(name='Use the numbers to Indicate your Choice.', value = "`1.`{}\n`2.`{}\n`3.`{}\n`4.`{}\n".format(option[2],option[3],option[4],option[5]), inline = False)
        await self.bot.say("", embed = embed1)



class Player:

    def __init__(self, bot, player_path, invent_path):
        self.bot = bot
        self.playerRoster = dataIO.load_json(player_path)
        self.playerInventories = dataIO.load_json(invent_path)
        self.monster = Monster(bot, "data/discordrpg/monsters.json")
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.map = Map(self, bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")

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
        await self.town.reload_town_records()
        town_record = await self.town.get_town_records(hometownid)
        print("New player is registering in {} from server {}".format(town_record['Town_Name'], ctx.message.server.name))
        completion = "yes" # TODO. retrieve requisite info. add it to dictionary and pass to _createplayer method.

        embed = discord.Embed(title = "Pick a Class", description = "Let's start off by finding what class your character is.", colour =0xff0000)
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
        #TODO add session counter for tut purposes.
        newplayer['User'] = author.name
        newplayer['HomeTownID'] = hometownid
        newplayer['CharName'] = charname
        newplayer['Race'] = race
        newplayer['Level'] = 1
        newplayer['Gold'] = 100
        newplayer['Location'] = town_record['Location']
        newplayer['Bio'] = bio.content
        newplayer['Last_Played'] = 'Never'
        newplayer['Sessions'] = 0
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
        print("New player registered in {} from server {}. Details: \n{}".format(town_record['Town_Name'], ctx.message.server.name, newplayer))
        self.saveplayers()
        self.saveinventories()

        return completion

    async def getCharacterSheet(self, user):
        author = user

        char_profile = await self.get_player_records(user.id)
        townID = char_profile['HomeTownID']
        char_town = await self.town.get_town_records(townID)
        current_loc = await self.map.get_distance_from_home(user, char_profile['Location'])

        if current_loc == 0:
            current_loc = "Currently in {}".format(char_town['Town_Name'])#Change to tile provider when complete.
        else:
            current_loc = "{} MU from {}".format(current_loc, char_town['Town_Name'])
        embed = discord.Embed(title= "{}".format(char_profile['CharName']), description=current_loc, color=0xff0000) #TODO will require a location provider. Part of map Class.
        embed.add_field(name='Bio', value = "Hailing from **{}**, *{}* is a {}. In his own words, '*{}*' ".format(char_town['Town_Name'],char_profile['CharName'], char_profile['Race'], char_profile['Bio']), inline = False)
        embed.add_field(name='Last Played', value=char_profile['Last_Played'], inline=True)
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
        if await self.check_player(userID): 
            self.playerRoster[userID]['Avatar'] = url
            self.saveplayers()
            await self.bot.say("Done!")
        else:
            await self.bot.say("You might not be registered with the RPG. Please try registering first.")

    async def setBio(self, ctx, userID):
        author = ctx.message.author
        current_player = await self.get_player_records(userID)
        if current_player == None:
            await self.bot.say("No current records for you, {}. Please use `{}rpg register to enter the game".format(author.mention, ctx.prefix))
            return

        await self.bot.say("Please provide me with a new Bio.")

        new_bio = await self.bot.wait_for_message(author = author)
        current_player['Bio'] = new_bio.content
        self.playerRoster[userID] = current_player
        await self.bot.say("Done!")
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

    async def getMonsterSheet(self, monsterID):
        await self.bot.say(monsterID)

        if monsterID in self.npcmonsters:
            #this method stub is actually a part check_monster method.
            pass

class  Map:
    def __init__(self, player, bot, tile_path, map_path):
        self.bot = bot
        self.fieldmap = dataIO.load_json(map_path)
        self.tiletypes = dataIO.load_json(tile_path)
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.player = player

    async def map_generator(self, user, location):
        #TODO i want this so rigoursly checked, either implicitly or explicitly in the other function calls that this try catch is not necessary.
        pass
        #TODOSOON add different tile types as -function- of tile difficulty and distance. make a number scale.    

    async def map_provider(self, user, locX, locY):
        # TODOSOON possibly move dict higher up the call stack?
        # ^^ Only possible once map generation is ctually complete
        location = {'X':locX, 'Y': locY}
        try:
            tileRecord = await self.get_tile_records(location)
            if tileRecord is None:
                await self.map_generator(user, location)
                tileRecord = await self.get_tile_records(location)
            print(tileRecord)
        except Exception as e:
            print("Exception: {}".format(e))

    async def get_distance_from_home(self,user,location):
        """def for returning the distance from home, because of how impotrant this is"""
        locX = location['X']
        locY = location['Y']
        player_record = await self.player.get_player_records(user.id)
        homeTownID = player_record["HomeTownID"]
        homeTown = await self.town.get_town_records(homeTownID)
        print(homeTown)
        townLocation = homeTown['Location']
        townX = townLocation['X']
        townY = townLocation['Y']

        distX = locX - townX
        distY = locY - townY
        pDistance = math.hypot(distX, distY)
        pDistance  = round(pDistance)
        return (pDistance)

    async def get_surrounds(self, user):
        # gets users current location.
        # checks self.fieldmap for all nine tiles around it, be 
        # x;y, x;y+, x;y-, x+;y, x+;y+, x+;y-, x-:y, x-;y+, x-;y-
        # ^^ nine tiles. pass and call for each option to the map provider.   
        pass #TODOSOON for now.
    
    async def check_tile(self,location):
        """ takes the give location and checks if its in fieldmap"""
        try:
            if location['X'] in self.fieldmap:
                if location['Y'] in self.fieldmap[location['X']]:
                    return True
                else:
                    return False #TODO check that forced generation is ensured higher up the call stack.
            else:
                return False
        except:
            return False

    async def get_tile_records(self, location):
        tileExists = await self.check_tile(location)

        if tileExists:
            return deepcopy(self.fieldmap[location['X']][location['Y']])
        else:
            # Calls mapp provider to create the tile, then attempts to return it.
            # ^^ Good idea but no. Implicitly check for this higher up the stack so that the user object doesnt need to be passed so far.
            return None


    def savemap(self):
        f = "data/discordrpg/map.json"
        dataIO.save_json(f, self.fieldmap)

class Town:

    def __init__(self,bot,towns_path):
        self.bot = bot
        self.known_towns = dataIO.load_json(towns_path)

    async def reload_town_records(self):
        self.known_towns = dataIO.load_json("data/discordrpg/towns.json")

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

        if town_record is None:
            await self.bot.say("Hmmm... It appears the town you are looking for is still in Rubble unfortunately. Torn down by a war long since forgotten.")
            return

        embed = discord.Embed(title= "{}".format(town_record['Town_Name']), description="The humble {} was rebuilt from the rubble On {}".format(town_record['Town_Name'],town_record['Created_At']) , color=0xff0000) #TODO will require a location provider. Part of map Class.
        embed.add_field(name='Location', value=town_record['Location'], inline=True)
        embed.add_field(name='Level', value=town_record['Level'], inline=True)
        embed.add_field(name='Current Buildings', value=town_record['Buildings'], inline=False)
        #TODONOW list iterator for display purposes.
        embed.set_thumbnail(url = town_record['Avatar'])

        await self.bot.say(" ", embed = embed)

    async def create_town(self, ctx):
        newTown = {}
        sid = ctx.message.server.id
        author = ctx.message.author

        if await self.check_town(sid):
            await self.bot.say("This guild is already signed up. If you would like to change something, Please try `{}rpgset`".format(ctx.prefix))
            return
        else:
            await self.bot.say("Hey there, {}. Thanks for signing up your server. Please provide a name for your new town! This will be the name of the whole server's town.".format(author.mention))
            response = await self.bot.wait_for_message(author = author) #TODO timeout
            townName = response.content
            await self.bot.say("{}? Alright, if you say so. Gimme a second to get things set up, I'll get back to you.".format(townName))
            newTown['Town_Name'] = townName
            newTown['Created_At'] = datetime.datetime.ctime(datetime.datetime.now())
            newTown['Level'] = 1
            newTown['Avatar'] = "http://orig09.deviantart.net/2440/f/2013/249/7/a/fantasy_rpg_town_by_e_mendoza-d6lb9td.jpg"
            newTown['Buildings'] = {}
            newTown['Location'] = {'X':1, 'Y':1} #TODO change to map provider.
            self.known_towns[sid] = newTown

        #TODO add town bio. Would be nice.
        #TODO Basic buildings tavern and Town Builder.
        await self.bot.say("Thank you for signing your guild up! Details for this town are to follow.") 

        await self.get_town_sheet(sid)

        self.savetowns()

        return newTown

    async def set_town_avatar(self, townID, url):
        if self.check_town(townID):
            self.known_towns[townID]['Avatar'] = url
            await self.bot.say("Done!")
        else:
            await self.bot.say("Your town might not be signed up with the RPG. Please try signup first.")
        self.savetowns()


    async def set_town_name(self,ctx, name):
        sid = ctx.message.server.id
        #TODO make a hollow container to a method of the town class when town customization becomes a thing.
        if sid not in self.known_towns:
            await self.bot.say("This town has never actually been created before, but I'll go ahead and establish your great wonder")
            await self.create_town(ctx)
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

