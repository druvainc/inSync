import requests
import time
import traceback

# Import Libs required for Bearer Token OAuth2.0
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

# https://developer.druva.com/docs/get-bearer-token
client_id = 'INVsCjjfIfKTATq0+2wUtoFfh9aixfnn'
secret_key = 'xNvNBWKJKYSQsrhMejJ1UFZD1+HNyONr'

# 
api_url = "https://apis.druva.com/"

# https://developer.druva.com/reference#reference-getting-started
def get_token(client_id, secret_key):
	global auth_token
	auth = HTTPBasicAuth(client_id, secret_key)
	client = BackendApplicationClient(client_id=client_id)
	oauth = OAuth2Session(client=client)
	response = oauth.fetch_token(token_url='https://apis.druva.com/token', auth=auth)
	auth_token = response['access_token']
	expires_at = response['expires_at']


#
def get_api_call(auth_token, api_url, api_path):
    nextpage = None
    while True:
        # print nextpage
        nextpage = _get_api_call(auth_token, api_url, api_path, nextpage)
        if not nextpage:
            break
#
def _get_api_call(auth_token, api_url, api_path, nextpage):
    headers = {'accept': 'application/json', 'Authorization': 'Bearer ' + auth_token}
    response = requests.get(api_url+api_path, headers=headers, params={'pageToken':nextpage})
    try:
        print 'Invoking API call'
        if response.status_code == 200:
            print response.json()
            return response.json()['nextPageToken']
        elif response.status_code == 429:
            print 'Sleeping for 60 seconds'
            time.sleep(60)
            return _get_api_call(auth_token, api_url, api_path, nextpage)
        else:
            print 'Failure occured in API call.'
            print '[ERROR CODE] : ', response.status_code
    except Exception as e:
        print traceback.format_exc()

#
get_token(client_id, secret_key)
print 'Auth_token: ', auth_token

########################################################################
# inSync: API call to List all Users.
print 'List all Users.'
api_path = "insync/usermanagement/v1/users"
get_api_call(auth_token, api_url, api_path)

# inSync: API call to List all Profiles.
print 'List all Profiles.'
api_path = "insync/profilemanagement/v1/profiles"
get_api_call(auth_token, api_url, api_path)

# inSync: API call to List all Devices.
print 'List all Devices.'
api_path = "insync/endpoints/v1/devices"
get_api_call(auth_token, api_url, api_path)

# inSync: API call to List all Devices Backups (Last Successful Bbackups).
print 'List all Devices Backups.'
api_path = "insync/endpoints/v1/backups"
get_api_call(auth_token, api_url, api_path)

# inSync: API call to List all Devices Restore activities.
print 'List all Devices Restore activities.'
api_path = "insync/endpoints/v1/restores"
get_api_call(auth_token, api_url, api_path)

# inSync: API call to List all Storages.
print 'List all Storages.'
api_path = "insync/storagemanagement/v1/storages"
get_api_call(auth_token, api_url, api_path)
########################################################################

