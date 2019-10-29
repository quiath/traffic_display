# -*- coding: utf-8 -*-
"""
Created on Sun Oct 27 15:00:41 2019

@author: tomek
"""

import math
import argparse

def latlon2xy(lat, lon, z):

    latRad = lat * math.pi / 180;
    n = 2 ** z;
    xTile = int(n * ((lon + 180) / 360))
    yTile = int(n * (1-(math.log(math.tan(latRad) + 1/math.cos(latRad)) /math.pi)) / 2 )
    
    return xTile, yTile

def main():
    parser = argparse.ArgumentParser(description="Convert latitude and longitude at the given zoom level to the tile coordinates")
    parser.add_argument("lat", type=float, help="latitude")
    parser.add_argument("lon", type=float, help="longitude")
    parser.add_argument("zoom", type=int, help="zoom level")
    
    args = parser.parse_args()
    
    x, y = latlon2xy(args.lat, args.lon, args.zoom)    
    
    print("x={} y={} z={}".format(x, y, args.zoom))
    
if __name__ == "__main__":
    main()
    
    