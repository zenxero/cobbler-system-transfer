#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# cobbler-system-transfer.py
#
# This python script will get a list of systems from one cobbler server
# and add them to another cobbler server using the cobbler API.
# This program mostly serves as an example of how to work with the API and
# won't work for every use case.

# Import modules
import sys
import xmlrpc.client
import json
import getpass

# Define old cobbler server api URL
oldcobbler = xmlrpc.client.Server("http://my-old-cobbler-server/cobbler_api")

# Define new cobbler server api URL
newcobbler = xmlrpc.client.Server("https://my-new-cobbler-server/cobbler_api")

# Prompt for cobbler username and password
user=input("Enter cobbler user name: ")
password=getpass.getpass("Enter password: ")

# Attempt a login via the api with provided credentials and fail out if we
# can't make a connection. We don't need to login to read the data out of the API,
# but we need valid credentials to add new entries.
try:
    token = newcobbler.login(user, password)
except:
    print("ERROR: Unable to login to newcobbler server with provided credentials")
    sys.exit(1)

# Attempt to get the system list from the new cobbler server and error out if
# we can't get the list. We get the list of systems so that we can check to
# see if the system already exists in the new cobbler server. If it does, we
# skip adding it.
try:
    newsystems = newcobbler.get_systems(token)
except:
    print("ERROR: Couldn't get list of systems from the newcobbler")
    sys.exit(1)

# Get the list of systems from the old cobbler server
for system in oldcobbler.get_systems():

    # Get all systems from the old cobbler where the hostname starts with the hostname "compute"
    if system['name'].startswith('compute'):

        # Get the MAC address and hostname of the systems in the old cobbler server
        # that match
        hostname = system['name']
        macaddr = system['interfaces']['eth0']['mac_address']

        # For this use case, we set the profile, env, and ks_meta as static values
        # We set the netboot value to "False" as well as the management class values
        profile = 'centos7'
        netboot = 'False'
        environment = 'research'
        metadata = {'ou': 'research_group'}
        classes = ['condor_node', 'docker_ce']

        # If any of the system hostnames in the new cobbler server don't match the
        # names that we pulled from the old cobbler server, then continue adding
        # the systems to the new cobbler server.
        if not any(machine.get('name') == system['name'] for machine in newsystems):
            print(f"Adding machine {hostname} to new cobbler server")

            # Try to add the systems to the new cobbler server and throw an error if
            # any of them couldn't be added.
            try:
                newsystem = newcobbler.new_system(token)
                newcobbler.modify_system(newsystem, 'name', hostname, token)
                newcobbler.modify_system(newsystem, 'modify_interface', {"macaddress-eth0": macaddr,}, token)
                newcobbler.modify_system(newsystem, 'profile', profile, token)
                newcobbler.modify_system(newsystem, 'netboot_enabled', netboot, token)
                newcobbler.modify_system(newsystem, 'env', environment, token)
                newcobbler.modify_system(newsystem, 'ks_meta', metadata, token)
                newcobbler.modify_system(newsystem, 'mgmt_classes', classes, token)
                newcobbler.save_system(newsystem, token)
            except:
                print(f"ERROR: Couldn't add newsystem {hostname} to newcobbler")
        # If the system already exists in the new cobbler server, print a warning that
        # we're skipping adding it.
        else:
            print(f"WARNING: Machine {hostname} already exists in new cobbler server, skipping...")

# Logout of the cobbler api
newcobbler.logout(token)
