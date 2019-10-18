# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 22:59:56 2019

@author: quiath
"""

import os
import json

import pygame
import pygame.image
import pygame.draw
import pygame.joystick

from net_image_cache import ImageCache

def read_config_json():
    defaults = {
        "tiles_hor": 4,
        "tiles_ver": 4,
        "tiles_size": 128,
        "check_freq": 120,
        "win_w": 1024,
        "win_h": 768
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
    



def main():

    config = read_config_json()
    
    TW, TH = config["tiles_hor"], config["tiles_ver"]
    TS = config["tiles_size"]
    CHECKFREQ = config["check_freq"]

    WINW, WINH = config["win_w"], config["win_h"]
    
    origin = config["origin"]
    
    # pygame
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()    
    clock = pygame.time.Clock()
    running = True
    total_time = 0
    total_loops = 0

    
    cache = ImageCache(TW, TH, config, tilesize = TS)

    
    view_ofs_x, view_ofs_y = 0, 0
    
    try:
        screen = pygame.display.set_mode((WINW, WINH))
    

        pygame.display.flip()
    
        #font = pygame.font.Font(None, 32)
    
        tiledsurf = pygame.Surface((TW * TS, TH * TS), depth=32)
    
        mysurf = pygame.Surface((WINW, WINW), depth=32)
        #myrect = mysurf.get_rect()
    
        #mysurf.fill((255, 255, 255))
        while running:
            mysurf.fill((0, 0, 0)) 

            total_time += clock.tick(30)
            
            for evt in pygame.event.get():
                if (evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE or 
                   evt.type == pygame.QUIT):
                    running = False
                    break
                
            if total_loops % CHECKFREQ == 0:
                traffic_d = cache.get_tiles(origin, total_loops > 0)
                #print(traffic_d)                
                for y in range(TH):
                    for x in range(TW):    
                        if (x, y) in traffic_d:
                            surf = pygame.image.load(traffic_d[x, y])
                            tiledsurf.blit(surf, (x * TS, y * TS))
            
            mysurf.blit(tiledsurf, (view_ofs_x, view_ofs_y))
    
            screen.blit(mysurf, (0, 0))
            pygame.display.flip()
            total_loops += 1
            
    finally:
        #time.sleep(1)
        pygame.quit()      

if __name__ == "__main__":
    main()

