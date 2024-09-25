import numpy as np

import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register

import game


class DavinciCodeEnv(gym.Env):
    """
    Environment Documentation: Davinci Code Multi-Agent Environment

    Description:
        This environment simulates a multi-agent game of Davinci Code, where multiple players compete to guess the correct tiles based on given clues.

    Observation Space:
        Type: MultiDiscrete
        The observation space consists of two components:

        1. player_obs:
            A 3D tensor representing the state of each player's tiles, with shape (num_players, 2 * max_tile_num, 3), where:
                - num_players: The total number of players in the game.
                - 2 * max_tile_num: The total number of tiles, multiplied by 2 (one set for each color).
                - 3: The number of features associated with each tile.

            Tile Features:
                Each tile is described by the following features:
                    - tile_direction:
                        - 0: Private tile
                        - 1: Public tile
                    - tile_color:
                        - 0: Unknown color
                        - 1: Black tile
                        - 2: White tile
                    - tile_number:
                        - 0: Unknown number
                        - 1 to max_tile_num: The specific number on the tile

        2. current_player_index:
            An integer indicating the index of the current player whose turn it is to act.

    Action Space:
        Type: MultiDiscrete
        The action space consists of three discrete values:
            - target_player_index: The index of the player being targeted for a guess.
            - tile_index: The index of the tile that the player is guessing.
            - number_on_tile: The specific number on the tile that the player is guessing.

    Reward Structure:
        TODO: Define the reward function, including positive and negative rewards based on correct or incorrect guesses.

    Starting State:
        The game board is initialized with two sets of tiles, each containing max_tile_num tiles, one set for each color (black and white).
        All players begin with initial_tiles, which are randomly drawn from the board at the start of the game.

    Episode Termination:
        TODO: Define the conditions under which an episode terminates, such as reaching a certain score, completing a set number of rounds, or other game-specific criteria.
    """

    def __init__(
        self,
        num_players=3,
        initial_player=0,
        max_tile_num=11,
        initial_tiles=4,
    ):
        self._num_players = num_players  # The number of players
        self._current_player_index = initial_player  # The index of the current player
        self._max_tile_num = max_tile_num  # The maximum number on the tiles
        self._initial_tiles = initial_tiles  # The number of tiles each player starts with

        self._observation_space_nvec = np.repeat(
            np.expand_dims(
                np.repeat(
                    np.expand_dims((3, 3, max_tile_num + 1), 0), 2 * max_tile_num, 0
                ),  # For each tile: (tile_direction, tile_color, tile_number)
                # tile_direction: 0 for does not exist, 1 for private, 2 for public
                # tile_color: 0 for unknown, 1 for black, 2 for white
                # tile_number: 0 for unknown, 1 to max_tile_num for the number on tile
                0,
            ),
            num_players,
            0,
        )
        self.observation_space = spaces.MultiDiscrete(self._observation_space_nvec, np.uint8)
        # MultiDiscrete observation space: MultiDiscrete(3, 3, max_tile_num+1)

        self.action_space = spaces.MultiDiscrete(
            [num_players - 1, 2 * max_tile_num, max_tile_num], np.uint8
        )  # MultiDiscrete action space: [target_player_index, tile_index, number_on_tile]

    def _get_obs(self):
        player_obs = np.zeros_like(self._observation_space_nvec, np.uint8)
        for player_index in range(self._num_players):
            for tile_index, tile in enumerate(
                sorted(
                    list(self.game_host.all_players[player_index].tile_set),
                    key=lambda x: x.number * 2 + x.color.value,
                )
            ):
                player_obs[player_index, tile_index, 0] = tile.direction.value + 1
                player_obs[player_index, tile_index, 1] = tile.color.value + 1
                player_obs[player_index, tile_index, 2] = tile.number

        player_obs = np.roll(
            player_obs, self._current_player_index, axis=0
        )  # Shift the current player's observation to the front

        mask_condition = player_obs[1 : self._num_players, :, 0] == 1  # Only show public tiles
        player_obs[1 : self._num_players, :, 2][
            mask_condition
        ] = 0  # Hide the number on private tiles from other players

        # current_player_index = self._game_host.get_next_player_index(self._current_player_index)

        return player_obs

    def _get_reward(self, action, invalid_action: bool, guess_result: bool) -> float:
        reward = np.float32(0.0)

        if invalid_action or self.game_host.all_players[action[0]].is_lose():
            reward = -3.0  # Penalty for invalid action
        elif guess_result:
            reward = 1.0  # Reward for correct guess
        else:
            reward = -1.0  # Penalty for incorrect guess

        return reward

    def _get_info(self):
        return {"current_player_index": self._current_player_index}

    def reset(self, seed=None, options=None, new_player_index=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self.game_host = game.GameHost(  # Set game_host to private variable after debugging
            self._num_players, self._initial_tiles, self._max_tile_num, super().np_random
        )
        self.game_host.init_game()

        if new_player_index is None:
            self._current_player_index = super().np_random.integers(self._num_players)
        assert 0 <= self._current_player_index < self._num_players, "Invalid player index"

        self.game_host.all_players[self._current_player_index].draw_tile(
            self.game_host.table_tile_set
        )

        observation = self._get_obs()
        info = self._get_info()

        return observation, info

    def step(self, action):
        def _normalize_action(action) -> bool:
            # Restrict the action to the valid range
            original_action = np.copy(action)
            action[0] = np.clip(action[0], 0, self._num_players - 1)
            action[1] = np.clip(
                action[1], 0, len(self.game_host.all_players[action[0]].tile_set) - 1
            )
            action[2] = np.clip(action[2], 0, self._max_tile_num - 1)

            invalid_action = not np.array_equal(action, original_action)

            # Offset the relative palyer index to the absolute index
            action[0] = (action[0] + self._current_player_index + 1) % self._num_players
            # Offset the tile index to the true number on the tile
            action[2] += 1

            return invalid_action

        action = np.copy(action)
        invalid_action = _normalize_action(action)

        target_player_index, tile_index, number_on_tile = action
        try:
            guess_result = self.game_host.all_players[self._current_player_index].make_guess(
                self.game_host.all_players, target_player_index, tile_index, number_on_tile
            )
        except ValueError:
            invalid_action = True
            guess_result = False

        terminated = (
            self.game_host.is_game_over()
        )  # An episode is done when there is only one player have private tiles
        reward = self._get_reward(action, invalid_action, guess_result)
        if not terminated and guess_result == False:
            self._current_player_index = self.game_host.get_next_player_index(
                self._current_player_index
            )  # Update the current player index to the next player
            try:
                self.game_host.all_players[self._current_player_index].draw_tile(
                    self.game_host.table_tile_set
                )
            except ValueError:
                pass
        observation = self._get_obs()
        info = self._get_info()
        return observation, reward, terminated, False, info

    def close(self):
        pass


register(
    id="DavinciCode-v0",
    entry_point="davinci_code_env:DavinciCodeEnv",
    max_episode_steps=300,
)
