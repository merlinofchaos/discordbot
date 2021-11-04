import requests
from patreon.jsonapi.url_util import build_url
from patreon.utils import user_agent_string
import json
import patreon
import datetime

class TokenClient(object):
    def __init__(self, config):
        self.oauth = patreon.OAuth(config['patreon']['client_id'], config['patreon']['client_secret'])
        self.dir = config['data_directory'] + '/'
        self.redirect = config['patreon']['domain'] + '/redirect'

    ##
    # On patreon redirect, fetch the access token, get the identity and store the code.
    def validate_code(self, code):
        # Call to validate the code.
        tokens = self.oauth.get_tokens(code, self.redirect)
        if not tokens:
            return False
        # Debugging
        print(tokens)

        # Fetch identity
        client = PatreonClient(self, 0)
        uid = client.get_identity(tokens['access_token'])
        if not uid:
            return False
        self.update_user_data(uid, tokens)
        return True

    ##
    # Update user_data from Patreon token data.
    def update_user_data(self, uid, tokens):
        # Store code in identity file
        user_data = {
            'token': tokens['access_token'],
            'expires': datetime.datetime.now() + datetime.timedelta(0, tokens['expires_in']),
            'refresh': tokens['refresh_token']
        }

        self.write_user_data(uid, user_data)
        return user_data

    ##
    # Given a user_data object, get a new fresh token.
    def update_refresh_token(self, uid, user_data = None):
        if not user_data:
            user_data = self.get_user_data(uid)

        tokens = self.oauth.refresh_token(user_data['refresh'], self.redirect)
        return self.update_user_data(uid, tokens)

    ##
    # Fetch a stored token from OAuth for the requested user id.
    def get_access_token(self, uid):
        # get token from user_data
        user_data = self.get_user_data(uid)
        if user_data is None:
            return None

        # If it has expired, use refresh token to get new one and write to user_data.
        if datetime.datetime.now() > user_data['expires']:
            user_data = self.update_refresh_token(uid, user_data)

        return user_data['token']

    ##
    # Construct the filename to store a user's data in.
    def user_file_name(self, uid):
        return self.dir + '/user/' + str(uid) + '.json'

    ##
    # Fetch user_data directly from storage.
    def get_user_data(self, uid):
        try:
            with open(self.user_file_name(uid)) as infile:
                user_data = json.load(infile)
        except:
            return None

        user_data['expires'] = datetime.datetime.strptime(user_data['expires'], "%Y-%m-%d %H:%M:%S.%f")
        return user_data

    ##
    # Write updated user_data for a user.
    def write_user_data(self, uid, user_data):
        # validate user_data has all needed keys.
        for key in ['token', 'expires', 'refresh']:
            if not user_data.get(key):
                return False

        with open(self.user_file_name(uid), 'w') as outfile:
            json.dump(user_data, outfile, default=str)


class PatreonClient(object):
    def __init__(self, config, uid, tokenclient = None):
        if tokenclient is None:
            tokenclient = TokenClient(config)
        self.tokenclient = tokenclient
        self.uid = uid
        self.urlbase = "https://www.patreon.com/api/oauth2/v2/{}"

    def get_access_token(self):
        return self.tokenclient.get_access_token(self.uid)

    def get(self, url, access_token = None):
        if not access_token:
            access_token = self.get_access_token()
        return requests.get(
            self.urlbase.format(build_url(url)),
            headers = {
                'Authorization': "Bearer {}".format(access_token),
                'User-Agent': user_agent_string(),
            }
        )

    def post(self, url, json):
        return requests.post(
            self.urlbase.format(build_url(url)),
            headers={
                'Authorization': "Bearer {}".format(self.get_access_token()),
                'User-Agent': user_agent_string(),
            },
            json=json
        )

    def patch(self, url, json):
        return requests.patch(
            self.urlbase.format(build_url(url)),
            headers={
                'Authorization': "Bearer {}".format(self.get_access_token()),
                'User-Agent': user_agent_string(),
            },
            json=json
        )

    ##
    # Get the user's identity. Takes an access_token argument as optional because this
    # can be called during the process of creating an identity.
    def get_identity(self, access_token = None):
        json = self.get('identity', access_token).json()
        data = json.get('data')
        if (not data):
            return False

        attributes = data.get('attributes')
        if (not attributes):
            return False

        return attributes.get('id')

    ##
    # Get info on a webhook.
    def get_webhook_info(self):
        data = self.get('webhooks').json()
        if not data.get('data'):
            return None

        if not isinstance(data['data'], list) or len(data['data']) == 0:
            return None

        return data['data'][0]['attributes']


