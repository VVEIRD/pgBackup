#=================================================#
# Template module for developing new modules      #
# Author: Roland von Werden                       #
# Release: 0.1                                    #
# License: MIT                                    #
#=================================================#

class Template
    
    """Template module"""
    
    def __init__(self, config=None):
        print ('Nothing to do')
    
    def runPreBackup(self):
        return False
    
    def runPostBackup(self):
        return False
    
    def callPre(self, clusterEntry, backupLocation, startTime, backupCopyLocation=None, walArchiveLocation=None):
        raise NotImplementedError('This Module has no pre backup call')
    
    def callPost(self, clusterEntry, backupLocation, backupResult, startTime, endTime, backupCopyLocation=None, walArchiveLocation=None, walArchiveBackupResult=None):
        raise NotImplementedError('This Module has no post backup call')

