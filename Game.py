from typing import Union
from enum import Enum
import random as rd
import PySimpleGUI as sg

class Color(Enum):
    BLACK = 0
    WHITE = 1

class Direction(Enum):
    PRIVATE = 0
    PUBLIC = 1

class InvalidGuessError(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message
    
class Tile:
    def __init__(self, color:Color, number:int, direction = Direction.PRIVATE) -> None:
        self.color = color
        self.number = number
        self.direction = direction

    def __str__(self) -> None:
        return f"Color: {self.color.name}, Number: {self.number}, Direction: {self.direction.name}"
    
    def opponent_print(self) -> None:
        if self.direction == Direction.PRIVATE:
            return f"Color: {self.color.name}"
        else:
            return f"Color: {self.color.name}, Number: {self.number}"

class TableTileSet:
    def __init__(self) -> None:
        self.tile_set = set()

    def init_tile_set(self) -> None:
        for color in Color:
            for number in range(0, 12):
                tile = Tile(color, number)
                self.tile_set.add(tile)

class PlayerTileSet:
    def __init__(self) -> None:
        self.tile_set = set()
        self.temp_tile:Tile

    def init_tile_set(self) -> None:
        self.tile_set.clear()

    def get_tile_list(self) -> list[set]:
        return sorted(list(self.tile_set), key=lambda x: x.number * 2 + x.color.value)
    
    def draw_tile(self, table_tile_set, direct_draw = False) -> bool:
        if len(table_tile_set.tile_set) == 0:
            return False
        else:
            tile = rd.choice(list(table_tile_set.tile_set))
            if direct_draw:
                self.tile_set.add(tile)
            else:
                self.temp_tile = tile
            table_tile_set.tile_set.remove(tile)
            return True
            
    
    def make_guess(self, all_players:list, target_index:int, tile_index:int, tile_number:int) -> bool:
        if (target_index >= len(all_players) 
            or target_index < 0 
            or target_index == all_players.index(self)
            or all_players[target_index].is_lose()
            or tile_number < 0
            or tile_number > 11):
            raise InvalidGuessError # invalid guess
        guessTarget = all_players[target_index]
        if tile_index < 0 or tile_index >= len(guessTarget.get_tile_list()):
            raise InvalidGuessError # invalid guess
        elif guessTarget.get_tile_list()[tile_index].direction == Direction.PUBLIC:
            raise InvalidGuessError # invalid guess
        elif guessTarget.verify_guess(tile_index, tile_number):
            return True # right guess
        else:
            if self.temp_tile != None:
                self.temp_tile.direction = Direction.PUBLIC
                self.tile_set.add(self.temp_tile)
                self.temp_tile = None
            return False # wrong guess

    def verify_guess(self, tile_index:int, tile_number:int) -> bool:
        tile = self.get_tile_list()[tile_index]
        if tile.number == tile_number:
            tile.direction = Direction.PUBLIC
            return True
        else:
            return False
        
    def end_turn(self) -> None:
        if self.temp_tile != None:
            self.temp_tile.direction = Direction.PRIVATE
            self.tile_set.add(self.temp_tile)
            self.temp_tile = None
        
    def is_lose(self) -> bool:
        if len(list(private_tile for private_tile in self.tile_set if private_tile.direction == Direction.PRIVATE)) == 0:
            return True
        else:
            return False

class GameHost:
    def __init__(self, numPlayer) -> None:
        self.table_tile_set = TableTileSet()
        self.all_players = [PlayerTileSet() for count in range(0, numPlayer)] # Set number of players here

    def init_tile_sets(self) -> None:
        self.table_tile_set.init_tile_set()
        for player in self.all_players:
            player.init_tile_set()
        for draw_count in range(0, 4):
            for player in self.all_players:
                player.draw_tile(self.table_tile_set, direct_draw=True)

    def is_gameover(self, output = False) -> bool:
        last_players = list(player for player in self.all_players if player.is_lose() == False)
        for index, player in enumerate(self.all_players):
            if len(last_players) <= 1:
                if output:
                    print(f"Game over, player {self.all_players.index(last_players[0])} wins")
                return True
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

    def make_guess(self, player) -> None:
        while True:
            try:
                guess_result = player.make_guess(self.all_players, int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
                return guess_result
            except InvalidGuessError:
                print('Invalid guess')

    def start_game(self) -> None:
        self.init_tile_sets()

        while(self.is_gameover() == False):
            last_players = list(player for player in self.all_players if player.is_lose() == False)
            for player in last_players:
                print(f"You are the player with index {self.all_players.index(player)}")
                self.show_self_status(player)
                
                self.show_opponent_status(player)

                if player.draw_tile(self.table_tile_set):
                    print(f"The tile you draw is {player.temp_tile}")
                else:
                    print('Unabled to draw, table is empty')
                print("Please make a guess")
                guess_result = self.make_guess(player)
                while(guess_result == True or guess_result == None):
                    if self.is_gameover():
                        break
                    print('Right guess, do another one or end your turn')
                    self.show_self_status(player)
                    self.show_opponent_status(player)
                    if int(input('To end turn, input -1. To continue, input any other number: ')) == -1:
                        player.end_turn()
                        break
                    else:
                        guess_result = self.make_guess()
                if self.is_gameover():
                    break
                print('Turn ends')
                print()

        self.is_gameover(output=True)
     
class Gui:
    None

class TestClass:
    None

NUMBER_OF_PLAYERS = 2

game_host = GameHost(NUMBER_OF_PLAYERS)
game_host.start_game()

"""
这段代码存在一些不规范之处，以下是一些潜在的问题和改进建议：

2. **命名约定**：Python通常使用`snake_case`命名变量和函数，而类名使用`CamelCase`。例如，`self.InitGame`、`self.IsOver`、`self.ShowSelfStatus`、`self.ShowOpponentStatus` 和 `self.make_guess` 应该改为 `init_game`、`is_over`、`show_self_status`、`show_opponent_status` 和 `make_guess`。

11. **注释和文档**：代码中几乎没有注释，这使得理解代码逻辑变得更加困难。应该添加适当的注释和文档字符串来解释每个类和方法的作用。

修正这些不规范的地方将使代码更加健壮、可维护和易于理解。
"""