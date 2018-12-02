#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# module: Email reporting
# @mzubkov
import sys, smtplib
sys.path.append(".")

from credentials import mailfrom, mailto, mailto_log, mailserv
from config import mailsubject, mail_bottom, mail_sign
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback, logging

def send_message(message):
    print("--Starting email connection..")
    
    try:
        smtpObj = smtplib.SMTP(mailserv)
        smtpObj.starttls()
    except Exception as e:
        logging.error(str(e)+traceback.format_exc())
        print('Error while estabilishing connection with SMTP, log saved to file report_log.log')
    
    else:
        try:    
            print("--Sending email report..")

            mail = MIMEMultipart()
            mail['From'] = mailfrom
            mail['To'] = mailto 
            mail['Subject'] = mailsubject
            
            report = message+mail_bottom+mail_sign
            
            mail.add_header('Content-Type', 'text/html')
            mail.attach(MIMEText(report, 'html'))
            smtpObj.send_message(mail)
            smtpObj.quit()
            print("\nEmail report successfully sent.")
        except Exception as e:
            logging.error(str(e)+traceback.format_exc())
            print('Error while sending message, log saved to file report_log.log')

def send_log(log_message):
    try:
        smtpObj = smtplib.SMTP(mailserv)
        smtpObj.starttls()
    except Exception as e:
        logging.error(str(e)+'\n'+traceback.format_exc())
        print('Error while estabilishing connection with SMTP, log saved to file report_log.log')
    else:
        try:    
            print("\n\n--Sending log email..")

            mail = MIMEMultipart()
            mail['From'] = mailfrom
            mail['To'] = mailto_log
            mail['Subject'] = "Log pimreport"
            mail.attach(MIMEText(log_message, 'plain'))
            smtpObj.send_message(mail)
            smtpObj.quit()
            print("\nLog email successfully sent.")
        except Exception as e:
            logging.error(str(e)+traceback.format_exc())
            print('Error while sending log message, log saved to file report_log.log')