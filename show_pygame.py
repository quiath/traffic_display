# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 22:59:56 2019

@author: quiath
"""

import os
#import json
import time
from collections import namedtuple

import pygame
import pygame.image
import pygame.draw
import pygame.joystick

from net_image_cache import ImageCache
from config_util import read_config_json

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
        
        self.tiledsurf = pygame.Surface((self.TW * self.TS, self.TH * self.TS), depth=32)
        self.font = font
        self.cache = ImageCache(self.TW, self.TH, config, tilesize = self.TS, refresh_s = self.refresh_s,
                       global_indexing = True)
        
        # set this at start to show something while the initial update
        self.move_flag = True
        # used for displaying the info about the update in progress
        self.need_update_flag = False
        
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
        
        if self.need_update_flag:
            rendered_text = self.font.render(
                    "Updating in progress...",
                    True, (64, 0, 64))                        
            self.mysurf.blit(rendered_text, (self.view_ofs_x, self.view_ofs_y + 2 * FONTSIZE))    


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

    def process_joy(self, joy):    
        if not joy:
            return
        b = [ joy.get_button(i) for i in range(joy.get_numbuttons()) ]

       
        evt = None
        
        if b[0]: 
            evt = Evt(pygame.KEYDOWN, pygame.K_PAGEUP)    
        if b[1]:
            evt = Evt(pygame.KEYDOWN, pygame.K_PAGEDOWN)    

        if joy.get_numaxes() >= 2:
            z = [ int(joy.get_axis(i) + 2.5) - 2 for i in range(2) ]
            if z[0] == 1:
                evt = Evt(pygame.KEYDOWN, pygame.K_RIGHT)        
            elif z[0] == -1:
                evt = Evt(pygame.KEYDOWN, pygame.K_LEFT)        
            if z[1] == 1:
                evt = Evt(pygame.KEYDOWN, pygame.K_DOWN)        
            elif z[1] == -1:
                evt = Evt(pygame.KEYDOWN, pygame.K_UP)        

        if evt:
            self.process_event(evt)
        
        
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
            #self.total_loops += 1
                
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
    pygame.joystick.init()
    
    joy = None
    if pygame.joystick.get_count() > 0:
        joy = pygame.joystick.Joystick(0)
        joy.init()
        #axes = joy.get_numaxes()    
    
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
                map_disp.process_joy(joy)
                
            map_disp.update()
                
            map_disp.render_info()
    
            screen.blit(mysurf, (0, 0))
            pygame.display.flip()

            
    finally:
        #time.sleep(1)
        pygame.quit()      

if __name__ == "__main__":
    main()

