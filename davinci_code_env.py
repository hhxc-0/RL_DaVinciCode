import numpy as np

import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register

import game


class DavinciCodeEnv(gym.Env):
    """
    Environment Documentation: Davinci Code Multi-Agent Environment

    Description:
        This environment simulates a multi-agent game of Davinci Code, where multiple players compete to guess the correct tiles based on provided clues.

    Observation Space:
        Type: MultiDiscrete
    A 3D tensor representing the state of each player's tiles, with a shape of (num_players, 2 * max_tile_num, 3), where:
        - dim 0: Index of the player
        - dim 1: Index of the tile
        - dim 2: Features of the tile, including:

    Tile Features:
        Each tile is characterized by the following features:
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

    Action Space:
        Type: MultiDiscrete
        The action space consists of three discrete values:
            - target_player_index: The index of the player targeted for a guess.
            - tile_index: The index of the tile being guessed.
            - number_on_tile: The specific number on the tile being guessed.

    Reward:
        The reward consists of two components:
            - invalid_action_penalty: A penalty for invalid actions, which depends on how far the action is from a correct action if it can be corrected, or how severely the action fails if it cannot be corrected.
            - guess_reward: A reward for guessing the correct number on the tile. This is a continuous reward of 1 when the guess is correct, decreasing as the distance between the guess and the correct number increases.

        The calculation of the resultant reward is as follows:
            - If the guess is valid, only the guess_reward is considered.
            - If the guess is invalid but can be corrected, the total reward is the sum of the guess_reward and the invalid_action_penalty.
            - If the guess is invalid and cannot be corrected, only the invalid_action_penalty is considered.

    Starting State:
        The game board is initialized with two sets of tiles, each containing max_tile_num tiles, one set for each color (black and white). All players start with initial_tiles, which are randomly drawn from the board at the beginning of the game.

    Episode Termination:
        The episode terminates when all players except one have revealed all their tiles as public, resulting in a winner.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        num_players=3,
        initial_player=0,
        max_tile_num=11,
        initial_tiles=4,
        render_mode=None,
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

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self._render_mode = render_mode

    def _get_obs(self) -> np.ndarray:
        player_obs = np.zeros_like(self._observation_space_nvec, np.uint8)
        for player_index in range(self._num_players):
            for tile_index, tile in enumerate(
                sorted(
                    list(self._game_host.all_players[player_index].tile_set),
                    key=lambda x: x.number * 2 + x.color.value,
                )
            ):
                player_obs[player_index, tile_index, 0] = tile.direction.value + 1
                player_obs[player_index, tile_index, 1] = tile.color.value + 1
                player_obs[player_index, tile_index, 2] = tile.number

        player_obs = np.roll(
            player_obs, self._current_player_index - 1, axis=0
        )  # Shift the current player's observation to the front

        mask_condition = player_obs[1 : self._num_players, :, 0] == 1  # Only show public tiles
        player_obs[1 : self._num_players, :, 2][
            mask_condition
        ] = 0  # Hide the number on private tiles from other players

        # current_player_index = self._game_host.get_next_player_index(self._current_player_index)

        return player_obs

    def _get_reward(
        self,
        target_player_index: int,
        tile_index: int,
        number_on_tile: int,
        invalid_action: bool,
        invalid_action_penalty: float,
        guess_result: bool,
    ) -> float:
        guess_reward = np.float32(0.0)
        penalty = np.float32(0.0)

        if invalid_action:
            penalty = np.float32(invalid_action_penalty)  # Penalty for invalid actions

        try:
            true_number_on_tile = (
                self._game_host.all_players[target_player_index].get_tile_list()[tile_index].number
            )
        except IndexError:
            # return penalty
            return 0
        distance = np.abs(true_number_on_tile - number_on_tile)
        guess_reward = np.float32(
            1 - (np.float32(distance) * 0.2)
        )  # Countinuous reward for guessing around the correct number
        guess_reward = np.clip(guess_reward, 0.0, 1.0)

        return guess_reward + penalty

    def _get_info(self, correct_guess: bool = False, invalid_action: bool = False) -> dict:
        return {
            "current_player_index": self._current_player_index,
            "correct_guess": correct_guess,
            "invalid_action": invalid_action,
        }

    def reset(self, seed=None, options=None, new_player_index=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self._game_host = game.GameHost(
            self._num_players, self._initial_tiles, self._max_tile_num, super().np_random
        )
        self._game_host.init_game()

        if new_player_index is None:
            self._current_player_index = super().np_random.integers(self._num_players)
        assert 0 <= self._current_player_index < self._num_players, "Invalid player index"

        self._game_host.all_players[self._current_player_index].draw_tile(
            self._game_host.table_tile_set
        )

        observation = self._get_obs()
        info = self._get_info()

        if self._render_mode == "human":
            self._render_frame()

        return observation, info

    def step(self, action):
        def _normalize_action(action) -> bool:
            # Restrict the action to the valid range
            original_action = np.copy(action)
            action[0] = np.clip(action[0], 0, self._num_players - 1)
            action[1] = np.clip(
                action[1], 0, len(self._game_host.all_players[action[0]].tile_set) - 1
            )
            action[2] = np.clip(action[2], 0, self._max_tile_num - 1)

            invalid_action = not np.array_equal(action, original_action)
            invalid_action_penalty = 0.0
            if invalid_action:
                invalid_action_penalty = np.clip(
                    -(np.abs(action - original_action).sum() * 0.05), -1.0, 0.0
                )
                # print(f"Invalid action: {original_action} -> {action}, penalty: {invalid_action_penalty}")

            # Offset the relative palyer index to the absolute index
            action[0] = (action[0] + self._current_player_index + 1) % self._num_players
            # Offset the tile index to the true number on the tile
            action[2] += 1

            return invalid_action, invalid_action_penalty

        action = np.copy(action)
        invalid_action, invalid_action_penalty = _normalize_action(action)

        target_player_index, tile_index, number_on_tile = action
        guess_result = False
        try:
            guess_result = self._game_host.all_players[self._current_player_index].make_guess(
                self._game_host.all_players, target_player_index, tile_index, number_on_tile
            )
        except ValueError as e:
            match e.args[0]:
                case game.PlayerTileSet.InvalidActionErrorEnum.TARGET_INDEX_OUT_OF_RANGE:
                    invalid_action_penalty = -1.0
                case game.PlayerTileSet.InvalidActionErrorEnum.TARGET_INDEX_INVALID:
                    invalid_action_penalty = -0.7
                case game.PlayerTileSet.InvalidActionErrorEnum.TILE_INDEX_OUT_OF_RANGE:
                    invalid_action_penalty = -1.0
                case game.PlayerTileSet.InvalidActionErrorEnum.TILE_NUMBER_OUT_OF_RANGE:
                    invalid_action_penalty = -1.0
                case game.PlayerTileSet.InvalidActionErrorEnum.TILE_ALREADY_PUBLIC:
                    invalid_action_penalty = -0.2
                case _:
                    raise e
            invalid_action = True
            guess_result = False
            # print(f"Invalid action: {e.args[0]}, penalty: {invalid_action_penalty}")

        terminated = (
            self._game_host.is_game_over()
        )  # An episode is done when there is only one player have private tiles
        reward = self._get_reward(
            target_player_index,
            tile_index,
            number_on_tile,
            invalid_action,
            invalid_action_penalty,
            guess_result,
        )
        if not terminated and guess_result == False:
            self._current_player_index = self._game_host.get_next_player_index(
                self._current_player_index
            )  # Update the current player index to the next player
            try:
                self._game_host.all_players[self._current_player_index].draw_tile(
                    self._game_host.table_tile_set
                )
            except ValueError:
                pass
        observation = self._get_obs()
        info = self._get_info(guess_result, invalid_action)

        if self._render_mode == "human":
            self._render_frame()

        return observation, reward, terminated, False, info

    def render(self):
        pass

    def _render_frame(self):
        print("----------------")
        print(f"Current Player: {self._current_player_index+1}")
        for player_index in np.roll(np.arange(self._num_players), -self._current_player_index):
            print(f"\nPlayer {player_index+1}'s tiles:")
            for tile_index, tile in enumerate(
                sorted(
                    list(self._game_host.all_players[player_index].tile_set),
                    key=lambda x: x.number * 2 + x.color.value,
                )
            ):
                print(f"Tile {tile_index+1}: {tile.direction.name} {tile.color.name} {tile.number}")
        print("----------------")

    def close(self):
        pass


class TupleObservation(gym.ObservationWrapper):
    def __init__(self, env):
        super().__init__(env)
        self.observation_space = gym.spaces.Tuple(
            [
                gym.spaces.MultiDiscrete(
                    nvec=env.observation_space.nvec[:, :, 0:2], dtype=env.observation_space.dtype
                ),
                gym.spaces.Box(
                    low=0,
                    high=env.observation_space.nvec[:, :, 2],
                    dtype=env.observation_space.dtype,
                ),
            ]
        )

    def observation(self, obs):
        obs = (obs[:, :, 0:2], obs[:, :, 2])
        return obs


register(
    id="DavinciCode-v0",
    entry_point="davinci_code_env:DavinciCodeEnv",
    max_episode_steps=300,
)
