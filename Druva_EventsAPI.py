# encoding=utf8
# -*- coding: utf-8 -*-

'''-----------------------------------------------------------------
Script usage: python.exe Druva_EventsAPI.py eventsConfiguration.cfg
Refer here: https://developer.druva.com/reference#get_eventmanagement-v2-events
--------------------------------------------------------------------'''

import configparser
import requests
import oauthlib
import time
import json
import csv 
import base64
import sys
import urllib
from urllib.parse import urlparse
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

'''
Note: Parses values from the input configuration file that is passed as args to this script
    1. Specify the 'output_location' in the config file where you want to see the output.
    2. Specify the 'output_format' in the config file  Supported formats: CEF,Syslog, CSV.
    3. Leave the 'trackerstring' empty, it gets auto-updated everytime the script runs.
'''
#------------------ Parse Config file values ----------------#
configFileLocation = sys.argv[1]
config_orig = configparser.ConfigParser()
config_orig.read(configFileLocation, encoding='utf-8'   )
config = dict(config_orig.items('Config'))
url = config['url']
api_url = config['api_url']
output_format = config['output_format']
output_location = config.get('output_location', '')
accessTokenURL = config['tokenurl']
trackerString =  config.get('trackerstring', '')

#----------Determine output file type--------------------#
is_csv = False
output_file = output_location + "inSync_events_" + time.strftime("%m_%d_%Y_%H_%M_%S",time.localtime(time.time())) + '.log'
if output_format=='CEF':
    api_url += '?format=CEF'
elif output_format=='Syslog':
    api_url += '?format=Syslog'
elif output_format=='CSV':
    is_csv = True
    output_file = output_file.strip('.log') + '.csv'

def create_session(access_token):
    s = requests.Session()
    s.headers.update({'Authorization': 'Bearer ' + access_token})
    #s.auth = (username, token)
    return s

def close_session(s):
    s.close()

#----------Generate Auth Token--------------------#
def get_token(client_id, secret_key):
    auth = HTTPBasicAuth(client_id, secret_key)
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    response = oauth.fetch_token(token_url="https://apis.druva.com/token", auth=auth)
    auth_token = response["access_token"]
    expires_at = response["expires_at"]
    return auth_token

#----------Write output to file--------------------#
def write_csv(f, events):
    fieldnames = events[0].keys()       #Getting fieldnames purposely from JSON response to automatically accomodate any future addition of headers. It will create new csv columns on the fly.
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for event in events:
        try:
            writer.writerow(event)
            # f.write(str(event).decode('utf-8'))
            # f.write('\n')
        except Exception as e:
            print (e)
            print (event)

def write_cef_syslog(f, events):
    for event in events:
        try:
            f.write(str(event))
            f.write('\n')
        except Exception as e:
            print (e)
            print (event)

def write_output(f, events):
    if is_csv:
        write_csv(f, events)
    else:
        write_cef_syslog(f, events)

#----------update tracker string to begin polling from the latest events--------------------#

def update_tracker(trackerString):

    with open(configFileLocation, 'w+') as configFile:
        config_orig.set('Config', 'trackerString', trackerString)
        config_orig.write(configFile)

#----------Retrieve events from Events API--------------------#
def _retrieve_events(f, s, tracker=False, trackerString=None):
    nextPageExists = None
    get_events = None
    while True:
        try:
            #construct URL
            if trackerString:
                get_events = s.get(url + api_url + "&tracker=" + urllib.parse.quote(trackerString))
            else:
                get_events = s.get(url + api_url)

            #parse response
            if get_events.status_code == 200:
                events=get_events.json()['events']
                nextPageExists = get_events.json()['nextPageExists']
                trackerString = get_events.json()['tracker']
            else:
                print ('Failure while getting events. [ERROR CODE] :', get_events.status_code)
                break
            
            #write output to file
            write_output(f, events)
            if not nextPageExists:
                update_tracker(trackerString)
                print ("-----End of events Response-----")
                print ("-----Please see the output_location mentioned in the config file for output data.")
                break
        except Exception as e:
            print ('Exception occurred while accesssing inSync Events. Exception : ', e)

'''
Sequence of Execution:
----------------------
    1. Read configuration values from 'eventsNew.cfg'
    2. Generate Auth Token/credentials
    3. Create Session
    4. Hit Druva Events API endpoint and poll for events
    5. Write data from events stream to output file.
'''

def retrieve_events(f):
    #For help on how to generate a clientID and Secret Key, please refer the Druva API Docs at below:
    #https://docs.druva.com/Druva_Cloud_Platform/Integration_with_Druva_APIs/Create_and_Manage_API_Credentials

    clientID = " "
    secretKey = " "
    
    access_token= get_token(clientID, secretKey)
    s = create_session(access_token)
    if(trackerString):
        _retrieve_events(f,s, True,trackerString)
    else:
        _retrieve_events(f, s, False)
    close_session(s)


def main():
    with open(output_file, 'w') as f:
        retrieve_events(f)

if __name__ == '__main__':
    main()


