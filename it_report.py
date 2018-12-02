#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
# module: Diagnostic report
# @mzubkov
from credentials import pimclient_username, pimclient_password, basic_username, basic_password
from config import it_report, pim_url, pim_url_query_catalog, pim_url_query_filters, pim_url_query_categories, \
pim_url_query_logs, graylog_url_catalog, graylog_date, graylog_alias_swap_catalog, graylog_url_catalog_all_messages, \
graylog_url_catalog_error, alert_template, alert_no_export
from datetime import datetime, timedelta
import requests, re, traceback, logging

def report(it_report_flag):
    def_result = {'status':'Ошибка получения данных', 'file_name':'Ошибка', 'errors':' ', 'scheduled':'Не удалось получить данные по запросу', \
    'graylog':'Ошибка получения данных', 'export_date':''}
    try:
        export_pim_catalog = last_export_status(pim_url_query_catalog, it_report_flag)
    except Exception as e:
        logging.error(str(e)+'\n'+traceback.format_exc())
        export_pim_catalog = def_result
    try:
        export_pim_filters = last_export_status(pim_url_query_filters, it_report_flag)
    except Exception as e:
        logging.error(str(e)+'\n'+traceback.format_exc())
        export_pim_filters = def_result
    try:
        export_pim_categories = last_export_status(pim_url_query_categories, it_report_flag)
    except Exception as e:
        logging.error(str(e)+'\n'+traceback.format_exc())
        export_pim_categories = def_result

    alert = False
    alert_message = '<b>ALERT:</b> '

    catalog_scheduled_date = export_pim_catalog['scheduled']
    filters_scheduled_date = export_pim_filters['scheduled']
    categories_scheduled_date = export_pim_categories['scheduled']

    if not it_report_flag:
        rep = '''\n<b>Запланированные выгрузки:</b>
Каталог - {0}
Фильтры - {1}
Категории - {2}'''
        report = rep.format(catalog_scheduled_date, filters_scheduled_date, categories_scheduled_date)
        return {'report':report, 'alert':alert, 'alert_message':alert_message}

    export_status_catalog = export_pim_catalog['status']
    file_name_catalog = export_pim_catalog['file_name']
    export_date_catalog = export_pim_catalog['export_date']
    log_catalog = export_pim_catalog['errors']
    graylog_status_catalog = export_pim_catalog['graylog']
    
    export_status_filters = export_pim_filters['status']
    file_name_filters = export_pim_filters['file_name']
    export_date_filters = export_pim_filters['export_date']
    log_filters = export_pim_filters['errors']
    graylog_status_filters = export_pim_filters['graylog']
    
    export_status_categories = export_pim_categories['status']
    file_name_categories = export_pim_categories['file_name']
    export_date_categories = export_pim_categories['export_date']
    log_categories = export_pim_categories['errors']
    graylog_status_categories = export_pim_categories['graylog'] 

    if export_date_catalog<datetime.today() - timedelta(hours=24):
        alert = True
        alert_message = alert_message+alert_no_export
        export_status_catalog = alert_no_export
        log_catalog = export_date_catalog = ""
        file_name_catalog = "Файл не найден"
        graylog_status_catalog = "Нет данных"
    else:
        if file_name_catalog is None:
            alert = True
            alert_message = alert_message+alert_template.format(export_status_catalog, log_catalog, export_date_catalog)
            graylog_status_catalog = "Нет данных"

    report = (it_report.format(export_status_catalog, log_catalog, file_name_catalog, graylog_status_catalog,
export_status_filters, log_filters, file_name_filters, graylog_status_filters,
export_status_categories, log_categories, file_name_categories, graylog_status_categories,
catalog_scheduled_date, filters_scheduled_date, categories_scheduled_date, export_date_catalog, export_date_filters, export_date_categories))
    
    return {'report':report, 'alert':alert, 'alert_message':alert_message}

def last_export_status(query, it_report_flag):
    startIndex = '0'
    response = requests.get(pim_url.format('JobHistory', query)+startIndex,auth=requests.\
        auth.HTTPBasicAuth(pimclient_username, pimclient_password),\
        verify=False).json()
    startIndex = int(response['totalSize']) - 100
    if startIndex<0:
        startIndex = '0'
    
# Find last PIM export status
    response = requests.get(pim_url.format('JobHistory', query)+str(startIndex),auth=requests.\
        auth.HTTPBasicAuth(pimclient_username, pimclient_password),\
        verify=False).json()
    all_jobs = response['rows']
    jobs = [obj['values'] for obj in all_jobs if obj['values'][5] in ['ExportSeries']]
    scheduled_date = 'не запланировано'
    for i in range(len(jobs),0,-1):
        if((jobs[i-1][3]!='Scheduled') & (jobs[i-1][5]=='ExportSeries')):
            status = jobs[i-1][3]+' - '+jobs[i-1][4]+'%'
            export_date = (datetime.strptime(jobs[i-1][2], '%Y-%m-%dT%H:%M:%S:%f%z')).replace(tzinfo=None)
            log_identifier = jobs[i-1][7]
            break
    for i in range(len(jobs),0,-1):
        if(jobs[i-1][3]=='Scheduled'):
            scheduled_date = (datetime.strptime(jobs[i-1][1], '%Y-%m-%dT%H:%M:%S:%f%z')).replace(tzinfo=None)
            break

    #delete this block. this block check and find last test pim export date. not actual after a6746670283 commit
    #for i in range(len(jobs),0,-1):
    #    if((jobs[i-1][3]!='Scheduled') & (jobs[i-1][5]=='TestExport')):
    #        test_export_date = (datetime.strptime(jobs[i-1][1], '%Y-%m-%dT%H:%M:%S:%f%z')).replace(tzinfo=None)
    #        if (test_export_date>export_date):
    #            status = jobs[i-1][3]+' - '+jobs[i-1][4]+'%'
    #            log_identifier = jobs[i-1][7]
    #            break
    
    if not it_report_flag:
        return {'scheduled':scheduled_date}

# Get export file name or error message
    file_name = None
    response = requests.get(pim_url.format('ProblemLogEntry', pim_url_query_logs.format(log_identifier)),auth=requests.auth.HTTPBasicAuth(pimclient_username, pimclient_password),verify=False).json()
    all_logs = response['rows']
    logs = [obj['values'] for obj in all_logs]
    file_name_catalog = "Файл не найден"
    errors = ['завершено']
    for entity in logs:
        if entity[4]=='Скопировать файл экспорта':
            file_name = re.search(r'Файл "(.*).(json|txt)"', entity[5]).group(1)
    if file_name is None:
        for entity in logs:
            if entity[0]=='Error':
                errors = []
                errors.append(entity[5])
    log = ''
    for error in errors:
        log += error

# Get graylog uploading info (uploading progress message or alias swap error)
    # search for message with upload progress info
    response = requests.get(graylog_url_catalog.format(file_name, graylog_date), headers={"accept":"application/json"},\
        auth=requests.auth.HTTPBasicAuth(basic_username, basic_password),\
        verify=False).json()
    graylog_status = 'Не удалось найти запись в логах'
    graylog_error = None
    for obj in response['messages']:
        graylog_status = obj['message']['message']
        graylog_status = re.sub(r'- ..3.*\dm:', '-', graylog_status)
        graylog_status = re.sub(r'\(data/.+\)', '', graylog_status)
        # search for alias swap error if progress is 100%
        if(re.search(r'Завершено: 100 %',graylog_status)):            
            graylog_error = search_for_alias_swap_error(obj)
        break
    # if not exist search for error message
    if response['messages']==[]:
        response = requests.get(graylog_url_catalog_error.format(file_name, graylog_date), headers={"accept":"application/json"},\
            auth=requests.auth.HTTPBasicAuth(basic_username, basic_password),\
            verify=False).json()
        for obj in response['messages']:
            graylog_status = obj['message']['message']
            graylog_status = re.sub(r'- ..3.*\dm:', '-', graylog_status)
            break
    # if also not exist search for last message
    if response['messages']==[]:
        response = requests.get(graylog_url_catalog_all_messages.format(file_name, graylog_date), headers={"accept":"application/json"},\
            auth=requests.auth.HTTPBasicAuth(basic_username, basic_password),\
            verify=False).json()
        for obj in response['messages']:
            graylog_status = obj['message']['message']
            # search for alias swap error if last message is ok
            if(re.search(r'Файл.*обработан',graylog_status)):
                graylog_error = search_for_alias_swap_error(obj)
                graylog_status = obj['message']['message']
                graylog_status = re.sub(r'- ..3.*\dm:', '-', graylog_status)
                break
            graylog_status = re.sub(r'- ..3.*\dm:', '-', graylog_status)
    if graylog_error is not None:
        graylog_status = graylog_error
    if(re.search(r'Файл.*обработан',graylog_status)):
        graylog_status = re.sub(r'CatalogParser: Файл.*обработан', 'Загрузка на сайт завершена без ошибок', graylog_status)
    if(re.search(r'Завершено: 100 %',graylog_status)):
        graylog_status = re.sub(r'ItemFileParser:.*%', 'Загрузка на сайт завершена без ошибок', graylog_status)
    
    return {'status':status, 'file_name':file_name, 'errors':log, 'scheduled':scheduled_date, 'graylog':graylog_status, 'export_date':export_date}

def search_for_alias_swap_error(obj):
    graylog_message_date = (datetime.strptime(obj['message']['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ'))
    graylog_date_1 = graylog_message_date - timedelta(0,60)
    graylog_date_2 = graylog_message_date + timedelta(0,60)
    graylog_date_range = 'rangetype=absolute&from={0}&to={1}'.format('{:%Y-%m-%dT%H:%M:%S.000Z}'.format(graylog_date_1),'{:%Y-%m-%dT%H:%M:%S.000Z}'.format(graylog_date_2))
    response_alias = requests.get(graylog_alias_swap_catalog.format(graylog_date_range), headers={"accept":"application/json"},\
        auth=requests.auth.HTTPBasicAuth(basic_username, basic_password),\
        verify=False).json()
    for obj1 in response_alias['messages']:
        graylog_error = obj1['message']['message']
        graylog_error = re.sub(r'- ..3.*\dm:', '-', graylog_error)
        graylog_error = re.sub(r'%[\S\s.\r\n\t]*$', '%.', graylog_error)
        return graylog_error
        break