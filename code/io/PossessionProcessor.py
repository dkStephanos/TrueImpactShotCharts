import pandas as pd

class PossessionProcessor:
    """
    csv cols: 
        gameId,
        period,
        possId,
        possNum,
        teamId,
        teamAbbr,
        outcome,
        ptsScored,
        wcStart,
        wcEnd,
        gcStart,
        gcEnd,
        basketX
    """
    def load_game(game_id):
        possessions_df = pd.read_csv('../data/src/possessions.csv', dtype={'gameId': str, 'teamId': str, 'possId': str})
        return possessions_df.loc[possessions_df['gameId'] == game_id].reset_index(drop=True)
    
    def load_games(game_ids: list = "all"):
        possessions_df = pd.read_csv('../data/src/possessions.csv', dtype={'gameId': str, 'teamId': str, 'possId': str})
        if game_ids != "all":
            possessions_df = possessions_df.loc[possessions_df['gameId'].isin(game_ids)].reset_index(drop=True)
        
        return possessions_df
    
    def extract_possessions_by_outcome(possessions_df, outcome):
        return possessions_df.loc[possessions_df['outcome'] == outcome].reset_index(drop=True)

    def extract_possession_by_timestamp(possessions_df, timestamp):
        return possessions_df.loc[(possessions_df['wcStart'] <= timestamp) & (possessions_df['wcEnd'] >= timestamp)].iloc[0]