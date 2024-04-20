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
        possessions_df = pd.read_csv('data/src/possessions.csv', dtype={'gameId': str, 'teamId': str})
        return possessions_df.loc[possessions_df['gameId'] == game_id]
    
    def extract_possessions_by_outcome(possessions_df, outcome):
        return possessions_df.loc[possessions_df['outcome'] == outcome]
