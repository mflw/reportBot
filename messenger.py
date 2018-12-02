#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

from config import chat_url, socks5
from credentials import test123_bot_token, pimreport_token, pim_channel_id, pim_group_id, my_chat_id
import  requests, time, logging, traceback


def send_message(text, silent_mode, notification_type):

    if notification_type == 'channel':
        chat = pim_channel_id
        token = test123_bot_token

    elif notification_type == 'group_alert':
        chat = pim_group_id
        token = pimreport_token

    elif notification_type == 'debug':
        chat = my_chat_id
        token = pimreport_token

    elif notification_type == 'log':
        chat = my_chat_id
        token = pimreport_token
    
    url = chat_url+token+'/'

    print('--Sending '+notification_type+' chat message')
    try:
        params = {'chat_id': chat, 'text': text, 'parse_mode':'HTML', 'disable_notification':silent_mode}
        r = requests.post(url+'sendMessage', json=params, proxies=dict(http='',\
            https=socks5))
        return r.json()
    except Exception as e:
        print("\nSome error ocured while sending chat message, saved to report_log.log")
        logging.error(str(e)+'\n'+traceback.format_exc())


# def get_updates_json(request):
#     r = requests.get(request + 'getUpdates', proxies=dict(http='',\
#         https=socks5))
#     return r.json()

# def last_update(data):  
#     results = data['result']
#     total_updates = len(results) - 1
#     return results[total_updates]

# def get_chat_id(update):  
#     chat_id = update['message']['chat']['id']
#     return chat_id