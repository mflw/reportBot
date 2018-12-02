#!/usr/bin/env python3.5 
# -*- coding: utf-8 -*-
import sys, logging
sys.path.append(".")

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s', level = logging.INFO, filename = 'report_log.log')

import pimreport, messenger, dynamic_queries, it_report, emailing
import urllib3, os, datetime, traceback
from config import help_info 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    global pr, dq, it, silent_mode

    if any(arg in sys.argv for arg in ('help', '-help', '--help')):
        #arguments list
        print(help_info)

    else:
        #clean logs
        open('report_log.log', 'w').close()
        logging.info('Start parametres: '+str(sys.argv)+' Last run - '+str(datetime.datetime.today())+'\n')
        #status report
        print('--Searching for export status..')
        pr = pimreport.report()
        
        
        # dynamic queries report
        print('--Searching for dynamic queries status..')
        dq = dynamic_queries.report(pr['catalog_generation_date'])
        
        
        #diagnostic report
        if 'it' in sys.argv:
            it_report_flag = True
            print('--Loading diagnostic information..')
        else:
            it_report_flag = pr['it_report_flag']
        it = it_report.report(it_report_flag)
        
        
        silent_mode = False
        if 'silent' in sys.argv:
            # silent mode for chat: iOS users will not receive a notification, Android users will receive a notification with no sound.
            silent_mode = True

        if len(sys.argv)==1:
            default()
        else:
            try:
                for arg in (arg for arg in sys.argv[1:] if arg not in ('it', 'silent')):
                    globals()[arg]()
            except KeyError as e:
                print(str(e) +'is not available option')
                logging.error(str(e)+'\n'+traceback.format_exc())


def default():
    #default
    messenger.send_message(pr['report']+'\n'+dq['report']+'\n'+it['report'], silent_mode, 'channel')
    if not pr['error']:
        emailing.send_message(pr['email_report']+dq['email_report'])
    send_logs()

def dbg() :
    #console debugging
    print(pr['report']+'\n'+dq['report']+'\n'+it['report'])
    if log_contain_errors():
        print('\nSome errors ocured, saved to report_log.log')

def dbgmail() :
    #console email message debugging
    if not pr['error']:
        print(pr['email_report']+dq['email_report'])
    if log_contain_errors():
        print('\nSome errors ocured, saved to report_log.log')
    
def dbgchat() :
    # global pr, dq, it
    #chat message to bot owner
    messenger.send_message(pr['report']+'\n'+dq['report']+'\n'+it['report'], silent_mode, 'debug')
    send_logs()

def alert() :
    #alert to group chat if status is not ok
    if it['alert'] is True:
        messenger.send_message(it['alert_message'], silent_mode, 'group_alert')
        send_logs()
    else:
        print("No alerts.")
        send_logs()

def chat() :
    #channel message only
    messenger.send_message(pr['report']+'\n'+dq['report']+'\n'+it['report'], silent_mode, 'channel')
    send_logs()

def mail() :
    #email message only
    if not pr['error']:
        emailing.send_message(pr['email_report']+dq['email_report'])
    send_logs()


def send_logs():
    #send log message to chatbot owner, if there are some errors in log
    if log_contain_errors():
        log = open('report_log.log', 'r')
        log_message = log.read()
        #emailing.send_log(log_message)
        messenger.send_message(log_message, False, 'log')
        log.close()


def log_contain_errors():    
    with open('report_log.log') as f:
        f.readline()
        f.readline()
        if f.readline():
            return True
    return False


if __name__ == '__main__':
    main()