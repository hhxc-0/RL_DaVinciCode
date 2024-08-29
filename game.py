from enum import Enum
import numpy as np


class Tile:
    class Colors(Enum):
        BLACK = 0
        WHITE = 1

    class Directions(Enum):
        PRIVATE = 0
        PUBLIC = 1

    def __init__(self, color: Colors, number: int, direction=Directions.PRIVATE) -> None:
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
        max_tile_number (int): The maximum number a tile can have
        tile_set (set[Tile]): The set of tiles on the table

    Methods:
        init_tile_set: Set the tile_set into two sets, one black and one white, with tile numbers ranging from 0 to MAX_TILE_NUMBER
    """

    def __init__(self, max_tile_number: int) -> None:
        assert max_tile_number and max_tile_number > 0, "Invalid max_tile_number"
        self.max_tile_number = max_tile_number
        self.tile_set = set()

    def init_tile_set(self) -> None:
        for color in Tile.Colors:
            for number in range(0, self.max_tile_number + 1):
                tile = Tile(color, number)
                self.tile_set.add(tile)


class PlayerTileSet:
    """
    This class is used to store the tiles that are owned by the player and perform actions to the tiles

    Attributes:
        max_tile_number (int): The maximum number a tile can have
        np_random (np.random.Generator): The random number generator
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

    def __init__(self, max_tile_number: int, np_random: np.random.Generator = None) -> None:
        assert max_tile_number and max_tile_number > 0, "Invalid max_tile_number"
        self.max_tile_number = max_tile_number
        self.np_random = np_random if np_random else np.random.default_rng()
        self.tile_set = set()
        self.temp_tile = None

    def init_tile_set(self) -> None:
        self.tile_set.clear()

    def get_tile_list(self) -> list[set]:
        return sorted(list(self.tile_set), key=lambda x: x.number * 2 + x.color.value)

    def draw_tile(self, table_tile_set, direct_draw=False) -> None:
        if len(table_tile_set.tile_set) == 0:
            raise ValueError("Empty table error")
        else:
            tile = self.np_random.choice(list(table_tile_set.tile_set))
            if direct_draw:
                self.tile_set.add(tile)
            else:
                self.temp_tile = tile
            table_tile_set.tile_set.remove(tile)

    def make_guess(
        self, all_players: list, target_index: int, tile_index: int, tile_number: int
    ) -> bool:
        if (
            target_index >= len(all_players)
            or target_index < 0
            or target_index == all_players.index(self)
            or all_players[target_index].is_lose()
            or tile_number < 0
            or tile_number > self.max_tile_number
        ):
            raise ValueError("invalid guess")
        guessTarget = all_players[target_index]
        if tile_index < 0 or tile_index >= len(guessTarget.get_tile_list()):
            raise ValueError("invalid guess")
        elif guessTarget.get_tile_list()[tile_index].direction == Tile.Directions.PUBLIC:
            raise ValueError("invalid guess")
        elif guessTarget.verify_guess(tile_index, tile_number):
            return True  # right guess
        else:
            if self.temp_tile != None:
                self.temp_tile.direction = Tile.Directions.PUBLIC
                self.tile_set.add(self.temp_tile)
                self.temp_tile = None
            return False  # wrong guess

    def verify_guess(self, tile_index: int, tile_number: int) -> bool:
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
        initial_tiles (int): The number of tiles each player starts with
        np_random (np.random.Generator): The random number generator
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

    def __init__(
        self, numPlayer: int, initial_tiles: int, max_tile_number: int, np_random: np.random.Generator = None
    ) -> None:
        assert initial_tiles and initial_tiles > 0, "Invalid initial_tiles"
        self.initial_tiles = initial_tiles
        self.np_random = np_random if np_random else np.random.default_rng()
        self.table_tile_set = TableTileSet(max_tile_number)
        self.all_players = [
            PlayerTileSet(max_tile_number, self.np_random) for count in range(0, numPlayer)
        ]  # Set number of players here

    def init_game(self) -> None:
        self.table_tile_set.init_tile_set()
        for player in self.all_players:
            player.init_tile_set()
        for draw_count in range(0, self.initial_tiles):
            for player in self.all_players:
                player.draw_tile(self.table_tile_set, direct_draw=True)

    def is_game_over(self) -> bool:
        last_players = list(player for player in self.all_players if player.is_lose() == False)
        if len(last_players) <= 1:
            return True
        else:
            return False
