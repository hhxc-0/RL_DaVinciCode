import numpy as np
from copy import deepcopy
import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register

import game


class DavinciCodeEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        num_players=3,
        initial_player=0,
        max_tile_num=12,
        initial_tiles=4,
        render_mode=None,
    ):
        self._num_players = num_players  # The number of players
        self._current_player_index = initial_player  # The index of the current player
        self._max_tile_num = max_tile_num  # The maximum number on the tiles
        self._initial_tiles = initial_tiles  # The number of tiles each player starts with

        # TODO: define observation space and action space

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self._render_mode = render_mode

        self._last_action_mask = None

    def _get_obs(self) -> dict:
        # Part1: main observation of tiles of each player
        def get_tile_obs(tile: game.Tile, force_visible: bool) -> np.ndarray:
            tile_obs = np.zeros(
                (
                    1  # exists
                    + 2  # light/dark one hot
                    + (1 + self._max_tile_num),  # unknown or the number on the tile one hot
                )
            )
            if tile is not None:
                tile_obs[0] = 1  # tile exists
                if tile.color == game.Tile.Colors.BLACK:
                    tile_obs[1] = 1  # dark tile
                    tile_obs[2] = 0
                else:
                    tile_obs[1] = 0
                    tile_obs[2] = 1  # light tile

                if tile.direction == game.Tile.Directions.PUBLIC or force_visible:
                    tile_obs[tile.number + 3] = 1  # number on the tile
                else:
                    tile_obs[3] = 1  # tile is not visible
            return tile_obs

        def get_action_mask():
            # TODO: implement
            raise NotImplementedError

        main_obs_list = []
        for player_index, player in enumerate(self.game_host.all_players):
            player_tile_list = player.get_tile_list()
            player_obs_list = []
            for tile in player_tile_list:
                player_obs_list.append(
                    get_tile_obs(tile, force_visible=player_index == self._current_player_index)
                )
            player_obs = np.array(player_obs_list)
            player_obs = np.pad(
                player_obs,
                pad_width=((0, 2 * self._max_tile_num - player_obs.shape[0]), (0, 0)),
                mode="constant",
                constant_values=0,
            )
            main_obs_list.append(player_obs)
        main_obs = np.array(main_obs_list)

        # Part2: tile just drawn
        temp_tile_obs = get_tile_obs(
            self.game_host.all_players[self._current_player_index].temp_tile, True
        )

        # Part3: action mask
        # TODO: implement
        action_mask = get_action_mask()

        obs = np.concatenate([main_obs.flatten(), temp_tile_obs, action_mask])
        return obs

    def _get_info(self, correct_guess: bool = False, invalid_action: bool = False) -> dict:
        return {
            "current_player_index": self._current_player_index,
            "correct_guess": correct_guess,
            "invalid_action": invalid_action,
        }

    def _get_reward(self):
        # TODO: Calculate reward
        raise NotImplementedError

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
        if (
            self._last_action_mask is not None
            and self._last_action_mask[target_player_index, tile_index, number_on_tile] == 0
        ):
            invalid_action = True
            truncated = True

        reward = self._get_reward()
        observation = self._get_obs()
        info = self._get_info(guess_result, invalid_action)

        if self._render_mode == "human":
            self._render_frame()

        return observation, reward, terminated, truncated, info

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


register(
    id="DavinciCode-v2",
    entry_point="davinci_code_env_v2:DavinciCodeEnv",
    max_episode_steps=300,
)
