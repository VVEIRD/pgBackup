#=================================================#
# Email Module to Report the result of the Backup #
# Author: Roland von Werden                       #
# Release: 0.1                                    #
# License: MIT                                    #
#=================================================#
import os, platform
import smtplib

from email.mime.text import MIMEText


class PgEmail:
    
    """Email notification about the result of the cluster backup"""
    
    smtpDefault = 25
    smtpSecure =  465
    
    def __init__(self, config=None):
        self.config = config if config != None else {}
        self.emailRecipients = []
        self.emailRecipients = config['emailRecipients'].split(',') if 'emailRecipients' in config else []
        self.emailSender = config['emailSender'] if 'emailSender' in config else None
        self.emailUser = config['emailUser'] if 'emailUser' in config else self.emailSender
        self.emailPassword = config['emailPassword'] if 'emailPassword' in config else None
        self.emailServer = config['emailSender'] if 'emailSender' in config else None
        self.useEncryption = config['useEncryption'] if 'useEncryption' in config else False
        self.port = int(config['port']) if 'port' in config else (self.smtpDefault if not self.useEncryption else self.smtpSecure)
        if config != None and 'debug' in config:
            print('=================================================')
            print('PgEmail Configuration')
            print('-------------------------------------------------')
            print('Recipients:     %s' % config['emailRecipients'] if 'emailRecipients' in config else 'NA')
            print('Sender:         %s' % self.emailSender)
            print('Server:         %s' % self.emailServer)
            print('Use encryption: %s' % self.useEncryption)
            print('Port:           %s' % str(self.port))
            print('=================================================')
        if (len(self.emailRecipients) == 0 
              or self.emailServer == None
              or self.emailSender == None):
            print('=================================================')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('ERROR! Not all necessary configuration items are present in /etc/pgbackup.')
            print('Please make sure the following parameter are set in the section "PgEmail":')
            print('  "emailRecipients"')
            print('  "emailSender"')
            print('  "emailServer"')
            print('  "useEncryption"')
            print('  "port"')
            print('  If you need a password to login to your emailing server, please use')
            print('    "emailUser" and "emailPassword"')
            print('  Ff "emailUser" is not set, "emailSender" will be used')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print('=================================================')
            self.ready=False
        else:
            self.ready=True
    
    def runPreBackup(self):
        return False
    
    def runPostBackup(self):
        return True
    
    def get_backup_size(start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def callPost(self, clusterInformation, backupLocation, backupCopyLocation, backupResult, walArchiveLocation=None, walArchiveBackupResult=None):
        messageText  = '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
        messageText += '~~             PostgreSQL Backup            ~~\r\n'
        messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
        messageText += 'Server:   %s\r\n' % platform.node()
        messageText += 'Binaries: %s\r\n' % clusterEntry[2]
        messageText += 'Cluster:  %s\r\n' % clusterEntry[0]
        messageText += 'Port:     %s\r\n' % clusterEntry[1]
        messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
        messageText += '~~                   Backup                 ~~\r\n'
        messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
        messageText += 'Location:   %s\r\n' % backupLocation
        messageText += 'Result:     %s\r\n' % backupResult
        messageText += 'WAL Backup: %s\r\n' % (walArchiveBackupResult if walArchiveBackupResult != None else 'NA')
        messageText += 'Size:       %s MB\r\n' % str(int(get_backup_size(backupLocation)/(1024*1024)))
        messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
        subject = 'Backup on %s for cluster %s: %s' % (platform.node(), clusterEntry[0], backupResult)
        message = MIMEText(messageText)
        message['subject'] = subject
        message['From'] = self.emailSender
        message['To'] = self.emailRecipients
        smtp = smtplib.SMTP(host=self.emailServer, port=self.port) if not self.useEncryption else smtplib.SMTP_SSL(host=self.emailServer, port=self.port)
        if self.emailPassword != None:
            smtp.login(user=self.emailUser, password=self.emailPassword)
        smtp.send_message(message)
        smtp.close()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        