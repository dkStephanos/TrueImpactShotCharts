import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean

class FeatureUtil:
    def is_position_in_paint(x, y):
        """
        Determine if a position (x, y) is in the paint of an NBA basketball court centered at (0, 0).
        The paint is 16 feet wide and extends from the baseline up to 19 feet towards the center.
        
        Args:
        x (float): The x-coordinate of the position (horizontal distance from the centerline in feet).
        y (float): The y-coordinate of the position (vertical distance from the centerline in feet).

        Returns:
        bool: True if the position is in the paint, otherwise False.
        """
        # Dimensions of the paint area
        PAINT_WIDTH_HALF = 8  # Half the width of the paint (16 feet total)
        PAINT_LENGTH = 19  # Length of the paint from the baseline towards the center

        # Adjust for the paint being vertically centered on the y-axis
        # The paint extends from the baseline to 19 feet towards the center
        in_vertical_bounds = abs(y) <= PAINT_LENGTH

        # The paint is horizontally centered around the basket (which is centered at x=0)
        in_horizontal_bounds = -PAINT_WIDTH_HALF <= x <= PAINT_WIDTH_HALF

        return in_vertical_bounds and in_horizontal_bounds
    
    def is_past_halfcourt(x, basket_x):
        """
        Determine if a position is past the half-court relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the half-court towards the opposing basket, otherwise False.
        """
        return (basket_x > 0 and x < 0) or (basket_x < 0 and x > 0)
    
    def is_past_far_three_point_line(x, y, basket_x):
        """
        Determine if a position is past the far three-point line relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the far three-point line towards the opposing basket, otherwise False.
        """
        # Calculate the far 3-point line from the opposite basket
        far_three_point_line = -basket_x - (23.75 if abs(basket_x) > 23.75 else abs(basket_x))

        # Check if the x position has crossed this line (assuming half-court offense to defense transition)
        return (basket_x > 0 and x < far_three_point_line) or (basket_x < 0 and x > far_three_point_line)
    
    def find_closest_defenders(df, off_id, timestamp):
        """
        Find the closest defender to each offensive player at a given moment, optimized to use squared distances for efficiency.

        Args:
        df (DataFrame): DataFrame containing columns 'playerId', 'x', 'y', 'teamId', and 'timestamp'.
        timestamp (int): The specific moment of the game to analyze.

        Returns:
        DataFrame: A DataFrame with offensive players and their closest defenders.
        """
        # Filter the DataFrame for the given timestamp
        moment_df = df[df['wcTime'] == timestamp]
        
        # Separate offensive and defensive players
        offense = moment_df[moment_df['teamId'] == off_id]
        defense = moment_df[(moment_df['teamId'] != off_id) & (moment_df['teamId'] != "-1")]

        # Initialize a list to store the results
        closest_defenders = []

        # Get positions as numpy arrays for vectorization
        offense_positions = offense[['x', 'y']].to_numpy()
        defense_positions = defense[['x', 'y']].to_numpy()
        defense_ids = defense['playerId'].values

        # Calculate the closest defender for each offensive player
        for offensive_player in offense.itertuples():
            # Calculate squared distances to all defenders
            distances = np.sum((offense_positions - defense_positions)**2, axis=1)
            
            # Get the index of the minimum distance
            min_index = np.argmin(distances)
            
            # Compute the actual minimum distance (sqrt)
            min_distance = np.sqrt(distances[min_index])

            # Find the closest defender
            closest_defender_id = defense_ids[min_index]
            
            # Append the result
            closest_defenders.append({
                'off_player_id': offensive_player.playerId,
                'closest_defender_id': closest_defender_id,
                'distance': min_distance
            })

        # Convert the list of results into a DataFrame
        return pd.DataFrame(closest_defenders)
    
    @staticmethod
    def travel_dist_all(event_df):
        """
        Calculate the total distance traveled by all players in an event DataFrame.
        Args:
            event_df (pd.DataFrame): Event DataFrame containing player location coordinates.
        Returns:
            pd.Series: Series containing total distance traveled by each player.
        """
        player_travel_dist = event_df.groupby("playerId")[["x", "y"]].apply(
            lambda x: np.sqrt(((np.diff(x, axis=0) ** 2).sum(axis=1)).sum())
        )
        return player_travel_dist

    @staticmethod
    def average_speed_all(event_df):
        """
        Calculate the average speed of all players in an event DataFrame.
        Args:
            event_df (pd.DataFrame): Event DataFrame containing player location coordinates.
        Returns:
            pd.Series: Series containing average speed in miles per hour for each player.
        """
        seconds = event_df["wcTime"].max() - event_df["wcTime"].min()
        player_speeds = (
            event_df.groupby("playerId")[["x", "y"]].apply(
                lambda x: np.sqrt(((np.diff(x, axis=0) ** 2).sum(axis=1)).sum())
            )
            / seconds
        ) * 0.681818  # Conversion factor from feet/second to miles/hour
        return player_speeds

    @staticmethod
    def distance_between_players(player_a, player_b):
        """
        Calculate the Euclidean distance between two players at each moment.
        Args:
            player_a (pd.DataFrame): DataFrame containing player A's location coordinates.
            player_b (pd.DataFrame): DataFrame containing player B's location coordinates.
        Returns:
            list: List of distances between player A and player B at each moment.
        """
        player_range = min(len(player_a), len(player_b))
        return [
            euclidean(
                player_a.iloc[i][["x", "y"]],
                player_b.iloc[i][["x", "y"]],
            )
            for i in range(player_range)
        ]

    @staticmethod
    def distance_between_players_with_moment(player_a, player_b):
        """
        Calculate the Euclidean distance between two players at each moment, including moment numbers.
        Args:
            player_a (pd.DataFrame): DataFrame containing player A's location coordinates and moment numbers.
            player_b (pd.DataFrame): DataFrame containing player B's location coordinates and moment numbers.
        Returns:
            list: List of tuples (distance, moment#) between player A and player B at each moment.
        """
        player_range = min(len(player_a), len(player_b))
        return [
            (euclidean(player_a.iloc[i][["x", "y"]], player_b.iloc[i][["x", "y"]]), player_a.iloc[i]["wcTime"])
            for i in range(player_range)
        ]

    @staticmethod
    def get_defender_for_player(moment_df, player_id, defensive_team_ids):
        """
        Determine the closest defender to a player.
        Args:
            moment_df (pd.DataFrame): DataFrame representing player locations and ball position at moments.
            player_id (int): ID of the player for whom to find the closest defender.
            defensive_team_ids (list): List of defensive team IDs.
        Returns:
            pd.DataFrame: DataFrame containing the closest defender moments and their distances.
        """
        defenders_df = moment_df[moment_df['teamId'].isin(defensive_team_ids)]
        player_df = moment_df[moment_df['playerId'] == player_id]

        distances = defenders_df.apply(
            lambda row: euclidean((row['x'], row['y']), (player_df['x'].iloc[0], player_df['y'].iloc[0])),
            axis=1
        )
        
        min_distance_index = distances.idxmin()
        closest_defender = defenders_df.loc[min_distance_index]

        return pd.DataFrame({
            'playerId': [player_id],
            'closestDefenderId': [closest_defender['playerId']],
            'distance': [distances[min_distance_index]],
            'moment': [moment_df['wcTime'].iloc[0]]
        })