#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 15:12:58 2019

@author: vivekmishra
"""
import json
import os
from flask import Flask,jsonify,make_response

import gzip
import sys
import re
#import pytz
from datetime import datetime


from selenium import webdriver
app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There! Welcome to Project Piranha</h1>"

@app.route("/get-report-uuid/<uuid>",methods=['GET'])
def get_report_uuid(uuid):
    if uuid:
        #The below code is reading through nginx logs for reading geo information
        data = ""
        INPUT_DIR = "/var/log/nginx/"
        lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["]) (["](?P<http_forward>.+)["]) (["](?P<country_code>.+)["])(["](?P<country>.+)["]) (["](?P<lat>.+)["])(["](?P<long>.+)["]) (["](?P<city>.+)["]) (["](?P<area_code>.+)["])""", re.IGNORECASE)
        mega = {}
        for f in os.listdir(INPUT_DIR):
            if f.endswith(".gz"):
                logfile = gzip.open(os.path.join(INPUT_DIR, f))
            else:
                logfile = open(os.path.join(INPUT_DIR, f))
        
            for l in logfile.readlines():
                data = re.search(lineformat, l)
                if data:
                    pixel_url = "ipb.php?op=i&tid="+uuid
                    if pixel_url in l:
                        datadict = data.groupdict()
                        datetimetemp = datadict["dateandtime"].split(" ")
                        datetimeobj = datetime.strptime(datetimetemp[0], "%d/%b/%Y:%H:%M:%S")
                        datetimestring = datetimeobj
    
                        final_data = {}
                        final_data['ip'] = datadict["ipaddress"]
                        final_data['datetimestring'] = datetimestring
                        final_data['url'] = datadict["url"]
                        final_data['bytessent'] = datadict["bytessent"]
                        final_data['country_code'] = datadict['country_code']
                        final_data['http_forward'] = datadict['http_forward']
                        final_data['country'] = datadict['country']
                        final_data['lat'] = datadict['lat']
                        final_data['long'] = datadict['long']
                        final_data['city'] = datadict['city']
                        final_data['area_code'] = datadict['area_code']
                        
                        
                        mega[final_data['ip']] = final_data
                        
        
            logfile.close()
        
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        filepath = APP_ROOT+'/IP-Biter/reports/'+uuid+'.json'
        with open(filepath) as json_file:  
            data = json.load(json_file)
            tracklist = data['trackList']
            for items in tracklist:
                ip = items['ip']
                #Get geo for this ip
                geo_dict = mega[ip]
                items['lat'] = geo_dict['lat']
                items['long'] = geo_dict['long']
                items['country'] = geo_dict['country']
                items['city'] = geo_dict['city']
                items['area_code'] = geo_dict['area_code']
            data['tracklist'] = tracklist
        return jsonify({'data': data})
    else:
        return "Please enter the UUID for which reports needs to returned"
    
@app.route("/create-tracker",methods=['GET'])
def create_tracker():
    #Running the php webURL   
    #r = requests.get('http://54.193.90.107/api/IP-Biter/ipb.php?op=dashboard') 
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox') # required when running as root user. otherwise you would get no sandbox errors. 
    driver = webdriver.Chrome('/usr/bin/chromedriver', options=chrome_options,service_args=['--verbose', '--log-path=/tmp/chromedriver.log'])
    driver.get('http://54.193.90.107/api/IP-Biter/ipb.php?op=dashboard') 
    #return jsonify({'data': driver.title})
    if driver:
        #Serving the latest created config file
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        filepath = APP_ROOT+'/IP-Biter/configs/'
        a = [s for s in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, s))]
        a.sort(key=lambda s: os.path.getmtime(os.path.join(filepath, s)),reverse=True)
        config_file = a[0] #First file created in this array represents the latest config file
        final_json = {}
        with open(filepath+config_file) as json_file:  
                data = json.load(json_file)
        final_json['uuid'] = data['trackUUID']
        final_json['tracking_image'] = data['trackingImageGeneratedUrl']
        final_json['shortened_url'] = data['trackingImageShortUrl']
        return jsonify({'data': final_json})
    else:
        return jsonify({'data':'Issue with php fpm service, please check if IP-Biter is running'})

@app.route("/get-all-report",methods=['GET'])
def get_all_report():
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    filepath = APP_ROOT+'/IP-Biter/reports/'
    a = [s for s in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(filepath, s)))
    final_list = []
    if len(a) >= 1:
        for files in a:
            with open(filepath+files) as json_file:  
                data = json.load(json_file)
                final_list.append(data)
        return jsonify({'data': final_list})
    else:
        return jsonify({'data':'No reports created yet'})
    
    
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route("/get-nginx",methods=['GET'])
def get_nginx():
    #tz = pytz.timezone('UTC')
    data = ""
    INPUT_DIR = "/var/log/nginx/"
    lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["]) (["](?P<http_forward>.+)["]) (["](?P<country_code>.+)["])(["](?P<country>.+)["]) (["](?P<lat>.+)["])(["](?P<long>.+)["]) (["](?P<city>.+)["]) (["](?P<area_code>.+)["])""", re.IGNORECASE)
    mega = []
    for f in os.listdir(INPUT_DIR):
        if f.endswith(".gz"):
            logfile = gzip.open(os.path.join(INPUT_DIR, f))
        else:
            logfile = open(os.path.join(INPUT_DIR, f))
    
        for l in logfile.readlines():
            data = re.search(lineformat, l)
            if data:
                pixel_url = "/mysql/"
                if pixel_url in l:
                    datadict = data.groupdict()
                    datetimetemp = datadict["dateandtime"].split(" ")
                    datetimeobj = datetime.strptime(datetimetemp[0], "%d/%b/%Y:%H:%M:%S")
                    datetimestring = datetimeobj

                    final_data = {}
                    final_data['ip'] = datadict["ipaddress"]
                    final_data['datetimestring'] = datetimestring
                    final_data['url'] = datadict["url"]
                    final_data['bytessent'] = datadict["bytessent"]
                    final_data['country_code'] = datadict['country_code']
                    final_data['http_forward'] = datadict['http_forward']
                    final_data['country'] = datadict['country']
                    final_data['lat'] = datadict['lat']
                    final_data['long'] = datadict['long']
                    final_data['city'] = datadict['city']
                    final_data['area_code'] = datadict['area_code']
                    
                    temp = {}
                    temp[final_data['ip']] = final_data
                    
                    mega.append(temp)
    
        logfile.close()
        
    return jsonify({'data':mega})


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)