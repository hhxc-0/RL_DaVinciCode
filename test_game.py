import pytest
import itertools
import random as rd
import game

class TestClass:
    @pytest.fixture(params=[2, 3, 4])
    def setup_init(self, request):
        game_host = game.GameHost(request.param)
        game_host.init_tile_sets()
        return game_host

    def test_init(self, setup_init, request):
        game_host = setup_init
        number_players = request.node.callspec.params['setup_init']
        assert len(game_host.all_players) == number_players # test if the number of generated players is correct
        for player in game_host.all_players:
            assert len(player.tile_set) == game.INITIAL_TILES # test if the number of tiles drawn by each player is correct
    
    def test_making_guesses(self, setup_init, request):
        game_host = setup_init
        number_players = request.node.callspec.params['setup_init']
        player_combs = list(itertools.permutations([player_index for player_index in range(0, number_players)], 2))
        for player_index in range(0, number_players):
            with pytest.raises(game.InvalidGuessError): # test the exception with target index that is the player it self
                game_host.all_players[player_index].make_guess(game_host.all_players, player_index, rd.randint(0, game.INITIAL_TILES), rd.randint(0, game.MAX_TILE_NUMBER))

        for player_comb in player_combs:
            with pytest.raises(game.InvalidGuessError): # test the exception with target index lower than bound
                game_host.all_players[player_comb[0]].make_guess(game_host.all_players, -1, rd.randint(0, game.INITIAL_TILES), rd.randint(0, game.MAX_TILE_NUMBER))

            with pytest.raises(game.InvalidGuessError): # test the exception with target index higher than bound
                game_host.all_players[player_comb[0]].make_guess(game_host.all_players, len(game_host.all_players)+1, rd.randint(0, game.INITIAL_TILES), rd.randint(0, game.MAX_TILE_NUMBER))

            with pytest.raises(game.InvalidGuessError): # test the exception with tile index lower than bound
                game_host.all_players[player_comb[0]].make_guess(game_host.all_players, player_comb[1], -1, rd.randint(0, game.MAX_TILE_NUMBER))

            with pytest.raises(game.InvalidGuessError): # test the exception with tile index higher than bound
                game_host.all_players[player_comb[0]].make_guess(game_host.all_players, player_comb[1], len(game_host.all_players[player_comb[1]].tile_set)+1, rd.randint(0, game.MAX_TILE_NUMBER))
                #game_host.all_players[0].make_guess(all_players: list, target_index: int, tile_index: int, tile_number: int)

    def test_empty_table_draw(self, setup_init, request):
        game_host = setup_init
        number_players = request.node.callspec.params['setup_init']
        while len(game_host.table_tile_set.tile_set) > 0:
            try:
                game_host.all_players[rd.randint(0, number_players-1)].draw_tile(game_host.table_tile_set)
            except game.EmptyTableError: # test the exception with an non-empty table
                pytest.fail('Unexpected EmptyTableError exception raised')

        with pytest.raises(game.EmptyTableError): # test the exception with an empty table
            game_host.all_players[rd.randint(0, number_players-1)].draw_tile(game_host.table_tile_set)

    def test_winner_appears(self, setup_init, request):
        game_host = setup_init
        number_players = request.node.callspec.params['setup_init']
        for draw in range(0, len(game_host.table_tile_set.tile_set)):
            try:
                game_host.all_players[rd.randint(0, number_players-1)].draw_tile(game_host.table_tile_set)
            except game.EmptyTableError: # test the exception with an non-empty table
                pytest.fail('Unexpected EmptyTableError exception raised')
        
        player_index = rd.randint(0, number_players-1)
        other_player_indexes = list(index for index in range(0, number_players))
        other_player_indexes.remove(player_index)
        for other_player_index in other_player_indexes:
            for tile in game_host.all_players[other_player_index].tile_set:
                # for tileTemp in game_host.all_players[other_player_index].tile_set:
                #     print(tileTemp)
                # print(game_host.is_game_over())
                assert game_host.is_game_over() == False
                tile.direction = game.Tile.Directions.PUBLIC
                
        assert game_host.is_game_over() == True