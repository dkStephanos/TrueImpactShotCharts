import pandas as pd

class TrackingProcessor:
    """
    csv cols: 
        gameId,
        playerId,
        playerName,
        teamId,
        teamAbbr,
        period,
        wcTime,
        gcTime,
        scTime,
        x,
        y,
        z,
        gameDate
    """
    def load_game(game_id):
        tracking_df = pd.read_csv('data/src/tracking.csv', dtype={'gameId': str, 'playerId': str, 'teamId': str})
        return tracking_df.loc[tracking_df['gameId'] == game_id].reset_index(drop=True)
    
    def load_games(game_ids: list = "all"):
        tracking_df = pd.read_csv('data/src/tracking.csv', dtype={'gameId': str, 'playerId': str, 'teamId': str})
        if game_ids != "all":
            tracking_df = tracking_df.loc[tracking_df['gameId'].isin(game_ids)].reset_index(drop=True)
        
        return tracking_df
    
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
        
        return moment_df.reset_index(drop=True)

    def ball_position_at_moment(moment_df, timestamp):
        # Filter the DataFrame for the specified timestamp and the ball (team_id = -1)
        ball_df = moment_df[(moment_df["timestamp"] == timestamp) & (moment_df["teamId"] == -1)]
        
        # Drop unnecessary columns
        ball_df = ball_df.drop(["gameId", "teamAbbr", "period", "wcTime", "gcTime", "scTime", "gameDate"], axis=1)
        
        return ball_df.reset_index(drop=True)
    
    def extract_possession_moments(tracking_df, possession):
        """Extract moments for the specified time frame (as defined by the incoming possession dict) from the game DataFrame."""
        return tracking_df.loc[(tracking_df["wcTime"] >= possession["wcStart"]) & (tracking_df["wcTime"] <= possession["wcEnd"])].reset_index(drop=True)
    
    def extract_moment_from_timestamps(tracking_df, start_time, end_time):
        """Extract moments for the specified time frame from the game DataFrame."""
        return tracking_df.loc[(tracking_df["wcTime"] >= start_time) & (tracking_df["wcTime"] <= end_time)].reset_index(drop=True)
    
    def extract_offensive_defensive_players(tracking_df, off_team_id):
        off_ids = list(tracking_df.loc[tracking_df["teamId"] == off_team_id]["playerId"].unique())
        def_ids = list(tracking_df.loc[tracking_df["teamId"] != off_team_id]["playerId"].dropna().unique())
        
        return off_ids, def_ids
    
    def mirror_court_data(tracking_df, column_name, basket_x=41.75):
        """
        Mirrors data points across the center line of a basketball court based on the basket_x value provided.
        This ensures all data points are standardized to one half of the court, assuming all action is towards the specified basket.

        Args:
            tracking_df (DataFrame): DataFrame containing the data with coordinates to be mirrored.
            column_name (str): The name of the column in the DataFrame that contains the x-coordinates.
            basket_x (float): The x-coordinate of the basket to which data should be mirrored. This standardizes
                            the data as if all action is moving towards this specified basket.

        Returns:
            DataFrame: A DataFrame with the specified coordinates mirrored onto the desired half of the court.
        """
        # Mirror the x-coordinates based on whether they match the specified basket_x
        tracking_df[column_name] = tracking_df.apply(
            lambda row: -row[column_name] if row["basket_x"] != basket_x else row[column_name],
            axis=1
        )

        return tracking_df
