from enum import Enum
import os
import base64
import streamlit as st
from st_clickable_images import clickable_images
from game import Tile, PlayerTileSet, GameHost

import numpy as np
import torch
from torch import nn
import gymnasium as gym
from actor_critic import ActorCritic
import davinci_code_env_v2


class App:
    """
    This class hosts the GUI and the game logic

    Attributes:
        game_stage(self.GameStage): Used to store the current game stage
        current_player(PlayerTileSet): Store the player currently interacting during the INTERACTING stage

    Methods:
        restore_session: Restore the state variables from st.session_state
        init_game: Initalize the game and the state variables
        show_game_over_page: Show the game over page
        store_session: Store the state variables into st.session_state
    """

    def __init__(self) -> None:
        self.game_stage: self.GameStage
        self.current_player_index: int

    class GameStage(Enum):
        UNINITIALIZED = 0
        INTERACTING = 1
        GAME_OVER = 2

    def restore_session(self) -> None:
        if "game_stage" not in st.session_state:
            st.session_state.game_stage = self.GameStage.UNINITIALIZED

        self.game_stage = st.session_state.game_stage
        match self.game_stage.value:
            case self.GameStage.UNINITIALIZED.value:
                self.init_game()

            case self.GameStage.INTERACTING.value:
                self.env = st.session_state.env
                self.input_number_missing = st.session_state.input_number_missing
                self.interact_page = self.InteractPage(self)
                self.interact_page.show_interact_page()

            case self.GameStage.GAME_OVER.value:
                self.env = st.session_state.env
                self.show_game_over_page()

            case _:
                raise ValueError

    def init_game(self) -> None:
        self.env = gym.make(
            "DavinciCode-v2",
            # max_episode_steps=100,
            num_players=NUMBER_OF_PLAYERS,
            # initial_player=0,
            max_tile_num=MAX_TILE_NUMBER,
            initial_tiles=INITIAL_TILES,
        )
        self.env.reset()
        self.game_stage = self.GameStage.INTERACTING
        self.input_number_missing = False
        self.store_session()
        st.rerun()

    class InteractPage:
        """
        This class is used to perform the game logic and GUI interactions during INTERACTING stage

        Attributes:
            app_self: self of the outer class
            tile_assets(self.Assets): A instance of self.Assets, used to store the URL of assets

        Methods:
            append_tile_row: Append a tile asset into a row of tiles
            next_player: Set current_player the next player
            show_interact_page: Show the interaction page and perform the game logic
        """

        def __init__(self, app_self) -> None:
            self.app_self = app_self
            self.tile_assets = self.Assets()

        class Assets:
            """
            This class is used to store the URL of assets
            """

            # @st.cache_resource
            def __init__(self) -> None:
                def rel_path_img_to_base64(rel_path):
                    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)
                    with open(abs_path, "rb") as image:
                        encoded = base64.b64encode(image.read()).decode()
                        return f"data:image/jpeg;base64,{encoded}"

                self.space_asset = rel_path_img_to_base64("assets/space.png")
                self.white_tile_asset = rel_path_img_to_base64("assets/white_tile.png")
                self.black_tile_asset = rel_path_img_to_base64("assets/black_tile.png")
                self.white_tile_assets = []
                self.black_tile_assets = []
                for tile_color in ("white_tile", "black_tile"):
                    if tile_color == "white_tile":
                        asset_list = self.white_tile_assets
                    else:
                        asset_list = self.black_tile_assets

                    for tile_number in range(0, MAX_TILE_NUMBER + 1):
                        asset_list.append(
                            rel_path_img_to_base64(
                                "assets/" + tile_color + "_" + str(tile_number) + ".png"
                            )
                        )

        def append_tile_row(self, tile, tile_row, default_show_number: bool):
            if tile.color.value == Tile.Colors.WHITE.value:
                if default_show_number or tile.direction.value == Tile.Directions.PUBLIC.value:
                    tile_row.append(self.tile_assets.white_tile_assets[tile.number])
                else:
                    tile_row.append(self.tile_assets.white_tile_asset)
            else:
                if default_show_number or tile.direction.value == Tile.Directions.PUBLIC.value:
                    tile_row.append(self.tile_assets.black_tile_assets[tile.number])
                else:
                    tile_row.append(self.tile_assets.black_tile_asset)

        def show_interact_page(self) -> None:
            # Title
            st.markdown("# The Da Vinci Code Game")

            # Links
            st.markdown(
                "#### [Github](https://github.com/hhxc-0/RL_DaVinciCode) | [Game rules](https://github.com/hhxc-0/RL_DaVinciCode?tab=readme-ov-file#da-vinci-code-game-rules)",
                unsafe_allow_html=True,
            )

            game_host = self.app_self.env.unwrapped.game_host

            # Player's information
            current_player_index = HUMAN_PLAYER_INDEX
            current_player_tile_set = game_host.all_players[current_player_index]
            tile_buttons = {}
            tile_row = []
            st.markdown(f"## Tiles of player {current_player_index} (you):")
            for tile in current_player_tile_set.get_tile_list():
                self.append_tile_row(tile, tile_row, True)

            if current_player_tile_set.temp_tile != None:
                st.markdown("### The final one is the one you just drawn")
                tile_row.append(self.tile_assets.space_asset)
                self.append_tile_row(current_player_tile_set.temp_tile, tile_row, True)

            tile_buttons[current_player_index] = clickable_images(
                tile_row,
                titles=[f"Image #{str(i)}" for i in range(len(tile_row))],
                div_style={
                    "display": "flex",
                    "justify-content": "center",
                    "flex-wrap": "wrap",
                },
                img_style={"margin": "5px", "height": "200px"},
                key=current_player_index,
            )

            tile_directions = ""
            for tile in current_player_tile_set.get_tile_list():
                tile_directions += str(
                    '<font color="red"> Public</font>'
                    if tile.direction.value == Tile.Directions.PUBLIC.value
                    else '<font color="green"> Private</font>'
                )
            st.markdown(
                f"### Tile status: {tile_directions}", unsafe_allow_html=True
            )  # unsafe_allow_html is unsafe

            # Other players' information and guessing interactions
            other_players = list(game_host.all_players)
            other_players.remove(current_player_tile_set)
            for other_player in other_players:
                st.markdown(
                    f"## Tiles of player {game_host.all_players.index(other_player)} (model):"
                )
                tile_row = []
                for tile in other_player.get_tile_list():
                    self.append_tile_row(tile, tile_row, False)

                if "button_keys" not in st.session_state:
                    st.session_state.button_keys = {
                        i: (i + 1) * (10**10) for i in range(NUMBER_OF_PLAYERS)
                    }
                tile_buttons[other_player] = clickable_images(
                    tile_row,
                    titles=[f"Image #{str(i)}" for i in range(len(tile_row))],
                    div_style={
                        "display": "flex",
                        "justify-content": "center",
                        "flex-wrap": "wrap",
                    },
                    img_style={"margin": "5px", "height": "200px"},
                    # key=game_host.all_players.index(other_player)
                    key=st.session_state.button_keys[game_host.all_players.index(other_player)],
                )

            st.markdown("### Please enter a number here and click on a tile to guess")

            if self.app_self.input_number_missing:
                st.markdown(
                    '<h3><font color="red">Please enter a number</font></h3>',
                    unsafe_allow_html=True,
                )
                self.app_self.input_number_missing = False

            guess_number = st.number_input(
                "guess number",
                min_value=1,
                max_value=MAX_TILE_NUMBER,
                value=None,
                step=1,
                label_visibility="hidden",
            )

            reset_button = st.button("Reset game", type="primary")

            # Detect clicks and perform guess
            if reset_button:
                self.app_self.game_stage = self.app_self.GameStage.UNINITIALIZED
                self.app_self.store_session()
                st.rerun()

            for other_player in other_players:
                if tile_buttons[other_player] > -1:
                    st.session_state.button_keys[game_host.all_players.index(other_player)] = (
                        st.session_state.button_keys[game_host.all_players.index(other_player)] + 1
                    )
                    if guess_number is None:
                        self.app_self.input_number_missing = True
                        self.app_self.store_session()
                        st.rerun()

                    action_player_index = other_players.index(other_player)
                    action_tile_index = tile_buttons[other_player]
                    action_number_on_tile = guess_number - 1
                    max_tile_num = self.app_self.env.unwrapped._max_tile_num
                    action = (
                        action_player_index * (2 * max_tile_num * max_tile_num)
                        + action_tile_index * max_tile_num
                        + action_number_on_tile
                    )
                    obs, _, terminated, truncated, info = self.app_self.env.step(action)
                    if info["invalid_action"]:
                        st.markdown(
                            '### <font color="red">Invalid guess</font>',
                            unsafe_allow_html=True,
                        )  # unsafe_allow_html is unsafe
                        st.rerun()
                    human_correct_guess = info["correct_guess"]

                    while self.app_self.env.unwrapped._current_player_index != HUMAN_PLAYER_INDEX:
                        dist, _ = model(torch.FloatTensor(obs).to(device))
                        action = dist.sample()
                        obs, _, terminated, truncated, info = self.app_self.env.step(action.cpu().numpy())

                        if terminated or truncated:
                            break
                    if human_correct_guess == True:
                        if game_host.is_game_over():
                            self.app_self.game_stage = self.app_self.GameStage.GAME_OVER
                        self.app_self.store_session()
                    else:
                        st.markdown(
                            '### <font color="yellow">Wrong guess</font>',
                            unsafe_allow_html=True,
                        )  # unsafe_allow_html is unsafe
                        self.app_self.store_session()
                    st.rerun()

            self.app_self.store_session()

    def show_game_over_page(self) -> None:
        # Title
        st.markdown("# The Da Vinci Code Game")

        # Links
        st.markdown(
            "#### [Github](https://github.com/hhxc-0/RL_DaVinciCode) | [Game rules](https://github.com/hhxc-0/RL_DaVinciCode?tab=readme-ov-file#da-vinci-code-game-rules)",
            unsafe_allow_html=True,
        )

        # Winner text
        last_player_index = self.env.unwrapped.game_host.all_players.index(
            set(
                player
                for player in self.env.unwrapped.game_host.all_players
                if player.is_lose() == False
            ).pop()
        )
        if last_player_index == HUMAN_PLAYER_INDEX:
            st.markdown(f"## Game over, the winner is player {last_player_index} (you)!")
        else:
            st.markdown(f"## Game over, the winner is player {last_player_index} (model)!")
        if st.button("Play again", type="primary"):
            self.game_stage = self.GameStage.UNINITIALIZED
            self.store_session()

    def store_session(self) -> None:
        st.session_state.game_stage = self.game_stage
        match self.game_stage.value:
            case self.GameStage.UNINITIALIZED.value:
                pass

            case self.GameStage.INTERACTING.value:
                st.session_state.env = self.env
                st.session_state.input_number_missing = self.input_number_missing

            case self.GameStage.GAME_OVER.value:
                pass


NUMBER_OF_PLAYERS = 3
MAX_TILE_NUMBER = 12
INITIAL_TILES = 4
HUMAN_PLAYER_INDEX = 0
USE_MODEL = True
MODEL_PATH = "./ppo_model_saves/" + "ppo_model_final.pth"

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.load(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), MODEL_PATH),
        map_location=device,
        weights_only=False,
    )
    model.to(device)
    app = App()
    app.restore_session()
