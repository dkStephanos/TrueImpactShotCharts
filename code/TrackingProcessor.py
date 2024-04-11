import pandas as pd

class TrackingProcessor:
    def load_game(game_id):
        tracking_df = pd.read_csv('/data/src/tracking.csv')
        return tracking_df.loc[tracking_df['GameId'] == game_id]
    
    def extract_player_locations_at_timestamp(tracking_df, timestamp):
        return tracking_df.loc[tracking_df['WcTime'] == timestamp]