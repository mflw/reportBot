#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# module: PIM reporting - Dynamic Queries refresh status
# @mzubkov
from credentials import pimclient_username, pimclient_password
from config import pim_url, pim_url_query_dynamic_queries, pim_url_query_logs
import datetime, requests, traceback, re, logging

def report(catalog_generation_date):
    err_msg = '\nНе удалось получить информацию об обновлении динамических привязок\n'
    error_trace_actual_date = ''
    error_trace_last_refresh_date = ''
    try:
        startIndex = get_startIndex()
        jobs = get_jobs(startIndex)
    except Exception as e:
        logging.error(str(e)+'\n'+traceback.format_exc())
        return {'report':err_msg, 'email_report':'<p>'+err_msg+'</p>'}
    
    try:
        last_refresh_date = get_last_date(jobs, startIndex)

        if last_refresh_date == 'более 7 дней назад.':
            actual_date = last_refresh_date
        elif (datetime.datetime.strptime(last_refresh_date,'%Y-%m-%d %H:%M') < catalog_generation_date):
            actual_date = last_refresh_date
        else:
            try:
                actual_date = get_actual_date(jobs, catalog_generation_date, startIndex)
            except Exception as e:
                actual_date = err_msg
                logging.error(str(e)+'\n'+traceback.format_exc())
    except Exception as e:
        last_refresh_date = err_msg
        logging.error(str(e)+'\n'+traceback.format_exc())
        try:
            actual_date = get_actual_date(jobs, catalog_generation_date, startIndex)
        except Exception as er:
            actual_date = err_msg
            logging.error(str(er)+'\n'+traceback.format_exc())

    report = '\nДинамические привязки к категориям были автоматически пересчитаны в PIM: {0}\nНа сайте динамические привязки к категориям от: {1}'
    report = (report.format(last_refresh_date, actual_date))

    email_report = '''<p>Динамические привязки к категориям были автоматически пересчитаны в PIM: {0}<br />
На сайте динамические привязки к категориям от: {1}</p>'''
    email_report = (email_report.format(last_refresh_date, actual_date))
    # technical issues message:
    # report = '\nПо тех причинам обновление привязок динамических категорий временно приостановлено.'
    # email_report = '<p>По тех причинам обновление привязок динамических категорий временно приостановлено.</p>'
    # manual update message
    # report = '\nНа сайте динамические привязки к категориям от: '
    # email_report = '<p>На сайте динамические привязки к категориям от: </p>'
    report = ''
    email_report = ''

    return {'report':report, 'email_report':email_report}

def get_startIndex():
    startIndex = '100'
    try:
        jobs = requests.get(pim_url.format('JobHistory', pim_url_query_dynamic_queries)+startIndex,auth=requests.\
            auth.HTTPBasicAuth(pimclient_username, pimclient_password),\
            verify=False).json()
        startIndex = int(jobs['totalSize']) - 100
        if startIndex<0:
            startIndex = '0'
        return startIndex
    except Exception as e:
        raise

def get_jobs(startIndex):
    url = pim_url.format('JobHistory', pim_url_query_dynamic_queries)+str(startIndex)
    try: 
        responce = requests.get(url,auth=requests.auth.\
            HTTPBasicAuth(pimclient_username, pimclient_password),\
            verify=False).json()
        jobs = responce['rows']
        return jobs
    except Exception as e:
        raise

def get_last_date(jobs, startIndex):
    try:
        actual_date = 'Не удалось получить данные.'
        for i in range(len(jobs),0,-1):
            if ((jobs[i-1]['values'][3]=='Completed') or i==1):
                log_identifier = jobs[i-1]['values'][7]
                if((datetime.datetime.strptime(jobs[i-1]['values'][1],'%Y-%m-%dT%H:%M:%S:%f%z')).date()<(datetime.datetime.today().date()-datetime.timedelta(days=7))):
                    return 'более 7 дней назад.'
                if(check_for_non_empty_job(log_identifier)):
                    last_date_string = jobs[i-1]['values'][1]
                    last_date = datetime.datetime.strptime(last_date_string,\
                        '%Y-%m-%dT%H:%M:%S:%f%z')
                    last_date = datetime.datetime.strftime(last_date,\
                        '%Y-%m-%d %H:%M')
                    break
            if i==1:
                startIndex = startIndex-100
                last_date = get_last_date(get_jobs(startIndex), startIndex)
        return last_date
    except Exception as e:
        raise
    raise Exception()

def check_for_non_empty_job(log_identifier):
    response = requests.get(pim_url.format('ProblemLogEntry', pim_url_query_logs.format(log_identifier)),auth=requests.auth.HTTPBasicAuth(pimclient_username, pimclient_password),verify=False).json()
    all_logs = response['rows']
    logs = [obj['values'] for obj in all_logs]
    group_number = 1
    for entity in logs:
        message = re.search('Total Structure Groups:', entity[5])
        if message is not None:
            group_number = re.search(r'\d+', entity[5]).group()
            break
    return (int(group_number)>1)

def get_actual_date(jobs, catalog_generation_date, startIndex):
    try:
        actual_date = 'Не удалось получить данные.'
        for i in range(len(jobs),0,-1):
            if (((jobs[i-1]['values'][3]=='Completed') & ((datetime.datetime.\
                strptime(jobs[i-1]['values'][2], '%Y-%m-%dT%H:%M:%S:%f%z')).\
                replace(tzinfo=None)<catalog_generation_date)) or i==1):
                log_identifier = jobs[i-1]['values'][7]
                if((datetime.datetime.strptime(jobs[i-1]['values'][1],'%Y-%m-%dT%H:%M:%S:%f%z')).date()<(datetime.datetime.today().date()-datetime.timedelta(days=7))):
                    return 'более 7 дней назад.'
                if(check_for_non_empty_job(log_identifier)):
                    actual_date_string = jobs[i-1]['values'][1]
                    actual_date = datetime.datetime.strptime(actual_date_string,\
                        '%Y-%m-%dT%H:%M:%S:%f%z')
                    actual_date = datetime.datetime.strftime(actual_date,\
                        '%Y-%m-%d %H:%M')
                    break
            if i==1:
                startIndex = startIndex-100
                actual_date = get_actual_date(get_jobs(startIndex), catalog_generation_date, startIndex)
        return actual_date
    except Exception as e:
        raise         
    raise Exception()