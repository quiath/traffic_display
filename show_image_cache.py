# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 22:12:36 2019

@author: quiath
"""

import time
import os
import os.path
import requests
from PIL import Image, ImageEnhance

import Adafruit_ILI9341 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


# Raspberry Pi configuration.
DC = 18
RST = 23
SPI_PORT = 0
SPI_DEVICE = 0




def file_from_uri(uri, filename):
    proxies = {}
   
    try: 
        r = requests.get(uri, proxies = proxies, timeout = (5, 20))   
    except:
        return False
    z = r.content        
    print(len(z), type(z))
    print(z[0], z[1], z[2])
    
    with open(filename, "wb") as f:
        f.write(z)
        return True
    
    return False

def get_tiles(url_template, triplet, w, h, tile_size, refresh_s):
    # {z}/{x}/{y}
    
    d = {}
    
    z, x0, y0 = triplet
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + h):    
            fn = "images/tile_z{z}_x{x}_y{y}.png".format(x=x, y=y, z=z)
            
            has_data = False
            if os.path.isfile(fn) and os.path.getsize(fn) > 0:
                modtime = os.path.getmtime(fn)
                utctime = time.time()
                print(fn, modtime, utctime, utctime - modtime)
                has_data = utctime - modtime < refresh_s
                
            """
            try:
                f = open(fn, "rb")
                cont = f.read()
                has_data = len(cont) > 0
            except FileNotFoundError:
                pass
            """

            if not has_data:
                has_data = file_from_uri(url_template.format(x=x, y=y, z=z, tile_size=tile_size), fn)
            if has_data:
                d[(x - x0, y - y0)] = fn

    return d
            
def cycle(disp, app_id, app_code, origin):
    tsw, tsh = 4, 4
    tile_size = 128
    tt = [ "traffictile", "flowlabeltile", "flowtile", "flowbasetile" ][1]

    head = "https://1.traffic.maps.api.here.com/maptile/2.1/" + tt
    mid = "/newest/normal.day/{z}/{x}/{y}/{tile_size}/"
    tail = "png8?app_id={}&app_code={}".format(app_id, app_code)
    template = head + mid + tail

    traffic_d = get_tiles(
                 template,
                 origin,
                 tsw, tsh, tile_size, 600
                )
    print(traffic_d)
    
    imfull = Image.new("RGB", (tsw * tile_size, tsh * tile_size))
    for y in range(tsh):
        for x in range(tsw):    
            if (x, y) in traffic_d:
    
                im = Image.open(traffic_d[(x, y)])
                imfull.paste(im, (x * tile_size, y * tile_size, (x + 1) * tile_size, (y + 1) * tile_size))
    #cropped.show()
    enh = ImageEnhance.Color(imfull)
    imfull = enh.enhance(2.0) 
    #imfull.show()

    if disp is None:
        print("Display....")
        # Create TFT LCD display class.
        disp = TFT.ILI9341(DC, rst=RST, width = 128, height = 128, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

        # Initialize display.
        disp.begin()

    print("Drawing image...")
    #cropped.resize((128, 128))

    line = 0
    for y in range(0, tile_size * tsh - 2 * tile_size, 32):
        line += 1
        for kx in range(0, tile_size * tsw - 2 * tile_size, 8):
            
            if line % 2:
                x = tile_size * tsw - 2 * tile_size - 1 - kx
            else:
                x = kx

            cropped = imfull.transform((tile_size, tile_size), 
                       Image.EXTENT, 
                       data = (x, y, x + 2 * tile_size, y + 2 * tile_size),
                       resample = Image.BILINEAR)

            cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
            cropped = cropped.transpose(Image.ROTATE_90)
            disp.display(cropped)
            time.sleep(0.1)

    return disp

def main():

    app_id = os.environ["TRAFFIC_APP_ID"]
    app_code = os.environ["TRAFFIC_APP_CODE"]
    origin = tuple( int(x) for x in os.environ["TRAFFIC_ORIGIN"].split(",") )


    disp = None
    while True:
        disp = cycle(disp, app_id, app_code, origin)


if __name__ == "__main__":
    main()
        
    
