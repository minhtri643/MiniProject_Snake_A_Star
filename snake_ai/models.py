"""Domain models for the snake and dynamic food system."""

import random
import time
from collections import deque

from .config import (
    COLOR_FOOD_FRESH,
    COLOR_FOOD_MID,
    COLOR_FOOD_URGENT,
    FOOD_DURATION,
    GRID_SIZE,
    INITIAL_LENGTH,
    INITIAL_POSITION,
    MAX_FOOD,
    MIN_FOOD,
)


class FoodItem:
    """A food item that expires after a configurable duration."""

    def __init__(self, pos, duration=FOOD_DURATION):
        self.pos = pos
        self.spawn_time = time.time()
        self.duration = duration

    @property
    def remaining_time(self):
        return max(0.0, self.duration - (time.time() - self.spawn_time))

    @property
    def is_expired(self):
        return self.remaining_time <= 0.0

    @property
    def urgency_color(self):
        if self.remaining_time > 2.0:
            return COLOR_FOOD_FRESH
        if self.remaining_time > 1.0:
            return COLOR_FOOD_MID
        return COLOR_FOOD_URGENT


class FoodManager:
    """Spawn, expire, and remove food without overlapping occupied cells."""

    def __init__(self, grid_size=GRID_SIZE, min_food=MIN_FOOD, max_food=MAX_FOOD):
        self.grid_size = grid_size
        self.min_food = min_food
        self.max_food = max_food
        self.target_count = random.randint(self.min_food, self.max_food)
        self.foods = []

    def get_food_positions(self):
        return {food.pos for food in self.foods}

    def update(self, snake_body):
        self.foods = [food for food in self.foods if not food.is_expired]
        if len(self.foods) >= self.target_count:
            return

        occupied = set(snake_body) | self.get_food_positions()
        for _ in range(self.target_count - len(self.foods)):
            new_pos = self._spawn_random_pos(occupied)
            if new_pos:
                self.foods.append(FoodItem(new_pos))
                occupied.add(new_pos)

    def _spawn_random_pos(self, occupied):
        available = [
            (x, y)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
            if (x, y) not in occupied
        ]
        return random.choice(available) if available else None

    def remove_at(self, pos):
        for index, food in enumerate(self.foods):
            if food.pos == pos:
                self.foods.pop(index)
                self.target_count = random.randint(self.min_food, self.max_food)
                return True
        return False

    def reset(self, snake_body):
        self.foods.clear()
        self.target_count = random.randint(self.min_food, self.max_food)
        self.update(snake_body)


class Snake:
    """Snake state and movement rules."""

    def __init__(self, start_pos=INITIAL_POSITION, initial_length=INITIAL_LENGTH):
        self.reset(start_pos, initial_length)

    def reset(self, start_pos=INITIAL_POSITION, initial_length=INITIAL_LENGTH):
        x, y = start_pos
        self.body = deque((x - index, y) for index in range(initial_length))
        self.direction = (1, 0)
        self.alive = True

    @property
    def head(self):
        return self.body[0]

    @property
    def tail(self):
        return self.body[-1]

    @property
    def length(self):
        return len(self.body)

    def get_body_set(self):
        return set(self.body)

    def move_to(self, next_pos, ate_food=False):
        self.body.appendleft(next_pos)
        if not ate_food:
            self.body.pop()
