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
        event_df = pd.read_csv('data/src/possessions.csv', dtype={'gameId': str, 'teamId': str})
        return event_df.loc[event_df['gameId'] == game_id]