from enum import Enum
import random as rd
import streamlit as st
from st_clickable_images import clickable_images

class Tile:
    class Colors(Enum):
        BLACK = 0
        WHITE = 1

    class Directions(Enum):
        PRIVATE = 0
        PUBLIC = 1

    def __init__(self, color:Colors, number:int, direction = Directions.PRIVATE) -> None:
        self.color = color
        self.number = number
        self.direction = direction

    def __str__(self) -> str:
        return f"Color: {self.color.name}, Number: {self.number}, Direction: {self.direction.name}"
    
    def opponent_print(self) -> None:
        if self.direction == self.Directions.PRIVATE:
            return f"Color: {self.color.name}"
        else:
            return f"Color: {self.color.name}, Number: {self.number}"

class TableTileSet:
    """
    This class is used to store the tiles that are on the table (not yet drawn by players)

    Attributes:
        tile_set (set[Tile]): The set of tiles on the table

    Methods:
        init_tile_set: Set the tile_set into two sets, one black and one white, with tile numbers ranging from 0 to MAX_TILE_NUMBER
    """
    def __init__(self) -> None:
        self.tile_set = set()

    def init_tile_set(self) -> None:
        for color in Tile.Colors:
            for number in range(0, MAX_TILE_NUMBER + 1):
                tile = Tile(color, number)
                self.tile_set.add(tile)

class PlayerTileSet:
    """
    This class is used to store the tiles that are owned by the player and perform actions to the tiles

    Attributes:
        tile_set (set[Tile]): The set of tiles owned by the player
        temp_tile (Tile): The tile just drawn by the player and not yet placed into the tile set

    Methods:
        init_tile_set: Set the tile_set empty
        get_tile_list: Get the sorted list of tiles
        draw_tile: Draw a tile and set it the temp_tile if direct_draw = False (by default), draw a tile and put it directly into the tile_set if direct_draw = True
        make_guess: Make a guess on one of the private tiles owned by other player(s)
        verify_guess: Verify the guess made by other players
        end_turn: The player decide to end their's turn actively
        is_lose: Test if the player loses the game
    """
    def __init__(self) -> None:
        self.tile_set = set()
        self.temp_tile = None

    def init_tile_set(self) -> None:
        self.tile_set.clear()

    def get_tile_list(self) -> list[set]:
        return sorted(list(self.tile_set), key=lambda x: x.number * 2 + x.color.value)
    
    def draw_tile(self, table_tile_set, direct_draw = False) -> None:
        if len(table_tile_set.tile_set) == 0:
            raise ValueError('Empty table error')
        else:
            tile = rd.choice(list(table_tile_set.tile_set))
            if direct_draw:
                self.tile_set.add(tile)
            else:
                self.temp_tile = tile
            table_tile_set.tile_set.remove(tile)
            
    
    def make_guess(self, all_players:list, target_index:int, tile_index:int, tile_number:int) -> bool:
        if (target_index >= len(all_players) 
            or target_index < 0
            or target_index == all_players.index(self)
            or all_players[target_index].is_lose()
            or tile_number < 0
            or tile_number > MAX_TILE_NUMBER):
            raise ValueError('invalid guess')
        guessTarget = all_players[target_index]
        if tile_index < 0 or tile_index >= len(guessTarget.get_tile_list()):
            raise ValueError('invalid guess')
        elif guessTarget.get_tile_list()[tile_index].direction == Tile.Directions.PUBLIC:
            raise ValueError('invalid guess')
        elif guessTarget.verify_guess(tile_index, tile_number):
            return True # right guess
        else:
            if self.temp_tile != None:
                self.temp_tile.direction = Tile.Directions.PUBLIC
                self.tile_set.add(self.temp_tile)
                self.temp_tile = None
            return False # wrong guess

    def verify_guess(self, tile_index:int, tile_number:int) -> bool:
        tile = self.get_tile_list()[tile_index]
        if tile.number == tile_number:
            tile.direction = Tile.Directions.PUBLIC
            return True
        else:
            return False
        
    def end_turn(self) -> None:
        if self.temp_tile != None:
            self.temp_tile.direction = Tile.Directions.PRIVATE
            self.tile_set.add(self.temp_tile)
            self.temp_tile = None
        
    def is_lose(self) -> bool:
        return not any(tile.direction == Tile.Directions.PRIVATE for tile in self.tile_set)
     
class GameHost:
    """
    This class performs the game flow

    Attributes:
        table_tile_set (TableTileSet): A set of tiles on the table
        all_players (list[PlayerTileSet]): A list of player instances
    
    Methods:
        init_game: Initialize everything about the game
        is_game_over: Test if the winner appears
        show_self_status: Display the status of the player
        show_opponent_status: Display the status of other players
        guesses_making_stage: Allow the player to make guesses
        start_game: Run the main game routine
    """
    def __init__(self, numPlayer) -> None:
        self.table_tile_set = TableTileSet()
        self.all_players = [PlayerTileSet() for count in range(0, numPlayer)] # Set number of players here

    def init_game(self) -> None:
        self.table_tile_set.init_tile_set()
        for player in self.all_players:
            player.init_tile_set()
        for draw_count in range(0, INITIAL_TILES):
            for player in self.all_players:
                player.draw_tile(self.table_tile_set, direct_draw=True)

    def is_game_over(self) -> bool:
        last_players = list(player for player in self.all_players if player.is_lose() == False)
        if len(last_players) <= 1:
            return True
        else:
            return False

class App:
    """
    This class hosts the GUI and the game logic

    Attributes:
        game_stage(self.GameStage): Used to store the current game stage
        current_player(PlayerTileSet): Store the player currently interacting during the INTERACTING stage
        abled_2_end_turn(bool): Indicates whether the current player is able to end their turn
    
    Methods:
        restore_session: Restore the state variables from st.session_state
        init_game: Initalize the game and the state variables
        show_game_over_page: Show the game over page
        store_session: Store the state variables into st.session_state
    """

    def __init__(self) -> None:
        self.game_stage:self.GameStage
        self.current_player:PlayerTileSet
        self.abled_2_end_turn:bool

    class GameStage(Enum):
        UNINITIALIZED = 0
        INTERACTING = 1
        GAME_OVER = 2

    def restore_session(self) -> None:
        if 'game_stage' not in st.session_state:
            st.session_state.game_stage = self.GameStage.UNINITIALIZED
        
        self.game_stage = st.session_state.game_stage
        match self.game_stage.value:
            case self.GameStage.UNINITIALIZED.value:
                self.init_game()

            case self.GameStage.INTERACTING.value:
                self.current_player = st.session_state.current_player
                game_host.table_tile_set = st.session_state.table_tile_set
                game_host.all_players = st.session_state.all_players
                self.abled_2_end_turn = st.session_state.abled_2_end_turn
                self.interact_page = self.InteractPage(self)
                self.interact_page.show_interact_page(self.current_player)

            case self.GameStage.GAME_OVER.value:
                game_host.all_players = st.session_state.all_players
                self.show_game_over_page()

            case _:
                raise ValueError

    def init_game(self) -> None:
        game_host.init_game()
        self.game_stage = self.GameStage.INTERACTING
        self.current_player = game_host.all_players[0]
        self.abled_2_end_turn = False
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
                self.space_asset = 'https://github.com/hhxc-0/RL-DaVinciCode/blob/main/assets/space.png?raw=true'
                self.white_tile_asset = 'https://github.com/hhxc-0/RL-DaVinciCode/blob/main/assets/white_tile.png?raw=true'
                self.black_tile_asset = 'https://github.com/hhxc-0/RL-DaVinciCode/blob/main/assets/black_tile.png?raw=true'
                self.white_tile_assets = []
                self.black_tile_assets = []
                for tile_color in ('white_tile', 'black_tile'):
                    if tile_color == 'white_tile':
                        asset_list = self.white_tile_assets
                    else:
                        asset_list = self.black_tile_assets

                    for tile_number in range(0, MAX_TILE_NUMBER + 1):
                        asset_list.append('https://github.com/hhxc-0/RL-DaVinciCode/blob/main/assets/' + tile_color + '_' + str(tile_number) + '.png?raw=true')

        def append_tile_row(self, tile, tile_row, default_show_number:bool):
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

        def next_player(self, player):
            last_players = list(last_player for last_player in game_host.all_players if player.is_lose() == False)
            if last_players.index(self.app_self.current_player) < len(last_players) - 1:
                self.app_self.current_player = last_players[last_players.index(self.app_self.current_player) + 1]
            else:
                self.app_self.current_player = last_players[0]

        def show_interact_page(self, player:PlayerTileSet) -> None:
            # Title
            st.markdown('# The Da Vinci Code Game')

            # Player's information
            tile_buttons = {}
            tile_row = []
            st.markdown(f'## Tiles of player {game_host.all_players.index(player)} (you):')
            st.markdown('### The final one is the one you just drawn')
            for tile in player.get_tile_list():
                self.append_tile_row(tile, tile_row, True)

            if player.temp_tile == None:
                try:
                    player.draw_tile(game_host.table_tile_set)
                except ValueError:
                    pass
            if player.temp_tile != None:
                tile_row.append(self.tile_assets.space_asset)
                self.append_tile_row(player.temp_tile, tile_row, True)

            tile_buttons[player] = (
                clickable_images(
                    tile_row,
                    titles=[f"Image #{str(i)}" for i in range(len(tile_row))],
                    div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
                    img_style={"margin": "5px", "height": "200px"},
                    key=game_host.all_players.index(player)
                )
            )

            tile_directions = ''
            for tile in player.get_tile_list():
                tile_directions += str('<font color="red"> Public</font>' if tile.direction.value == Tile.Directions.PUBLIC.value else '<font color="green"> Private</font>')
            st.markdown(f'### Tile status: {tile_directions}', unsafe_allow_html=True) # unsafe_allow_html is unsafe

            # Other players' information and guessing interactions
            other_players = list(game_host.all_players)
            other_players.remove(player)
            for other_player in other_players:
                st.markdown(f'## Tiles of player {game_host.all_players.index(other_player)}:')
                tile_row = []
                for tile in other_player.get_tile_list():
                    self.append_tile_row(tile, tile_row, False)

                if 'button_keys' not in st.session_state:
                    st.session_state.button_keys = {i:(i+1)*(10**10) for i in range(NUMBER_OF_PLAYERS)}
                tile_buttons[other_player] = (
                    clickable_images(
                        tile_row,
                        titles=[f"Image #{str(i)}" for i in range(len(tile_row))],
                        div_style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap"},
                        img_style={"margin": "5px", "height": "200px"},
                        # key=game_host.all_players.index(other_player)
                        key=st.session_state.button_keys[game_host.all_players.index(other_player)]
                    )
                )

            st.markdown('### Please enter a number here and click on a tile to guess')
            guess_number = st.number_input('', min_value=0, max_value=MAX_TILE_NUMBER, value=0, step=1)

            if self.app_self.abled_2_end_turn:
                end_turn_button = st.button('End turn')
            else:
                end_turn_button = False

            # Detect clicks and perform guess
            if self.app_self.abled_2_end_turn == True and end_turn_button:
                self.app_self.abled_2_end_turn = False
                player.end_turn()
                self.next_player(player)
                self.app_self.store_session()
            
            for other_player in other_players:
                if tile_buttons[other_player] > -1:
                    st.session_state.button_keys[game_host.all_players.index(other_player)] = st.session_state.button_keys[game_host.all_players.index(other_player)] + 1
                    try:
                        guess_result = player.make_guess(game_host.all_players, game_host.all_players.index(other_player), tile_buttons[other_player], guess_number)
                        if guess_result == True:
                            st.markdown('### <font color="green">Right guess</font>', unsafe_allow_html=True) # unsafe_allow_html is unsafe
                            if game_host.is_game_over():
                                self.app_self.game_stage = self.app_self.GameStage.GAME_OVER
                            self.app_self.abled_2_end_turn = True
                            self.app_self.store_session()
                        else:
                            st.markdown('### <font color="yellow">Wrong guess</font>', unsafe_allow_html=True) # unsafe_allow_html is unsafe
                            self.next_player(player)
                            self.app_self.store_session()
                        st.rerun()
                    except ValueError:
                        st.markdown('### <font color="red">Invalid guess</font>', unsafe_allow_html=True) # unsafe_allow_html is unsafe
                        st.rerun()
            self.app_self.store_session()

    def show_game_over_page(self) -> None:
        # Title
        st.markdown('# The Da Vinci Code Game')

        # Winner text
        last_player_index = game_host.all_players.index(set(player for player in game_host.all_players if player.is_lose() == False).pop())
        st.markdown(f'## Game over, the winner is player {last_player_index}!')
        if st.button('Play again'):
            self.game_stage = self.GameStage.UNINITIALIZED
            self.store_session()

    def store_session(self) -> None:
        st.session_state.game_stage = self.game_stage
        match self.game_stage.value:
            case self.GameStage.UNINITIALIZED.value:
                pass

            case self.GameStage.INTERACTING.value:
                st.session_state.current_player = self.current_player
                st.session_state.table_tile_set = game_host.table_tile_set
                st.session_state.all_players = game_host.all_players
                st.session_state.abled_2_end_turn = self.abled_2_end_turn
                
            case self.GameStage.GAME_OVER.value:
                pass

NUMBER_OF_PLAYERS = 3
MAX_TILE_NUMBER = 11
INITIAL_TILES = 4

if __name__ == '__main__':
    game_host = GameHost(NUMBER_OF_PLAYERS)
    app = App()
    app.restore_session()