
import pygame
import random

import sys
import os
import math

try:
    import _path
except:
    pass

import tiledtmxloader

import cProfile
import re

# Define some colors 
BLACK    = (   0,   0,   0) 
WHITE    = ( 255, 255, 255) 
RED      = ( 255,   0,   0)
BLUE     = (   0,   0, 255)
YELLOW = (247, 241, 49)
PURPLE = (194, 60, 158)
GREEN = (0, 150, 0)
TEAL = (49, 247, 247)

SCREEN_SIZE=[700,500]

LEVEL = 0
                 
class Player (pygame.sprite.Sprite): 
  
    # -- Attributes
    win_level = False
    game_over_lose = False

    # Set speed vector of player
    change_x = 0
    change_y = 0

    # Triggered if the player wants to jump.
    jump_ready = False

    # Count of frames since the player hit 'jump' and we
    # collided against something. Used to prevent jumping
    # when we haven't hit anything.
    frame_since_collision = 0
    frame_since_jump = 0

    #Coin count
    coin_tally = 0
    
    # -- Methods 
    # Constructor function 
    def __init__(self,x,y): 
        # Call the parent's constructor 
        pygame.sprite.Sprite.__init__(self) 
          
        # Set height, width 
        self.image = pygame.Surface([15, 15]) 
        self.image.fill((RED))
  
        # Make our top-left corner the passed-in location. 
        self.rect = self.image.get_rect() 
        self.rect.x = x
        self.rect.y = y
      
    # Change the speed of the player 
    def changespeed_x(self,x):
        self.change_x = x

    def changespeed_y(self,y):
        self.change_y = y
          
    # Find a new position for the player 
    def updte(self, blocks, goal_blocks, coins): 

        # Save the old x position, update, and see if we collided.
        old_x = self.rect.x
        new_x = old_x + self.change_x
        self.rect.x = new_x

        # Save the old y position, update, and see if we collided.
        old_y = self.rect.y 
        new_y = old_y + self.change_y
        self.rect.y = new_y

        # If the player recently asked to jump, and we have recently
        # had ground under our feet, go ahead and change the velocity
        # to send us upwards
        if self.frame_since_collision < 6 and self.frame_since_jump < 6:
            self.frame_since_jump = 100
            self.change_y -= 8

        # Increment frame counters
        self.frame_since_collision+=1
        self.frame_since_jump+=1

        if self.game_over_lose or self.win_level:
            self.change_x = 0
            self.change_y = 0

    # Calculate effect of gravity.
    def calc_grav(self):
        self.change_y += .35

        # See if we are on the ground.
        if self.rect.y >= 500 and self.change_y >= 0:
             self.game_over_lose = True

    # Called when user hits 'jump' button
    def jump(self,blocks):
        self.jump_ready = True
        self.frame_since_jump = 0

class Game():
    
    # Create sprites and player
    block_list = None
    goal_list = None
    coins = None
    all_sprites_list = None
    player_list = None
    player = None
    cam_world_pos_x = 0
    cam_world_pos_y = 0

    #tmxloader definitions and load map
    level_map = tiledtmxloader.tmxreader.TileMapParser().parse_decode("Lvl1.tmx")
    renderer = tiledtmxloader.helperspygame.RendererPygame()
    resources = tiledtmxloader.helperspygame.ResourceLoaderPygame()
    resources.load(level_map)
    
    level_count = LEVEL

    def __init__(self):

        # Create sprite lists
        self.all_sprites_list = pygame.sprite.Group()
        self.player_list = pygame.sprite.Group() #RenderUpdates()

        self.player = Player(20, 15)
        self.player_list.add(self.player)
        self.all_sprites_list.add(self.player)
        
        # Decides player position
        self.player.rect.x = 40
        self.player.rect.y = 405

        self.cam_world_pos_x = 350
        self.cam_world_pos_y = 1000
            
    def process_events(self):
        for event in pygame.event.get(): # User did something           
            if event.type == pygame.QUIT: # If user clicked close 
                return True # Flag that we are done so we exit this loop
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.player.game_over_lose:
                    self.__init__()

                if self.player.win_level or self.level_count in [0,5]:
                    self.level_count += 1
                    self.__init__()
                    
                if self.level_count == 6:
                    self.level_count = 1
                    self.__init__()
            '''
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.cam_world_pos_x -= 20
                if event.key == pygame.K_RIGHT:
                    self.cam_world_pos_x += 20
                if event.key == pygame.K_UP:
                    self.cam_world_pos_y -= 20
                if event.key == pygame.K_DOWN:
                    self.cam_world_pos_y += 20
            '''                
                    
            if not self.player.win_level or self.player.game_over_lose:   
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.player.changespeed_x(-6)
                    if event.key == pygame.K_RIGHT:
                        self.player.changespeed_x(6)
                    if event.key == pygame.K_UP:
                        self.player.jump(self.block_list)
                    if event.key == pygame.K_DOWN:
                        self.player.changespeed_y(6)
                        
                if event.type == pygame.KEYUP: 
                    if event.key == pygame.K_LEFT: 
                        self.player.changespeed_x(-0)
                    if event.key == pygame.K_RIGHT: 
                        self.player.changespeed_x(0)
                
        return False

    def run_logic(self):
        
        self.player.calc_grav()
        self.player.updte(self.block_list, self.goal_list, self.coins)
        
        if self.player.rect.x >= 400:
            diff = self.player.rect.x - 400
            self.cam_world_pos_x += diff
            self.player.rect.x = 400
    
        if self.player.rect.x <= 10:
            self.player.rect.x = 10
            
    def tmx(self, screen):            
        screen.fill(BLACK)
            
        assert self.level_map.orientation == "orthogonal"
        self.renderer.set_camera_position_and_size(self.cam_world_pos_x, self.cam_world_pos_y, \
                                                 SCREEN_SIZE[0], SCREEN_SIZE[1])

        sprite_layers = tiledtmxloader.helperspygame.get_layers_from_map(self.resources)
        sprite_layers = [layer for layer in sprite_layers if not layer.is_object_group]
  
        for sprite_layer in sprite_layers:
            if sprite_layer.is_object_group:
                        # we dont draw the object group layers
                        # you should filter them out if not needed
                continue
            else:
                self.renderer.render_layer(screen, sprite_layer)
            
def main():
    
    #Initialise pygame
    pygame.init() 

    # Create screen and caption
    screen = pygame.display.set_mode(SCREEN_SIZE) 
    pygame.display.set_caption("Masterful Block Jump")
                
    #Loop until the user clicks the close button. 
    done = False
  
    # Used to manage how fast the screen updates 
    clock = pygame.time.Clock() 

    game = Game()
    game.tmx(screen)
    
    # -------- Main Program Loop ----------- 
    while not done:

        done = game.process_events()
        game.run_logic()
        
        game.player_list.draw(screen)

        print(clock.get_fps())
        
        clock.tick(60)
        pygame.display.flip()
 
    pygame.quit ()

if __name__ == "__main__":
    main()
