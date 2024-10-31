import numpy as np
from copy import deepcopy
import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register

import game


def get_original_index(transformed_index: int, current_player_index: int, num_players: int) -> int:
    """
    Given the transformed index of a player, return the original index of the player.

    Args:
        transformed_index (int): The transformed index of the player.
        current_player_index (int): The original index of the current player.
        num_players (int): The total number of players.

    Returns:
        int: The original index of the player.
    """
    return (transformed_index - 1 + current_player_index) % num_players


class DavinciCodeEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        num_players=2,
        initial_player=0,
        max_tile_num=12,
        initial_tiles=4,
        render_mode=None,
    ):
        self._num_players = num_players  # The number of players
        self._current_player_index = initial_player  # The index of the current player
        self._max_tile_num = max_tile_num  # The maximum number on the tiles
        self._initial_tiles = initial_tiles  # The number of tiles each player starts with

        # Define the new observation space structure
        self._observation_space_nvec = np.zeros((2 * max_tile_num, 4), dtype=np.uint8)
        self._observation_space_nvec[:, 0] = (
            np.arange(2 * max_tile_num) // max_tile_num
        )  # Color: 0 for black, 1 for white
        self._observation_space_nvec[:, 1] = np.arange(1, 2 * max_tile_num + 1) % (
            max_tile_num + 1
        )  # Number: 1 to max_tile_num
        self._observation_space_nvec[:, 2] = (
            0  # Player ID: 0 for public deck, 1 for current player, 2 to n for other players
        )
        self._observation_space_nvec[:, 3] = 0  # Order in hand: 0 for deck, 1 to n for hand

        self.observation_space = spaces.Dict(
            {
                "observation": spaces.Box(
                    low=0,
                    high=np.max(self._observation_space_nvec),
                    shape=self._observation_space_nvec.shape,
                    dtype=np.uint8,
                ),
                "action_mask": spaces.Box(
                    low=0,
                    high=1,
                    shape=(num_players - 1, 2 * max_tile_num, max_tile_num),
                    dtype=np.uint8,
                ),
            }
        )

        self.action_space = spaces.MultiDiscrete(
            [num_players - 1, 2 * max_tile_num, max_tile_num], np.uint8
        )  # MultiDiscrete action space: [target_player_index, tile_index, number_on_tile]

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self._render_mode = render_mode

        self._last_action_mask = None

    def _get_obs(self) -> dict:
        player_obs = np.zeros((2 * self._max_tile_num, 4), dtype=np.uint8)
        tile_count = 0

        # Record the tiles in each player's hand
        for player_pos, player_index in enumerate(np.roll(np.arange(self._num_players), -self._current_player_index)):
            tile_set = deepcopy(self.game_host.all_players[player_index].tile_set)
            if player_index == self._current_player_index and self.game_host.all_players[player_index].temp_tile is not None:
                # Record the tile in the current player's hand
                tile_set.add(self.game_host.all_players[player_index].temp_tile)
            
            for tile_index, tile in enumerate(
                sorted(
                    list(tile_set),
                    key=lambda x: x.number * 2 + x.color.value,
                )
            ):
                player_obs[tile_count, 0] = tile.color.value + 1  # Color: 1 for black, 2 for white
                player_obs[tile_count, 1] = (
                    tile.number
                    if player_index == self._current_player_index
                    or tile.direction == game.Tile.Directions.PUBLIC
                    else 0
                )  # Number: 1 to max_tile_num or 0 for unknown
                player_obs[tile_count, 2] = player_pos + 1  # Player ID: 1 for current player, 2 to n for other players
                player_obs[tile_count, 3] = tile_index + 1  # Order in hand: 1 to n
                tile_count += 1

        # Record the tiles in the deck
        for tile in self.game_host.table_tile_set.tile_set:
            # player_obs[tile_count, 0] = tile.color.value + 1  # Color: 1 for black, 2 for white
            player_obs[tile_count, 0] = 0  # Color: 0 for deck
            player_obs[tile_count, 1] = 0  # Number: 0 for unknown
            player_obs[tile_count, 2] = 0  # Player ID: 0 for deck
            player_obs[tile_count, 3] = 0  # Order in hand: 0 for deck
            tile_count += 1

        # Generate the action mask
        action_mask = self._generate_action_mask()
        self._last_action_mask = action_mask

        return {"observation": player_obs, "action_mask": action_mask}

    def _generate_action_mask(self) -> np.ndarray:
        action_mask = np.zeros(
            (self._num_players - 1, 2 * self._max_tile_num, self._max_tile_num), dtype=np.uint8
        )
        for target_player_index in range(self._num_players - 1):
            for tile_index in range(2 * self._max_tile_num):
                for number_on_tile in range(self._max_tile_num):
                    if self._is_valid_action(target_player_index, tile_index, number_on_tile + 1):
                        action_mask[target_player_index, tile_index, number_on_tile] = 1

        # Update action_mask based on history_guesses
        for target_player_index in range(self._num_players - 1):
            original_index = get_original_index(
                target_player_index + 2, self._current_player_index, self._num_players
            )
            target_player = self.game_host.all_players[original_index]
            for tile_index in range(2 * self._max_tile_num):
                if tile_index < len(target_player.get_tile_list()):
                    tile = target_player.get_tile_list()[tile_index]
                    for guess in tile.history_guesses:
                        action_mask[target_player_index, tile_index, guess - 1] = 0
        return action_mask

    def _is_valid_action(self, target_player_index: int, tile_index: int, tile_number: int) -> bool:
        try:
            original_index = get_original_index(
                target_player_index + 2, self._current_player_index, self._num_players
            )
            target_player = self.game_host.all_players[original_index]
            if target_player.is_lose():
                return False
            if tile_number < 1 or tile_number > self._max_tile_num:
                return False
            if tile_index < 0 or tile_index >= len(target_player.get_tile_list()):
                return False
            if target_player.get_tile_list()[tile_index].direction == game.Tile.Directions.PUBLIC:
                return False
            return True
        except (IndexError, ValueError):
            return False

    def _get_info(self, correct_guess: bool = False, invalid_action: bool = False) -> dict:
        return {
            "current_player_index": self._current_player_index,
            "correct_guess": correct_guess,
            "invalid_action": invalid_action,
        }

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self.game_host = game.GameHost(
            self._num_players, self._initial_tiles, self._max_tile_num, super().np_random
        )
        self.game_host.init_game()
        self._current_player_index = 0

        assert 0 <= self._current_player_index < self._num_players, "Invalid player index"

        self.game_host.all_players[self._current_player_index].draw_tile(
            self.game_host.table_tile_set,
            direct_draw=True,
        )

        observation = self._get_obs()
        info = self._get_info()

        if self._render_mode == "human":
            self._render_frame()

        return observation, info

    def step(self, action):
        target_player_index, tile_index, number_on_tile = action
        guess_result = False
        invalid_action = False

        original_index = get_original_index(
            target_player_index + 2, self._current_player_index, self._num_players
        )

        try:
            guess_result = self.game_host.all_players[self._current_player_index].make_guess(
                self.game_host.all_players, original_index, tile_index, number_on_tile + 1
            )
        except ValueError as e:
            # print("error", e.args[0])
            pass

        terminated = self.game_host.is_game_over()
        truncated = False
        if self._last_action_mask is not None and self._last_action_mask[target_player_index, tile_index, number_on_tile] == 0:
            invalid_action = True
            truncated = True

        # Calculate reward
        if terminated:
            if not self.game_host.all_players[self._current_player_index].is_lose():
                reward = 50  # Large reward for winning the game
            else:
                reward = -50  # Large penalty for losing the game
        elif invalid_action:
            reward = -15  # Penalty for not following the action mask
        else:
            # if guess_result:
            #     reward = 10  # Reward for guessing correctly
            # else:
            #     reward = -1  # Penalty for guessing incorrectly
            true_number_on_tile = (
                self.game_host.all_players[target_player_index].get_tile_list()[tile_index].number
            )
            distance = np.abs(true_number_on_tile - number_on_tile)
            reward = np.float32(
                5 - (np.float32(distance) * 1.0)
            )  # Countinuous reward for guessing around the correct number
            reward = np.clip(reward, -5.0, 5.0)

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
        info = self._get_info(guess_result, invalid_action)

        if self._render_mode == "human":
            self._render_frame()

        return observation, reward, terminated, truncated, info

    def render(self):
        pass

    def _render_frame(self):
        print("----------------")
        print(f"Current Player: {self._current_player_index+1}")
        for player_index in np.roll(np.arange(self._num_players), -self._current_player_index):
            print(f"\nPlayer {player_index+1}'s tiles:")
            for tile_index, tile in enumerate(
                sorted(
                    list(self.game_host.all_players[player_index].tile_set),
                    key=lambda x: x.number * 2 + x.color.value,
                )
            ):
                print(f"Tile {tile_index+1}: {tile.direction.name} {tile.color.name} {tile.number}")
        print("----------------")

    def close(self):
        pass

    @property
    def current_player_index(self):
        return self._current_player_index


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
    id="DavinciCode-v1",
    entry_point="davinci_code_env_v1:DavinciCodeEnv",
    max_episode_steps=300,
)
