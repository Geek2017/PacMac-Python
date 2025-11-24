import os
import random
import asyncio
import pygame
import sys

# Initialize Pygame
pygame.init()

# Check if running in browser
IS_WEB = sys.platform == "emscripten"

# Screen dimensions
SCREEN_WIDTH = 420
SCREEN_HEIGHT = 360

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 20
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
        self.change_x = x
        self.change_y = y
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


class PowerPellet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([12, 12])
        self.image.fill((255, 0, 0))  # Red color for cherry/power pellet
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, image, walls):
        super().__init__()
        self.base_image = image
        self.image = image.copy()
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.walls = walls
        self.speed = 2
        self.direction = random.choice(["left", "right", "up", "down"])
        self.steps_remaining = random.randint(15, 60)
        self.edible = False
        self.stuck_counter = 0

    def update(self):
        # Random wandering: keep a direction for a few steps, change when blocked or timer expires
        if self.steps_remaining <= 0 or not self._can_move(self.direction):
            self._choose_new_direction()

        dx, dy = self._delta_for_direction(self.direction)
        old_pos = (self.rect.x, self.rect.y)
        self.rect.x += dx
        self.rect.y += dy

        if pygame.sprite.spritecollideany(self, self.walls):
            self.rect.x -= dx
            self.rect.y -= dy
            self.steps_remaining = 0
            self.stuck_counter += 1
        else:
            self.steps_remaining -= 1
            # Only reset stuck counter if ghost actually moved
            if old_pos != (self.rect.x, self.rect.y):
                self.stuck_counter = 0
            else:
                self.stuck_counter += 1

        if self.stuck_counter > 60:
            self._teleport_to_free_spot()
            self.stuck_counter = 0

    def set_edible(self, edible=True):
        self.edible = edible
        self.image = self.base_image.copy()
        if edible:
            tint = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            tint.fill((80, 80, 255, 200))
            self.image.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

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

    def _teleport_to_free_spot(self):
        # If a ghost is stuck too long, relocate it to a random open spot
        for _ in range(30):
            new_x = random.randint(20, SCREEN_WIDTH - self.rect.width - 20)
            new_y = random.randint(20, SCREEN_HEIGHT - self.rect.height - 20)
            old_pos = self.rect.topleft
            self.rect.topleft = (new_x, new_y)
            if not pygame.sprite.spritecollideany(self, self.walls):
                return
            self.rect.topleft = old_pos


# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PacMac")

# Load images
pacman_image = pygame.Surface((30, 30))
pacman_image.fill(YELLOW)

ghost_images = []
for img_name in ["ghl.png", "kajabi.png", "sk.png", "sys.png"]:
    try:
        img_path = os.path.join("imgs", img_name) if not IS_WEB else f"imgs/{img_name}"
        image = pygame.image.load(img_path)
        image = pygame.transform.scale(image, (24, 24))
        ghost_images.append(image)
    except (pygame.error, FileNotFoundError) as e:
        print(f"Error loading image {img_name}: {e}, using placeholder")
        # Create colored placeholder for each ghost
        placeholder = pygame.Surface((24, 24))
        colors = [(255, 0, 0), (255, 184, 255), (0, 255, 255), (255, 184, 82)]
        placeholder.fill(colors[len(ghost_images) % len(colors)])
        ghost_images.append(placeholder)


def reset_game():
    all_sprites_list.empty()
    wall_list.empty()
    ghost_list.empty()
    pellet_list.empty()
    power_pellet_list.empty()

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

    # Create power pellets near starting point (but not too close!)
    power_positions = [(140, 60), (180, 60)]
    for px, py in power_positions:
        power_pellet = PowerPellet(px, py)
        if not pygame.sprite.spritecollideany(power_pellet, wall_list):
            power_pellet_list.add(power_pellet)
            all_sprites_list.add(power_pellet)

    # Create player
    player = Player(30, 30)
    all_sprites_list.add(player)

    # Create ghosts
    ghost_spawns = [(60, 260), (340, 260), (340, 140), (200, 200)]
    for i, ghost_image in enumerate(ghost_images):
        x, y = ghost_spawns[i % len(ghost_spawns)]
        ghost = Ghost(x, y, ghost_image, wall_list)
        ghost.set_edible(False)
        ghost_list.add(ghost)
        all_sprites_list.add(ghost)

    return player, ghost_list, pellet_list, power_pellet_list, all_sprites_list, wall_list


all_sprites_list = pygame.sprite.Group()
wall_list = pygame.sprite.Group()
ghost_list = pygame.sprite.Group()
pellet_list = pygame.sprite.Group()
power_pellet_list = pygame.sprite.Group()
ghost_edible = False
power_timer = 0

# Create walls
wall_coords = [
    # Outer boundary walls
    [0, 0, 10, SCREEN_HEIGHT], [SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT],
    [0, 0, SCREEN_WIDTH, 10], [0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10],

    # Second layer - with gaps in top middle
    [40, 40, 140, 10],  # Left part of top wall
    [220, 40, SCREEN_WIDTH - 260, 10],  # Right part of top wall (gap in middle)
    [40, 40, 10, SCREEN_HEIGHT - 80],  # Left wall
    [SCREEN_WIDTH - 50, 40, 10, SCREEN_HEIGHT - 80],  # Right wall

    # Third layer
    [80, 80, SCREEN_WIDTH - 160, 10],
    [80, 120, 10, SCREEN_HEIGHT - 160],
    [SCREEN_WIDTH - 90, 120, 10, SCREEN_HEIGHT - 160],

    # Inner walls
    [140, 160, SCREEN_WIDTH - 280, 10],
    [140, 200, 10, 60],  # Shortened left inner wall
    [220, 200, SCREEN_WIDTH - 360, 10],
    [220, 240, 10, 40],  # Shortened middle wall
    [280, 120, 10, SCREEN_HEIGHT - 200],

    # Bottom horizontal wall - removed to create gap
    # [100, 260, 120, 10]  # Removed for opening
]
player, ghost_list, pellet_list, power_pellet_list, all_sprites_list, wall_list = reset_game()


# Game loop
async def main():
    global ghost_edible, power_timer, player, ghost_list, pellet_list, power_pellet_list, all_sprites_list, wall_list

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
                        player, ghost_list, pellet_list, power_pellet_list, all_sprites_list, wall_list = reset_game()
                        game_over = False
                        win = False
                        score = 0
                        # Reset power state - DON'T assign here, causes Python scoping issues!
                        globals()['ghost_edible'] = False
                        globals()['power_timer'] = 0
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
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        player.changespeed(0, player.change_y)
                    elif event.key in (pygame.K_UP, pygame.K_DOWN):
                        player.changespeed(player.change_x, 0)

        if not game_over and not win:
            # Game logic
            player.update(wall_list)
            ghost_list.update()

            pellet_hit_list = pygame.sprite.spritecollide(
                player, pellet_list, True)
            for pellet in pellet_hit_list:
                score += 1
                all_sprites_list.remove(pellet)

            # Check for power pellet collision
            power_hit_list = pygame.sprite.spritecollide(
                player, power_pellet_list, True)
            for power_pellet in power_hit_list:
                score += 5
                all_sprites_list.remove(power_pellet)
                # Activate power mode for 10 seconds (600 frames at 60 fps)
                globals()['ghost_edible'] = True
                globals()['power_timer'] = 600
                for ghost in ghost_list:
                    ghost.set_edible(True)

            # Handle power timer countdown
            if ghost_edible and power_timer > 0:
                globals()['power_timer'] = power_timer - 1
                if globals()['power_timer'] == 0:
                    globals()['ghost_edible'] = False
                    for ghost in ghost_list:
                        ghost.set_edible(False)

            ghost_hit_list = pygame.sprite.spritecollide(player, ghost_list, False)
            if ghost_hit_list:
                if ghost_edible:
                    for ghost in ghost_hit_list:
                        ghost.kill()
                        score += 10
                    # Check if all ghosts are eliminated
                    if len(ghost_list) == 0:
                        win = True
                else:
                    game_over = True

            # Win condition: collect all pellets OR eliminate all ghosts
            if (len(pellet_list) == 0 and len(power_pellet_list) == 0) or len(ghost_list) == 0:
                win = True

        # Drawing
        screen.fill(BLACK)

        # Draw game sprites
        all_sprites_list.draw(screen)

        # Draw score at top with background
        font = pygame.font.Font(None, 28)
        text = font.render("Score: " + str(score), 1, WHITE)
        score_bg = pygame.Surface((140, 35))
        score_bg.fill(BLACK)
        screen.blit(score_bg, (5, 5))
        screen.blit(text, (10, 10))

        if game_over:
            font = pygame.font.Font(None, 60)
            text = font.render("Game Over", 1, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            screen.blit(text, text_rect)
            font = pygame.font.Font(None, 24)
            text = font.render("Press 'r' to restart", 1, WHITE)
            text_rect = text.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 45))
            screen.blit(text, text_rect)

        if win:
            font = pygame.font.Font(None, 60)
            text = font.render("You Win!", 1, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            screen.blit(text, text_rect)
            font = pygame.font.Font(None, 24)
            text = font.render("Press 'r' to restart", 1, WHITE)
            text_rect = text.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 45))
            screen.blit(text, text_rect)

        # Update the display
        pygame.display.flip()
        clock.tick(60)

        # Allow browser to process events (CRITICAL for web!)
        await asyncio.sleep(0)

    pygame.quit()


# Run the game
asyncio.run(main())
