import pygame as pg
import pygame.event
import numpy
from math import sin, cos, acos, hypot
import os
import pickle
from twisted.internet import protocol, reactor
import threading
from socket import socket, AF_INET, SOCK_DGRAM
from net_functions import *
from copy import copy, deepcopy
import time

pg.init()
true_width, true_height = pygame.display.Info().current_w, pygame.display.Info().current_h
WIDTH = int(true_width * 0.8)
HEIGHT = int(true_height * 0.8)
FPS = 60
running = True
clock = pg.time.Clock()
screen = pg.display.set_mode((WIDTH, HEIGHT))
ASSETS_PATH = 'Assets/'
controls = [[pg.K_w, pg.K_d, pg.K_s, pg.K_a, pg.K_SPACE, pg.KMOD_SHIFT]]
G = 1


# xd

class EchoServer(protocol.Protocol):
    def connectionMade(self):
        game.connected = 1

    def dataReceived(self, data):
        recv_pack = eval(data.decode())
        game.pack = recv_pack
        send_pack = game.info
        self.transport.write(str(send_pack).encode())
        clock.tick(FPS)

    def connectionLost(self, reason):
        game.connected = 0


class EchoClient(protocol.Protocol):
    def connectionMade(self):
        game.connected = 1
        send_pack = game.info
        self.transport.write(str(send_pack).encode())
        clock.tick(FPS)

    def dataReceived(self, data):
        recv_pack = eval(data.decode())
        game.pack = recv_pack
        send_pack = game.info
        self.transport.write(str(send_pack).encode())
        clock.tick(FPS)

    def connectionLost(self, reason):
        game.connected = 0
        print("connection lost")


class ClientFactory(protocol.ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed - goodbye!")
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print("Connection lost - goodbye!")
        reactor.stop()


def client(ip):
    f = ClientFactory()
    reactor.connectTCP(ip, 8080, f)
    reactor.run(installSignalHandlers=False)


def server():
    print('server started')
    factory = protocol.ServerFactory()
    factory.protocol = EchoServer
    reactor.listenTCP(8080, factory)
    reactor.run(installSignalHandlers=False)


class Main:
    def __init__(self):
        self.map = Map()
        self.menu = Menu()
        self.camera = Camera()
        self.pers1 = Human()
        self.pers2 = Human()
        self.pers1.enemy = self.pers2
        self.pers2.enemy = self.pers1
        self.pers2.main_chr = 0
        self.pers2.rect.x, self.pers2.rect.y = self.pers1.truecords
        self.gui = GUI(self.pers1, self.pers2)
        self.mode = 0
        self.events = []
        self.connected = 0
        self.pack = None
        self.host = True
        self.multiplayer_flg = 0

    def update(self):
        self.events = []
        if self.mode == 0:
            self.mode = self.menu.update()
        if self.mode == 1:
            self.map.update()
            self.camera.update()
            self.pers1.update()
            self.pers2.update()
            self.gui.update(self.pers1, self.pers2)
        if self.mode == 2:
            if self.connected and self.pack:
                self.check_pack()
            else:
                ...
            if self.host:
                if not self.multiplayer_flg:
                    self.server_thread = threading.Thread(target=server)
                    self.server_thread.start()
                    self.multiplayer_flg = 1
            else:
                if not self.multiplayer_flg:
                    opn = scan_lan(8080)
                    self.client_thread = threading.Thread(target=client, args=[opn[0]])
                    self.client_thread.start()
                    self.multiplayer_flg = 1
            self.map.update()
            self.camera.update()
            self.pers1.update()
            self.pers2.update()
            self.gui.update(self.pers1, self.pers2)
            if self.pers1.HP <= 0:
                self.mode = 3
            if self.pers2.HP <= 0:
                self.mode = 3
            # self.pers1.HP -= 1
            # self.pers2.HP -= 1
        if self.mode == 3:
            print('GAME OVER!!!')
        self.info = [self.pers1.info]

    def check_pack(self):
        # pack = [self.pers1.info, self.pers2.info]
        # persinfo = [self.HP, self.maxHP, self.name, self.pic, animsforinfo, self.animation_counter]
        pack = deepcopy(self.pack)
        print(pack)
        characters = [self.pers2]
        for i in range(1):
            characters[i].HP = pack[i][0]
            characters[i].maxHP = pack[i][1]
            characters[i].name = pack[i][2]
            characters[i].pic = pack[i][3]
            '''anims = deepcopy(pack[i][4])
            for x in range(len(anims)):
                for y in range(len(anims[x])):
                    # print(anims[x][y])
                    anims[x][y] = (pg.image.load(anims[x][y][0]) if anims[x][y][-1] > 0 else pygame.transform.flip(
                        pg.image.load(anims[x][y][0]), True, False), anims[x][y][0], anims[x][y][-1])
            characters[i].animations = anims.copy()'''
            characters[i].animation_counter = pack[i][4].copy()
            characters[i].vertical_speed = pack[i][5]
            characters[i].horizontal_speed = pack[i][6]
            characters[i].x = pack[i][7]
            characters[i].y = pack[i][8]
            # characters[i].rect.x = pack[i][7]
            # characters[i].rect.y = pack[i][8]
    # def information_gathering(self):


class GUI:
    # если будем менять настройки разрешения во время работы игры надо будет заинитить гуи заново
    # 1536 864
    def __init__(self, chr1, chr2):
        self.chr1 = chr1
        self.chr2 = chr2

        path = os.path.join(os.path.dirname(__file__), 'Assets')
        path = os.path.join(path, 'Sprites')

        self.chr_font = pygame.font.Font(None, 40)
        self.chr1_font_color = (63, 72, 204)
        self.chr2_font_color = (255, 0, 0)

        self.text_chr1 = self.chr_font.render(chr1.name, True, self.chr1_font_color)
        self.text_chr2 = self.chr_font.render(chr2.name, True, self.chr2_font_color)

        self.text_chr1_rect = self.text_chr1.get_rect()
        self.text_chr1_rect.left = HEIGHT // 40
        self.text_chr1_rect.top = HEIGHT // 40

        self.text_chr2_rect = self.text_chr2.get_rect()
        self.text_chr2_rect.right = WIDTH - HEIGHT // 40
        self.text_chr2_rect.top = HEIGHT // 40

        self.pic1 = chr1.pic
        self.image_chr1 = pygame.image.load(os.path.join(path, self.pic1)).convert()
        self.image_chr1 = pygame.transform.scale(self.image_chr1, (HEIGHT // 5, HEIGHT // 5))
        self.image_chr1_rect = self.image_chr1.get_rect()
        self.image_chr1_rect.left = self.text_chr1_rect.left
        self.image_chr1_rect.top = self.text_chr1_rect.bottom + HEIGHT // 54

        self.pic2 = chr2.pic
        self.image_chr2 = pygame.image.load(os.path.join(path, self.pic2)).convert()
        self.image_chr2 = pygame.transform.scale(self.image_chr2, (HEIGHT // 5, HEIGHT // 5))
        self.image_chr2_rect = self.image_chr2.get_rect()
        self.image_chr2_rect.right = WIDTH - HEIGHT // 40
        self.image_chr2_rect.top = self.text_chr2_rect.bottom + HEIGHT // 54

        self.image_hp1 = pygame.image.load(os.path.join(path, 'hp_bar.png'))
        self.image_hp1 = pygame.transform.scale(self.image_hp1, (HEIGHT // 5, HEIGHT // 21))
        self.image_hp1_rect = self.image_hp1.get_rect()
        self.image_hp1_rect.left = self.text_chr1_rect.left
        self.image_hp1_rect.top = self.image_chr1_rect.bottom + HEIGHT // 54

        self.image_hp2 = pygame.image.load(os.path.join(path, 'hp_bar.png'))
        self.image_hp2 = pygame.transform.scale(self.image_hp2, (HEIGHT // 5, HEIGHT // 21))
        self.image_hp2_rect = self.image_hp2.get_rect()
        self.image_hp2_rect.right = self.text_chr2_rect.right
        self.image_hp2_rect.top = self.image_chr2_rect.bottom + HEIGHT // 54

        self.green_hp1 = pygame.Surface(
            (HEIGHT // 5 - self.image_hp1_rect.width // 6, HEIGHT // 21 // 3 * 2 - HEIGHT // 21 // 3 * 2 * 0.1))
        self.green_hp1_rect = self.green_hp1.get_rect()
        self.green_hp1_rect.left = self.image_hp1_rect.left + self.image_hp1_rect.width // 6
        self.green_hp1_rect.centery = self.image_hp1_rect.centery

        self.red_hp1 = pygame.Surface((0, HEIGHT // 21 // 3 * 2 - HEIGHT // 21 // 3 * 2 * 0.1))
        self.red_hp1_rect = self.red_hp1.get_rect()
        self.red_hp1_rect.height = self.green_hp1_rect.height

        self.green_hp2 = pygame.Surface(
            (HEIGHT // 5 - self.image_hp2_rect.width // 6, HEIGHT // 21 // 3 * 2 - HEIGHT // 21 // 3 * 2 * 0.1))
        self.green_hp2_rect = self.green_hp2.get_rect()
        self.green_hp2_rect.left = self.image_hp2_rect.left + self.image_hp2_rect.width // 6
        self.green_hp2_rect.centery = self.image_hp2_rect.centery

        self.red_hp2 = pygame.Surface((0, HEIGHT // 21 // 3 * 2 - HEIGHT // 21 // 3 * 2 * 0.1))
        self.red_hp2_rect = self.red_hp1.get_rect()
        self.red_hp2_rect.height = self.green_hp2_rect.height

        self.to_blit = [[self.text_chr1, self.text_chr1_rect], [self.text_chr2, self.text_chr2_rect],
                        [self.image_chr1, self.image_chr1_rect], [self.image_chr2, self.image_chr2_rect],
                        [self.green_hp1, self.green_hp1_rect], [self.green_hp2, self.green_hp2_rect],
                        [self.red_hp1, self.red_hp1_rect], [self.red_hp2, self.red_hp2_rect],
                        [self.image_hp1, self.image_hp1_rect], [self.image_hp2, self.image_hp2_rect]]

    def update(self, chr1, chr2):
        self.to_blit = [[self.text_chr1, self.text_chr1_rect], [self.text_chr2, self.text_chr2_rect],
                        [self.image_chr1, self.image_chr1_rect], [self.image_chr2, self.image_chr2_rect],
                        [self.green_hp1, self.green_hp1_rect], [self.green_hp2, self.green_hp2_rect],
                        [self.red_hp1, self.red_hp1_rect], [self.red_hp2, self.red_hp2_rect],
                        [self.image_hp1, self.image_hp1_rect], [self.image_hp2, self.image_hp2_rect]]

        self.chr1 = chr1
        self.chr2 = chr2

        self.green_hp1.fill((0, 255, 0))
        self.red_hp1 = pygame.Surface(
            (self.green_hp1_rect.width * (1 - self.chr1.HP / self.chr1.maxHP), self.green_hp1_rect.height))
        self.red_hp1_rect = self.red_hp1.get_rect()
        self.red_hp1_rect.right = self.green_hp1_rect.right
        self.red_hp1_rect.top = self.green_hp1_rect.top
        self.red_hp1.fill((255, 0, 0))

        self.green_hp2.fill((0, 255, 0))
        self.red_hp2 = pygame.Surface(
            (self.green_hp2_rect.width * (1 - self.chr2.HP / self.chr2.maxHP), self.green_hp2_rect.height))
        self.red_hp2_rect = self.red_hp2.get_rect()
        self.red_hp2_rect.right = self.green_hp2_rect.right
        self.red_hp2_rect.top = self.green_hp2_rect.top
        self.red_hp2.fill((255, 0, 0))

        self.blit_gui()

    def blit_gui(self):
        for el in self.to_blit:
            screen.blit(el[0], el[1])


class Map:
    def __init__(self):
        self.hitboxes = numpy.loadtxt('xd.txt')
        self.size = (len(self.hitboxes), len(self.hitboxes[0]))

        self.mapimage = pygame.image.load('map.png')
        self.mapsprite = pygame.sprite.Sprite()
        self.mapsprite.image = self.mapimage
        self.mapsprite.rect = self.mapsprite.image.get_rect()
        print('map initialized')

    def update(self):
        self.render()
        # game.camera.move(1, 1)

    def render(self):
        camerax, cameray = game.camera.cam_x, game.camera.cam_y
        self.visible_area = self.hitboxes[camerax:camerax + int(WIDTH), cameray:cameray + int(HEIGHT)]
        self.mapsprite.rect.x = -camerax
        self.mapsprite.rect.y = -cameray
        screen.blit(self.mapsprite.image, self.mapsprite.rect)


class Menu:
    def __init__(self):
        print('menu initialized')

    def update(self):
        btn = self.check_buttons()
        if btn == 1:
            return 1
        elif btn == 2:
            return 2

    def check_buttons(self):
        return 2


class Camera:
    def __init__(self):
        self.cam_x = 0
        self.cam_y = 0

        print('camera initialized')

    def update(self):
        # self.cam_x = int(len(game.map.hitboxes) - WIDTH)
        # self.cam_y = int(len(game.map.hitboxes[0]) - HEIGHT)
        # print(self.cam_x, self.cam_y)
        ...

    def set(self, x, y):
        ans = [0, 0]
        if x >= game.map.size[0] - WIDTH:
            print('horizontal border ->')
            ans[0] = 1
        if x < 0:
            print('horizontal border <-')
            ans[0] = -1
        if ans[0] == 0:
            self.cam_x = x
        if y >= game.map.size[1] - HEIGHT:
            print('vertical border ->')
            ans[1] = 1
        if y < 0:
            print('vertical border <-')
            ans[1] = -1
        if ans[1] == 0:
            self.cam_y = y
        return ans

    def move(self, x, y):
        '''ans = [0, 0]
        if x >= game.map.size[0] - WIDTH:
            print('horizontal border')
            ans[0] = 1
        else:
            self.cam_x += x
        if y >= game.map.size[1] - HEIGHT:
            print('vertical border')
            ans[1] = 1
        else:
            self.cam_y += y

        return ans'''
        ...


class Object:
    def __init__(self):
        pass


class Pawn:
    def __init__(self):
        self.truecords = (WIDTH // 2, HEIGHT // 2)
        self.x, self.y = 0, 0
        pygame.sprite.Sprite.__init__(self)
        self.group = pygame.sprite.Group()
        self.group.add(self)
        self.combo = []
        self.last_combo_time = time.time()
        self.animation_counter = [0, 1]
        self.default_animation = None
        self.current_animation = None
        self.controls_num = 0
        self.animframes_divisor = 1
        self.horizontal_speed = 0
        self.vertical_speed = 0
        self.last_direction = 1
        self.jump_power = 3
        self.grav_accel = G
        self.onfloor = 0
        # self.jump_cooldown =
        self.jumpflg = 0
        self.lascoords = (None, None)
        self.cam_xlock, self.cam_ylock = 0, 0
        self.xcamflg, self.ycamflg = 0, 0
        self.left, self.right, self.top, self.bottom = 0, 0, 0, 0
        self.cd = {self.mouse: 0}
        self.maxcd = {self.mouse: 15}
        self.stun_cnt = 0
        self.hang_cnt = 0

    def move(self, x, y):
        # print(x, y)
        camerax, cameray = game.camera.cam_x, game.camera.cam_y
        x2 = self.rect.x
        y2 = self.rect.y
        w = self.rect.w
        h = self.rect.h
        b = self.rect.bottom
        t = self.rect.top
        lastx, lasty = 0, 0
        area = game.map.hitboxes
        # print(area[self.rect.x, self.rect.y]) if area[self.rect.x, self.rect.y] else 0
        self.left, self.right, self.top, self.bottom = False, False, False, False
        for j in range(1, abs(x) + 1):
            if x2 - j <= 0:
                self.left = True
            elif x2 + w + j >= WIDTH:
                self.right = True
            else:
                if not self.left:
                    self.left = all([area[camerax + x2 - j, cameray + i] for i in range(y2, y2 + h)])
                if not self.right:
                    self.right = all([area[camerax + x2 + w + j, cameray + i] for i in range(y2, y2 + h)])

            if self.left:
                lastx = -j + 1
                break
            if self.right:
                lastx = j - 1
                break

        for j in range(1, abs(y) + 1):
            if y2 - j <= 0:
                self.top = True
            if y2 + h + j >= HEIGHT:
                self.bottom = True
            else:
                if not self.top:
                    self.top = all([area[camerax + i, cameray + y2 - j] for i in range(x2, x2 + w)])
                if not self.bottom:
                    self.bottom = all([area[camerax + i, cameray + y2 + h + j] for i in range(x2, x2 + w)])
                flg = 1
            if self.top:
                lasty = -j + 1
                break
            if self.bottom:
                lasty = j - 1
                break

        if ((x < 0 and not self.left) or (x > 0 and not self.right)) and WIDTH > self.rect.x + x > 0:
            self.x += x
        else:
            self.x += lastx

        if ((y < 0 and not self.top) or (y > 0 and not self.bottom)) and HEIGHT > self.rect.y + y > 0:
            self.y += y
        else:
            self.y += lasty

    def cam_targeting(self, main):
        tx, ty = self.truecords
        if main:
            r1, r2 = game.camera.cam_x if self.xcamflg else self.x, game.camera.cam_y if self.ycamflg else self.y
            x = game.camera.set(r1, r2)
            camx, camy = game.camera.cam_x, game.camera.cam_y
            if x[0] == 1 or self.rect.x > tx + abs(self.horizontal_speed):
                self.xcamflg = 1
                self.rect.x = self.x - camx + tx
            elif x[0] == -1 or self.rect.x < tx - abs(self.horizontal_speed):
                self.xcamflg = -1
                self.rect.x = self.x - camx + tx
            else:
                self.xcamflg = 0
                # self.rect.x = tx
            if x[1] == 1 or self.rect.y > ty + abs(self.vertical_speed):
                self.ycamflg = 1
                self.rect.y = self.y - camy + ty
            elif x[1] == -1 or self.rect.y < ty - abs(self.vertical_speed):
                self.ycamflg = -1
                self.rect.y = self.y - camy + ty
            else:
                self.ycamflg = 0
                # self.rect.y = ty
        else:
            camx, camy = game.camera.cam_x, game.camera.cam_y
            self.rect.x = self.x - camx + tx
            self.rect.y = self.y - camy + ty

    def events_check(self):
        keyboard = pygame.key.get_pressed()
        keys = []
        mouse = pygame.mouse.get_pressed()
        if keyboard[pygame.K_g]:
            self.knockback(150, 14)
        for i in range(len(controls[self.controls_num])):
            x = controls[self.controls_num][i]
            if keyboard[x]:
                keys.append(i)
        self.control(keys, mouse)

    def physics(self):
        if self.horizontal_speed < 0:
            self.last_direction = 0
        if self.horizontal_speed > 0:
            self.last_direction = 1
        self.move(int(self.horizontal_speed), int(self.vertical_speed))
        self.onfloor = self.bottom
        if self.onfloor:
            self.grav_accel = G
            self.vertical_speed = 0
            self.horizontal_speed += (-self.horizontal_speed) / 5
        else:
            # self.grav_accel += G
            self.vertical_speed += self.grav_accel
        self.horizontal_speed = 0 if abs(self.horizontal_speed) < 1 else self.horizontal_speed
        self.vertical_speed = 0 if abs(self.vertical_speed) < 1 else self.vertical_speed
        if self.hang_cnt:
            self.vertical_speed = 0
            self.horizontal_speed = 0
            self.hang_cnt -= 1

    def animation_update(self):
        animlen = len(self.current_animation)
        if self.animation_counter[0] / self.animframes_divisor < animlen:
            self.image = self.current_animation[self.animation_counter[0] // self.animframes_divisor]
            self.animation_counter[0] += 1
        else:
            if self.animation_counter[1]:
                self.animation_counter[0] = 0
            else:
                self.current_animation = self.default_animation()
                self.animation_counter[0] = 0
                self.animframes_divisor = 1

    def set_animation(self, animation, loop=True, div=1):
        if self.current_animation != animation:
            self.animframes_divisor = div
            self.current_animation = animation
            self.animation_counter[0] = 0
            if loop:
                self.animation_counter[1] = 1
            else:
                self.animation_counter[1] = 0

    def knockback(self, alpha, velocity):
        if not self.onfloor:
            velocity /= 3
        self.vertical_speed -= velocity * sin(alpha / 57.3)
        self.horizontal_speed += velocity * cos(alpha / 57.3)

    def update_cd(self):

        for key in self.cd.keys():
            if self.cd[key] != 0:
                if self.cd[key] < self.maxcd[key]:
                    self.cd[key] += 1
                else:
                    self.cd[key] = 0

    def mouse(self, alpha):
        self.enemy.stun_cnt = max(30, self.enemy.stun_cnt)
        self.enemy.hang_cnt = max(30, self.enemy.hang_cnt)
        self.cd[self.mouse] = 1
        if alpha > 340 or alpha <= 20:
            self.combo.append(1)
        elif alpha > 20 and alpha <= 90:
            self.combo.append(-3)
        elif alpha > 90 and alpha <= 160:
            self.combo.append(-2)
        elif alpha > 160 and alpha <= 200:
            self.combo.append(-1)
        elif alpha > 200 and alpha <= 270:
            self.combo.append(3)
        elif alpha > 270 and alpha <= 340:
            self.combo.append(2)
        self.attack()


class Human(Pawn, pygame.sprite.Sprite):
    def __init__(self):
        super(Human, self).__init__()
        animpath_run = ASSETS_PATH + 'Sprites/Animations/running_1/'
        animpath_atk = ASSETS_PATH + 'sprites/Animations/attacking/'
        self.image = pg.image.load(ASSETS_PATH + 'Sprites/Static/Human/idle1.png')
        self.idle_right = [pg.image.load(ASSETS_PATH + 'Sprites/Static/Human/idle1.png')]
        self.idle_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.idle_right))
        self.default_animation = lambda: self.idle_right if self.last_direction else self.idle_left
        self.current_animation = self.default_animation()
        self.rect = self.image.get_rect()
        self.runanimation_right = [pygame.image.load(animpath_run + f'{i}.png') for i in range(1, 7)]
        self.runanimation_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.runanimation_right))
        self.stoppinganimation_right = [pygame.image.load(ASSETS_PATH + 'Sprites/stopping.png')]
        self.stoppinganimation_left = list(
            map(lambda i: pygame.transform.flip(i, True, False), self.stoppinganimation_right))

        '''
        self.atkanimation_right = [pygame.image.load(animpath_atk + f'pr_{i}.png') for i in range(1, 6)]
        self.atkanimation_left = [pygame.transform.flip(pygame.image.load(animpath_atk + f'pr_{i}.png'), True, False)
                                  for i in range(1, 6)]
        self.atkanimation_upright = [pygame.image.load(animpath_atk + f'pur_{i}.png') for i in range(1, 6)]
        self.atkanimation_upleft = [pygame.transform.flip(pygame.image.load(animpath_atk + f'pur_{i}.png'), True, False)
                                    for i in range(1, 6)]
        self.atkanimation_downright = [pygame.image.load(animpath_atk + f'pdr_{i}.png') for i in range(1, 6)]
        self.atkanimation_downleft = [
            pygame.transform.flip(pygame.image.load(animpath_atk + f'pdr_{i}.png'), True, False) for i in range(1, 6)]
        

        self.animations = [self.idle_right, self.idle_left, self.runanimation_left, self.runanimation_right,
                           self.atkanimation_right,
                           self.atkanimation_upright, self.atkanimation_upleft, self.atkanimation_left,
                           self.atkanimation_downleft, self.atkanimation_downright, self.stoppinganimation_right,
                           self.stoppinganimation_left]'''
        self.combo1_1_right = [pygame.image.load(ASSETS_PATH + f'Sprites/Animations/combo_1/attack1_{i}.png') for i in
                               range(1, 4)]
        self.combo1_2_right = [pygame.image.load(ASSETS_PATH + f'Sprites/Animations/combo_1/attack2_{i}.png') for i in
                               range(1, 6)]
        self.combo1_3_right = [pygame.image.load(ASSETS_PATH + f'Sprites/Animations/combo_1/attack3_{i}.png') for i in
                               range(1, 2)]
        self.combo1_4_right = [pygame.image.load(ASSETS_PATH + f'Sprites/Animations/combo_1/attack4_{i}.png') for i in
                               range(1, 5)]
        self.combo1_1_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.combo1_1_right))
        self.combo1_2_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.combo1_2_right))
        self.combo1_3_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.combo1_3_right))
        self.combo1_4_left = list(map(lambda i: pygame.transform.flip(i, True, False), self.combo1_4_right))

        self.animation_counter = [0, 0]
        self.moves = []
        self.pic = 'Human.png'
        self.name = 'Human'
        self.maxHP = 1000
        self.main_chr = 1
        self.HP = self.maxHP
        self.combo_expiration = 1
        self.info = [self.HP, self.maxHP, self.name, self.pic, self.animation_counter, self.vertical_speed,
                     self.horizontal_speed, self.x, self.y, self.rect.x, self.rect.y]
        self.enemy = ''

        self.enemygroup = ''

    def update(self):
        if self.main_chr:
            self.events_check()
        self.cam_targeting(self.main_chr)

        self.physics()
        # self.rect.x, self.rect.y = self.x, self.y
        self.animation_update()
        self.group.draw(screen)
        self.info = [self.HP, self.maxHP, self.name, self.pic, self.animation_counter, self.vertical_speed,
                     self.horizontal_speed, self.x, self.y, self.rect.x, self.rect.y]

        self.update_cd()

    def control(self, keys, mouse):
        speed = 3
        right, left = 1, 3
        keys_1 = pygame.key.get_pressed()
        if self.current_animation == self.runanimation_right and not right in keys:
            self.set_animation(self.stoppinganimation_right, True)
        if self.current_animation == self.runanimation_left and not left in keys:
            self.set_animation(self.stoppinganimation_left, True)
        if self.horizontal_speed == 0 and (
                self.current_animation == self.stoppinganimation_right or self.current_animation == self.stoppinganimation_left):
            if self.last_direction == 1:
                self.set_animation(self.idle_right, True)
            else:
                self.set_animation(self.idle_left, True)
        if keys_1[pygame.K_h]:
            self.HP -= 1
        if not self.stun_cnt:
            if 0 in keys:
                ...
                # self.move(0, -speed)
            if 2 in keys:
                ...
                # self.move(0, speed)
            if right in keys and self.bottom:
                self.horizontal_speed += speed
                self.set_animation(self.runanimation_right)
                # self.move(speed, 0)
            if left in keys and self.bottom:
                self.horizontal_speed -= speed
                self.set_animation(self.runanimation_left)
                # self.move(-speed, 0)

            if 4 in keys and (self.jumpflg or self.bottom) and self.vertical_speed > -15:
                self.jumpflg = 1
                self.vertical_speed += -self.jump_power
            else:
                self.jumpflg = 0

            if keys_1[pygame.K_b]:
                self.debug_stun()
            if mouse[0] and self.cd[self.mouse] == 0:
                pos = pygame.mouse.get_pos()
                x = pos[0] - int(WIDTH // 2)
                y = int(HEIGHT // 2) - pos[1]
                sinalpha = y / hypot(x, y)
                cosalpha = x / hypot(x, y)
                if sinalpha < 0:
                    cosalpha = -cosalpha
                alpha = acos(cosalpha) * 57.3
                if sinalpha < 0:
                    alpha += 180
                self.mouse(alpha)

        else:
            print('here')
            self.stun_cnt -= 1

    def debug_stun(self):
        self.stun_cnt = max(30, self.stun_cnt)
        self.hang_cnt = max(30, self.hang_cnt)

    def attack(self):
        print(self.combo)
        if time.time() - self.last_combo_time >= self.combo_expiration:
            self.combo = [self.combo[-1]]
        if self.combo == [1]:
            self.set_animation(self.combo1_1_right, False, 3)
        if self.combo == [1, 1]:
            self.set_animation(self.combo1_2_right, False, 2)
        if self.combo == [1, 1, 1]:
            self.set_animation(self.combo1_3_right, False, 3)
        if self.combo == [1, 1, 1, 1]:
            self.set_animation(self.combo1_3_right, False, 3)
            self.combo = []
        self.last_combo_time = time.time()


game = Main()

while running:
    screen.fill((0, 0, 0))
    for event in pg.event.get():
        if event.type == pg.WINDOWCLOSE:
            exit(0)
            running = False

    game.update()
    clock.tick(FPS)
    pg.display.update()
    pg.display.flip()
