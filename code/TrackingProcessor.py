import pandas as pd

class TrackingProcessor:
    def load_game(game_id):
        tracking_df = pd.read_csv('data/src/tracking.csv', dtype={'gameId': str, 'playerId': str})
        return tracking_df.loc[tracking_df['gameId'] == game_id]
    
    def extract_player_locations_at_timestamp(tracking_df, timestamp):
        return tracking_df.loc[tracking_df['wcTime'] == timestamp]
    
    def extract_possession_moments(tracking_df, possession):
        """Extract moments for the specified time frame from the game DataFrame."""
        return tracking_df.loc[(tracking_df["wcTime"] >= possession["wcStart"]) & (tracking_df["wcTime"] <= possession["wcEnd"])]