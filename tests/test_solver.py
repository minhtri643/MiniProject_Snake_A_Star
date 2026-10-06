"""Unit tests for core pathfinding and model behavior."""

import unittest

from snake_ai.models import Snake
from snake_ai.solver import AStarSolver, manhattan_distance


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.solver = AStarSolver(grid_size=5)

    def test_manhattan_distance(self):
        self.assertEqual(manhattan_distance((0, 0), (3, 4)), 7)

    def test_a_star_finds_shortest_open_path(self):
        path = self.solver.a_star((0, 0), (2, 2), obstacles=set())
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))
        self.assertEqual(len(path) - 1, 4)

    def test_a_star_avoids_obstacles(self):
        obstacles = {(1, 0), (1, 1), (1, 2), (1, 3)}
        path = self.solver.a_star((0, 0), (2, 0), obstacles)
        self.assertIsNotNone(path)
        self.assertTrue(all(cell not in obstacles for cell in path))

    def test_snake_grows_only_after_eating(self):
        snake = Snake(start_pos=(2, 2), initial_length=3)
        snake.move_to((2, 1), ate_food=False)
        self.assertEqual(snake.length, 3)
        snake.move_to((2, 0), ate_food=True)
        self.assertEqual(snake.length, 4)


if __name__ == "__main__":
    unittest.main()
