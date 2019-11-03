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

    
def render_info(mysurf, font, last_refreshed, origin, view_ofs_x, view_ofs_y):

    lastm = int(time.time() - last_refreshed)
    lasts = lastm % 60
    lastm = lastm // 60
    
    rendered_text = font.render(
            "last refreshed {:02d}m{:02d}s ago ".format(
                    lastm, lasts),
            True, (64, 0, 64))            
    
    mysurf.blit(rendered_text, (view_ofs_x, view_ofs_y))

    rendered_text = font.render(
            "Origin: {}".format(tuple(origin)),
            True, (64, 0, 64))            
    
    mysurf.blit(rendered_text, (view_ofs_x, view_ofs_y + FONTSIZE))    


def move_origin(evt, TW, TH, origin):
    if evt.type == pygame.KEYDOWN:
        if evt.key == pygame.K_RIGHT:
            origin[1] += 1
        elif evt.key == pygame.K_LEFT:
            origin[1] -= 1                
        elif evt.key == pygame.K_DOWN:
            origin[2] += 1
        elif evt.key == pygame.K_UP:
            origin[2] -= 1     
        elif evt.key == pygame.K_PAGEUP:
            origin[0] += 1    
            origin[1] = (origin[1] + TW // 2) * 2 - TW // 2
            origin[2] = (origin[2] + TH // 2) * 2 - TH // 2
        elif evt.key == pygame.K_PAGEDOWN:
            origin[0] -= 1    
            origin[1] = (origin[1] + TW // 2) // 2 - TW // 2
            origin[2] = (origin[2] + TH // 2) // 2 - TH // 2

            
def update(origin, map_screen_tile_to_name, last_refreshed, TS, TW, TH, total_loops, cache, tiledsurf):            
    traffic_d = cache.get_tiles(origin, total_loops > 0)
    if any(not x[1] for x in traffic_d.values()) or total_loops == 0:
        last_refreshed = time.time()
             
    for y in range(TH):
        for x in range(TW):    
            tile_zxy = (origin[0], origin[1] + x, origin[2] + y)

            if tile_zxy in traffic_d:
                rfn, rdata = traffic_d[tile_zxy]
                #print(rfn, rdata, map_screen_tile_to_name.get((x, y), ""))
                if rdata and rfn == map_screen_tile_to_name.get((x, y), ""):
                    continue
                
                map_screen_tile_to_name[(x, y)] = rfn
                try:
                    surf = pygame.image.load(rfn)
                    tiledsurf.blit(surf, (x * TS, y * TS))
                except:
                    print("Error while parsing image", rfn)
                    pass
    
    return last_refreshed 

    
def main():

    config = read_config_json()
    
    TW, TH = config["tiles_hor"], config["tiles_ver"]
    TS = config["tiles_size"]
    CHECK_EVERY_N_FRAMES = config["check_every_n_frames"]

    WINW, WINH = config["win_w"], config["win_h"]
    
    origin = config["origin"]
    refresh_s = config.get("refresh_s", 600)

    # pygame
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()    
    clock = pygame.time.Clock()
    running = True
    total_time = 0
    total_loops = 0

    
    cache = ImageCache(TW, TH, config, tilesize = TS, refresh_s = refresh_s,
                       global_indexing = True)

    
    view_ofs_x, view_ofs_y = 0, 0
    
    last_refreshed = 0
    
    try:
        screen = pygame.display.set_mode((WINW, WINH))
    
        pygame.display.flip()
    
        font = pygame.font.Font(None, FONTSIZE)
    
        tiledsurf = pygame.Surface((TW * TS, TH * TS), depth=32)
    
        mysurf = pygame.Surface((WINW, WINW), depth=32)
        #myrect = mysurf.get_rect()
    
        #mysurf.fill((255, 255, 255))
        
        map_screen_tile_to_name = {}
       
        while running:
            mysurf.fill((0, 0, 0)) 

            total_time += clock.tick(30)
            
            for evt in pygame.event.get():
                if (evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE or 
                    evt.type == pygame.QUIT):
                    running = False
                    break                
                
                move_origin(evt, TW, TH, origin)
                
            if total_loops % CHECK_EVERY_N_FRAMES == 0:
                last_refreshed = update(origin, map_screen_tile_to_name, last_refreshed, TS, TW, TH, total_loops, cache, tiledsurf)
                
            mysurf.blit(tiledsurf, (view_ofs_x, view_ofs_y))
            
            render_info(mysurf, font, last_refreshed, origin, view_ofs_x, view_ofs_y)
    
            screen.blit(mysurf, (0, 0))
            pygame.display.flip()
            total_loops += 1
            
    finally:
        #time.sleep(1)
        pygame.quit()      

if __name__ == "__main__":
    main()

