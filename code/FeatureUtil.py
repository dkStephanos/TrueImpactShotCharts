import pandas as pd

class FeatureUtil:
    def player_positions_at_moment(moment_df, timestamp, player_ids="all"):
        # Handle the player_ids input
        if isinstance(player_ids, list):
            pass  # If player_ids is already a list, do nothing
        elif player_ids == "all":
            player_ids = list(moment_df["playerId"].dropna().unique())  # Get all unique playerIds if 'all'
        
        # Filter the DataFrame for the specified timestamp and player_ids
        moment_df = moment_df[(moment_df["timestamp"] == timestamp) & (moment_df["playerId"].isin(player_ids))]
        
        # Drop unnecessary columns
        moment_df = moment_df.drop(["gameId", "teamAbbr", "period", "wcTime", "gcTime", "scTime", "gameDate"], axis=1)
        
        return moment_df

    def ball_position_at_moment(moment_df, timestamp):
        # Filter the DataFrame for the specified timestamp and the ball (team_id = -1)
        ball_df = moment_df[(moment_df["timestamp"] == timestamp) & (moment_df["teamId"] == -1)]
        
        # Drop unnecessary columns
        ball_df = ball_df.drop(["gameId", "teamAbbr", "period", "wcTime", "gcTime", "scTime", "gameDate"], axis=1)
        
        return ball_df
