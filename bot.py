#!/usr/bin/python3 -u
# bot.py

import os
import sys
abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

import asyncio
import discord
import utils
import web

config = utils.load_config()
client = discord.Client()

# Run webserver
loop = asyncio.get_event_loop()
loop.run_until_complete(web.run(config, client))

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(config['discord']['token'])
