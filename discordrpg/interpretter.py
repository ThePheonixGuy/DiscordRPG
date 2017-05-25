import discord
from discord.ext import commands
import asyncio
import aiohttp
from cogs.utils.dataIO import dataIO
import requests
import os

class Interpretter:
    """API.ai Interpretter Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.API_URL = "https://api.api.ai/v1/"
        self.session = 12345
        self.responses = dataIO.load_json("data/interpretter/output.json")

    @commands.command(pass_context = True)
    async def interpret(self, ctx, * , query_text):
        await self.bot.send_typing(ctx.message.channel)
        """Attempts to interpret a query and provide a response."""
        response = await self.search_responses(query_text)
        
        if response is not None:
            await self.bot.say(response)
        else:
            await self.bot.say("Sorry... I forgot what we were talking about... Please try asking me again.")


    async def _interpret(self, args):
        headers = {
            'Authorization' : 'Bearer {{token here}}' #TODO change to input-able key
        }
        params = {'query' : args, 'lang' : 'en', 'sessionId' : self.session}
        queryapi = "{}query?v=20150910".format(self.API_URL)

        async with aiohttp.get(queryapi, headers = headers, params = params) as response:
            r = await response.json()
            try:
                stripped_r = self.response_stripper(r)
            except KeyError as e:
                print(e)
                return None

            return stripped_r

            

        # for rpg commands, use custom payloads. they will be contained in output['result']['fulfillment']['messages'][1][]

    def response_stripper(self, response):
        # for final rpg implementation, make action top level key and the different responses there of as different query lists and responses.
        # or maybe query? alows for easier top level searching?
        # actually this idea might be better. Queries.
        r = {}
        query = response['result']['resolvedQuery'].lower()
        r['query'] = response['result']['resolvedQuery'].lower()
        r['speech'] = response['result']['fulfillment']['speech']
        try:
            messages = response['result']['fulfillment']['messages']
            if len(messages) > 1:
                r['action'] = response['result']['fulfillment']['messages'][1]['payload']['action']
            else:
                r['action'] = 'None'
                self.responses[query] = r
                self.save_output(self.responses)
                return r
        except:
            r['action'] = 'None'
        
        self.responses[query] = r
        self.save_output(self.responses)
        return r

    def create_message(self, stripped_r):
        speech = stripped_r['speech']
        if len(speech) > 0:
            action = stripped_r['action']
            query = stripped_r['query']
            output = "{}\n```Matched Query: {}\nActions: {}```".format(speech, query, action)
            return output
        else:
            return None

    async def search_responses(self, args):
        # Check for query in output.json
        # If there, then use those params instead.
        # Callstack needs to have interpret call last.
        stripped_r = None
        for entry in self.responses:
            if entry == args:
                stripped_r = self.responses[entry]

        if stripped_r == None:
            # call down stack to the interpreter
            stripped_r = await self._interpret(args)
            

        return self.create_message(stripped_r)


    async def checkmention(self, message):
        if message.channel.id == "301474329651052545":

            if message.author.id != self.bot.user.id:
                await self.bot.send_typing(message.channel)
                #word_list = message.content.split()
                #word_list = word_list[1:]
                #args = " ".join(word_list)
                args = message.content
                response = await self._interpret(args)
                if not response:
                    #rejected message.
                    return

                await self.bot.send_message(message.channel, response)

    def save_output(self, file):
        f = "data/interpretter/output.json"
        dataIO.save_json(f, file)

def check_folders():
    if not os.path.exists("data/interpretter"):
        print("Creating data/interpretter folder...")
        os.makedirs("data/interpretter")

def check_files():
    f = "data/interpretter/output.json"
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, {})


def setup(bot):
    check_folders()
    check_files()
    n = Interpretter(bot)
    #bot.add_listener(n.checkmention, "on_message")
    bot.add_cog(n)

