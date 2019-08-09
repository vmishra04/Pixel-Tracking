#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 15:12:58 2019

@author: vivekmishra
"""
import json
import os
from flask import Flask,jsonify
app = Flask(__name__)

@app.route("/endpoint")
def hello():
    return "<h1 style='color:blue'>Hello There!</h1>"

@app.route("/get-report-uuid/<uuid>",methods=['GET'])
def get_report_uuid(uuid):
    if uuid:
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        filepath = APP_ROOT+'/public_html/reports/'+uuid+'.json'
        data = json.load(filepath)
        return jsonify({'data': data})
    else:
        return "Please enter the UUID for which reports needs to returned"


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
