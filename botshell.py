#!/usr/bin/python3 -u

import os
import sys
from pathlib import Path
import patreonclient
import utils
import termtables
import discord

import os
import sys
abspath = os.path.abspath(sys.argv[0])
dname = os.path.dirname(abspath)
os.chdir(dname)

def print_help():
    print("""Usage: botshell.py COMMAND
Administer the patreon discord bot.

Commands:
  status                                Display the status of all configured users.
  channel UID SERVERNAME CHANNEL        Set a given UID to transmit to the specified server and channel.
    """)
    exit(0)

def print_status(config):
    guild_client = utils.GuildClient(config)
    header = ['User', 'Webhook', 'Server', 'Channel']
    output = []
    for filename in os.listdir(config['data_directory'] + '/user'):
        if not filename.endswith(".json"):
            continue
        uid = Path(filename).stem
        client = patreonclient.PatreonClient(config, uid)
        webhook = client.get_webhook_info()
        if webhook is None:
            webhook_status = "None"
        elif webhook['paused']:
            webhook_status = "Paused"
        else:
            webhook_status = "Active"
        gd = guild_client.get_guild_data(uid)
        output.append([
            uid,
            webhook_status,
            gd.get('name') or "None",
            gd.get('channel') or "None',"
        ])
    
    termtables.print(output, header=header)

def set_channel(config, uid, guildname, channelname):
    # Validate uid exists and has a webhook.
    client = patreonclient.PatreonClient(config, uid)
    webhook = client.get_webhook_info()
    if webhook is None:
        print(str(uid) + " is not valid or does not have a configured webhook.")
        exit(1)

    # Validate discord has access to guild.
    guildname_exists = False
    channelname_exists = False
    async def run_test(client):
        nonlocal guildname_exists
        nonlocal guildname
        nonlocal channelname_exists
        nonlocal channelname
        for guild in client.guilds:
            if guild.name == guildname:
                guildname_exists = True
                for channel in guild.channels:
                    if (channel.name == channelname):
                        channelname_exists = True
                        break
                break

    class NonInteractiveClient(discord.Client):
        async def on_ready(self):
            await self.wait_until_ready()
            await run_test(self)
            await self.close()

        async def on_error(self, event, *args, **kwargs):
            raise

    client = NonInteractiveClient()
    client.run(config['discord']['token'])
    
    if not guildname_exists:
        print(guildname + " is not a server the bot has access to.")
        exit(1)
    # validate discord has access to channel.
    if not channelname_exists:
        print(channelname + " is not a channel the bot has access to.")
        exit(1)

    # update the data.
    guild_client = utils.GuildClient(config)
    guild_client.write_guild_data(uid, {'name': guildname, 'channel': channelname})
    print("Updated " + uid + " to " + guildname + ":" + channelname)
    exit(0)
config = utils.load_config()
if len(sys.argv) < 2:
    print_help()

command = sys.argv[1]

if command == 'status':
    print_status(config)
elif command == 'channel':
    if len(sys.argv) < 5:
        print_help()
    else:
        set_channel(config, sys.argv[2], sys.argv[3], sys.argv[4])
    print_help()
