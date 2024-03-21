from enum import Enum
import random as rd
import PySimpleGUI as sg

class Color(Enum):
    BLACK = 0
    WHITE = 1

class Direction(Enum):
    PRIVATE = 0
    PUBLIC = 1

class Tile:
    def __init__(self, color:Color, number:int, direction = Direction.PRIVATE):
        self.color = color
        self.number = number
        self.direction = direction

    def __str__(self):
        return f"Color: {self.color.name}, Number: {self.number}, Direction: {self.direction.name}"
    
    def OpponentPrint(self):
        if self.direction == Direction.PRIVATE:
            return f"Color: {self.color.name}"
        else:
            return f"Color: {self.color.name}, Number: {self.number}"

class TableTileSet:
    def __init__(self):
        self.tileSet = set()

    def InitTileSet(self):
        for color in Color:
            for number in range(0, 12):
                tile = Tile(color, number)
                self.tileSet.add(tile)

class PlayerTileSet:
    def __init__(self):
        self.tileSet = set()
        self.tempTile:Tile

    def InitTileSet(self):
        self.tileSet.clear()

    def GetTileList(self):
        return sorted(list(self.tileSet), key=lambda x: x.number * 2 + x.color.value)
    
    def DrawTile(self, tableTileSet):
        if len(tableTileSet.tileSet) > 0:
            tile = rd.choice(list(tableTileSet.tileSet))
            self.tempTile = tile
            tableTileSet.tileSet.remove(tile)
            return True
        else:
            return False
    
    def MakeGuess(self, targetIndex:int, tileIndex:int, tileNumber:int) -> bool:
        if (targetIndex >= len(self.allPlayers) 
            or targetIndex < 0 
            or targetIndex == self.allPlayers.index(self)
            or self.allPlayers[targetIndex].IsLose()
            or tileNumber < 0
            or tileNumber > 11):
            return None # invalid guess
        guessTarget = self.allPlayers[targetIndex]
        if tileIndex < 0 or tileIndex >= len(guessTarget.GetTileList()):
            return None # invalid guess
        elif guessTarget.GetTileList()[tileIndex].direction == Direction.PUBLIC:
            return None # invalid guess
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
        
    def EndTurn(self):
        if self.tempTile != None:
            self.tempTile.direction = Direction.PRIVATE
            self.tileSet.add(self.tempTile)
            self.tempTile = None
        
    def IsLose(self):
        if len(list(privateTile for privateTile in self.tileSet if privateTile.direction == Direction.PRIVATE)) == 0:
            return True
        else:
            return False

class GameHost:
    def __init__(self, numPlayer) -> None:
        self.tableTileSet = TableTileSet()
        self.allPlayers = [PlayerTileSet() for count in range(0, numPlayer)] # Set number of players here

    def InitGame(self):
        self.tableTileSet.InitTileSet()
        for player in self.allPlayers:
            player.InitTileSet()
        for drawCount in range(0, 4):
            for player in self.allPlayers:
                tile = rd.choice(list(self.tableTileSet.tileSet))
                player.tileSet.add(tile)
                self.tableTileSet.tileSet.remove(tile)

    def IsOver(self, output = False):
        lastPlayers = list(player for player in self.allPlayers if player.IsLose() == False)
        for index, player in enumerate(self.allPlayers):
            if len(lastPlayers) <= 1:
                if output:
                    print(f"Game over, player {self.allPlayers.index(lastPlayers[0])} wins")
                return True
        return False

    def ShowSelfStatus(self, player):
        print(f"Your tile list is:")
        for tile in player.GetTileList():
            print(tile)

    def ShowOpponentStatus(self, player):
        otherPlayers = list(self.allPlayers)
        otherPlayers.remove(player)
        for otherPlayer in otherPlayers:
            print(f"The tile list of Player {self.allPlayers.index(otherPlayer)} is")
            for index, tile in enumerate(otherPlayer.GetTileList()):
                print(index, ' ', tile.OpponentPrint())

    def MakeGuess(self, player):
        guessResult = player.MakeGuess(int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
        while(guessResult == None):
            print('Invalid guess')
            guessResult = player.self.MakeGuess(int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
        return guessResult

    def StartGame(self):
        self.InitGame()

        while(self.IsOver() == False):
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
                    if self.IsOver():
                        break
                    print('Right guess, do another one or end your turn')
                    self.ShowSelfStatus(player)
                    self.ShowOpponentStatus(player)
                    if int(input('To end turn, input -1. To continue, input any other number: ')) == -1:
                        player.EndTurn()
                        break
                    else:
                        guessResult = self.MakeGuess()
                if self.IsOver():
                    break
                print('Turn ends')
                print()

        self.IsOver(output=True)
     
class Gui:
    None

class TestClass:
    None

NUMBER_OF_PLAYERS = 2

gameHost = GameHost(NUMBER_OF_PLAYERS)
gameHost.StartGame()

"""
这段代码存在一些不规范之处，以下是一些潜在的问题和改进建议：

1. **全局变量的使用**：`self.tableTileSet`, `self.allPlayers`, 和 `lastPlayers` 是作为全局变量定义的。这是一种不好的实践，因为它可能导致代码难以维护和理解。应该考虑将这些变量封装在一个类或函数中。

2. **命名约定**：Python通常使用`snake_case`命名变量和函数，而类名使用`CamelCase`。例如，`self.InitGame`、`self.IsOver`、`self.ShowSelfStatus`、`self.ShowOpponentStatus` 和 `self.MakeGuess` 应该改为 `init_game`、`is_over`、`show_self_status`、`show_opponent_status` 和 `make_guess`。

3. **魔法数字**：代码中有一些硬编码的数字（比如牌的数量12），这些应该被定义为常量，以提高代码的可读性和可维护性。

4. **异常处理**：`self.MakeGuess` 函数在接收无效猜测时返回 `None`，但这不是一个好的异常处理方式。应该抛出一个异常，然后在调用该函数的地方处理这个异常。

5. **代码重复**：`self.InitGame` 函数中的牌抽取代码与 `DrawTile` 方法非常相似，这表明可以重构以减少重复。

6. **不一致的方法访问**：`Tile` 类中的 `OpponentPrint` 方法在调用时使用了不同的大小写（`opponentPrint`），这可能会导致运行时错误。

8. **代码组织**：整个游戏逻辑都在全局作用域中执行，这不是一个好的实践。应该将游戏逻辑放入一个或多个函数中，或者更好的是，创建一个游戏类来封装所有的逻辑。

9. **类型注解**：代码中使用了类型注解，这是一个好习惯，但是应该确保所有函数和方法都使用了类型注解以保持一致性。

10. **硬编码的玩家数量**：玩家数量被硬编码为3，这应该作为一个可配置的参数。

11. **注释和文档**：代码中几乎没有注释，这使得理解代码逻辑变得更加困难。应该添加适当的注释和文档字符串来解释每个类和方法的作用。

12. **输入验证**：`self.MakeGuess` 函数直接从 `input` 读取值，而没有进行任何形式的验证。应该添加适当的验证来确保输入是有效的。

14. **函数中的全局变量访问**：`self.ShowOpponentStatus` 和其他函数直接访问 `player` 变量，这可能不是全局定义的，会导致运行时错误。

修正这些不规范的地方将使代码更加健壮、可维护和易于理解。
"""