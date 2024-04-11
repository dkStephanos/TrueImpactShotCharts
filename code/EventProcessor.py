import pandas as pd

class EventProcessor:
    def load_game(game_id):
        event_df = pd.read_csv('data/src/events.csv', dtype={'gameId': str})
        return event_df.loc[event_df['gameId'] == game_id]
    
    def extract_shots(event_df):
        # Initialize an empty list to hold the indices of offensive rebounds
        return event_df.loc[event_df['eventType'] == 'SHOT']

    def extract_off_rebounds(event_df):
        # Filter the DataFrame for offensive rebounds -- we exclude team rebounds here
        return event_df.loc[(event_df['eventType'] == 'REB') & (event_df['dReb'] == False) & (event_df['playerId'].notnull())]