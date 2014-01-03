exec(open("importer.py").read()) # Add tmx to path (ignore this)

import pygame
import tmx

# Enemy and Player superclass
class Char(pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super(Char, self).__init__(*groups)
        
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.resting = False
        self.dy = 0

        #animation constants
        self.i = 7
        self.j = 7
    
    def update(self, dt, game, left_anim, right_anim, speed):
        last = self.rect.copy()
        
        for i in left_anim:
            i.set_colorkey((255, 255, 255))
        for i in right_anim:
            i.set_colorkey((255, 255, 255))

        if self.direction == -1:
            self.rect.x -= speed * dt
            if self.i <= 7 and self.i > 0:
                self.image = self.left_anim[0]
                self.i -= 1
            elif self.i <= 0 and self.i > -7:
                self.image = self.left_anim[1]
                self.i -= 1
            elif self.i <= -7:
                self.i = 7

        if self.direction == 1:
            self.rect.x += speed * dt
            #animation
            if self.j <= 7 and self.j > 0:
                self.image = self.right_anim[0]
                self.j -= 1
            elif self.j <= 0 and self.j > -7:
                self.image = self.right_anim[1]
                self.j -= 1
            elif self.j <= -7:
                self.j = 7

        # Gravity
        self.dy = min(400, self.dy + 50)
        self.rect.y += self.dy * dt

        # Platform collision detection
        new = self.rect
        self.resting = False
        for cell in game.tilemap.layers['triggers'].collide(new, 'platform'):
            blockers = cell['platform']
            if 'l' in blockers and last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if 'r' in blockers and last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if 't' in blockers and last.bottom <= cell.top and new.bottom > cell.top:
                self.resting = True
                new.bottom = cell.top
                self.dy = 0
            if 'b' in blockers and last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0

        for mov_plat in pygame.sprite.spritecollide(self, game.mov_plats, False):
            self.rect.bottom = mov_plat.rect.top
            mov_plat.dy = 0
            self.resting = True

class Spider(Char):

    image = pygame.image.load('spd1_lf1.gif')
    left_anim = [image, pygame.image.load('spd1_lf2.gif')]
    right_anim = [pygame.image.load('spd1_rt1.gif'), pygame.image.load('spd1_rt2.gif')]
    hp = 50
    direction = -1

    def update(self, dt, game):
        Char.update(self, dt, game, self.left_anim, self.right_anim, 50)
        
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction == 1:
                self.rect.right = cell.left
            elif self.direction == -1:
                self.rect.left = cell.right
            self.direction *= -1

class Skeleton(Char):

    image = pygame.image.load('skl1_lf1.gif')
    left_anim = [image, pygame.image.load('skl1_lf2.gif')]
    right_anim = [pygame.image.load('skl1_rt1.gif'), pygame.image.load('skl1_rt2.gif')]
    hp = 100
    direction = -1
    
    def update(self, dt, game):
        Char.update(self, dt, game, self.left_anim, self.right_anim, 20)
        
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction == 1:
                self.rect.right = cell.left
            elif self.direction == -1:
                self.rect.left = cell.right + 1
            self.direction *= -1

class Player(Char):

    image = pygame.image.load('man2_rt1.gif')
    left_anim = [pygame.image.load('man2_lf1.gif'), pygame.image.load('man2_lf2.gif')]
    right_anim = [image, pygame.image.load('man2_rt2.gif')]

    direction = 1

    gun_cooldown = 0
    gun_cooldown_two = 0
    gunpoint = 1
    cnt = 0

    invinc = 0

    coin_tally = 0
    weapon = 0
    hp = 200
    
    def update(self, dt, game):
        Char.update(self, dt, game, self.left_anim, self.right_anim, 300)

        self.direction = 0
        
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.direction = -1
            self.gunpoint = -1

        if key[pygame.K_RIGHT]:
            self.direction = 1
            self.gunpoint = 1

        if self.resting and key[pygame.K_UP]:
            self.dy = -700

        # Gun
        if key[pygame.K_RSHIFT] and not (self.gun_cooldown or self.gun_cooldown_two):
            if self.gunpoint == 1:
                Bullet(self.rect.midright, 1, game.playersprites)
            elif self.gunpoint == -1:
                Bullet(self.rect.midleft, -1, game.playersprites)
            self.cnt += 1
            self.gun_cooldown_two = 1
            if self.cnt == 3:
                self.gun_cooldown = .75
                self.cnt = 0
        self.gun_cooldown_two = max(0, self.gun_cooldown - dt)
        self.gun_cooldown = max(0, self.gun_cooldown - dt)

        # coins
        for coin in pygame.sprite.spritecollide(self, game.coins, True):
            self.coin_tally += 1

        for enemy in pygame.sprite.spritecollide(self, game.enemies, False):
            if not self.invinc:
                self.rect.x -= 20 * self.direction
                self.hp -= 20
                self.invinc = .75
        self.invinc = max(0, self.invinc - dt)

        if self.invinc:
            self.image.set_colorkey((0, 0, 0))
    
        game.tilemap.set_focus(self.rect.x, self.rect.y)

class Coin(pygame.sprite.Sprite):

    image = pygame.image.load('coin.png')
    image.set_colorkey((255, 255, 255))

    def __init__(self, location, *groups):
        super(Coin, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
    

class MovingPlatform(pygame.sprite.Sprite):

    image = pygame.image.load('mov_plat.png')
    image.set_colorkey((255, 255, 255))
    delta = -3
    init_y = 0

    def __init__(self, location, *groups):
        super(MovingPlatform, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.init_y = self.rect.y

    def update(self, dt, game):
        self.rect.y += self.delta
        if self.rect.y <= self.init_y - 500:
            self.delta *= -1
        elif self.rect.y > self.init_y:
            self.delta *= -1

class Bullet(pygame.sprite.Sprite):
    image = pygame.image.load('bullet.png')
    def __init__(self, location, direction, *groups):
        super(Bullet, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.direction = direction
        self.lifespan = 1

    def update(self, dt, game):
        self.lifespan -= dt
        if self.lifespan < 0:
            self.kill()
            return
        self.rect.x += self.direction * 400 * dt

        for enemy in pygame.sprite.spritecollide(self, game.enemies, False):
            enemy.hp -= 20
            enemy.rect.x -= -7 * self.direction
            if enemy.hp <= 0:
                enemy.kill()
            self.kill()

class Game(object):
    def main(self, screen):
        clock = pygame.time.Clock()
        
        background = pygame.image.load('background.png')

        self.tilemap = tmx.load('Lvl1redux.tmx', screen.get_size())

        self.sprites = tmx.SpriteLayer()
        self.tilemap.layers.append(self.sprites)

        self.playersprites = tmx.SpriteLayer()
        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        self.player = Player((start_cell.px, start_cell.py), self.playersprites)
        self.tilemap.layers.append(self.playersprites)

        # bliting coin tally
        totalcoins = 0
        font = pygame.font.Font(None, 25)     

        self.enemies = tmx.SpriteLayer()
        
        self.spiders = tmx.SpriteLayer()
        for spider in self.tilemap.layers['triggers'].find('enemy'):
            Spider((spider.px, spider.py), self.enemies)
        self.tilemap.layers.append(self.spiders)

        self.skeletons = tmx.SpriteLayer()
        for skeleton in self.tilemap.layers['triggers'].find('skeleton'):
            Skeleton((skeleton.px, skeleton.py), self.enemies)
        self.tilemap.layers.append(self.skeletons)
        self.tilemap.layers.append(self.enemies)

        self.coins = tmx.SpriteLayer()
        totalcoins = 0
        for coin in self.tilemap.layers['triggers'].find('coin'):
            Coin((coin.px, coin.py), self.coins)
            totalcoins += 1
        self.tilemap.layers.append(self.coins)
        
        self.mov_plats = tmx.SpriteLayer()
        for mov_plat in self.tilemap.layers['triggers'].find('mov_plat'):
            MovingPlatform((mov_plat.px, mov_plat.py), self.mov_plats)
        self.tilemap.layers.append(self.mov_plats)        

        done = False
        while not done:
            dt = clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                if self.player.rect.y > 950 and event.type == pygame.MOUSEBUTTONDOWN:
                    self.main(screen)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LALT:
                        self.main(screen)

            self.tilemap.update(dt / 1000., self)
            screen.blit(background, (0, 0))
            self.tilemap.draw(screen)

            #blitting coin tally
            coin_text = font.render("Coins: "+ str(self.player.coin_tally) + "/" +
                                str(totalcoins), True, (255, 255, 255))   
            screen.blit(coin_text, [530, 0])
            
            pygame.display.flip()
                
        pygame.quit()

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    Game().main(screen)

