"""
pifi

Usage:
  pifi status
  pifi add <ssid> [<password>]
  pifi list seen
  pifi list pending
  pifi --version

Options:
  -h --help    Show this help
  --version    Show pifi version

"""
from docopt import docopt

import NetworkManager
import json
import os

import pifi.nm_helper as nm
import pifi.var_io as var_io

import uuid

def status(exit=exit, nm=nm):
    devices = 0

    for ApModeDevice in nm.managedAPCapableDevices():
        devices += 1
        print("Network Mangager reports AP mode support on %s" % ApModeDevice.Interface)
        if ApModeDevice.State != 100:
            print("Device is not activated")
            exit(0)
        current_connection = ApModeDevice.GetAppliedConnection(0)
        if current_connection[0]['802-11-wireless']['mode'] == "ap":
            print("Device is currently acting as an Access Point")
        else:
            ssid = current_connection[0]['802-11-wireless']['ssid']
            ssid = bytearray([ord(byte) for byte in ssid])
            print("Device is connected to %s" % ssid.decode("utf-8"))

    if (devices == 0):
        print("ERROR: Network Manager reports no AP mode support on any managed device")
        exit(2)

def add(ssid, password, var_io=var_io):
    pending = var_io.readPendingConnections()

    if password is not None:
        new_connection = {
                'connection': {
                    'id': str(ssid),
                    'type': '802-11-wireless',
                    'autoconnect': True,
                    'uuid': str(uuid.uuid4())
                },

                '802-11-wireless': {
                    'mode': 'infrastructure',
                    'security': '802-11-wireless-security',
                    'ssid': ssid
                },

                '802-11-wireless-security': {
                    'key-mgmt': 'wpa-psk', # We only support WPA2-PSK networks for now
                    'psk': password
                },

                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
        }

    else:
        new_connection = {
                'connection': {
                    'id': str(ssid),
                    'type': '802-11-wireless',
                    'autoconnect': True,
                    'uuid': str(uuid.uuid4())
                },

                '802-11-wireless': {
                    'mode': 'infrastructure',
                    'ssid': ssid
                },

                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
        }


    pending.append(new_connection)

    try:
        var_io.writePendingConnections(pending)
    except PermissionError:
        print("Error writing to /var/lib/pifi/pending, make sure you are running with sudo")

def list_seen():
    for ssid in var_io.readSeenSSIDs():
        print(ssid)

def list_pending():
    for con in var_io.readPendingConnections():
        try:
            print(con['802-11-wireless']['ssid'])
        except KeyError:
            print("WARN: Found non wireless pending connection: %s" % 
                    con['connection']['id'])

def main():
    arguments = docopt(__doc__, version='pifi version 0.3.0')
    
    if arguments['status']:
        status()
    if arguments['add']:
        if '<password>' is not None:
            add(arguments['<ssid>'], arguments['<password>'])
        else:
            add(arguments['<ssid>'], None)
    if arguments['list'] and arguments['seen']:
        list_seen()
    if arguments['list'] and arguments['pending']:
        list_pending()
