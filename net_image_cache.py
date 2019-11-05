# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 22:03:59 2019

@author: quiath
"""

import time
import os
import os.path
import requests

class ImageCache:
    types = [ "traffictile", "flowlabeltile", "flowtile", "flowbasetile" ]
    def __init__(self, tsw, tsh, 
                 credentials, 
                 tilesize = 128, 
                 tiletype = "traffictile", 
                 imgdir = "images", 
                 refresh_s = 600,
                 global_indexing = False,
                 proxies = {}):
        self.imgdir = imgdir
        self.proxies = proxies
        self.tsw = tsw
        self.tsh = tsh
        self.global_indexing = global_indexing
        if tiletype in ImageCache.types:
            self.tiletype = tiletype
        else:
            self.tiletype = ImageCache.types[0]
        self.tilesize = tilesize
        if "app_id" not in credentials:
            raise Exception("missing app_id")
        if "app_code" not in credentials:
            raise Exception("missing app_code")            
        self.credentials = credentials
        
        head = "https://1.traffic.maps.api.here.com/maptile/2.1/" + self.tiletype
        mid = "/newest/normal.day/{z}/{x}/{y}/"
        tail = "{tilesize}/png8?app_id={app_id}&app_code={app_code}".format(
                tilesize=tilesize,
                app_id=credentials["app_id"], 
                app_code=credentials["app_code"])
        self.template = head + mid + tail        
        self.refresh_s = refresh_s
        

    def file_from_uri(self, uri, filename):
       
        try: 
            r = requests.get(uri, proxies = self.proxies, timeout = (5, 20))   
        except:
            return False
        z = r.content        
        print("Received length and type", len(z), type(z))
        #print(z[0], z[1], z[2])
        
        with open(filename, "wb") as f:
            f.write(z)
            return True
        
        return False
    
    def get_tiles(self, triplet, updated_only):
        # {z}/{x}/{y}
        
        d = {}
        
        z, x0, y0 = triplet
        for y in range(y0, y0 + self.tsh):
            for x in range(x0, x0 + self.tsw):    
                fn = "{imgdir}/tile_{tiletype}_z{z}_x{x}_y{y}.png".format(
                        tiletype=self.tiletype,
                        imgdir=self.imgdir,
                        x=x, y=y, z=z)
                
                has_data = False
                if os.path.isfile(fn) and os.path.getsize(fn) > 0:
                    modtime = os.path.getmtime(fn)
                    utctime = time.time()
                    print("File: {} local ts: {:.0f} UTC ts: {:.0f} last modified ago: {:.0f}".format(fn, modtime, utctime, utctime - modtime))
                    has_data = utctime - modtime < self.refresh_s
                    if updated_only and has_data and not self.global_indexing:
                        continue
    
                had_data = has_data
                if not has_data:
                    has_data = self.file_from_uri(self.template.format(x=x, y=y, z=z), fn)
                    
                if self.global_indexing:
                    d[(z, x, y)] = (fn, had_data)
                else:
                    if has_data:
                        d[(x - x0, y - y0)] = fn    
                   
    
        return d

