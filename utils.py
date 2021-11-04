import os
import yaml
import json
import hashlib
import hmac

def load_config():
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print("Unable to load config.yaml")
            print(exc)
            exit(1)

    # Validate config items.
    if not config.get('patreon'):
        print("Missing patreon section.")
        exit(1)

    patreon = config['patreon']
    for key in ['client_id', 'client_secret', 'domain']:
        if not patreon.get(key):
            print("Patreon section missing", key)
            exit(1)

    if not patreon.get('port'):
        config['patreon']['port'] = 8080

    if not patreon.get('host'):
        config['patreon']['host'] = 'localhost'

    if not config.get('discord'):
        print("Missing discord section.")
        exit(1)

    discord = config['discord']
    for key in ['token']:
        if not discord.get(key):
            print("Patreon section missing", key)
            exit(1)

    if not discord.get('template'):
        config['discord']['template'] = '**NEW PATREON POST**\n{title}\nhttps://www.patreon.com{url}'
    if not config.get('data_directory'):
        config['data_directory'] = "data"

    try:
        os.makedirs(config['data_directory'], exist_ok=True)
        os.makedirs(config['data_directory'] + '/user', exist_ok=True)
        os.makedirs(config['data_directory'] + '/guild', exist_ok=True)
    except:
        print("Unable to create data directory.")
        exit(1)
    return config

class GuildClient(object):
    def __init__(self, config):
        self.dir = config['data_directory'] + '/'

    ##
    # Construct the filename to store a guild's data in.
    def guild_file_name(self, uid):
        return self.dir + '/guild/' + str(uid) + '.json'
        
    ##
    # Fetch guild_data directly from storage.
    def get_guild_data(self, uid):
        try:
            with open(self.guild_file_name(uid)) as infile:
                guild_data = json.load(infile)
        except:
            return None

        return guild_data

    ##
    # Write updated guild_data for a guild.
    def write_guild_data(self, uid, guild_data):
        # validate guild_data has all needed keys.
        for key in ['name', 'channel']:
            if not guild_data.get(key):
                return False

        with open(self.guild_file_name(uid), 'w') as outfile:
            json.dump(guild_data, outfile, default=str)


##
# Verify signature for a given webhook.
def verify_signature(message, key, expected):
    digester = hmac.new(
        bytes(key, encoding='utf-8'),
        bytes(message),
        hashlib.md5
    )

    return expected == digester.hexdigest()
