#!/usr/bin/python3
#=================================================#
# PostgreSQL Backup software.                     #
#                                                 #
# Author: Roland von Werden                       #
# Release: 0.1                                    #
# License: MIT                                    #
#=================================================#

import os, getpass, sys, subprocess, glob, configparser
from datetime import datetime

if getpass.getuser() != "postgres":
    print("The backup has to be executed as user postgres, try su - postgres -c 'python3 %s'" % (os.path.realpath(__file__)))
    sys.exit(1)

def pg_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

baseDir = os.path.dirname(os.path.realpath(__file__))

print("==============================================================")
print(" ==                                                        ==")
print(" ==      P O S T G R E S Q L   1 2   B A C K U P           ==")
print(" ==                                                        ==")
print(" == Author:    Roland von Werden                           ==")
print(" == License:   MIT                                         ==")
print(" == Version:   0.1                                         ==")
print("==============================================================")

pgConfig = configparser.ConfigParser()
pgConfig.read_file(open('/etc/pgbackup'))

pgBackupBase = pgConfig['DEFAULT']['backup_base']          if pgConfig.has_option('DEFAULT', 'backup_base') else '/u99/pgbackup'
pgWalArchiveBase = pgConfig['DEFAULT']['wal_archive_base'] if pgConfig.has_option('DEFAULT', 'wal_archive_base') else '/u99/pgarchive'

# Import all module paths
if pgConfig.has_option('DEFAULT', 'module_paths'):
    for pgModPath in pgConfig['DEFAULT']['module_paths'].split(','):
        sys.path.insert(0,pgModPath.strip())

#Load modules
pgModulesPre = {}
pgModulesPost = {}
if pgConfig.has_option('DEFAULT', 'load_modules'):
    for pgMod in pgConfig['DEFAULT']['load_modules'].split(','):
        print ('Loading module: %s' % pgMod)
        try:
            modConfig = pgConfig[pgMod] if pgConfig.has_section(pgMod) else []
            mod = __import__(pgMod, fromlist=[pgMod])
            klass = getattr(mod, pgMod)
            # klass = pg_import('%s.%s' % (pgMod, pgMod))
            pgModule = klass(config=modConfig)
            if pgModule.runPreBackup():
                pgModulesPre[pgMod] = pgModule;
            if pgModule.runPostBackup():
                pgModulesPost[pgMod] = pgModule;
        except:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Error loading module: %s" % pgMod)
            print("Please correct the problem and try again")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
pgcluster = open('/etc/pgcluster')
OS_PATH = str(os.environ['PATH'])
for pgcString in pgcluster:
    startTime = datetime.now()
    clusterEntry = pgcString.split(':')
    # Backup is disabled for this cluster
    if pgcString.startswith('#') or len(clusterEntry) > 5 and clusterEntry[5].strip() == "0":
        if not pgcString.startswith('#'):
            print("Skipping backup for cluster %s" % (clusterEntry[0]))
            print("==============================================================")
        continue
    print("Starting backup for cluster %s" % (clusterEntry[0]))
    print("==============================================================")
    pgData = clusterEntry[0]
    pgPort = clusterEntry[1]
    pgBin = clusterEntry[2]
    pgBackup = '%s/%s/tsm/'       % (pgBackupBase,     pgPort)
    pgBackupCopy = '%s/%s/local/' % (pgBackupBase,     pgPort)
    pgWalArchive = '/%s/%s/'      % (pgWalArchiveBase, pgPort)
    os.environ['PATH'] = OS_PATH + os.pathsep + pgBin + '/bin'
    os.environ['PGDATA'] = pgData
    os.environ['PGPORT'] = pgPort
    pgBackupResult = 'ERROR'
    pgBackupArchivedWal = 'ERROR'
    # TODO
    # Implement Pre Backup Call
    # Delete local backup
    subprocess.call(['rm'] + glob.glob('%s*.tar.gz' % (pgBackupCopy)))
    # Backup pgdata
    if 0 == subprocess.call(['%s/bin/pg_basebackup' % (pgBin), '--pgdata=%s' % (pgBackup), '--format=t', '--gzip', '--compress=4', '--progress', '--verbose']):
        pgBackupResult = 'OK'
    # Backup archived wal files
    if 0 == subprocess.call(['tar', '-czf', '%s/archived_wal_%s.tar.gz' % (pgBackup, datetime.now().strftime("%Y_%m_%d_%H_%M")), pgWalArchive]):
        pgBackupArchivedWal = 'OK'
        # Delete all archived wal files that are older than 2 days
        subprocess.call(['find', pgWalArchive, '-mtime', '+2', '-exec', 'rm', '{}', ';'])
    # Hard link generated backups to local copy
    print('Hard Linking %s to %s' % (pgBackup, pgBackupCopy))
    subprocess.call(['cp', '-avl'] + glob.glob('%s*.tar.gz' % (pgBackup)) + [pgBackupCopy])
    endTime = datetime.now()
    elapsed = endTime - startTime
    for mod in pgModulesPost:
        try:
            modPost = pgModulesPost[mod]
            modPost.callPost(clusterEntry=clusterEntry, backupLocation=pgBackup, backupResult=pgBackupResult, startTime=startTime, endTime=endTime, backupCopyLocation=pgBackupCopy, walArchiveLocation=pgWalArchive, walArchiveBackupResult=pgBackupArchivedWal)
        except Exception as e:
            print('Error calling module: %s' % str(modPost))
            print(e)
    with open ('%s/logs/pgbackup.log' % (baseDir), 'a') as backup_log:
        backup_log.write('%s:%s:%s:%s:%s\n' % (pgData, startTime.strftime("%Y-%m-%d-%H.%M.%S"),  int(elapsed.total_seconds()), pgBackupResult, pgBackupArchivedWal))
    print('Backup completed: %s in %d seconds' % (pgBackupResult, elapsed.total_seconds()))
    print('Backup of Wal Archive completed: %s' % (pgBackupArchivedWal))
    print("==============================================================")

os.environ['PATH'] = OS_PATH
os.environ['PGDATA'] = ''
os.environ['PGPORT'] = ''


