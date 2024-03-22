from enum import Enum
import random as rd
# import streamlit as st
# import PySimpleGUI as sg
import wx

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
     
class Gui:
    """
    This class hosts the GUI
    """
    def __init__(self) -> None:
        self.app = wx.App()

    def input_guess(self):
        # self.frame.Refresh()
        self.frame = self.MainFrame()
        self.app.MainLoop()

    class MainFrame(wx.Frame):
        def __init__(self):
            BACKGROUND_COLOR = wx.Colour(192, 192, 192)
            BACKGROUND_COLOR = wx.Colour(255, 255, 255)
            TILE_SCALE = 0.5
            TEXT_FONT = wx.Font(int(60 * TILE_SCALE), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Segoe UI')
            TILE_NUMBER_FONT = wx.Font(int(60 * TILE_SCALE), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Segoe UI')

            super().__init__(None, title="The Da Vinci Code", size=(300, 200))
            
            panel = wx.Panel(self)
            panel.SetBackgroundColour(BACKGROUND_COLOR)
            
            white_tile_bitmap = wx.Image("./assets/white_tile.png", wx.BITMAP_TYPE_PNG)
            white_tile_bitmap.Rescale(int(white_tile_bitmap.GetSize()[0] * TILE_SCALE), int(white_tile_bitmap.GetSize()[1] * TILE_SCALE))
            black_tile_bitmap = wx.Image("./assets/black_tile.png", wx.BITMAP_TYPE_PNG)
            black_tile_bitmap.Rescale(int(black_tile_bitmap.GetSize()[0] * TILE_SCALE), int(black_tile_bitmap.GetSize()[1] * TILE_SCALE))
            
            vertical_sizer = wx.BoxSizer(wx.VERTICAL)
            self.tile_button_dict = {}
            for player in game_host.all_players:
                player_index_text = wx.StaticText(panel, wx.NewId(), f"Tiles of player {game_host.all_players.index(player):}")
                player_index_text.SetFont(TEXT_FONT)
                vertical_sizer.Add(player_index_text, 0, wx.ALL, 5)   

                horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
                for tile in player.tile_set:
                    if tile.color == Tile.Colors.WHITE:
                        temp_bitmap = white_tile_bitmap.ConvertToBitmap()
                    elif tile.color == Tile.Colors.BLACK:
                        temp_bitmap = black_tile_bitmap.ConvertToBitmap()
                    
                    # 在位图上绘制文字
                    dc = wx.MemoryDC(temp_bitmap)
                    dc.SetTextForeground(wx.Colour(0, 0, 0, 256))  # 设置文字颜色
                    dc.SetFont(TILE_NUMBER_FONT)  # 设置文字字体
                    text = str(tile.number)
                    tw, th = dc.GetTextExtent(text)  # 获取文字的宽度和高度
                    dc.DrawText(text, (temp_bitmap.GetWidth() - tw) // 2, (temp_bitmap.GetHeight() - th) // 2)  # 将文字绘制到位图上
                    dc.SelectObject(wx.NullBitmap)  # 结束绘图

                    tile_botton_id = wx.NewId()
                    tile_botton = wx.BitmapButton(panel, tile_botton_id, bitmap=temp_bitmap, style=wx.BORDER_NONE)
                    self.tile_button_dict[tile_botton_id] = (player, tile)
                    tile_botton.SetBackgroundColour(BACKGROUND_COLOR)
                    self.Bind(wx.EVT_BUTTON, self.on_button_click, tile_botton)
                    horizontal_sizer.Add(tile_botton, 0, wx.ALL, 5)
                vertical_sizer.Add(horizontal_sizer, 0, wx.ALL, 5)        
            panel.SetSizer(vertical_sizer)
            del dc
            self.Show()
        
        def on_button_click(self, event):
            button_id = event.GetId()
            wx.MessageBox(f"Button {self.tile_button_dict[button_id]} Clicked!", "Info", wx.OK | wx.ICON_INFORMATION)

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
        self.gui = Gui()
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
                self.gui.input_guess()

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

NUMBER_OF_PLAYERS = 3
MAX_TILE_NUMBER = 11
INITIAL_TILES = 4

if __name__ == '__main__':
    game_host = GameHost(NUMBER_OF_PLAYERS)
    game_host.start_game()
