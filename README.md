# Patreon Discord bot

This bot is a simple bot that will relay posts from Patreon to Discord. It requires authorization on both the Patreon and Discord APIs.

## Requirements
* Python -- I've only tested this with python 3.6
* A webserver configured to proxy such as apache or nginx.
* A discord bot
* A patreon account

## Basic configuration

### Install dependencies
Install requirements with:
```bash
pip install -r requirements.txt
```

### Discord
A tutorial on getting a bot onto discord is at: https://realpython.com/how-to-make-a-discord-bot-python/

TL;DR:
* You'll need the bot's secret
* You'll need to create the oauth URL so your bot can join a server (aka Guild) and a server owner will need to do this.

### Patreon
You'll need to create a patreon client at: https://www.patreon.com/portal/registration/register-clients. You'll need to specify the domain that your bot will be running on for the redirect. That URL will be, replacing example.com for your own: `https://www.example.com/redirect`. 

### Configuration file
Create a config.yaml:
```yaml
patreon:
  client_id: 'YOUR PATREON CLIENT ID'
  client_secret: 'YOUR PATREON SECRET'
  domain: 'http://www.example.com'
  port: '[OPTIONAL] defaults to 8080'
  host: '[OPTIONAL] The host to bind to. Defaults to localhost and is recommended to only do this and proxy with a real webserver.'
      
discord:
  token: 'YOUR BOT DISCORD TOKEN'
  template: '[OPTIONAL] Defaults to: **NEW PATREON POST**\n{title}\nhttps://www.patreon.com{url}'

data_directory: '[OPTIONAL]. Defaults to: data'
```

## Starting your bot
Run bot.py.

## Authorizing Patreon
The Patreon administrator must visit your bot at, for example: `https://www.example.com/setup`

If your config is correct, after authorization you'll be redirected back and see a simple success message.

## Connecting Patreon posts to Discord channel
Once Patreon is authorized, you can see the status of the authorization using the botshell.
```bash
./botshell.py status
```
If the webhook is properly created, connect it to a channel, using the userid you see in the status.

```shell
./botshell.py connect USERID "Server name" "channel name"
```

At this time the bot only connects to one server and channel per user.

## Installing the bot as a python service.

* You'll want to create a user for the bot and a place for it to live.

Put this in `/etc/systemd/system/discordbot.service`:
```ini
[Unit]
Description=Discordbot
After=multi-user.target

[Service]
Type=simple
User=discordbot
Group=discordbot
Restart=always
ExecStart=/usr/bin/python3 /home/discordbot/bot.py

[Install]
WantedBy=multi-user.target
```

Then if everything works:
```shell
sudo systemctl start discordbot
```