"""
Shooter 2D estilo arcade en un solo archivo usando Pygame.

Características:
- Estados: MENÚ, JUGANDO, GAME OVER
- Jugador con movimiento WASD/Flechas
- Disparo con barra espaciadora
- Enemigos con aparición progresiva y dificultad creciente
- Sistema de vidas y puntaje
- Fondo dinámico sencillo sin assets externos
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass

import pygame


# =========================
# Configuración general
# =========================
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650
FPS = 60
TITLE = "Arcade Shooter - Pygame"

# Colores
WHITE = (245, 245, 245)
BLACK = (18, 18, 18)
DARK_BLUE = (10, 16, 40)
CYAN = (80, 220, 255)
GREEN = (60, 220, 120)
RED = (230, 70, 90)
YELLOW = (255, 220, 70)
PURPLE = (180, 100, 255)


@dataclass
class GameConfig:
    """Parámetros de dificultad y balance del juego."""

    player_speed: float = 5.2
    bullet_speed: float = 9.0
    base_enemy_speed: float = 1.8
    enemy_speed_growth: float = 0.08
    max_enemy_speed: float = 6.0
    spawn_interval_ms: int = 1200
    spawn_interval_min_ms: int = 320
    spawn_interval_decrease_ms: int = 18
    score_per_enemy: int = 10
    player_max_lives: int = 3


class Player(pygame.sprite.Sprite):
    """Entidad controlada por el jugador."""

    def __init__(self, x: int, y: int, speed: float):
        super().__init__()
        self.image = pygame.Surface((48, 32), pygame.SRCALPHA)
        # Dibujamos una nave simple con polígonos/rectángulos
        pygame.draw.polygon(self.image, CYAN, [(0, 16), (22, 2), (47, 16), (22, 30)])
        pygame.draw.rect(self.image, WHITE, (16, 12, 18, 8), border_radius=3)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self, keys: pygame.key.ScancodeWrapper):
        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed

        self.rect.x += int(dx)
        self.rect.y += int(dy)

        # Mantener dentro de la pantalla
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))


class Bullet(pygame.sprite.Sprite):
    """Proyectil disparado por el jugador."""

    def __init__(self, x: int, y: int, speed: float):
        super().__init__()
        self.image = pygame.Surface((8, 16), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 8, 16), border_radius=2)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed

    def update(self):
        self.rect.y -= int(self.speed)
        # Eliminar bala si sale de pantalla (evita fugas de memoria)
        if self.rect.bottom < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    """Enemigo que desciende desde la parte superior."""

    def __init__(self, x: int, speed: float):
        super().__init__()
        size = random.randint(28, 48)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # Enemigo simple con forma circular y detalle interior
        pygame.draw.circle(self.image, RED, (size // 2, size // 2), size // 2)
        pygame.draw.circle(self.image, PURPLE, (size // 2, size // 2), size // 3)
        self.rect = self.image.get_rect(midtop=(x, -size))
        self.speed = speed

    def update(self):
        self.rect.y += int(self.speed)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class GameManager:
    """Controlador principal: estados, lógica, render y eventos."""

    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fuentes
        self.font_small = pygame.font.SysFont("consolas", 24)
        self.font_medium = pygame.font.SysFont("consolas", 34, bold=True)
        self.font_large = pygame.font.SysFont("consolas", 52, bold=True)

        self.config = GameConfig()
        self.state = self.MENU
        self.running = True

        # Fondo animado (estrellas)
        self.stars = [
            [random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(1, 3)]
            for _ in range(120)
        ]

        self.reset_game()

    def reset_game(self):
        """Reinicia toda la partida para un nuevo intento."""
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()

        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60, self.config.player_speed)
        self.all_sprites.add(self.player)

        self.lives = self.config.player_max_lives
        self.score = 0
        self.enemy_speed_current = self.config.base_enemy_speed
        self.spawn_interval_current = self.config.spawn_interval_ms
        self.last_spawn_time = 0

        # Control de disparo para evitar spam excesivo
        self.shoot_cooldown_ms = 180
        self.last_shot_time = 0

    def spawn_enemy(self):
        x = random.randint(28, SCREEN_WIDTH - 28)
        enemy = Enemy(x, self.enemy_speed_current)
        self.enemies.add(enemy)
        self.all_sprites.add(enemy)

    def shoot_bullet(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time >= self.shoot_cooldown_ms:
            bullet = Bullet(self.player.rect.centerx, self.player.rect.top + 4, self.config.bullet_speed)
            self.bullets.add(bullet)
            self.all_sprites.add(bullet)
            self.last_shot_time = now

    def update_difficulty(self):
        """Aumenta gradualmente dificultad según puntaje."""
        # Cada 100 puntos sube velocidad enemiga y baja intervalo de spawn
        tier = self.score // 100
        self.enemy_speed_current = min(
            self.config.base_enemy_speed + tier * self.config.enemy_speed_growth,
            self.config.max_enemy_speed,
        )
        self.spawn_interval_current = max(
            self.config.spawn_interval_ms - tier * self.config.spawn_interval_decrease_ms,
            self.config.spawn_interval_min_ms,
        )

    def update_background(self):
        """Anima estrellas para dar sensación de movimiento."""
        for star in self.stars:
            star[1] += star[2]
            if star[1] > SCREEN_HEIGHT:
                star[0] = random.randint(0, SCREEN_WIDTH)
                star[1] = 0
                star[2] = random.randint(1, 3)

    def draw_background(self):
        self.screen.fill(DARK_BLUE)
        for x, y, speed in self.stars:
            color = (120 + speed * 35, 130 + speed * 30, 180 + speed * 25)
            pygame.draw.circle(self.screen, color, (x, y), speed)

    def handle_events(self):
        """Procesa eventos globales y por estado."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if self.state == self.MENU:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset_game()
                        self.state = self.PLAYING
                elif self.state == self.PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.shoot_bullet()
                elif self.state == self.GAME_OVER:
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        self.reset_game()
                        self.state = self.PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU

    def update_playing(self):
        """Actualización principal de la partida activa."""
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # Disparo continuo manteniendo espacio
        if keys[pygame.K_SPACE]:
            self.shoot_bullet()

        self.bullets.update()
        self.enemies.update()

        # Spawn progresivo
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time >= self.spawn_interval_current:
            self.spawn_enemy()
            self.last_spawn_time = now

        # Colisiones bala-enemigo
        collisions = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        if collisions:
            destroyed = len(collisions)
            self.score += destroyed * self.config.score_per_enemy

        # Colisiones jugador-enemigo
        hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        if hits:
            self.lives -= len(hits)
            if self.lives <= 0:
                self.lives = 0
                self.state = self.GAME_OVER

        # Enemigos que cruzan la pantalla restan vida
        for enemy in list(self.enemies):
            if enemy.rect.top > SCREEN_HEIGHT:
                enemy.kill()
                self.lives -= 1
                if self.lives <= 0:
                    self.lives = 0
                    self.state = self.GAME_OVER
                    break

        self.update_difficulty()

    def draw_hud(self):
        score_text = self.font_small.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font_small.render(f"Vidas: {self.lives}", True, GREEN if self.lives > 1 else RED)
        self.screen.blit(score_text, (16, 12))
        self.screen.blit(lives_text, (16, 42))

    def draw_menu(self):
        title = self.font_large.render("ARCADE SHOOTER", True, CYAN)
        subtitle = self.font_small.render("Mueve: WASD o Flechas | Dispara: ESPACIO", True, WHITE)
        start_msg = self.font_medium.render("Pulsa ENTER o ESPACIO para comenzar", True, YELLOW)

        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 35)))
        self.screen.blit(start_msg, start_msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))

    def draw_game_over(self):
        game_over = self.font_large.render("GAME OVER", True, RED)
        final_score = self.font_medium.render(f"Puntaje final: {self.score}", True, WHITE)
        restart = self.font_small.render("R o ENTER: reiniciar | ESC: menú", True, YELLOW)

        self.screen.blit(game_over, game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 85)))
        self.screen.blit(final_score, final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 10)))
        self.screen.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 55)))

    def draw(self):
        self.draw_background()

        if self.state == self.MENU:
            self.draw_menu()
        elif self.state == self.PLAYING:
            self.all_sprites.draw(self.screen)
            self.draw_hud()
        elif self.state == self.GAME_OVER:
            self.all_sprites.draw(self.screen)
            self.draw_hud()
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        """Game loop principal con control de FPS a 60."""
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update_background()

            if self.state == self.PLAYING:
                self.update_playing()

            self.draw()

        pygame.quit()
        sys.exit()


def main():
    game = GameManager()
    game.run()


if __name__ == "__main__":
    main()
