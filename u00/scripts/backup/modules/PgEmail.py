#=================================================#
# Email Module to Report the result of the Backup #
# Author: Roland von Werden                       #
# Release: 0.1                                    #
# License: MIT                                    #
#                                                 #
# Changelog:                                      #
# - 13 Jan 2020:                                  #
#   __init__ and callPost now try an catch any    #
#   occuring error to display line and error and  #
#   then reraise the exception                    #
#=================================================#

import sys, os, platform
import smtplib

from email.mime.text import MIMEText


class PgEmail:
    
    """Email notification about the result of the cluster backup"""
    
    smtpDefault = 25
    smtpSecure =  465
    
    def __init__(self, config=None):
        try:
            self.config = config if config != None else {}
            self.emailRecipients = []
            self.emailRecipients = config['emailRecipients'].split(',') if 'emailRecipients' in config else []
            self.emailSender = config['emailSender'] if 'emailSender' in config else None
            self.emailUser = config['emailUser'] if 'emailUser' in config else self.emailSender
            self.emailPassword = config['emailPassword'] if 'emailPassword' in config else None
            self.emailServer = config['emailServer'] if 'emailServer' in config else None
            self.useEncryption = (config['useEncryption'].strip().lower() == 'true') if 'useEncryption' in config else False
            try:
                self.port = int(config['port']) if 'port' in config else (self.smtpDefault if not self.useEncryption else self.smtpSecure)
            except ValueError:
                self.port = self.smtpDefault if not self.useEncryption else self.smtpSecure
                print('PgEmail: Configuration error - "port" in /etc/pgbackup is not an integer!')
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
                print('  If "emailUser" is not set, "emailSender" will be used')
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                print('=================================================')
                self.ready=False
            else:
                self.ready=True
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('An unexpected error occurd while loading PgEmail', exc_type, fname, exc_tb.tb_lineno)
            raise e
    
    def runPreBackup(self):
        return False
    
    def runPostBackup(self):
        return True
    
    def get_backup_size(self, start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def callPre(self, clusterEntry, backupLocation, startTime, backupCopyLocation=None, walArchiveLocation=None):
        raise NotImplementedError('This Module has no pre backup call')
    
    def callPost(self, clusterEntry, backupLocation, backupResult, startTime, endTime, backupCopyLocation=None, walArchiveLocation=None, walArchiveBackupResult=None):
        try:
            elapsed = int((endTime - startTime).total_seconds())
            messageText  = '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
            messageText += '~~             PostgreSQL Backup            ~~\r\n'
            messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
            messageText += 'Server:     %s\r\n' % platform.node()
            messageText += 'Binaries:   %s\r\n' % clusterEntry[2]
            messageText += 'Cluster:    %s\r\n' % clusterEntry[0]
            messageText += 'Port:       %s\r\n' % clusterEntry[1]
            messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
            messageText += '~~                   Backup                 ~~\r\n'
            messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
            messageText += 'Start:      %s\r\n' % startTime.strftime("%Y-%m-%d %H:%M:%S")
            messageText += 'End:        %s\r\n' % endTime.strftime("%Y-%m-%d %H:%M:%S")
            messageText += 'Location:   %s\r\n' % backupLocation
            messageText += 'Result:     %s\r\n' % backupResult
            messageText += 'WAL Backup: %s\r\n' % (walArchiveBackupResult if walArchiveBackupResult != None else 'NA')
            messageText += 'Size:       %s MB\r\n' % str(int(self.get_backup_size(backupLocation)/(1024*1024)))
            messageText += 'Duration:   %s s\r\n' % str(elapsed)
            messageText += '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\r\n'
            subject = 'Backup on %s for cluster %s: %s' % (platform.node(), clusterEntry[0], backupResult)
            message = MIMEText(messageText)
            message['subject'] = subject
            message['From'] = self.emailSender.replace('$h', platform.node())
            message['To'] = ','.join(self.emailRecipients)
            smtp = smtplib.SMTP(host=self.emailServer, port=self.port) if not self.useEncryption else smtplib.SMTP_SSL(host=self.emailServer, port=self.port)
            if self.emailPassword != None:
                smtp.login(user=self.emailUser, password=self.emailPassword)
            smtp.send_message(message)
            smtp.close()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('An unexpected error occurd while sending  the email:', exc_type, fname, exc_tb.tb_lineno)
            raise e
