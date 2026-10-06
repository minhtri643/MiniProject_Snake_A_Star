"""Pygame application and rendering layer."""

import sys
import time

import pygame

from .config import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    CELL_SIZE,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_GRID,
    COLOR_PANEL,
    COLOR_SIDEBAR_BG,
    COLOR_SNAKE_BODY_1,
    COLOR_SNAKE_BODY_2,
    COLOR_SNAKE_EYE,
    COLOR_SNAKE_HEAD,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    DEFAULT_SPEED_INDEX,
    GRID_SIZE,
    INITIAL_LENGTH,
    INITIAL_POSITION,
    MAX_FOOD,
    MIN_FOOD,
    SIDEBAR_WIDTH,
    SPEED_LEVELS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .models import FoodManager, Snake
from .solver import AStarSolver


class SnakeGame:
    """Coordinate game state, AI decisions, user input, and rendering."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake AI - A* Search & Survival Engine")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = self._get_font(19, bold=True)
        self.font_bold = self._get_font(14, bold=True)
        self.font_regular = self._get_font(12)
        self.font_small = self._get_font(11, bold=True)

        self.snake = Snake(INITIAL_POSITION, INITIAL_LENGTH)
        self.food_manager = FoodManager(GRID_SIZE, MIN_FOOD, MAX_FOOD)
        self.solver = AStarSolver(GRID_SIZE)

        self.high_score = 0
        self.speed_index = DEFAULT_SPEED_INDEX
        self.paused = False
        self.show_path = True
        self.reset_game(update_high_score=False)

    @staticmethod
    def _get_font(size, bold=False):
        for name in ["Segoe UI", "Arial", "Roboto", "Helvetica"]:
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except (TypeError, pygame.error):
                continue
        return pygame.font.Font(None, size)

    @property
    def current_fps(self):
        return SPEED_LEVELS[self.speed_index][1]

    @property
    def board_capacity(self):
        return GRID_SIZE * GRID_SIZE

    def reset_game(self, update_high_score=True):
        if update_high_score:
            self.high_score = max(self.high_score, getattr(self, "score", 0))
        self.snake.reset(INITIAL_POSITION, INITIAL_LENGTH)
        self.food_manager.reset(self.snake.body)
        self.score = 0
        self.start_time = time.time()
        self.elapsed_time = 0.0
        self.game_over = False
        self.game_won = False
        self.ai_status_text = "Initializing A*..."
        self.current_path = None
        self.last_free_space = self.board_capacity - INITIAL_LENGTH

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos)

    def _handle_key(self, key):
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.reset_game()
        elif key == pygame.K_p:
            self.show_path = not self.show_path
        elif key in (pygame.K_1, pygame.K_KP1):
            self.speed_index = 0
        elif key in (pygame.K_2, pygame.K_KP2):
            self.speed_index = 1
        elif key in (pygame.K_3, pygame.K_KP3):
            self.speed_index = 2
        elif key in (pygame.K_4, pygame.K_KP4):
            self.speed_index = 3
        elif key == pygame.K_RIGHT:
            self.speed_index = (self.speed_index + 1) % len(SPEED_LEVELS)
        elif key == pygame.K_LEFT:
            self.speed_index = (self.speed_index - 1) % len(SPEED_LEVELS)

    def _handle_mouse_click(self, pos):
        x, y = pos
        if 660 <= x <= 930 and 460 <= y <= 495:
            self.paused = not self.paused
        elif 660 <= x <= 930 and 505 <= y <= 540:
            self.reset_game()
        elif 660 <= x <= 930 and 550 <= y <= 585:
            self.speed_index = (self.speed_index + 1) % len(SPEED_LEVELS)
        elif 660 <= x <= 930 and 595 <= y <= 630:
            self.show_path = not self.show_path

    def update(self):
        if self.paused or self.game_over or self.game_won:
            return
        if self.snake.length >= self.board_capacity:
            self._set_victory()
            return

        self.elapsed_time = time.time() - self.start_time
        self.food_manager.update(self.snake.body)
        next_step, path, status, free_space = self.solver.get_next_move(
            self.snake,
            self.food_manager.foods,
            step_delay=1.0 / self.current_fps,
        )
        self.ai_status_text = status
        self.current_path = path
        if free_space > 0:
            self.last_free_space = free_space

        if next_step is None or not self._is_valid_move(next_step):
            self.game_over = True
            return

        ate_food = next_step in self.food_manager.get_food_positions()
        if ate_food:
            self.food_manager.remove_at(next_step)
            self.score += 1
            self.high_score = max(self.high_score, self.score)

        self.snake.move_to(next_step, ate_food=ate_food)
        if self.snake.length >= self.board_capacity:
            self._set_victory()
        elif ate_food:
            self.food_manager.update(self.snake.body)

    def _is_valid_move(self, position):
        x, y = position
        inside_board = 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE
        body_without_tail = set(list(self.snake.body)[:-1])
        return inside_board and position not in body_without_tail

    def _set_victory(self):
        self.game_won = True
        self.ai_status_text = "VICTORY! All 400 cells filled!"

    def draw(self):
        self.screen.fill(COLOR_BG)
        self._draw_board()
        if self.show_path and self.current_path:
            self._draw_path(self.current_path)
        self._draw_foods()
        self._draw_snake()
        self._draw_sidebar()

        if self.game_won:
            self._draw_overlay_message(
                "ABSOLUTE VICTORY!",
                "All 400 cells filled (100% of the board) - Press R to play again",
                (250, 204, 21),
            )
        elif self.game_over:
            self._draw_overlay_message(
                "GAME OVER", "Press R to try again", (239, 68, 68)
            )
        elif self.paused:
            self._draw_overlay_message(
                "PAUSED", "Press SPACE to continue", (56, 189, 248)
            )
        pygame.display.flip()

    def _draw_board(self):
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                rect = pygame.Rect(
                    x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE
                )
                pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)
        pygame.draw.line(
            self.screen,
            COLOR_BORDER,
            (BOARD_WIDTH, 0),
            (BOARD_WIDTH, BOARD_HEIGHT),
            2,
        )

    def _draw_path(self, path):
        if len(path) < 2:
            return
        points = [
            (
                cell[0] * CELL_SIZE + CELL_SIZE // 2,
                cell[1] * CELL_SIZE + CELL_SIZE // 2,
            )
            for cell in path
        ]
        surface = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        food_path = "Eat food" in self.ai_status_text
        path_color = (0, 242, 254, 120) if food_path else (168, 85, 247, 120)
        dot_color = (0, 242, 254, 180) if food_path else (168, 85, 247, 180)
        pygame.draw.lines(surface, path_color, False, points, 3)
        for point in points[1:-1]:
            pygame.draw.circle(surface, dot_color, point, 4)
        self.screen.blit(surface, (0, 0))

    def _draw_foods(self):
        for food in self.food_manager.foods:
            x = food.pos[0] * CELL_SIZE
            y = food.pos[1] * CELL_SIZE
            center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
            radius = CELL_SIZE // 2 - 4
            color = food.urgency_color
            progress = max(0.0, food.remaining_time / food.duration)

            glow = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                glow,
                (*color[:3], 60),
                (CELL_SIZE // 2, CELL_SIZE // 2),
                radius + 3,
            )
            self.screen.blit(glow, (x, y))
            pygame.draw.circle(self.screen, color, center, radius)

            if progress > 0.05:
                ring = pygame.Rect(
                    center[0] - radius - 1,
                    center[1] - radius - 1,
                    (radius + 1) * 2,
                    (radius + 1) * 2,
                )
                pygame.draw.arc(
                    self.screen,
                    (255, 255, 255),
                    ring,
                    -1.5708,
                    -1.5708 + 2 * 3.14159 * progress,
                    2,
                )

            label = self.font_small.render(
                f"{food.remaining_time:.1f}s", True, (255, 255, 255)
            )
            self.screen.blit(label, label.get_rect(center=center))

    def _draw_snake(self):
        body_length = self.snake.length
        for index, (x, y) in enumerate(self.snake.body):
            px, py = x * CELL_SIZE, y * CELL_SIZE
            rect = pygame.Rect(px + 2, py + 2, CELL_SIZE - 4, CELL_SIZE - 4)
            if index == 0:
                pygame.draw.rect(
                    self.screen, COLOR_SNAKE_HEAD, rect, border_radius=8
                )
                center = (px + CELL_SIZE // 2, py + CELL_SIZE // 2)
                for eye_x in (center[0] - 4, center[0] + 4):
                    pygame.draw.circle(
                        self.screen, COLOR_SNAKE_EYE, (eye_x, center[1] - 4), 3
                    )
                    pygame.draw.circle(
                        self.screen, COLOR_BG, (eye_x, center[1] - 4), 1
                    )
                continue

            ratio = index / max(1, body_length)
            color = tuple(
                int(start * (1 - ratio) + end * ratio)
                for start, end in zip(COLOR_SNAKE_BODY_1, COLOR_SNAKE_BODY_2)
            )
            pygame.draw.rect(self.screen, color, rect, border_radius=5)

    def _draw_sidebar(self):
        pygame.draw.rect(
            self.screen,
            COLOR_SIDEBAR_BG,
            pygame.Rect(BOARD_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT),
        )
        title = self.font_title.render("SNAKE A* ADVANCED", True, COLOR_SNAKE_HEAD)
        subtitle = self.font_small.render(
            "Priority: Length -> Time", True, COLOR_TEXT_MUTED
        )
        self.screen.blit(title, (BOARD_WIDTH + 15, 18))
        self.screen.blit(subtitle, (BOARD_WIDTH + 15, 44))

        self._draw_card(
            BOARD_WIDTH + 15,
            68,
            290,
            110,
            [
                ("Current score:", f"{self.score} food", (34, 197, 94)),
                ("High score:", self.high_score, (250, 204, 21)),
                (
                    "Snake length:",
                    f"{self.snake.length} / {self.board_capacity} cells",
                    COLOR_TEXT_MAIN,
                ),
                (
                    "Board coverage:",
                    f"{self.snake.length / self.board_capacity * 100:.1f}%",
                    COLOR_TEXT_MUTED,
                ),
            ],
        )

        total_free = self.board_capacity - self.snake.length
        food_details = [
            f"#{index + 1}:{food.remaining_time:.1f}s"
            for index, food in enumerate(self.food_manager.foods)
        ]
        food_text = " | ".join(food_details) if food_details else "Spawning..."
        self._draw_card(
            BOARD_WIDTH + 15,
            188,
            290,
            120,
            [
                ("Survival time:", f"{self.elapsed_time:.1f}s", COLOR_TEXT_MAIN),
                (
                    "Remaining empty cells:",
                    f"{total_free} ({total_free / self.board_capacity * 100:.1f}%)",
                    (56, 189, 248),
                ),
                (
                    "Safe-space volume:",
                    f"{self.last_free_space} cells",
                    (168, 85, 247),
                ),
                ("3s food timers:", food_text, COLOR_TEXT_MUTED),
            ],
        )

        _, phase_label, phase_color = self.solver.get_phase(self.snake.length)
        phase_card = pygame.Rect(BOARD_WIDTH + 15, 318, 290, 75)
        pygame.draw.rect(self.screen, COLOR_PANEL, phase_card, border_radius=8)
        self.screen.blit(
            self.font_small.render(
                "STRATEGY & ADAPTIVE PHASE:", True, COLOR_TEXT_MUTED
            ),
            (BOARD_WIDTH + 25, 325),
        )
        self.screen.blit(
            self.font_bold.render(phase_label, True, phase_color),
            (BOARD_WIDTH + 25, 344),
        )
        self.screen.blit(
            self.font_regular.render(self.ai_status_text, True, COLOR_TEXT_MAIN),
            (BOARD_WIDTH + 25, 368),
        )

        speed_name = SPEED_LEVELS[self.speed_index][0]
        speed_card = pygame.Rect(BOARD_WIDTH + 15, 402, 290, 42)
        pygame.draw.rect(self.screen, COLOR_PANEL, speed_card, border_radius=8)
        self.screen.blit(
            self.font_small.render(f"SPEED: {speed_name}", True, COLOR_TEXT_MAIN),
            (BOARD_WIDTH + 25, 414),
        )

        self._draw_button(
            BOARD_WIDTH + 15,
            456,
            290,
            36,
            "Continue [SPACE]" if self.paused else "Pause [SPACE]",
            (37, 99, 235) if self.paused else (51, 65, 85),
        )
        self._draw_button(
            BOARD_WIDTH + 15,
            500,
            290,
            36,
            "Start a new game [R]",
            (185, 28, 28),
        )
        self._draw_button(
            BOARD_WIDTH + 15,
            544,
            290,
            36,
            f"Change speed (1-4): {self.current_fps} FPS",
            (67, 56, 202),
        )
        self._draw_button(
            BOARD_WIDTH + 15,
            588,
            290,
            36,
            f"A* path [P]: {'ON' if self.show_path else 'OFF'}",
            (16, 185, 129) if self.show_path else (100, 116, 139),
        )

    def _draw_card(self, x, y, width, height, rows):
        pygame.draw.rect(
            self.screen,
            COLOR_PANEL,
            pygame.Rect(x, y, width, height),
            border_radius=8,
        )
        current_y = y + 8
        for label, value, value_color in rows:
            label_surface = self.font_regular.render(label, True, COLOR_TEXT_MUTED)
            value_surface = self.font_bold.render(str(value), True, value_color)
            self.screen.blit(label_surface, (x + 10, current_y))
            value_rect = value_surface.get_rect(
                right=x + width - 10, centery=current_y + 8
            )
            self.screen.blit(value_surface, value_rect)
            current_y += 24

    def _draw_button(self, x, y, width, height, text, background_color):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, background_color, rect, border_radius=6)
        label = self.font_bold.render(text, True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_overlay_message(self, title, subtitle, color):
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 200))
        self.screen.blit(overlay, (0, 0))
        title_surface = self.font_title.render(title, True, color)
        subtitle_surface = self.font_regular.render(subtitle, True, COLOR_TEXT_MAIN)
        self.screen.blit(
            title_surface,
            title_surface.get_rect(
                center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 - 20)
            ),
        )
        self.screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(
                center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 + 20)
            ),
        )

    def run(self):
        """Run the main game loop."""
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.current_fps)
