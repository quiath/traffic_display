# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 22:59:56 2019

@author: quiath
"""

import os
import json
import time

import pygame
import pygame.image
import pygame.draw
import pygame.joystick

from net_image_cache import ImageCache

FONTSIZE = 32

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
        
        self.tiledsurf = pygame.Surface((self.TW * self.TS, self.TH * self.TS), depth=32)
        self.font = font
        self.cache = ImageCache(self.TW, self.TH, config, tilesize = self.TS, refresh_s = self.refresh_s,
                       global_indexing = True)
        
        self.move_flag = False
        
    def render_info(self):
    
        lastm = int(time.time() - self.last_refreshed)
        lasts = lastm % 60
        lastm = lastm // 60
        
        rendered_text = self.font.render(
                "last refreshed {:02d}m{:02d}s ago ".format(
                        lastm, lasts),
                True, (64, 0, 64))            
        
        self.mysurf.blit(rendered_text, (self.view_ofs_x, self.view_ofs_y))
    
        rendered_text = self.font.render(
                "Origin: {}".format(tuple(self.origin)),
                True, (64, 0, 64))            
        
        self.mysurf.blit(rendered_text, (self.view_ofs_x, self.view_ofs_y + FONTSIZE))    


    def process_event(self, evt):
        TW, TH = self.TW, self.TH
        if evt.type == pygame.KEYDOWN:
            self.move_flag = True
            if evt.key == pygame.K_RIGHT:
                self.origin[1] += 1
            elif evt.key == pygame.K_LEFT:
                self.origin[1] -= 1                
            elif evt.key == pygame.K_DOWN:
                self.origin[2] += 1
            elif evt.key == pygame.K_UP:
                self.origin[2] -= 1     
            elif evt.key == pygame.K_PAGEUP:
                self.origin[0] += 1    
                self.origin[1] = (self.origin[1] + TW // 2) * 2 - TW // 2
                self.origin[2] = (self.origin[2] + TH // 2) * 2 - TH // 2
            elif evt.key == pygame.K_PAGEDOWN:
                self.origin[0] -= 1    
                self.origin[1] = (self.origin[1] + TW // 2) // 2 - TW // 2
                self.origin[2] = (self.origin[2] + TH // 2) // 2 - TH // 2

            
    def update(self):        
        if self.total_loops % self.CHECK_EVERY_N_FRAMES == 0 or self.move_flag:

            TW, TH, TS = self.TW, self.TH, self.TS
            traffic_d = self.cache.get_tiles(self.origin, self.total_loops > 0)
            if any(not x[1] for x in traffic_d.values()) or self.total_loops == 0:
                self.last_refreshed = time.time()
            self.total_loops += 1
                
            for y in range(TH):
                for x in range(TW):    
                    tile_zxy = (self.origin[0], self.origin[1] + x, self.origin[2] + y)
        
                    if tile_zxy in traffic_d:
                        rfn, rdata = traffic_d[tile_zxy]
                        #print(rfn, rdata, map_screen_tile_to_name.get((x, y), ""))
                        if rdata and rfn == self.map_screen_tile_to_name.get((x, y), ""):
                            continue
                        
                        self.map_screen_tile_to_name[(x, y)] = rfn
                        try:
                            surf = pygame.image.load(rfn)
                            self.tiledsurf.blit(surf, (x * TS, y * TS))
                        except:
                            print("Error while parsing image", rfn)
                            pass
                        
        self.total_loops += 1
        self.move_flag = False
        self.mysurf.blit(self.tiledsurf, (self.view_ofs_x, self.view_ofs_y))
    
def main():

    config = read_config_json()
    
    WINW, WINH = config["win_w"], config["win_h"]
    
    # pygame
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()    
    clock = pygame.time.Clock()
    running = True
    total_time = 0
    
    try:
        screen = pygame.display.set_mode((WINW, WINH))
    
        pygame.display.flip()
    
        font = pygame.font.Font(None, FONTSIZE)
    
        mysurf = pygame.Surface((WINW, WINW), depth=32)
        
        map_disp = MapDisplay(config, mysurf, font)
       
        while running:
            mysurf.fill((0, 0, 0)) 

            total_time += clock.tick(30)
            
            for evt in pygame.event.get():
                if (evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE or 
                    evt.type == pygame.QUIT):
                    running = False
                    break                
                
                map_disp.process_event(evt)
                
            map_disp.update()
                
            map_disp.render_info()
    
            screen.blit(mysurf, (0, 0))
            pygame.display.flip()

            
    finally:
        #time.sleep(1)
        pygame.quit()      

if __name__ == "__main__":
    main()

