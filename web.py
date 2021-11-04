from aiohttp import web
import patreonclient
import utils

##
# Run the webserver.
async def run(config, discord):
    app = web.Application()

    app['config'] = config
    app['discord'] = discord

    setup_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, config['patreon']['host'], config['patreon']['port'])
    await site.start()
    print ("Started webserver on " + config['patreon']['host'] + ':' + str(config['patreon']['port']))

##
# Webserver routes live here.
def setup_routes(app):
    routes = web.RouteTableDef()

    @routes.get('/setup')
    async def setup(request):
        config = request.app['config']['patreon']
        response = ''
        response += '<html><body>'
        response += '<a href="https://www.patreon.com/oauth2/authorize?response_type=code&client_id=' + config['client_id'] + '&redirect_uri=' + config['domain'] + '/redirect&scope=campaigns w:campaigns.webhook">Click here to start Patreon authorization.</a>'
        response += '</body></html>'
        return web.Response(text=response, content_type="text/html")

    @routes.get('/redirect')
    async def patreonauth(request):
        config = request.app['config']
        token_client = patreonclient.TokenClient(config)
        code = request.rel_url.query.get('code')
        if not code:
            return web.Response(text='Missing code.')

        if token_client.validate_code(code):
            return web.Response(text='Success!')
        else:
            return web.Response(text='Auth failed!')

    @routes.post('/webhook')
    async def webhook(request):
        config = request.app['config']
        # Get data
        try:
            data = await request.json()
        except:
            return web.Response(text='invalid post data')

        # Reject if missing Patreon headers.
        if not request.headers.get('X-Patreon-Signature'):
            return web.Response(text='unsigned')

        # get uid from data
        if not data.get('data') or not data['data'].get('relationships') or not data['data']['relationships'].get('user') or not data['data']['relationships']['user'].get('data') or not data['data']['relationships']['user']['data'].get('id'):
            return web.Response(text='invalid data')

        uid = data['data']['relationships']['user']['data']['id']
        guild_client = utils.GuildClient(config)
        gd = guild_client.get_guild_data(uid)
        if not gd:
            return web.Response(text='no destination')

        # fetch user config for this webhook
        client = patreonclient.PatreonClient(config, uid)
        webhook = client.get_webhook_info()
        if not webhook:
            return web.Response(text='missing webhook config')

        # Verify data signature
        raw_data = await request.read()

        if not utils.verify_signature(raw_data, webhook['secret'], request.headers['X-Patreon-Signature']):
            return web.Response(text='signing failed')

        # notify discord channel
        message = 'TODO'

        # Find guild and channel.
        channel = None
        for guild in request.app['discord'].guilds:
            if guild.name == gd['name']:
                for c in guild.channels:
                    if c.name == gd['channel']:
                        channel = c
                        break
                break

        if not channel:
            return web.Response(text='channel not found')

        attributes = data['data']['attributes']
#        message = '**NEW PATREON POST**\n' + attributes['title'] + '\n' + 'https://www.patreon.com' + attributes['url']
        message = config['discord']['template'].format(**attributes)
        await channel.send(message)

        return web.Response(text='success')

    app.add_routes(routes)
