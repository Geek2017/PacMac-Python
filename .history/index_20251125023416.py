# main.py  — ready for Pygbag
import asyncio
import os
import random
import pygame

# ---------- CONSTANTS ----------
SCREEN_WIDTH, SCREEN_HEIGHT = 420, 360
BLACK, WHITE, YELLOW = (0, 0, 0), (255, 255, 255), (255, 255, 0)

# ---------- SPRITES ----------


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.change_x = self.change_y = 0
        self.last_dir, self.mouth_open, self.mouth_timer = "right", True, 0
        self.mouth_interval = 10
        self._draw_pacman()

    def changespeed(self, x, y):
        self.change_x, self.change_y = x, y
        if x < 0:
            self.last_dir = "left"
        elif x > 0:
            self.last_dir = "right"
        elif y < 0:
            self.last_dir = "up"
        elif y > 0:
            self.last_dir = "down"

    def update(self, walls):
        self.rect.x += self.change_x
        for block in pygame.sprite.spritecollide(self, walls, False):
            if self.change_x > 0:
                self.rect.right = block.rect.left
            else:
                self.rect.left = block.rect.right
        self.rect.y += self.change_y
        for block in pygame.sprite.spritecollide(self, walls, False):
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            else:
                self.rect.top = block.rect.bottom
        self.mouth_timer += 1
        if self.mouth_timer >= self.mouth_interval:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0
            self._draw_pacman()

    def _draw_pacman(self):
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center, radius = (self.size // 2, self.size // 2), self.size // 2
        pygame.draw.circle(surf, YELLOW, center, radius)
        if self.mouth_open:
            if self.last_dir == "left":
                wedge = [(center[0], center[1]),
                         (0, 0),           (0, self.size)]
            elif self.last_dir == "up":
                wedge = [(center[0], center[1]),
                         (0, 0),           (self.size, 0)]
            elif self.last_dir == "down":
                wedge = [(center[0], center[1]), (0, self.size),
                         (self.size, self.size)]
            else:
                wedge = [(center[0], center[1]), (self.size, 0),
                         (self.size, self.size)]
            pygame.draw.polygon(surf, (0, 0, 0, 0), wedge)
        self.image = surf


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface([w, h])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(topleft=(x, y))


class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 5])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))


class PowerPellet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([12, 12])
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, img, walls):
        super().__init__()
        self.base_image = img
        self.image = img.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.walls, self.speed = walls, 2
        self.direction, self.steps_remaining = random.choice(
            ["left", "right", "up", "down"]), random.randint(15, 60)
        self.edible, self.stuck_counter = False, 0

    def update(self):
        if self.steps_remaining <= 0 or not self._can_move(self.direction):
            self._choose_new_direction()
        dx, dy = self._delta(self.direction)
        old = self.rect.topleft
        self.rect.move_ip(dx, dy)
        if pygame.sprite.spritecollideany(self, self.walls):
            self.rect.topleft = old
            self.steps_remaining = 0
            self.stuck_counter += 1
        else:
            self.steps_remaining -= 1
            self.stuck_counter = 0 if self.rect.topleft != old else self.stuck_counter + 1
        if self.stuck_counter > 60:
            self._teleport()

    def set_edible(self, state=True):
        self.edible = state
        self.image = self.base_image.copy()
        if state:
            tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint.fill((80, 80, 255, 200))
            self.image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _delta(self, d): return (-self.speed, 0) if d == "left" else (self.speed,
                                                                      0) if d == "right" else (0, -self.speed) if d == "up" else (0, self.speed)

    def _can_move(self, d):
        dx, dy = self._delta(d)
        self.rect.move_ip(dx, dy)
        hit = pygame.sprite.spritecollideany(self, self.walls)
        self.rect.move_ip(-dx, -dy)
        return not hit

    def _choose_new_direction(self):
        for d in random.sample(["left", "right", "up", "down"], 4):
            if self._can_move(d):
                self.direction, self.steps_remaining = d, random.randint(
                    15, 60)
                return
        self.steps_remaining = 0

    def _teleport(self):
        for _ in range(30):
            nx = random.randint(20, SCREEN_WIDTH-24-20)
            ny = random.randint(20, SCREEN_HEIGHT-24-20)
            old = self.rect.topleft
            self.rect.topleft = (nx, ny)
            if not pygame.sprite.spritecollideany(self, self.walls):
                return
            self.rect.topleft = old

# ---------- GAME RESET ----------


def reset_game():
    all_sprites, walls, ghosts, pellets, powers = [
        pygame.sprite.Group() for _ in range(5)]

    # walls
    for x, y, w, h in [
        (0, 0, 10, SCREEN_HEIGHT), (SCREEN_WIDTH-10, 0, 10, SCREEN_HEIGHT),
        (0, 0, SCREEN_WIDTH, 10), (0, SCREEN_HEIGHT-10, SCREEN_WIDTH, 10),
        (40, 40, 140, 10), (220, 40, SCREEN_WIDTH -
                            260, 10), (40, 40, 10, SCREEN_HEIGHT-80),
        (SCREEN_WIDTH-50, 40, 10, SCREEN_HEIGHT-80), (80, 80, SCREEN_WIDTH-160, 10),
        (80, 120, 10, SCREEN_HEIGHT-160), (SCREEN_WIDTH -
                                           90, 120, 10, SCREEN_HEIGHT-160),
        (140, 160, SCREEN_WIDTH-280, 10), (140, 200,
                                           10, 60), (220, 200, SCREEN_WIDTH-360, 10),
        (220, 240, 10, 40), (280, 120, 10, SCREEN_HEIGHT-200)
    ]:
        wall = Wall(x, y, w, h)
        walls.add(wall)
        all_sprites.add(wall)

    # pellets
    for x in range(20, SCREEN_WIDTH-20, 20):
        for y in range(20, SCREEN_HEIGHT-20, 20):
            p = Pellet(x, y)
            if not pygame.sprite.spritecollideany(p, walls):
                pellets.add(p)
                all_sprites.add(p)

    # power pellets
    for px, py in [(140, 60), (180, 60)]:
        pp = PowerPellet(px, py)
        if not pygame.sprite.spritecollideany(pp, walls):
            powers.add(pp)
            all_sprites.add(pp)

    # player
    player = Player(30, 30)
    all_sprites.add(player)

    # ghosts
    imgs = []
    for name in ["ghl.png", "kajabi.png", "sk.png", "sys.png"]:
        try:
            img = pygame.image.load(os.path.join("imgs", name))
            img = pygame.transform.scale(img, (24, 24))
        except pygame.error:
            img = pygame.Surface((24, 24))
            img.fill(WHITE)
        imgs.append(img)
    spawns = [(60, 260), (340, 260), (340, 140), (200, 200)]
    for i, im in enumerate(imgs):
        gx, gy = spawns[i % len(spawns)]
        g = Ghost(gx, gy, im, walls)
        ghosts.add(g)
        all_sprites.add(g)

    return player, ghosts, pellets, powers, all_sprites, walls

# ---------- ASYNC MAIN LOOP ----------


async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PacMac")
    clock = pygame.time.Clock()

    player, ghosts, pellets, powers, sprites, walls = reset_game()
    ghost_edible, power_timer, score, running, game_over, win = False, 0, 0, True, False, False

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if game_over or win:
                    if e.key == pygame.K_r:
                        player, ghosts, pellets, powers, sprites, walls = reset_game()
                        ghost_edible, power_timer, score, game_over, win = False, 0, 0, False, False
                else:
                    if e.key == pygame.K_LEFT:
                        player.changespeed(-3, 0)
                    elif e.key == pygame.K_RIGHT:
                        player.changespeed(3, 0)
                    elif e.key == pygame.K_UP:
                        player.changespeed(0, -3)
                    elif e.key == pygame.K_DOWN:
                        player.changespeed(0, 3)
            elif e.type == pygame.KEYUP and not (game_over or win):
                if e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    player.changespeed(0, player.change_y)
                if e.key in (pygame.K_UP,   pygame.K_DOWN):
                    player.changespeed(player.change_x, 0)

        if not (game_over or win):
            player.update(walls)
            ghosts.update()
            for p in pygame.sprite.spritecollide(player, pellets, True):
                score += 1
                sprites.remove(p)
            for pp in pygame.sprite.spritecollide(player, powers, True):
                score += 5
                sprites.remove(pp)
                ghost_edible, power_timer = True, 600
                for g in ghosts:
                    g.set_edible(True)
            if ghost_edible and power_timer > 0:
                power_timer -= 1
                if power_timer == 0:
                    ghost_edible = False
                    for g in ghosts:
                        g.set_edible(False)
            g_hit = pygame.sprite.spritecollide(player, ghosts, False)
            if g_hit:
                if ghost_edible:
                    for g in g_hit:
                        g.kill()
                        score += 10
                    if len(ghosts) == 0:
                        win = True
                else:
                    game_over = True
            if (not pellets and not powers) or not ghosts:
                win = True

        screen.fill(BLACK)
        sprites.draw(screen)
        font = pygame.font.Font(None, 28)
        screen.blit(font.render(f"Score: {score}", 1, WHITE), (10, 10))
        if game_over:
            t = pygame.font.Font(None, 60).render("Game Over", 1, WHITE)
            screen.blit(t, t.get_rect(
                center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
            screen.blit(pygame.font.Font(None, 24).render("Press 'r' to restart", 1, WHITE),
                        (SCREEN_WIDTH/2-90, SCREEN_HEIGHT/2+45))
        if win:
            t = pygame.font.Font(None, 60).render("You Win!", 1, WHITE)
            screen.blit(t, t.get_rect(
                center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
            screen.blit(pygame.font.Font(None, 24).render("Press 'r' to restart", 1, WHITE),
                        (SCREEN_WIDTH/2-90, SCREEN_HEIGHT/2+45))
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)  # yield to browser event loop

# ---------- DESKTOP ENTRY POINT ----------
if __name__ == "__main__":
    import sys
    if sys.platform != "emscripten":  # skip when running under Pygbag
        asyncio.run(main())
