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

from selenium import webdriver
app = Flask(__name__)

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There! Welcome to Project Piranha</h1>"

@app.route("/get-report-uuid/<uuid>",methods=['GET'])
def get_report_uuid(uuid):
    if uuid:
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        filepath = APP_ROOT+'/IP-Biter/reports/'+uuid+'.json'
        with open(filepath) as json_file:  
            data = json.load(json_file)
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
    data = ""
    INPUT_DIR = "/var/log/nginx/"
    lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)
    final_data = {}
    for f in os.listdir(INPUT_DIR):
        if f.endswith(".gz"):
            logfile = gzip.open(os.path.join(INPUT_DIR, f))
        else:
            logfile = open(os.path.join(INPUT_DIR, f))
    
            for l in logfile.readlines():
                data = re.search(lineformat, l)
                if data:
                    datadict = data.groupdict()
                    ip = datadict["ipaddress"]
                    datetimestring = datadict["dateandtime"]
                    url = datadict["url"]
                    bytessent = datadict["bytessent"]
                    referrer = datadict["refferer"]
                    useragent = datadict["useragent"]
                    status = datadict["statuscode"]
                    method = data.group(6)
                    
                    final_data['ip'] = ip
                    final_data['datetimestring'] = datetimestring
                    final_data['url'] = url
                    final_data['bytessent'] = bytessent
    
        logfile.close()
        
    return jsonify({'data':final_data})


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)