import os
import random
import pygame

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.change_x = 0
        self.change_y = 0
        self.last_dir = "right"
        self.mouth_open = True
        self.mouth_timer = 0
        self.mouth_interval = 10
        self._draw_pacman()

    def changespeed(self, x, y):
        self.change_x += x
        self.change_y += y
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
        block_hit_list = pygame.sprite.spritecollide(self, walls, False)
        for block in block_hit_list:
            if self.change_x > 0:
                self.rect.right = block.rect.left
            else:
                self.rect.left = block.rect.right

        self.rect.y += self.change_y
        block_hit_list = pygame.sprite.spritecollide(self, walls, False)
        for block in block_hit_list:
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            else:
                self.rect.top = block.rect.bottom

        # Animate mouth open/close
        self.mouth_timer += 1
        if self.mouth_timer >= self.mouth_interval:
            self.mouth_open = not self.mouth_open
            self.mouth_timer = 0
            self._draw_pacman()

    def _draw_pacman(self):
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        center = (self.size // 2, self.size // 2)
        radius = self.size // 2
        pygame.draw.circle(surface, YELLOW, center, radius)

        if self.mouth_open:
            # Cut out a triangular wedge for the mouth
            if self.last_dir == "left":
                wedge = [(center[0], center[1]),
                         (0, 0),
                         (0, self.size)]
            elif self.last_dir == "up":
                wedge = [(center[0], center[1]),
                         (0, 0),
                         (self.size, 0)]
            elif self.last_dir == "down":
                wedge = [(center[0], center[1]),
                         (0, self.size),
                         (self.size, self.size)]
            else:  # right
                wedge = [(center[0], center[1]),
                         (self.size, 0),
                         (self.size, self.size)]
            pygame.draw.polygon(surface, (0, 0, 0, 0), wedge)

        self.image = surface


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x


class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 5])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, image, walls):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.walls = walls
        self.speed = 2
        self.direction = random.choice(["left", "right", "up", "down"])
        self.steps_remaining = random.randint(15, 60)

    def update(self):
        # Random wandering: keep a direction for a few steps, change when blocked or timer expires
        if self.steps_remaining <= 0 or not self._can_move(self.direction):
            self._choose_new_direction()

        dx, dy = self._delta_for_direction(self.direction)
        self.rect.x += dx
        self.rect.y += dy
        if pygame.sprite.spritecollideany(self, self.walls):
            self.rect.x -= dx
            self.rect.y -= dy
            self.steps_remaining = 0
        else:
            self.steps_remaining -= 1

    def _delta_for_direction(self, direction):
        if direction == "left":
            return -self.speed, 0
        if direction == "right":
            return self.speed, 0
        if direction == "up":
            return 0, -self.speed
        return 0, self.speed  # down

    def _can_move(self, direction):
        dx, dy = self._delta_for_direction(direction)
        self.rect.x += dx
        self.rect.y += dy
        blocked = pygame.sprite.spritecollideany(self, self.walls)
        self.rect.x -= dx
        self.rect.y -= dy
        return not blocked

    def _choose_new_direction(self):
        for direction in random.sample(["left", "right", "up", "down"], 4):
            if self._can_move(direction):
                self.direction = direction
                self.steps_remaining = random.randint(15, 60)
                return
        self.steps_remaining = 0


# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PacMac")

# Load images
pacman_image = pygame.Surface((30, 30))
pacman_image.fill(YELLOW)

ghost_images = []
for img_name in ["ghl.png", "kajabi.png", "sk.png", "sys.png"]:
    try:
        img_path = os.path.join("imgs", img_name)
        image = pygame.image.load(img_path)
        image = pygame.transform.scale(image, (30, 30))
        ghost_images.append(image)
    except pygame.error as e:
        print(f"Error loading image {img_name}: {e}")
        placeholder = pygame.Surface((30, 30))
        placeholder.fill(WHITE)
        ghost_images.append(placeholder)


def reset_game():
    all_sprites_list.empty()
    wall_list.empty()
    ghost_list.empty()
    pellet_list.empty()

    # Create walls
    for item in wall_coords:
        wall = Wall(item[0], item[1], item[2], item[3])
        wall_list.add(wall)
        all_sprites_list.add(wall)

    # Create pellets
    for x in range(20, SCREEN_WIDTH - 20, 20):
        for y in range(20, SCREEN_HEIGHT - 20, 20):
            pellet = Pellet(x, y)
            # Skip pellets that would spawn inside walls
            if not pygame.sprite.spritecollideany(pellet, wall_list):
                pellet_list.add(pellet)
                all_sprites_list.add(pellet)

    # Create player
    player = Player(30, 30)
    all_sprites_list.add(player)

    # Create ghosts
    ghost_spawns = [(60, 340), (460, 340), (460, 80), (260, 80)]
    for i, ghost_image in enumerate(ghost_images):
        x, y = ghost_spawns[i % len(ghost_spawns)]
        ghost = Ghost(x, y, ghost_image, wall_list)
        ghost_list.add(ghost)
        all_sprites_list.add(ghost)

    return player, ghost_list, pellet_list, all_sprites_list, wall_list


all_sprites_list = pygame.sprite.Group()
wall_list = pygame.sprite.Group()
ghost_list = pygame.sprite.Group()
pellet_list = pygame.sprite.Group()

# Create walls
wall_coords = [
    [0, 0, 10, SCREEN_HEIGHT], [SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT],
    [0, 0, SCREEN_WIDTH, 10], [0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10],
    [40, 40, 440, 10], [40, 40, 10, 300], [490, 40, 10, 300],
    [80, 80, 360, 10], [80, 120, 10, 220], [430, 120, 10, 220],
    [140, 120, 300, 10], [140, 200, 10, 200], [200, 160, 220, 10],
    [200, 240, 10, 160], [260, 200, 10, 200], [320, 160, 10, 220],
    [380, 240, 60, 10], [80, 320, 140, 10]
]
player, ghost_list, pellet_list, all_sprites_list, wall_list = reset_game()


# Game loop
running = True
game_over = False
win = False
clock = pygame.time.Clock()
score = 0

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_over or win:
                if event.key == pygame.K_r:
                    player, ghost_list, pellet_list, all_sprites_list, wall_list = reset_game()
                    game_over = False
                    win = False
                    score = 0
            else:
                if event.key == pygame.K_LEFT:
                    player.changespeed(-3, 0)
                elif event.key == pygame.K_RIGHT:
                    player.changespeed(3, 0)
                elif event.key == pygame.K_UP:
                    player.changespeed(0, -3)
                elif event.key == pygame.K_DOWN:
                    player.changespeed(0, 3)
        elif event.type == pygame.KEYUP:
            if not game_over and not win:
                if event.key == pygame.K_LEFT:
                    player.changespeed(3, 0)
                elif event.key == pygame.K_RIGHT:
                    player.changespeed(-3, 0)
                elif event.key == pygame.K_UP:
                    player.changespeed(0, 3)
                elif event.key == pygame.K_DOWN:
                    player.changespeed(0, -3)

    if not game_over and not win:
        # Game logic
        player.update(wall_list)
        ghost_list.update()

        pellet_hit_list = pygame.sprite.spritecollide(
            player, pellet_list, True)
        for pellet in pellet_hit_list:
            score += 1
            all_sprites_list.remove(pellet)

        if len(pellet_list) == 0:
            win = True

        ghost_hit_list = pygame.sprite.spritecollide(player, ghost_list, False)
        if ghost_hit_list:
            game_over = True

    # Drawing
    screen.fill(BLACK)
    all_sprites_list.draw(screen)

    font = pygame.font.Font(None, 36)
    text = font.render("Score: " + str(score), 1, WHITE)
    screen.blit(text, (10, 10))

    if game_over:
        font = pygame.font.Font(None, 72)
        text = font.render("Game Over", 1, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        screen.blit(text, text_rect)
        font = pygame.font.Font(None, 36)
        text = font.render("Press 'r' to restart", 1, WHITE)
        text_rect = text.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
        screen.blit(text, text_rect)

    if win:
        font = pygame.font.Font(None, 72)
        text = font.render("You Win!", 1, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        screen.blit(text, text_rect)
        font = pygame.font.Font(None, 36)
        text = font.render("Press 'r' to restart", 1, WHITE)
        text_rect = text.get_rect(
            center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
        screen.blit(text, text_rect)

    # Update the display
    pygame.display.flip()
    clock.tick(60)

# Quit Pygame
pygame.quit()
