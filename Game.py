from enum import Enum
import random as rd

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
    
    def DrawTile(self):
        if len(tableTileSet.tileSet) > 0:
            tile = rd.choice(list(tableTileSet.tileSet))
            self.tempTile = tile
            tableTileSet.tileSet.remove(tile)
            return True
        else:
            return False
    
    def MakeGuess(self, targetIndex:int, tileIndex:int, tileNumber:int) -> bool:
        if (targetIndex >= len(allPlayers) 
            or targetIndex < 0 
            or targetIndex == allPlayers.index(self)
            or allPlayers[targetIndex].IsLose()
            or tileNumber < 0
            or tileNumber > 11):
            return None # invalid guess
        guessTarget = allPlayers[targetIndex]
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
        
class TestClass:
    None

tableTileSet = TableTileSet()
allPlayers = [PlayerTileSet() for count in range(0, 3)] # Set number of players here
lastPlayers = allPlayers

def InitGame():
    tableTileSet.InitTileSet()
    for player in allPlayers:
        player.InitTileSet()
    for drawCount in range(0, 4):
        for player in allPlayers:
            tile = rd.choice(list(tableTileSet.tileSet))
            player.tileSet.add(tile)
            tableTileSet.tileSet.remove(tile)

def IsOver(output = False):
    lastPlayers = list(player for player in allPlayers if player.IsLose() == False)
    for index, player in enumerate(allPlayers):
        if len(lastPlayers) <= 1:
            if output:
                print(f"Game over, player {allPlayers.index(lastPlayers[0])} wins")
            return True
    return False

def ShowSelfStatus():
    print(f"Your tile list is:")
    for tile in player.GetTileList():
        print(tile)

def ShowOpponentStatus():
    otherPlayers = list(allPlayers)
    otherPlayers.remove(player)
    for otherPlayer in otherPlayers:
        print(f"The tile list of Player {allPlayers.index(otherPlayer)} is")
        for index, tile in enumerate(otherPlayer.GetTileList()):
            print(index, ' ', tile.opponentPrint())

def MakeGuess():
    guessResult = player.MakeGuess(int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
    while(guessResult == None):
        print('Invalid guess')
        guessResult = player.MakeGuess(int(input('Target index: ')), int(input('Tile index: ')), int(input('Tile number: ')))
    return guessResult

InitGame()

while(True):
    lastPlayers = list(player for player in allPlayers if player.IsLose() == False)
    for player in lastPlayers:
        print(f"You are the player with index {allPlayers.index(player)}")
        ShowSelfStatus()
        
        ShowOpponentStatus()

        if player.DrawTile():
            print(f"The tile you draw is {player.tempTile}")
        else:
            print('Unabled to draw, table is empty')
        print("Please make a guess")
        guessResult = MakeGuess()
        while(guessResult == True or guessResult == None):
            if IsOver():
                break
            print('Right guess, do another one or end your turn')
            ShowSelfStatus()
            ShowOpponentStatus()
            if int(input('To end turn, input -1. To continue, input any other number: ')) == -1:
                player.EndTurn()
                break
            else:
                guessResult = MakeGuess()
        if IsOver():
            break
        print('Turn ends')
        print()
        
    if IsOver():
            break

IsOver(output=True)