# Discord
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from .utils import checks
from __main__ import send_cmd_help
# Others
import os
from copy import deepcopy, copy
import datetime
import time
import math
import random
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
        self.map = Map(
            self.player, bot, "data/discordrpg/tiletypes.json", "data/discordrpg/map.json")
        self.settings_path = "data/discordrpg/settings.json"
        self.settings = dataIO.load_json(self.settings_path)
        self.logged_in_users = []
        self.default_options = ["Survey the Landscape",
                                "Have a look around",
                                "Check Inventory",
                                "Meditate",
                                "Rest"]

    @commands.group(name='rpgset', pass_context=True)
    async def rpgset(self, ctx):
        """Settings for the RPG on this server"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @rpgset.command(pass_context=True)
    async def townname(self, ctx, *, name):
        """Allows you to set a name for this server's Home Town"""
        author = ctx.message.author
        sid = ctx.message.server
        await self.town.set_town_name(ctx, name)

    @rpgset.command(pass_context=True)
    async def townavatar(self, ctx, *, avatarurl):
        """Allows you to set a new Avatar picture for this server's Home Town"""
        # TODOLATER allow attachment grabbing. its possible, but im lazy
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
    async def signup(self, ctx):
        """Allows an admin or moderator to signup this server into the RPG"""
        await self.town.create_town(ctx)

    @rpg.command(pass_context=True)
    async def character(self, ctx):
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

        embed = discord.Embed(title="Options for {}".format(current_player[
                              'CharName']), description="Use the numbers to make a choice.", colour=0xfd0000)
        embed.add_field(
            name='Options', value="`1.` Get Character Sheet\n`2.` Change Avatar\n`3.` Change Bio\n`4.` View Home Town", inline=False)
        embed.set_author(name='{}'.format(author.name),
                         icon_url='{}'.format(author.avatar_url))
        embed.set_thumbnail(
            url='https://i.ytimg.com/vi/Pq824AM9ZHQ/maxresdefault.jpg')
        await self.bot.say("", embed=embed)

        response = await self.bot.wait_for_message(author=author)
        if '1' in response.content:
            # Return the character sheet
            await self.player.getCharacterSheet(author)
        elif '2' in response.content:
            # Grab url, validate it and save to the players profile in
            # players.json
            await self.bot.say("Please provide me with a url only, to use as an image for your character sheet.")
            # TODOLATER allow attachment grabbing. its possible, but im lazy
            avatarurl = await self.bot.wait_for_message(author=author)

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

        else:
            await self.bot.say("Invalid response. Please try again.")

    @rpg.command(pass_context=True, no_pm=False)
    async def register(self, ctx):
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

    @rpg.command(pass_context=True, no_pm=False)
    async def viewtown(self, ctx):
        """View the details of the guild's town you are currently in"""
        sid = ctx.message.server.id
        await self.town.get_town_sheet(sid)

    @rpg.command(pass_context=True, no_pm=False)
    async def viewmonster(self, ctx, *, monsterID):
        """Testing Stub. Please do not use."""
        await self.monster.getMonsterSheet(monsterID)

    @rpg.command(pass_context=True, no_pm=False)
    async def viewtile(self, ctx, locX: int, locY: int):
        """Testing sub. Please do not use."""
        user = ctx.message.author
        location = {"X" : locX, "Y" : locY}
        current_player = await self.player.get_player_records(user.id)
        tile = await self.map.map_provider(user, location)
        await self.bot.say(tile)

    @rpg.command(pass_context=True, no_pm=False)
    async def findtile(self, ctx, tile_type):
        """Stub. Do not Use"""
        user = ctx.message.author
        tile = await self.map.find_tile(tile_type)
        await self.bot.say(tile)

    @rpg.command(pass_context=True, no_pm=False)
    async def viewplayer(self, ctx, user: discord.Member):
        """Allows you to see the character sheet of another player in the game."""

        hasProfile = await self.player.check_player(user.id)

        if hasProfile:
            await self.player.getCharacterSheet(user)
        else:
            await self.bot.say("That player does not yet exist. Perhaps consider asking them to join using `{}rpg register`?".format(ctx.prefix))

    @rpg.command(pass_context=True, no_pm=False)
    async def logout(self, ctx):
        """Logs you out of your current session, if there is one"""
        await self._logout(ctx)

    @rpg.command(pass_context=True, no_pm=False)
    async def play(self, ctx):
        """Runs a session of DiscordRPG"""
        # from this point onwards, CTX cannot be used for resources like server ID's.
        # Needs to be pulled from the existing resources, in the dicts.
        userDO = ctx.message.author
        await self.reload_town_records()
        current_player = await self.player.get_player_records(userDO.id)
        player_town = await self.town.get_town_records(current_player['HomeTownID'])

        if player_town is None:
            await self.bot.say("Hmmm... It appears your town is still in Rubble unfortunately."
                               "Torn down by a war long since forgotten. "
                               "Get an admin of this server to try `{}rpg signup`".format(ctx.prefix))
            return

        if not self._login(userDO):
            await self.bot.say("You already have an Ongoing play session. "
                               "If you can't find it, please try "
                               "`{}rpg logout`".format(ctx.prefix))
            return
        # TODO remove when complete.
        await self.bot.say("This is still under construction. Any bugs are please to be reported using `;;contact` followed by the error given. Thanks for testing out DiscordRPG!")
        
        

        if 'Never' in current_player['Last_Played']:
            await self.bot.say("Thank you for signing up. Welcome to your next grand adventure")
            await self.first_adventure_town(ctx, current_player, player_town)

    async def first_adventure_town(self, ctx, current_player, player_town):
        user = ctx.message.author
        player_race = current_player['Race']
        player_old_wep = ""

        if 'W' in player_race:
            player_old_wep = "Half Blade"
        elif 'R' in player_race:
            player_old_wep = "Dagger"
        elif 'S' in player_race:
            player_old_wep = "Wand"

        header = ["Awakening", ("First, nothing. Then, just white pain."
                  " You wake up on the cold, hard stones."
                  " Dazed and Confused,"
                  " you wonder how it is you ended up here."
                  " Opening your eyes to the eye-shattering sunlight,"
                  " you sit yourself up and take a look around."
                  " Doesn't look like much,"
                  " a simple town you think to yourself."
                  " You stand up and decide to have a look around.")]
        option = ["Take a look around."]

        em1 = await self.embed_builder(ctx, current_player, header, option)

        await self.bot.say("", embed=em1)

        valid = False
        while not valid:
            response = await self.loop_checks(ctx)
            if not response:
                valid = True
                return
            elif '1' in response.content:
                option = ["Try for the gate. It's time to get out of here.",
                          "Approach the Fountain.",
                          "Take a closer look at the buildings around you."]
                # the 1 reference here is to keep the "Awakening chapter heading"
                header[1] = (" You pull yourself to your feet. As you do, "
                             "a stranger calls out to you, 'Woah hold on there friend! Name's Timm.' "
                             "He hands you a tankard,which you gulp down.\n "
                             "Timm continues, 'Some big fella's dragged you in overnight. "
                             "I saw it from my shop, Timms Town Improvement! "
                             "How about you come round and have a look when you're ready? "
                             "I've also put some coin in your pocket. You could use it.'"
                             "\n You have a look around the town. It's all in a circle, "
                             "clearly having only just being rebuilt from Rubble. "
                             "You see a dirty Fountain in the centre of the courtyard. "
                             "You notice a Gate behind you, seemingly ungaurded.\n\n "
                             "What shall you do next?")

                em1 = await self.embed_builder(ctx, current_player, header, option)
                await self.bot.say("", embed=em1)
                valid = True
                break
            else:
                await self.bot.say("No correct response detected. Please try again.")
                continue

        valid = False
        while not valid:
            response = await self.loop_checks(ctx)
            if not response:
                valid = True
                return
            elif '1' in response.content:
                # Approach the gate.
                option = ["Turn Around. You don't have enough strength to face that yet.",
                          "Ignore the advice. Ask to leave the gate."]
                header[0] = ("The Gate and the Gate Keeper")
                header[1] = ("It's a sad, wooden afair."
                             " The wood looks rotted and pieced together."
                             " How this serves as protection for anything is anyone's guess."
                             "\n Out of your periphery you notice a large being approaching."
                             " You turn suddenly, reaching for your trusty {}"
                             ", but you remember it's not there. All your things, gone."
                             "\n A large Orcish man approaches you, easily twice your height."
                             " 'I am the gate keeper here. Why do you wish to leave?'"
                             ". Clearly not looking to fight, he lowers his weapon, a large golden axe."
                             " 'The road is not safe. The town's only just been built back up."
                             " We are still clearing the area around the town.' ".format(player_old_wep))
                em1 = await self.embed_builder(ctx, current_player, header, option)
                await self.bot.say("", embed=em1)

                response = await self.loop_checks(ctx)
                if not response:
                    valid = True
                    return
                if '1' in response.content:
                    await self.bot.say("Please repeat your option.")
                    valid = False
                    continue
                elif '2' in response.content:
                    await self.first_adventure_outside(ctx, current_player, player_town)
                    valid = True
                    break
            elif '2' in response.content:
                # Look at the fountain
                option = ["Try for the gate. It's time to get out of here.",
                          "Stay staring at the fountain.",
                          "Take a closer look at the buildings around you."]
                header[0] = ("The Old Fountain")
                header[1] = (" It seems no-one has gotten around to sorting this out."
                             " It has a dirty, worn out plaque underneath it, barely readable."
                             "\n Still covered in Algae, the base is cracked."
                             " There are some old coins, some still glittering, most are faded."
                             "\n The fountain itself is a very plain structure,"
                             " with three bowl-shaped tiers.")
                em1 = await self.embed_builder(ctx, current_player, header, option)
                await self.bot.say("", embed=em1)
                #TODO interactable that allows you to dive into the fountain for some extra cash.
                # naaaah. to lazy
                continue
            elif '3' in response.content:
                # Look around at the buildings.
                town_name = player_town['Town_Name']
                town_buildings = ", ".join(player_town['Buildings'])
                building_info_string = ""
                building_info = dataIO.load_json(
                "data/discordrpg/buildings.json")
                for building in player_town['Buildings']:
                    info = building_info[building]
                    building_info_string += "**{}**: *{}*\n".format(building, info['Desc'])

                option = ["Try for the gate. It's time to get out of here.",
                          "Approach the Fountain."]
                header[0] = ("{}, the town.".format(town_name))
                header[1] = ("Doing a quick roundabout, you notice the town has a {}."
                             ". Nothing all too impressive, but a decent start,"
                             " you think to yourself."
                             "\n\n{}".format(town_buildings, building_info_string))

                em1 = await self.embed_builder(ctx, current_player, header, option)
                await self.bot.say("", embed=em1)
                continue
            else:
                await self.bot.say("No correct response detected. Please try again.")
                continue

    async def first_adventure_outside(self, ctx, current_player, player_town):
        #TODO continue gameplay here
        # get location of town. Add 1 to loc_y.
        # get tile details for that location.
        # from details, return a string of the tile.
        # options? default tile interaction options?
        user = ctx.message.author
        player_race = current_player['Race']
        location = player_town['Location']
        location['Y'] += 1
        tile = await self.map.get_tile_records(current_player, location)
        print(tile)

        option = self.default_options
        header = ["Title","Description"]
        header[0] = "The Green Mile"
        header[1] = ("The Gate Keeper reluctantly opens the gate."
                     " He warns you one last time, you should wait,"
                     " but you're a {}, and waiting isn't in your blood."
                     " There is no stone beneath your feet, just cold grass."
                     " You realise you must be {}.".format(player_race, "in a grassland"))

        em1 = await self.embed_builder(ctx, current_player, header, option)
        await self.bot.say("", embed=em1)
        return

    async def reload_town_records(self):
        self.town = Town(self.bot, "data/discordrpg/towns.json")

    async def exit_check(self, text):
        text = text.lower()
        if 'exit' in text:
            return True
        else:
            return False

    def _login(self, user):
        if user.id in self.logged_in_users:
            return False
        else:
            self.logged_in_users.append(user.id)
            print(self.logged_in_users)
            return True
        # TODO return as an embed, 
        # a login message as well as details last played
        # and current location.

    async def _logout(self, ctx):
        user = ctx.message.author
        try:
            self.logged_in_users.remove(user.id)
            print(self.logged_in_users)
            await self.bot.say("Logged out succesfully..")
        except:
            await self.bot.say("It seems you are not currently logged in. "
                               "Have you tried `{}rpg play`?".format(ctx.prefix))

    async def loop_checks(self, ctx):
        user = ctx.message.author
        if user.id not in self.logged_in_users:
            return False
        response = await self.bot.wait_for_message(timeout=600, author=user)
        if response is None:
            await self._logout(ctx)
            return False
        if await self.exit_check(response.content):
            await self.bot.say(("Are you sure you wish to end the session here?"
                                " Say `yes` to confirm"))
            response = await self.bot.wait_for_message(timeout=600, author=user)
            if response is None:
                await self._logout(ctx)
                return False
            elif 'y' in response.content.lower():
                await self._logout(ctx)
                return False
        return response

    async def embed_builder(self, ctx, user, header, option):
        value = ""
        count = 1
        for item in option:
            value += "`{}.`{}\n".format(count, item)
            count += 1
        em = discord.Embed(title="{}".format(
            header[0]), description="{}".format(header[1]), colour=0xfd0000)
        em.add_field(name='Use the numbers to Indicate your Choice.',
                     value=value, inline=False)
        em.set_author(name='{}'.format(user["CharName"]))
        em.set_thumbnail(url=user['Avatar'])
        em.set_footer(text="Say Exit to logout from this session.")
        return em

    async def generic_adventure(self, ctx, current_player, player_town):
        option = []
        em1 = discord.Embed(title="{}".format(
            option[0]), description="{}".format(option[1]), colour=0xfd0000)
        em1.add_field(name='Use the numbers to Indicate your Choice.', value="`1.`{}\n`2.`{}\n`3.`{}\n`4.`{}\n".format(
            option[2], option[3], option[4], option[5]), inline=False)
        await self.bot.say("", embed=embed1)


class Player:

    def __init__(self, bot, player_path, invent_path):
        self.bot = bot
        self.playerRoster = dataIO.load_json(player_path)
        self.playerInventories = dataIO.load_json(invent_path)
        self.monster = Monster(bot, "data/discordrpg/monsters.json")
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.map = Map(self, bot, "data/discordrpg/tiletypes.json",
                       "data/discordrpg/map.json")

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
        # order = charname, race, hometown, bio. stats to be inferred from
        # race.
        author = ctx.message.author
        newplayer = {}
        race = ""
        charname = ""
        bio = ""
        hometownid = ctx.message.server.id
        hometownname = ctx.message.server.name
        await self.town.reload_town_records()
        town_record = await self.town.get_town_records(hometownid)
        print("New player is registering in {} from server {}".format(
            town_record['Town_Name'], ctx.message.server.name))
        # TODO. retrieve requisite info. add it to dictionary and pass to
        # _createplayer method.
        completion = "yes"

        embed = discord.Embed(
            title="Pick a Class", description="Let's start off by finding what class your character is.", colour=0xff0000)
        embed.add_field(
            name='Class', value="Choose from the following Classes:", inline=False)
        embed.add_field(name='Warrior', value='The Melee Class. Specialising in close quarters combat, the warrior is lethal with a selecton of weapons.\n*Type `1` to select this class.*', inline=False)
        embed.add_field(name='Rogue', value='Specialising in ranged combat and steath, the Rogue is Death from a Distance, with a touch of magic to make life easier\n*Type `2` to select this class.*', inline=False)
        embed.add_field(
            name='Sorcerer', value="Nothing above their power, the arcane arts allow the Sorcerers to bend any element to their will\n*Type `3` to select this class.*", inline=False)
        embed.set_thumbnail(
            url='http://unrealitymag.com/wp-content/uploads/2011/11/torchlight1.jpg')
        await self.bot.say(' ', embed=embed)
        raceChoice = await self.bot.wait_for_message(author=author)

        if '1' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Warrior's name?")
            race = "Warrior"
        elif '2' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Rogue's name?")
            race = "Rogue"
        elif '3' in raceChoice.content:
            await self.bot.say("Awesome! Now, What is this Sorcerers's name?")
            race = "Sorcerer"
        charname = await self.bot.wait_for_message(author=author)
        charname = charname.content

        await self.bot.say("Please provide a short backstory about yourself, {}".format(charname))

        bio = await self.bot.wait_for_message(author=author)

        await self.bot.say("Great, welcome to {}, {}".format(town_record['Town_Name'], charname))
        # TODO add session counter for tut purposes.
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
            newplayer[
                'Avatar'] = "https://s-media-cache-ak0.pinimg.com/736x/77/02/6b/77026b08f33fb0b4a35434553c4fccc8.jpg"
        elif 'R' in race:
            newplayer['BaseStats'] = {'HP': 40, 'Mana': 15, 'Stamina': 20}
            newplayer[
                'Avatar'] = "https://s-media-cache-ak0.pinimg.com/736x/8c/2b/da/8c2bdafd9c5c5b2ec38b81741aa5e879.jpg"
        elif 'S' in race:
            newplayer['BaseStats'] = {'HP': 35, 'Mana': 30, 'Stamina': 15}
            newplayer[
                'Avatar'] = "https://s-media-cache-ak0.pinimg.com/originals/c3/e5/25/c3e525a719eaa6ae0df486baa672391c.jpg"
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
        print("New player registered in {} from server {}. Details: \n{}".format(
            town_record['Town_Name'], ctx.message.server.name, newplayer))
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
            # Change to tile provider when complete.
            current_loc = "Currently in {}".format(char_town['Town_Name'])
        else:
            current_loc = "{} MU from {}".format(
                current_loc, char_town['Town_Name'])
        # TODO will require a location provider. Part of map Class.
        embed = discord.Embed(title="{}".format(
            char_profile['CharName']), description=current_loc, color=0xff0000)
        embed.add_field(name='Bio', value="Hailing from **{}**, *{}* is a {}. In his own words, '*{}*' ".format(
            char_town['Town_Name'], char_profile['CharName'], char_profile['Race'], char_profile['Bio']), inline=False)
        embed.add_field(name='Last Played', value=char_profile[
                        'Last_Played'], inline=True)
        embed.add_field(name='Level', value=char_profile['Level'], inline=True)
        embed.add_field(name='Health', value=char_profile[
                        'BaseStats']['HP'], inline=True)
        embed.add_field(name='Mana', value=char_profile[
                        'BaseStats']['Mana'], inline=True)
        embed.add_field(name='Stamina', value=char_profile[
                        'BaseStats']['Stamina'], inline=True)
        embed.add_field(name='Gold', value=char_profile['Gold'], inline=True)
        embed.set_author(name='{}'.format(author.name),
                         icon_url='{}'.format(author.avatar_url))
        embed.set_thumbnail(url=char_profile['Avatar'])

        await self.bot.say(" ", embed=embed)

    async def setProfileAvatar(self, userID, url):
        # TODO check it for keyerror. use check method.
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

        new_bio = await self.bot.wait_for_message(author=author)
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


class Monster:

    def __init__(self, bot, monster_path):
        self.bot = bot
        self.npcmonsters = dataIO.load_json(monster_path)

    async def getMonsterSheet(self, monsterID):
        await self.bot.say(monsterID)

        if monsterID in self.npcmonsters:
            # this method stub is actually a part check_monster method.
            pass


class Map:

    def __init__(self, player, bot, tile_path, map_path):
        self.bot = bot
        self.fieldmap = dataIO.load_json(map_path)
        self.tiletypes = dataIO.load_json(tile_path)
        self.town = Town(bot, "data/discordrpg/towns.json")
        self.player = player

    async def reload_map(self):
        self.fieldmap = dataIO.load_json("data/discordrpg/towns.json")

    async def map_generator(self, user, location):
        # TODO 
        # take the location. Check if its in the map using check tile.
        # if not, select tile. 
        # selection based off dist from town. <- pulled from user object.
        # should be the only thing? if else for it?
        try:
            tile_info = dataIO.load_json("data/discordrpg/tiletypes.json")
        except:
            raise RuntimeError("Tile type data is corrupt. Please reload it")


        if not await self.check_tile(location):
            tile = None
            #logic and choose tile and save it.
            dist = await self.get_distance_from_home(user, location)
            print(dist)
            player_record = await self.player.get_player_records(user.id)
            #choose tile by level
            #TODO implement multiple selections based off distance. ie lvl 4 to 6.
            if dist < 5:
                #level 1
                tile = random.choice(list(tile_info["01"]))
                tile = {tile : tile_info['01'][tile]}
                tile[tile_info['01'][tile]]["Location"] = lcoation
                tile[tile_info['01'][tile]]["Distance"] = dist
                tile[tile_info['01'][tile]]["Founding_Player"] = player_record["CharName"]
                print(tile)

            elif dist < 10:
                #level 2
                tile = random.choice(list(tile_info["02"]))
                tile = {tile : tile_info['02'][tile]}
                tile["Distance"] = dist
                tile["Founding_Player"] = player_record["CharName"]
                print(tile)
                
            elif dist < 15:
                #level 3
                tile = random.choice(list(tile_info["03"]))
                tile = {tile : tile_info['03'][tile]}
                tile["Distance"] = dist
                tile["Founding_Player"] = player_record["CharName"]
                print(tile)
                
            elif dist < 20:
                #level 4
                tile = random.choice(list(tile_info["04"]))
                tile = {tile : tile_info['04'][tile]}
                tile["Distance"] = dist
                tile["Founding_Player"] = player_record["CharName"]
                print(tile)
                
            elif dist < 25:
                #level 5
                tile = random.choice(list(tile_info["05"]))
                tile = {tile : tile_info['05'][tile]}
                tile["Distance"] = dist
                tile["Founding_Player"] = player_record["CharName"]
                print(tile)
                
            elif dist >= 25:
                #level 6
                tile = random.choice(list(tile_info["06"]))
                tile = {tile : tile_info['06'][tile]}
                tile["Distance"] = dist
                tile["Founding_Player"] = player_record["CharName"]
                print(tile)
                

            #TODO refine the required elements and pull them correctly.
            #save tile to map.
            x = str(location['X'])
            y = str(location['Y'])
            try:
                oldmap_at_x = self.fieldmap[x]
            except:
                self.fieldmap[x] = {}
            self.fieldmap[x][y] = tile 
            self.savemap()
            #await self.reload_map()
            return tile
        else:
            return self.get_tile_records(user, location)


    async def map_provider(self, user, location):
        # TODO fix key errors? XD
        tileRecord = await self.get_tile_records(user, location)
        if tileRecord is None:
            tileRecord = await self.map_generator(user, location)
        return tileRecord

    async def get_distance_from_home(self, user, location):
        """def for returning the distance from home, because of how impotrant this is"""
        locX = location['X']
        locY = location['Y']
        player_record = await self.player.get_player_records(user.id)
        homeTownID = player_record["HomeTownID"]
        homeTown = await self.town.get_town_records(homeTownID)
        townLocation = homeTown['Location']
        townX = townLocation['X']
        townY = townLocation['Y']

        distX = locX - townX
        distY = locY - townY
        pDistance = math.hypot(distX, distY)
        pDistance = round(pDistance)
        return (pDistance)

    async def get_surrounds(self, user, location):
        # gets users current location.
        # checks self.fieldmap for all nine tiles around it, be
        # x;y, x;y+, x;y-, x+;y, x+;y+, x+;y-, x-:y, x-;y+, x-;y-
        # ^^ nine tiles. pass and call for each option to the map provider.
        pass  # TODO SOON for now.

    async def check_tile(self, location):
        """ takes the give location and checks if its in fieldmap"""
        x = str(location['X'])
        y = str(location['Y'])
        try:
            if x in self.fieldmap:
                if y in self.fieldmap[x]:
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False

    async def get_tile_records(self, user, location):
        tileExists = await self.check_tile(location)
        x = str(location['X'])
        y = str(location['Y'])
        if tileExists:
            return deepcopy(self.fieldmap[x][y])
        else:
            await self.map_generator(user, location)
            return deepcopy(self.fieldmap[x][y])

    async def find_tile(self, tile_type):
        item = await self._find_tile_type(self.fieldmap, tile_type)
        return item

    async def _find_tile_type(self, obj, tile_type):
        #TODO modify mapgen to add a location subdict
        if tile_type in obj: return obj[tile_type]
        for k, v in obj.items():
            if isinstance(v,dict):
                item = await self._find_tile_type(v, tile_type)
                if item is not None:
                    return item

    def savemap(self):
        f = "data/discordrpg/map.json"
        dataIO.save_json(f, self.fieldmap)


class Town:

    def __init__(self, bot, towns_path):
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

        location = "X: {}\nY: {}".format(
            town_record['Location']['X'], town_record['Location']['Y'])

        buildings = ", ".join(town_record['Buildings'])

        embed = discord.Embed(title="{}".format(town_record['Town_Name']), description="The humble {} was rebuilt from the rubble on {}. \n{}".format(
            town_record['Town_Name'], town_record['Created_At'], town_record['Description']), color=0xff0000)
        embed.add_field(name='Location', value=location, inline=True)
        embed.add_field(name='Level', value=town_record['Level'], inline=True)
        embed.add_field(name='Current Buildings',
                        value=buildings, inline=False)
        # TODO NOW list iterator for display purposes.
        embed.set_thumbnail(url=town_record['Avatar'])

        await self.bot.say(" ", embed=embed)

    async def create_town(self, ctx):
        newTown = {}
        sid = ctx.message.server.id
        author = ctx.message.author

        if await self.check_town(sid):
            await self.bot.say("This guild is already signed up."
                               " If you would like to change something,"
                               " Please try `{}rpgset`".format(ctx.prefix))
            return
        else:
            await self.bot.say("Hey there, {}. Thanks for signing up your server."
                               "Please provide a name for your new town!"
                               " This will be the name of the whole server's town.".format(author.mention))
            # TODO timeout
            response = await self.bot.wait_for_message(author=author)
            townName = response.content
            await self.bot.say("{}? Alright, if you say so."
                               " Gimme a second to get things set up,"
                               " I'll get back to you.".format(townName))

            townLevelDetail = dataIO.load_json(
                "data/discordrpg/townlevels.json")

            newTown['Town_Name'] = townName
            newTown['Created_At'] = datetime.datetime.ctime(
                datetime.datetime.now())
            newTown['Level'] = 1
            newTown[
                'Avatar'] = "http://orig09.deviantart.net/2440/f/2013/249/7/a/fantasy_rpg_town_by_e_mendoza-d6lb9td.jpg"
            newTown['Buildings'] = townLevelDetail["001"]["Buildings"]
            newTown['Description'] = townLevelDetail["001"]["Description"]
            # TODO change to map provider.
            newTown['Location'] = {'X': 1, 'Y': 1}
            self.known_towns[sid] = newTown

        # TODO add town bio. Would be nice.
        # TODO Basic buildings tavern and Town Builder.
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

    async def set_town_name(self, ctx, name):
        sid = ctx.message.server.id
        # TODO make a hollow container to a method of the town class when town
        # customization becomes a thing.
        if sid not in self.known_towns:
            await self.bot.say("This town has never actually been created before,"
                               " but I'll go ahead and establish your great wonder")
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
        raise RuntimeError(
            "Data file tiletypes.json is either missing from the data folder or corrupt. Please redownload it and place it in your bot's data/discordrpg/ folder")

    f = "data/discordrpg/monsters.json"
    if not dataIO.is_valid_json(f):
        raise RuntimeError(
            "Data file monsters.json is either missing from the data folder or corrupt. Please redownload it and place it in your bot's data/discordrpg/ folder")

    f = "data/discordrpg/townlevels.json"
    if not dataIO.is_valid_json(f):
        raise RuntimeError(
            "Data file townlevels.json is either missing from the data folder or corrupt. Please redownload it and place it in your bot's data/discordrpg/ folder")


def setup(bot):
    check_folders()
    check_files()
    if validatorsAvail:
        bot.add_cog(DiscordRPG(bot))
    else:
        raise RuntimeError("You need to run pip3 install validators")
