import pygame
import random
import math
import sys
import os

# Функция для получения абсолютного пути к ресурсам
def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
WIDTH, HEIGHT = 1280, 720
FPS = 60
BASE_TANK_SPEED = 2.5
BASE_BULLET_SPEED = 8
MAX_BULLETS = 5

# Цвета
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 180, 0),
    "blue": (30, 30, 150),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "gray": (80, 80, 80),
    "dark_gray": (40, 40, 40)
}

# Инициализация окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Танковый бой - Многоуровневая игра')
clock = pygame.time.Clock()

class LevelSystem:
    @staticmethod
    def get_params(level):
        return {
            'enemies': min(3 + level, 15),  # Максимум 15 врагов
            'enemy_health': 50 + level * 10,
            'enemy_speed': 0.8 + level * 0.1,
            'enemy_fire_rate': 0.5 + level * 0.1,
            'player_heal': 20 + level * 2
        }

# Загрузка ресурсов
try:
    tank_image = pygame.image.load(resource_path('tank.png')).convert_alpha()
    tank_image = pygame.transform.scale(tank_image, (45, 45))
    background = pygame.transform.scale(pygame.image.load(resource_path('background.jpg')).convert(), (WIDTH, HEIGHT))

    # Звуки
    shoot_sound = pygame.mixer.Sound(resource_path('shoot.wav'))
    explosion_sound = pygame.mixer.Sound(resource_path('explosion.wav'))
    move_channel = pygame.mixer.Channel(3)
except Exception as e:
    print(f"Ошибка загрузки ресурсов: {e}")
    pygame.quit()
    sys.exit()

class Tank:
    def __init__(self, x, y, is_bot=False, level=1):
        self.x = x
        self.y = y
        self.angle = 0
        self.bullets = []
        self.is_bot = is_bot
        self.last_shot = 0
        self.params = {
            'speed': BASE_TANK_SPEED * (0.8 if is_bot else 1.0),
            'bullet_speed': BASE_BULLET_SPEED,
            'health': 100,
            'max_health': 100,
            'fire_delay': 600,
            'damage': 20,
            'upgrades': 0
        }

        if is_bot:
            self._init_bot(level)

    def _init_bot(self, level):
        params = LevelSystem.get_params(level)
        self.params.update({
            'speed': BASE_TANK_SPEED * params['enemy_speed'],
            'health': params['enemy_health'],
            'max_health': params['enemy_health'],
            'fire_delay': 1500 / params['enemy_fire_rate'],
            'bullet_speed': BASE_BULLET_SPEED * 1.1
        })

    def draw(self, surface):
        rotated_image = pygame.transform.rotate(tank_image, self.angle)
        rect = rotated_image.get_rect(center=(self.x, self.y))
        surface.blit(rotated_image, rect.topleft)
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface):
        bar_width = 40
        bar_height = 5
        pos = (self.x - bar_width//2, self.y - 35)
        pygame.draw.rect(surface, COLORS['red'], (pos[0], pos[1], bar_width, bar_height))
        pygame.draw.rect(surface, COLORS['green'],
                         (pos[0], pos[1], bar_width * (self.params['health']/self.params['max_health']), bar_height))

    def shoot(self):
        if pygame.time.get_ticks() - self.last_shot > self.params['fire_delay']:
            rad = math.radians(self.angle)
            bullet_count = 1 + self.params['upgrades'] // 3
            spread = 15

            for i in range(bullet_count):
                angle_offset = spread * (i - (bullet_count-1)/2)
                new_angle = rad + math.radians(angle_offset)

                self.bullets.append({
                    'x': self.x + math.cos(new_angle)*30,
                    'y': self.y - math.sin(new_angle)*30,
                    'dx': math.cos(new_angle) * self.params['bullet_speed'],
                    'dy': -math.sin(new_angle) * self.params['bullet_speed'],
                    'damage': self.params['damage']
                })

            self.last_shot = pygame.time.get_ticks()
            shoot_sound.play()

class GameSession:
    def __init__(self):
        self.current_level = 1
        self.player = Tank(WIDTH//2, HEIGHT-100)
        self.enemies = []
        self.running = True
        self.score = 0
        self.kills = 0
        self._init_enemies()

    def _init_enemies(self):
        params = LevelSystem.get_params(self.current_level)
        for _ in range(params['enemies']):
            self.enemies.append(Tank(
                random.randint(100, WIDTH-100),
                random.randint(100, HEIGHT//2),
                is_bot=True,
                level=self.current_level
            ))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.player.shoot()

        keys = pygame.key.get_pressed()
        move_vec = [0, 0]

        if keys[pygame.K_a]: move_vec[0] -= 1
        if keys[pygame.K_d]: move_vec[0] += 1
        if keys[pygame.K_w]: move_vec[1] -= 1
        if keys[pygame.K_s]: move_vec[1] += 1

        if move_vec != [0, 0]:
            move_dir = math.atan2(move_vec[1], move_vec[0])
            self.player.angle = math.degrees(move_dir) - 90
            speed = self.player.params['speed']
            self.player.x += math.cos(move_dir) * speed
            self.player.y += math.sin(move_dir) * speed
            self.player.x = max(30, min(WIDTH-30, self.player.x))
            self.player.y = max(30, min(HEIGHT-30, self.player.y))
            if not move_channel.get_busy():
                move_channel.play(pygame.mixer.Sound(resource_path('move.wav')), loops=-1)
        else:
            move_channel.stop()

    def update_bots(self):
        for bot in self.enemies:
            dx = self.player.x - bot.x
            dy = self.player.y - bot.y
            distance = math.hypot(dx, dy)

            if distance > 400:
                angle = math.degrees(math.atan2(dy, dx)) + 90
                bot.angle = angle
                bot.x += math.cos(math.radians(angle)) * bot.params['speed']
                bot.y -= math.sin(math.radians(angle)) * bot.params['speed']
            else:
                bot.angle = math.degrees(math.atan2(-dy, dx))
                if random.random() < 0.02 * self.current_level:
                    bot.shoot()

            bot.x = max(30, min(WIDTH-30, bot.x))
            bot.y = max(30, min(HEIGHT//2, bot.y))

    def check_collisions(self):
        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                if math.hypot(bullet['x']-enemy.x, bullet['y']-enemy.y) < 30:
                    enemy.params['health'] -= bullet['damage']
                    self.score += 10

                    if enemy.params['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.score += 50
                        self.kills += 1

                        params = LevelSystem.get_params(self.current_level)
                        heal_amount = params['player_heal']
                        self.player.params['health'] = min(
                            self.player.params['health'] + heal_amount,
                            self.player.params['max_health']
                        )

                        self.upgrade_weapon()
                        explosion_sound.play()

                    try:
                        self.player.bullets.remove(bullet)
                    except ValueError:
                        pass

        for enemy in self.enemies:
            for bullet in enemy.bullets[:]:
                if math.hypot(bullet['x']-self.player.x, bullet['y']-self.player.y) < 30:
                    self.player.params['health'] -= 5 + self.current_level
                    enemy.bullets.remove(bullet)
                    explosion_sound.play()

    def upgrade_weapon(self):
        self.player.params['upgrades'] += 1

        if self.player.params['upgrades'] % 2 == 0:
            self.player.params['damage'] += 3

        if self.player.params['upgrades'] % 3 == 0:
            self.player.params['bullet_speed'] *= 1.1

        if self.player.params['upgrades'] % 5 == 0:
            self.player.params['fire_delay'] = max(
                self.player.params['fire_delay'] * 0.9,
                200
            )

        if self.player.params['upgrades'] % 4 == 0:
            self.player.params['max_health'] += 10
            self.player.params['health'] = min(
                self.player.params['health'] + 10,
                self.player.params['max_health']
            )

    def draw_hud(self):
        font = pygame.font.Font(None, 28)
        texts = [
            (f"Уровень: {self.current_level}", (20, 20), COLORS['yellow']),
            (f"Здоровье: {self.player.params['health']}/{self.player.params['max_health']}", (20, 50), COLORS['green']),
            (f"Счет: {self.score}", (WIDTH - 200, 20), COLORS['white']),
            (f"Улучшения: {self.player.params['upgrades']}", (20, 80), COLORS['orange']),
            (f"Урон: {self.player.params['damage']}", (20, 110), COLORS['red']),
            (f"Убийств: {self.kills}", (WIDTH - 200, 50), COLORS['blue'])
        ]

        for text, pos, color in texts:
            surf = font.render(text, True, color)
            screen.blit(surf, pos)

    def run(self):
        while self.running and self.player.params['health'] > 0:
            self.handle_input()
            self.update_bots()
            self.check_collisions()

            for entity in [self.player] + self.enemies:
                for bullet in entity.bullets[:]:
                    bullet['x'] += bullet['dx']
                    bullet['y'] += bullet['dy']
                    if bullet['x'] < 0 or bullet['x'] > WIDTH or bullet['y'] < 0 or bullet['y'] > HEIGHT:
                        entity.bullets.remove(bullet)

            screen.blit(background, (0, 0))

            for enemy in self.enemies:
                enemy.draw(screen)
                for bullet in enemy.bullets:
                    pygame.draw.circle(screen, COLORS['red'], (int(bullet['x']), int(bullet['y'])), 4)

            self.player.draw(screen)
            for bullet in self.player.bullets:
                pygame.draw.circle(screen, COLORS['yellow'], (int(bullet['x']), int(bullet['y'])), 6)

            self.draw_hud()
            pygame.display.flip()
            clock.tick(FPS)

            if not self.enemies:
                self.current_level += 1
                self._init_enemies()
                self.player.params['health'] = min(
                    self.player.params['health'] + 20,
                    self.player.params['max_health']
                )

        self.show_game_over()

    def show_game_over(self):
        self.show_end_screen(f"Игра окончена! Пройдено уровней: {self.current_level-1}")

    def show_end_screen(self, text):
        menu = MainMenu()
        while True:
            screen.fill(COLORS['dark_gray'])
            title = pygame.font.Font(None, 48).render(text, True, COLORS['white'])
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

            # Кнопки
            mouse_pos = pygame.mouse.get_pos()
            for i, (btn_text, action) in enumerate([
                ("Меню", self.return_to_menu),
                ("Заново", lambda: GameSession().run()),
                ("Выход", self.quit_game)
            ]):
                y = 200 + i*60
                rect = pygame.Rect(WIDTH//2 - 100, y, 200, 50)
                color = COLORS['green'] if rect.collidepoint(mouse_pos) else COLORS['gray']
                pygame.draw.rect(screen, color, rect, border_radius=5)
                text_surf = pygame.font.Font(None, 32).render(btn_text, True, COLORS['black'])
                screen.blit(text_surf, (rect.x + 20, rect.y + 15))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    for i, (_, action) in enumerate([
                        ("Меню", self.return_to_menu),
                        ("Заново", lambda: GameSession().run()),
                        ("Выход", self.quit_game)
                    ]):
                        rect = pygame.Rect(WIDTH//2 - 100, 200 + i*60, 200, 50)
                        if rect.collidepoint(mouse_pos):
                            action()

    def return_to_menu(self):
        self.running = False
        main_menu()

    def quit_game(self):
        pygame.quit()
        sys.exit()

class MainMenu:
    def __init__(self):
        self.font = pygame.font.Font(None, 32)
        self.buttons = [
            {'rect': pygame.Rect(WIDTH//2 - 100, 200, 200, 50), 'text': "Играть"},
            {'rect': pygame.Rect(WIDTH//2 - 100, 280, 200, 50), 'text': "Выход"}
        ]

    def draw(self):
        screen.fill(COLORS['dark_gray'])
        title = self.font.render("Танковый бой - Многоуровневая игра", True, COLORS['white'])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            color = COLORS['green'] if btn['rect'].collidepoint(mouse_pos) else COLORS['gray']
            pygame.draw.rect(screen, color, btn['rect'], border_radius=5)
            text_surf = self.font.render(btn['text'], True, COLORS['black'])
            screen.blit(text_surf, (btn['rect'].x + 20, btn['rect'].y + 15))

    def handle_click(self, pos):
        if self.buttons[0]['rect'].collidepoint(pos):
            GameSession().run()
        elif self.buttons[1]['rect'].collidepoint(pos):
            pygame.quit()
            sys.exit()

    def run(self):
        while True:
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
            pygame.display.flip()
            clock.tick(FPS)

def main_menu():
    menu = MainMenu()
    menu.run()

if __name__ == "__main__":
    main_menu()