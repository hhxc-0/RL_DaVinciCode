from enum import Enum
import random as rd
import PySimpleGUI as sg

class InvalidGuessError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)
    
class EmptyTableError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

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
    def __init__(self) -> None:
        self.tile_set = set()

    def init_tile_set(self) -> None:
        for color in Tile.Colors:
            for number in range(0, MAX_TILE_NUMBER + 1):
                tile = Tile(color, number)
                self.tile_set.add(tile)

class PlayerTileSet:
    def __init__(self) -> None:
        self.tile_set = set()
        self.temp_tile = None

    def init_tile_set(self) -> None:
        self.tile_set.clear()

    def get_tile_list(self) -> list[set]:
        return sorted(list(self.tile_set), key=lambda x: x.number * 2 + x.color.value)
    
    def draw_tile(self, table_tile_set, direct_draw = False) -> None:
        if len(table_tile_set.tile_set) == 0:
            raise EmptyTableError
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
            raise InvalidGuessError # invalid guess
        guessTarget = all_players[target_index]
        if tile_index < 0 or tile_index >= len(guessTarget.get_tile_list()):
            raise InvalidGuessError # invalid guess
        elif guessTarget.get_tile_list()[tile_index].direction == Tile.Directions.PUBLIC:
            raise InvalidGuessError # invalid guess
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
        return not any(private_tile.direction == Tile.Directions.PRIVATE for private_tile in self.tile_set)

class GameHost:
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

    def is_game_over(self, output = False) -> bool:
        last_players = list(player for player in self.all_players if player.is_lose() == False)
        if len(last_players) <= 1:
            if output:
                print(f"Game over, player {self.all_players.index(last_players[0])} wins")
            return True
        else:
            return False

    def show_self_status(self, player) -> None:
        print(f"Your tile list is:")
        for tile in player.get_tile_list():
            print(tile)

    def show_opponent_status(self, player) -> None:
        other_players = list(self.all_players)
        other_players.remove(player)
        for other_player in other_players:
            print(f"The tile list of Player {self.all_players.index(other_player)} is")
            for index, tile in enumerate(other_player.get_tile_list()):
                print(index, ' ', tile.opponent_print())

    def guesses_making_stage(self, player) -> bool:
        while True:
            try:
                guess_result = player.make_guess(self.all_players, int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
                return guess_result
            except InvalidGuessError:
                print('Invalid guess')

    def start_game(self) -> None:
        self.init_game()

        while(self.is_game_over() == False):
            last_players = list(player for player in self.all_players if player.is_lose() == False)
            for player in last_players:
                print(f"You are the player with index {self.all_players.index(player)}")
                self.show_self_status(player)
                
                self.show_opponent_status(player)

                try:
                    player.draw_tile(self.table_tile_set)
                    print(f"The tile you draw is {player.temp_tile}")
                except EmptyTableError:
                    print('Unabled to draw, table is empty')

                print("Please make a guess")
                guess_result = self.guesses_making_stage(player)
                while(guess_result == True):
                    if self.is_game_over():
                        break
                    print('Right guess, do another one or end your turn')
                    self.show_self_status(player)
                    self.show_opponent_status(player)
                    if int(input('To end turn, input -1. To continue, input any other number: ')) == -1:
                        player.end_turn()
                        break
                    else:
                        guess_result = self.guesses_making_stage(player)
                if self.is_game_over():
                    break
                print('Turn ends')
                print()

        self.is_game_over(output=True)
     
class Gui:
    None

NUMBER_OF_PLAYERS = 3
MAX_TILE_NUMBER = 11
INITIAL_TILES = 4

if __name__ == '__main__':
    game_host = GameHost(NUMBER_OF_PLAYERS)
    game_host.start_game()
