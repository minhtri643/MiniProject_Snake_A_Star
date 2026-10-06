"""A* pathfinding and survival strategy for the autonomous snake."""

import heapq
from collections import deque

from .config import COLOR_PHASE_1, COLOR_PHASE_2, COLOR_PHASE_3, GRID_SIZE


def manhattan_distance(a, b):
    """Return the Manhattan distance between two grid cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class AStarSolver:
    """Choose food-seeking moves while preserving space and tail access."""

    def __init__(self, grid_size=GRID_SIZE):
        self.grid_size = grid_size
        self.directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def get_phase(self, length):
        if length < 50:
            return 1, "Phase 1: Maximum speed", COLOR_PHASE_1
        if length < 150:
            return 2, "Phase 2: Volume balance", COLOR_PHASE_2
        return 3, "Phase 3: Maximum survival", COLOR_PHASE_3

    def get_neighbors(self, pos, obstacles):
        x, y = pos
        return [
            (x + dx, y + dy)
            for dx, dy in self.directions
            if 0 <= x + dx < self.grid_size
            and 0 <= y + dy < self.grid_size
            and (x + dx, y + dy) not in obstacles
        ]

    def a_star(self, start, goal, obstacles):
        """Find a shortest path from start to goal using Manhattan distance."""
        if start == goal:
            return [start]

        open_set = [(manhattan_distance(start, goal), 0, 0, start)]
        came_from = {}
        g_score = {start: 0}
        counter = 0

        while open_set:
            _, _, _, current = heapq.heappop(open_set)
            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return list(reversed(path))

            current_g = g_score[current]
            for neighbor in self.get_neighbors(current, obstacles):
                tentative_g = current_g + 1
                if neighbor in g_score and tentative_g >= g_score[neighbor]:
                    continue
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heuristic = manhattan_distance(neighbor, goal)
                counter += 1
                heapq.heappush(
                    open_set,
                    (tentative_g + heuristic, heuristic, counter, neighbor),
                )
        return None

    def bfs_reachable(self, start, obstacles):
        """Count the connected cells reachable from start."""
        visited = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in self.get_neighbors(current, obstacles):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return len(visited)

    def is_food_path_safe_advanced(self, snake, path_to_food, phase):
        """Simulate eating and verify tail access plus sufficient free space."""
        if not path_to_food or len(path_to_food) < 2:
            return False, 0

        virtual_body = deque(snake.body)
        for next_step in path_to_food[1:-1]:
            virtual_body.appendleft(next_step)
            virtual_body.pop()
        virtual_body.appendleft(path_to_food[-1])

        virtual_head = virtual_body[0]
        virtual_tail = virtual_body[-1]
        obstacles = set(list(virtual_body)[:-1])
        tail_path = self.a_star(virtual_head, virtual_tail, obstacles)
        if not tail_path:
            return False, 0

        free_space = self.bfs_reachable(virtual_head, obstacles)
        snake_len = snake.length
        max_board_space = self.grid_size * self.grid_size - snake_len

        if phase == 1:
            is_safe = free_space >= min(6, max_board_space)
        elif phase == 2:
            is_safe = free_space >= min(int(snake_len * 0.60), max_board_space)
        else:
            required = min(int(snake_len * 0.75), max_board_space)
            is_safe = free_space >= required and len(tail_path) >= 2
        return is_safe, free_space

    def find_longest_tail_chasing_move(self, snake):
        """Choose a safe neighbor maximizing space and distance to the tail."""
        obstacles = set(list(snake.body)[:-1])
        neighbors = self.get_neighbors(snake.head, obstacles)
        valid_moves = []

        for neighbor in neighbors:
            simulated_body = deque(snake.body)
            simulated_body.appendleft(neighbor)
            simulated_body.pop()
            simulated_tail = simulated_body[-1]
            simulated_obstacles = set(list(simulated_body)[:-1])
            tail_path = self.a_star(neighbor, simulated_tail, simulated_obstacles)
            if tail_path is None:
                continue

            tail_distance = len(tail_path)
            free_space = self.bfs_reachable(neighbor, simulated_obstacles)
            direct_distance = manhattan_distance(neighbor, simulated_tail)
            score = free_space * 100 + tail_distance * 10 + direct_distance
            valid_moves.append((score, neighbor, tail_path))

        if not valid_moves:
            return None, None
        _, move, path = max(valid_moves, key=lambda candidate: candidate[0])
        return move, path

    def find_longest_survival_move(self, snake):
        """Choose the neighboring cell with the largest reachable area."""
        obstacles = set(list(snake.body)[:-1])
        neighbors = self.get_neighbors(snake.head, obstacles)
        if not neighbors:
            return None
        return max(neighbors, key=lambda cell: self.bfs_reachable(cell, obstacles))

    def get_next_move(self, snake, food_items, step_delay=0.05):
        """Run the complete food-selection and survival decision pipeline."""
        phase, phase_label, _ = self.get_phase(snake.length)
        obstacles = set(list(snake.body)[:-1])
        safe_candidates = []

        for food in food_items:
            path = self.a_star(snake.head, food.pos, obstacles)
            if not path or len(path) <= 1:
                continue

            steps = len(path) - 1
            if steps * step_delay > food.remaining_time:
                continue

            is_safe, free_space = self.is_food_path_safe_advanced(snake, path, phase)
            if is_safe:
                safe_candidates.append(
                    {"steps": steps, "path": path, "free_space": free_space}
                )

        if safe_candidates:
            if phase == 1:
                safe_candidates.sort(key=lambda candidate: candidate["steps"])
            elif phase == 2:
                safe_candidates.sort(
                    key=lambda candidate: candidate["steps"]
                    - candidate["free_space"] * 0.1
                )
            else:
                safe_candidates.sort(
                    key=lambda candidate: (-candidate["free_space"], candidate["steps"])
                )

            chosen = safe_candidates[0]
            return (
                chosen["path"][1],
                chosen["path"],
                f"[{phase_label}] Eat food ({chosen['steps']} steps)",
                chosen["free_space"],
            )

        tail_move, tail_path = self.find_longest_tail_chasing_move(snake)
        if tail_move:
            path_len = len(tail_path) if tail_path else 0
            return (
                tail_move,
                tail_path,
                f"[{phase_label}] Chase tail and stretch body (L={path_len})",
                0,
            )

        survival_move = self.find_longest_survival_move(snake)
        if survival_move:
            return survival_move, None, f"[{phase_label}] Open area (Flood-Fill)", 0
        return None, None, "Dead end (Game Over)", 0
