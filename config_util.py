# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 12:55:44 2019

@author: quiath
"""

import os
import json

def read_config_json():
    defaults = {
        "tiles_hor": 4,
        "tiles_ver": 4,
        "tiles_size": 128,
        "check_every_n_frames": 120,
        "win_w": 1024,
        "win_h": 768,
        "refresh_s": 600
    }

    if "TRAFFIC_APP_ID" in os.environ:
        defaults["app_id"] = os.environ["TRAFFIC_APP_ID"]
    if "TRAFFIC_APP_CODE" in os.environ: 
        defaults["app_code"] = os.environ["TRAFFIC_APP_CODE"]
    if "TRAFFIC_ORIGIN" in os.environ:    
        defaults["origin"] = tuple( int(x) for x in os.environ["TRAFFIC_ORIGIN"].split(",") )            
    
    d = {}
    try:
        with open("config.json") as f:
            d = json.load(f)
    except FileNotFoundError:
        pass
    
    for k in defaults:
        if k not in d:
            d[k] = defaults[k]
            
    return d