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
        possessions_df = pd.read_csv('data/src/possessions.csv', dtype={'gameId': str, 'teamId': str, 'possId': str})
        return possessions_df.loc[possessions_df['gameId'] == game_id].reset_index(drop=True)
    
    def extract_possessions_by_outcome(possessions_df, outcome):
        return possessions_df.loc[possessions_df['outcome'] == outcome].reset_index(drop=True)

    def extract_possesion_by_timestamp(possessions_df, timestamp):
        return possessions_df.loc[(possessions_df['wcStart'] <= timestamp) & (possessions_df['wcEnd'] >= timestamp)].reset_index(drop=True)