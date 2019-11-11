# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 13:17:37 2019

@author: quiath
"""


import time
from collections import namedtuple


from PIL import Image, ImageEnhance


from net_image_cache import ImageCache
from config_util import read_config_json

"""
contents of config.json enabling a 128x128 LCD display
if "lcd" is not set, PIL built in Image.show() is used (e.g. for debugging)

{
"tiles_hor": 4,
"tiles_ver": 4,
"tiles_size": 128,
"check_every_n_frames": 120,
"win_w": 800,
"win_h": 600,
"lcd": 1,
"lcd_w": 128,
"lcd_h": 128,
"app_id": "YOUR_APP_ID",
"app_code": "YOUR_APP_CODE",
"origin": [13,4092,2723]
}


"""

config = read_config_json()

RPi_has_LCD = config.get("lcd", False)
if RPi_has_LCD:
    import Adafruit_ILI9341 as TFT
    import Adafruit_GPIO as GPIO
    import Adafruit_GPIO.SPI as SPI

    # Raspberry Pi configuration.
    DC = 18
    RST = 23
    SPI_PORT = 0
    SPI_DEVICE = 0


FONTSIZE = 32
Evt = namedtuple("Evt", "type, key")


class MapDisplay:
    def __init__(self, config, targetsurf, font):
        self.mysurf = targetsurf

        self.TW, self.TH = config["tiles_hor"], config["tiles_ver"]
        self.TS = config["tiles_size"]
        self.CHECK_EVERY_N_FRAMES = config["check_every_n_frames"]

        self.origin = config["origin"]
        self.refresh_s = config.get("refresh_s", 600)
        self.view_ofs_x, self.view_ofs_y = 0, 0
        self.last_refreshed = time.time()
        self.map_screen_tile_to_name = {}
        self.total_loops = 0

        self.tiledsurf = Image.new("RGB", (self.TW * self.TS, self.TH * self.TS)) 
        self.font = font
        self.cache = ImageCache(self.TW, self.TH, config, tilesize = self.TS, refresh_s = self.refresh_s,
                       global_indexing = True)

        # set this at start to show something while the initial update
        self.move_flag = True
        # used for displaying the info about the update in progress
        self.need_update_flag = False

        # PIL!
        self.mysurf_w, self.mysurf_h = self.mysurf.size
        self.window_move = (self.mysurf_w < self.TS * self.TW)
        self.src_x = 0
        self.src_y = 0


    def render_info(self):

        lastm = int(time.time() - self.last_refreshed)
        lasts = lastm % 60
        lastm = lastm // 60
        
        print("last refreshed {:02d}m{:02d}s ago ".format(lastm, lasts))
        

    def process_event(self, evt):
        pass
    
    def process_joy(self, joy):
        pass

    def update(self):
        if (self.total_loops % self.CHECK_EVERY_N_FRAMES == 0 or
            self.move_flag) and not self.need_update_flag:
            self.need_update_flag = True
        elif self.need_update_flag:
            self.need_update_flag = False
            TW, TH, TS = self.TW, self.TH, self.TS
            traffic_d = self.cache.get_tiles(self.origin, self.total_loops > 0)
            if any(not x[1] for x in traffic_d.values()) or self.total_loops == 0:
                self.last_refreshed = time.time()

            for y in range(TH):
                for x in range(TW):
                    tile_zxy = (self.origin[0], self.origin[1] + x, self.origin[2] + y)

                    if tile_zxy in traffic_d:
                        rfn, rdata = traffic_d[tile_zxy]

                        if rdata and rfn == self.map_screen_tile_to_name.get((x, y), ""):
                            continue

                        self.map_screen_tile_to_name[(x, y)] = rfn
                        try:
                            surf = Image.open(rfn)
                            self.tiledsurf.paste(surf, (x * TS, y * TS, (x + 1) * TS, (y + 1) * TS))
                        except:
                            print("Error while parsing image", rfn)
                            pass

        self.total_loops += 1
        self.move_flag = False
        
        enh = ImageEnhance.Color(self.tiledsurf)
        enhanced = enh.enhance(2.0)
        result_img = enhanced

        if RPi_has_LCD:
            x, y = self.src_x, self.src_y
            cropped = enhanced.transform((self.mysurf_w, self.mysurf_h),
                    Image.EXTENT,
                    data = (x, y, x + 1 * self.mysurf_w, y + 1 * self.mysurf_h), # TODO: scale down
                       resample = Image.BILINEAR)

            cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
            cropped = cropped.transpose(Image.ROTATE_90)

            result_img = cropped
            
            if self.window_move:
                HSTEP = 4
                VSTEP = 16
                VSTEP2 = 2 * VSTEP
    
                delta_x = HSTEP if (self.src_y // VSTEP2) % 2 == 0 else -HSTEP
                self.src_x += delta_x
                if self.src_x + self.mysurf_w >= self.TW * self.TS:
                    self.src_x = self.TW * self.TS - self.mysurf_w - 1
                    self.src_y += VSTEP // 2
                elif self.src_x < 0:
                    self.src_x = 0
                    self.src_y += VSTEP // 2
                if self.src_y + self.mysurf_h >= self.TH * self.TS:
                    self.src_x, self.src_y = 0, 0


        self.mysurf.paste(result_img, 
                          (self.view_ofs_x,
                           self.view_ofs_y,
                           self.view_ofs_x + result_img.size[0],
                           self.view_ofs_y + result_img.size[1]))


def main():
    if RPi_has_LCD:

        WINW, WINH = config["lcd_w"], config["lcd_h"]
    else:
        WINW, WINH = config["win_w"], config["win_h"]

    if RPi_has_LCD:
        rpi_disp = TFT.ILI9341(DC, rst=RST, width = WINW, height = WINH, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))
        rpi_disp.begin()

    running = True

    try:
        font = None 

        mysurf =  Image.new("RGB", (WINW, WINH))  

        map_disp = MapDisplay(config, mysurf, font)

        while running:
            map_disp.update()

            map_disp.render_info()

            if RPi_has_LCD:
                rpi_disp.display(mysurf)
            else:
                mysurf.show()
                time.sleep(5)


    finally:
        pass


if __name__ == "__main__":
    main()
