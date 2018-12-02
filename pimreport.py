#!/usr/bin/env python3.5 
# -*- coding: utf-8 -*-

from credentials import basic_username, basic_password
from config import t_report, email_report, url_category, url_filter, url_filenames, gr_beginning,\
    gr_finish, gr_cat_begin
import datetime, requests, re, traceback, logging


def file_regex(filename):
    r = re.search('(\w{5})_(\w{7,10})_f_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\_(\d{1,})', filename).group()
    return r

def get_filename(url):

    r = requests.get(url).json()
    r =  r['hits']['hits'][0]['_source']['file_name']
    r = file_regex(r)
    return r

def get_all_filenames(url):

    data = {"_source": "false","aggs":{"aggs1":{"terms":{"field":"file_name"}}}}
    headers = {'Content-type': 'application/json'}
    r = requests.post(url, json = data, headers=headers).json()
    return r['aggregations']['aggs1']['buckets']


def get_graylog_time(filename, url_ending):
    r = requests.get(gr_beginning+filename+url_ending,\
        headers={"accept":"application/json"}, auth=requests.auth.HTTPBasicAuth(basic_username, basic_password),\
        verify=False).json()
    if not r['messages']:
        raise TypeError('Не удалось получить информацию по запросу.')
    r = re.search('\d{4}-\d{2}-\d{2}\w\d{2}:\d{2}:\d{2}', r['messages'][0]['message']['timestamp'])
    if r is None:
        raise TypeError('Не удалось получить информацию по запросу.')
    r = r.group()
    r = datetime.datetime.strptime(r, '%Y-%m-%dT%H:%M:%S') +datetime.timedelta(hours=3)
    return str(r)

def find_full(url):
    arr_names = []
    arr_source = get_all_filenames(url)
    for i in range(len(arr_source)):
        arr_names.append(arr_source[i]['key'])
    for i in range(len(arr_names)):
        if re.search('_f_', arr_names[i]):
            full_name = arr_names[i]
    full_name = file_regex(full_name)
    return full_name

def get_datetime_from_file(file_name):

    file_datetime = re.search('(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})',\
        file_name).group()
    file_datetime = datetime.datetime.strptime(file_datetime,\
    '%Y-%m-%d_%H-%M-%S')
    return file_datetime


def report():
    error_flag = False

    try:
        catalog_name = find_full(url_filenames)
        catalog_datetime = get_datetime_from_file(catalog_name)
    except Exception as e:
        error_flag = False
        logging.error(str(e)+'\n'+traceback.format_exc())
        catalog_name = catalog_datetime = catalog_upload_finish = 'Не удалось получить информацию по запросу'
    else:
        try:
            catalog_upload_finish = get_graylog_time(catalog_name, gr_finish)
        except Exception as e:
            logging.error(str(e)+'\n'+traceback.format_exc())
            catalog_upload_finish = 'Не удалось получить информацию по запросу'

    try:    
        filter_name = get_filename(url_filter)
        filter_datetime = get_datetime_from_file(filter_name)
    except Exception as e:
        error_flag = False
        logging.error(str(e)+'\n'+traceback.format_exc())
        filter_name = filter_datetime = filter_upload_finish = 'Не удалось получить информацию по запросу'
    else:
        try:
            filter_upload_finish = get_graylog_time(filter_name, gr_finish)
        except Exception as e:
            logging.error(str(e)+'\n'+traceback.format_exc())
            filter_upload_finish = 'Не удалось получить информацию по запросу'
        
    try:
        category_name = get_filename(url_category)
        category_datetime = get_datetime_from_file(category_name)
    except Exception as e:
        error_flag = False
        logging.error(str(e)+'\n'+traceback.format_exc())
        category_name = category_datetime = category_upload_finish = 'Не удалось получить информацию по запросу'
    else:
        try:
            category_upload_finish = get_graylog_time(category_name, gr_finish)
        except Exception as e:
            logging.error(str(e)+'\n'+traceback.format_exc())
            category_upload_finish = 'Не удалось получить информацию по запросу'

    #catalog_upload_begin = get_graylog_time(catalog_name, gr_cat_begin)
    catalog_upload_begin, catalog_error_tag, catalog_error_close_tag, filters_error_tag, filters_error_close_tag, \
    category_error_tag, category_error_close_tag, catalog_error_email_tag, catalog_error_close_email_tag, \
    filters_error_email_tag, filters_error_close_email_tag, category_error_email_tag, category_error_close_email_tag = [''] * 13

    error_tags = ['<i>', ' - более 1 дня назад!</i>', '<span style="color: #ff0000;">', '</span>']
    it_report_flag = False
    try:
        if (catalog_datetime + datetime.timedelta(days=1)).date()<datetime.datetime.today().date():
            catalog_error_tag, catalog_error_close_tag, catalog_error_email_tag, catalog_error_close_email_tag = error_tags
            it_report_flag = True
        if (filter_datetime + datetime.timedelta(days=1)).date()<datetime.datetime.today().date():
            filters_error_tag, filters_error_close_tag, filters_error_email_tag, filters_error_close_email_tag = error_tags
            it_report_flag = True
        if (category_datetime + datetime.timedelta(days=1)).date()<datetime.datetime.today().date():
            category_error_tag, category_error_close_tag, category_error_email_tag, category_error_close_email_tag = error_tags
            it_report_flag = True
    except Exception as e:
        #if xxx_datetime contains error message, do nothing
        error_flag = it_report_flag = True

    message = (t_report.format(catalog_datetime, catalog_upload_begin, catalog_name,\
            catalog_upload_finish, filter_datetime, filter_name,\
            filter_upload_finish, category_datetime, category_name,\
            category_upload_finish, \
            catalog_error_tag, catalog_error_close_tag, filters_error_tag, filters_error_close_tag, category_error_tag, category_error_close_tag))
    
    email = email_report.format(catalog_datetime, catalog_upload_begin, catalog_name,\
            catalog_upload_finish, filter_datetime, filter_name,\
            filter_upload_finish, category_datetime, category_name,\
            category_upload_finish, \
            catalog_error_email_tag, catalog_error_close_email_tag, filters_error_email_tag, filters_error_close_email_tag, category_error_email_tag, category_error_close_email_tag)


    return {'report':message, 'email_report':email, 'catalog_generation_date':catalog_datetime, 'it_report_flag':it_report_flag, 'error':error_flag}