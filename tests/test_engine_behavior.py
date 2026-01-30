import unittest

from src.engine.game import TriominoGame
from src.models.board import ValidPlacement
from src.engine.rules import calculate_draw_failure_penalty, calculate_pass_penalty


class TestEngineBehavior(unittest.TestCase):
    def test_execute_place_invalid_does_not_remove_tile(self):
        game = TriominoGame(player_names=["A", "B"], seed=1)
        game.setup_round()
        game.play_opening()

        player = game.current_player
        initial_hand_size = player.hand_size
        initial_score = player.score

        tile = player.hand[0]
        invalid = ValidPlacement(
            row=0,
            col=0,
            orientation="up",
            rotation=0,
            edges_matched=0,
        )

        result = game.execute_place(player, tile, invalid, draws_made=0)

        self.assertFalse(result.success)
        self.assertEqual(player.hand_size, initial_hand_size)
        self.assertEqual(player.score, initial_score)

    def test_draw_failure_penalty_three(self):
        points, event = calculate_draw_failure_penalty(3)
        self.assertEqual(points, -40)
        self.assertEqual(event.points, -40)

    def test_pass_penalty(self):
        points, event = calculate_pass_penalty()
        self.assertEqual(points, -10)
        self.assertEqual(event.points, -10)


if __name__ == "__main__":
    unittest.main()
