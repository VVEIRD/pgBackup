#!/usr/bin/python3
#=================================================#
# Register existing Cluster to /etc/pgcluster     #
#                                                 #
# Author: Roland von Werden                       #
# Release: 0.1                                    #
# License: MIT                                    #
#=================================================#

import sys, os, getpass, subprocess, glob, configparser, re
from datetime import datetime


if getpass.getuser() != "root":
    print("This script has to be executed as root, try su - root -c 'python3 %s'" % (os.path.realpath(__file__)))
    sys.exit(1)

auto_add = False

for arg in sys.argv[1:]:
    if arg.lower() == '-a' or  arg.lower() == '--auto_add':
        auto_add = True

pgConfigs = []
pgcluster = ''
with open('/etc/pgcluster', 'r') as content_file:
    for pgcString in content_file:
        if not pgcString.startswith('#'):
            pgcluster += pgcString + '\r\n'

# Find possible postgresql configurations
for root, dirs, files in os.walk('/'):
    # Ignore hidden files
    if '.' in root:
        continue
    for file in files:
        if file == 'postgresql.conf' and root not in pgcluster:
            print('PostgreSQL configuration found: %s' % os.path.join(root, file))
            pgConfigs.append(os.path.join(root, file))

print('')

for cfgFile in pgConfigs:
    print('Add "%s" to "/etc/pgcluster"? (Y/n)' % cfgFile)
    if not auto_add:
        ch = input()
        if ch.strip().lower() == 'n':
            continue
    else:
        print("Answered Y with automatic mode")
    config_string = ''
    with open(cfgFile, 'r') as f:
        config_string = '[DEFAULT]\n'
        for cString in f:
            if not cString.startswith('#'):
                cString = re.sub(r'\#.*', '', cString).strip()
                config_String += cString + '\n'
    pgConfig = configparser.ConfigParser()
    pgConfig.read_string(config_string)
    pgData = os.sep.join(cfgFile.split(os.sep)[0:-1])
    print('Using PGDATA: %s' % pgData)
    port = 5432
    if pgConfig.has_option('DEFAULT', 'port'):
        print('Port found: %s' % pgConfig['DEFAULT']['port'])
        port = int(pgConfig['DEFAULT']['port'])
    else:
        print('Using default port 5432')
    # Try reading binaries from postmaster.opts
    pgBin = None
    postmasterOpts = os.sep.join([pgData, 'postmaster.opts'])
    if os.path.exists(postmasterOpts):
        postmaster_opts_data = ''
        with open(postmasterOpts, 'r') as f:
           postmaster_opts_data = f.read()
        pgBin = os.sep.join(postmaster_opts_data.split(' ')[0].split(os.sep)[0:-2])
    if pgBin != '':
        print('Found PG Binaries: %s' % pgBin)
    pgVersionFile = os.sep.join([pgData, 'PG_VERSION'])
    pgVersion= None
    if os.path.exists(pgVersionFile):
        pgVersion = ''
        with open(pgVersionFile, 'r') as f:
           pgVersion = f.read().strip()
    pgBackup = '1'
    print('Activate backup? (Y/n)')
    if not auto_add:
        ch = input()
        if ch.strip().lower() == 'n':
            pgBackup = '0'
    else:
        pgBackup = '0'
        print('Answered N woth automatic mode')
    print('')
    print('')
    print('Please check if the following configuration is correct:')
    print('')
    print('PostgreSQL Binaries: %s' % pgBin)
    print('            Cluster: %s' % pgData)
    print('               Port: %s' % port)
    print('            Version: %s' % pgVersion)
    print('      Active Backup: %s' % pgBackup)
    print('')
    if pgBin == None or pgVersion == None:
        print('Not all configuration could be detected, please add the cluster manually!')
        continue
    if not auto_add:
        print('Add cluster to /etc/pgcluster? (y/N)')
        ch = input()
    else:
        print('Answered Y woth automatic mode')
    if ch.strip().lower() == 'y' or auto_add:
        with open('/etc/pgcluster', 'a') as file:
            file.write('%s:%s:%s:%s:1:%s\n' % (pgData, str(port), pgBin, str(pgVersion), str(pgBackup)))