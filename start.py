#!/usr/bin/env python

import argparse
import json
from datetime import datetime, timedelta

from pathlib import Path
tokens_file = tokens_file = (Path(__file__).parent / 'tokens.json').as_posix()

def fetch_results(config):
    import requests
    from bs4 import BeautifulSoup
    url = 'https://signon.aau.dk/cas/login?service=http://wifipassword.aau.dk/oneday'


    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = {
        'username': config['username'],
        'password': config['password'],
        'execution': soup.find('input', attrs={'name':'execution'}).get('value'),
        '_eventId': 'submit',
        'geolocation': '',
        'submit': 'LOGIN',
    }

    r2 = requests.post(url, data=data)
    r2.raise_for_status()

    soup2 = BeautifulSoup(r2.text, 'html.parser')

    results = {}
    for row in soup2.find_all('tr'):
        aux = row.find_all('td')
        if len(aux) != 0:
            parsed_date = datetime.strptime(aux[1].string, '%d/%m/%Y')
            date = parsed_date.strftime('%Y-%m-%d')
            results[date] = aux[0].string
    return results

def run_nmcli_cmd(params):
    import subprocess
    cmd = ['nmcli'] + params

    result = subprocess.run(cmd, capture_output=True, check=True, env={'LANG': 'C'})
    return result.stdout.decode('utf-8').strip()

def fetch_current_password(connection_profile):

    cmd = [
        '-g', #get value
        '802-11-wireless-security.psk', #password
        'connection', #the connection
        'show', #show
        '--show-secrets', #enable printing of password
        connection_profile, #the connection profile
    ]
    return run_nmcli_cmd(cmd)

def set_current_password(connection_profile, password):

    cmd = [
        'connection',
        'modify',
        connection_profile,
        '802-11-wireless-security.psk',
        password,
    ]
    return run_nmcli_cmd(cmd)

def add_connection(connection_profile, password):
    cmd [
        'dev',
        'wifi',
        'connect',
        connection_profile,
        'password',
        password,
    ]
    run_nmcli_cmd(cmd)

def read_config():
    global tokens_file
    import json
    try:
        with open(tokens_file, 'r') as f:
            config = json.load(f)
    except:
        config = {}
    return config

def write_config(new_config):
    global tokens_file
    new_config.pop('show_password')

    with open(tokens_file, 'w') as json_file:
        json.dump(new_config, json_file, indent=2)

def ask_user_input(config):
    from getpass import getpass
    if config['username'].strip() == '':
        config['username'] = input('Username: ')
    if config['password'].strip() == '':
        config['password'] = getpass()
    if config['connection'].strip() == '':
        newval = input('Connection name (Default: AAU-1-DAY):')
        if newval == '':
            newval = 'AAU-1-DAY'
        config['connection'] = newval

def check_for_wifi_passwords(config, today, next_day):
    wifidict = config['wifipassword']
    if today not in wifidict or next_day not in wifidict:
        config['wifipassword'] = fetch_results(config)

def print_wifi_password(config):
    if config['show_password'] is not True:
        return
    if len(config['wifipassword']) == 0:
        print('No wifipasswords found')
    print('Upcoming wifipasswords')
    for k, v in config['wifipassword'].items():
        print(f'  {k}: "{v}"')

def nmcli_set_password(config, todays_date):
    print('todo')
    #if not wifi_exists
    # create_wifi
    #else
    # get_password
    # if not password == old password:
    #   set_password(new_password)

def build_config(args):
    default_config = {
        'username': '',
        'password': '',
        'connection': '',
        'show_password': False,
        'wifipassword': {}
    }
    config = read_config()
    for k, v in config.items():
        default_config[k] = v
    for k, v in vars(args).items():
        if v is not None:
            default_config[k] = v
    ask_user_input(default_config)
    return default_config

def parse_nmcli_show():
    print('TODO')
    #for l in lines:
    #    if l.startswith('802-11-wireless.ssid'):
    #        value = l.split(':', 1)[1].strip()
    #        break



def run(args):

    config = build_config(args)
    todays_date = datetime.today().strftime('%Y-%m-%d')
    upper_limit_date = (datetime.today() + timedelta(days=3)).strftime('%Y-%m-%d')
    check_for_wifi_passwords(config, todays_date, upper_limit_date)
    # nmcli_set_password(config, todays_date)
    print_wifi_password(config)
    write_config(config)


parser = argparse.ArgumentParser(description='Connects to 1-day wifi')
parser.add_argument('--username', '-u', nargs='?', type=str, help='The username for the user which have access to the password site.')
parser.add_argument('--password', '-p', nargs=1, type=str, help='The password for the user which have access to the password site.')
parser.add_argument('--connection', '-c', nargs=1, type=str, help='The name of the connection to use.')
parser.add_argument('--show-password', '-s', help='Print the wifipassword', action=argparse.BooleanOptionalAction)

args = parser.parse_args()

run(args)

