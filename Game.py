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
    def __init__(self, message):
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
    
    def OpponentPrint(self) -> None:
        if self.direction == Direction.PRIVATE:
            return f"Color: {self.color.name}"
        else:
            return f"Color: {self.color.name}, Number: {self.number}"

class TableTileSet:
    def __init__(self) -> None:
        self.tileSet = set()

    def InitTileSet(self) -> None:
        for color in Color:
            for number in range(0, 12):
                tile = Tile(color, number)
                self.tileSet.add(tile)

class PlayerTileSet:
    def __init__(self) -> None:
        self.tileSet = set()
        self.tempTile:Tile

    def InitTileSet(self) -> None:
        self.tileSet.clear()

    def GetTileList(self) -> list[set]:
        return sorted(list(self.tileSet), key=lambda x: x.number * 2 + x.color.value)
    
    def DrawTile(self, tableTileSet, directDraw = False) -> bool:
        if len(tableTileSet.tileSet) == 0:
            return False
        else:
            tile = rd.choice(list(tableTileSet.tileSet))
            if directDraw:
                self.tileSet.add(tile)
            else:
                self.tempTile = tile
            tableTileSet.tileSet.remove(tile)
            return True
            
    
    def MakeGuess(self, targetIndex:int, tileIndex:int, tileNumber:int) -> bool:
        if (targetIndex >= len(self.allPlayers) 
            or targetIndex < 0 
            or targetIndex == self.allPlayers.index(self)
            or self.allPlayers[targetIndex].IsLose()
            or tileNumber < 0
            or tileNumber > 11):
            raise InvalidGuessError # invalid guess
        guessTarget = self.allPlayers[targetIndex]
        if tileIndex < 0 or tileIndex >= len(guessTarget.GetTileList()):
            raise InvalidGuessError # invalid guess
        elif guessTarget.GetTileList()[tileIndex].direction == Direction.PUBLIC:
            raise InvalidGuessError # invalid guess
        elif guessTarget.VerifyGuess(tileIndex, tileNumber):
            return True # right guess
        else:
            if self.tempTile != None:
                self.tempTile.direction = Direction.PUBLIC
                self.tileSet.add(self.tempTile)
                self.tempTile = None
            return False # wrong guess

    def VerifyGuess(self, tileIndex:int, tileNumber:int) -> bool:
        tile = self.GetTileList()[tileIndex]
        if tile.number == tileNumber:
            tile.direction = Direction.PUBLIC
            return True
        else:
            return False
        
    def EndTurn(self) -> None:
        if self.tempTile != None:
            self.tempTile.direction = Direction.PRIVATE
            self.tileSet.add(self.tempTile)
            self.tempTile = None
        
    def IsLose(self) -> bool:
        if len(list(privateTile for privateTile in self.tileSet if privateTile.direction == Direction.PRIVATE)) == 0:
            return True
        else:
            return False

class GameHost:
    def __init__(self, numPlayer) -> None:
        self.tableTileSet = TableTileSet()
        self.allPlayers = [PlayerTileSet() for count in range(0, numPlayer)] # Set number of players here

    def InitTileSets(self) -> None:
        self.tableTileSet.InitTileSet()
        for player in self.allPlayers:
            player.InitTileSet()
        for drawCount in range(0, 4):
            for player in self.allPlayers:
                player.DrawTile(self.tableTileSet, directDraw=True)

    def IsGameOver(self, output = False) -> bool:
        lastPlayers = list(player for player in self.allPlayers if player.IsLose() == False)
        for index, player in enumerate(self.allPlayers):
            if len(lastPlayers) <= 1:
                if output:
                    print(f"Game over, player {self.allPlayers.index(lastPlayers[0])} wins")
                return True
        return False

    def ShowSelfStatus(self, player) -> None:
        print(f"Your tile list is:")
        for tile in player.GetTileList():
            print(tile)

    def ShowOpponentStatus(self, player) -> None:
        otherPlayers = list(self.allPlayers)
        otherPlayers.remove(player)
        for otherPlayer in otherPlayers:
            print(f"The tile list of Player {self.allPlayers.index(otherPlayer)} is")
            for index, tile in enumerate(otherPlayer.GetTileList()):
                print(index, ' ', tile.OpponentPrint())

    def MakeGuess(self, player) -> None:
        while True:
            try:
                guessResult = player.MakeGuess(int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
                return guessResult
            except InvalidGuessError:
                print('Invalid guess')

    def StartGame(self) -> None:
        self.InitTileSets()

        while(self.IsGameOver() == False):
            lastPlayers = list(player for player in self.allPlayers if player.IsLose() == False)
            for player in lastPlayers:
                print(f"You are the player with index {self.allPlayers.index(player)}")
                self.ShowSelfStatus(player)
                
                self.ShowOpponentStatus(player)

                if player.DrawTile(self.tableTileSet):
                    print(f"The tile you draw is {player.tempTile}")
                else:
                    print('Unabled to draw, table is empty')
                print("Please make a guess")
                guessResult = self.MakeGuess(player)
                while(guessResult == True or guessResult == None):
                    if self.IsGameOver():
                        break
                    print('Right guess, do another one or end your turn')
                    self.ShowSelfStatus(player)
                    self.ShowOpponentStatus(player)
                    if int(input('To end turn, input -1. To continue, input any other number: ')) == -1:
                        player.EndTurn()
                        break
                    else:
                        guessResult = self.MakeGuess()
                if self.IsGameOver():
                    break
                print('Turn ends')
                print()

        self.IsGameOver(output=True)
     
class Gui:
    None

class TestClass:
    None

NUMBER_OF_PLAYERS = 2

gameHost = GameHost(NUMBER_OF_PLAYERS)
gameHost.StartGame()

"""
这段代码存在一些不规范之处，以下是一些潜在的问题和改进建议：

2. **命名约定**：Python通常使用`snake_case`命名变量和函数，而类名使用`CamelCase`。例如，`self.InitGame`、`self.IsOver`、`self.ShowSelfStatus`、`self.ShowOpponentStatus` 和 `self.MakeGuess` 应该改为 `init_game`、`is_over`、`show_self_status`、`show_opponent_status` 和 `make_guess`。

11. **注释和文档**：代码中几乎没有注释，这使得理解代码逻辑变得更加困难。应该添加适当的注释和文档字符串来解释每个类和方法的作用。

修正这些不规范的地方将使代码更加健壮、可维护和易于理解。
"""