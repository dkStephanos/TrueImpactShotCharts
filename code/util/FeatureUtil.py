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
    
    def is_past_halfcourt(x, y, basket_x):
        """
        Determine if a position is past the half-court relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the half-court towards the offensive basket, otherwise False.
        """
        # Adjust the condition to reflect the movement towards the offensive basket
        return (basket_x > 0 and x > 0) or (basket_x < 0 and x < 0)

    def is_past_far_three_point_line(x, y, basket_x):
        """
        Determine if a position is past the far three-point line relative to a given basket location on the x-axis.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, either 41.75 or -41.75.

        Returns:
        bool: True if the position is past the far three-point line towards the offensive basket, otherwise False.
        """
        # Correctly calculate the far 3-point line relative to the offensive basket
        if basket_x > 0:
            far_three_point_line = basket_x - 23.75
        else:
            far_three_point_line = basket_x + 23.75

        # Adjust the check to consider the direction towards the offensive basket
        return (basket_x > 0 and x > far_three_point_line) or (basket_x < 0 and x < far_three_point_line)

    def is_in_zone_of_death(x, y, basket_x):
        """
        Determine if a player is in the 'zone of death' which is defined as the area in the backcourt
        between the half-court and the 3-point line extending to the baseline, taking into account the curved and straight portions of the 3-point line.

        Args:
        x (float): The x-coordinate of the player's position.
        y (float): The y-coordinate of the player's position.
        basket_x (float): The x-coordinate of the basket, determines which side is the shooting basket.

        Returns:
        bool: True if the player is in the 'zone of death', False otherwise.
        """
        half_court_x = 0
        corner_three_distance = 22  # 3-point distance at the corners
        top_key_three_distance = 23.75  # 3-point distance at the top of the arc
        three_pt_line_transition_x = 14  # Where the 3-point line starts to straighten

        # Determine if the player is in the backcourt
        in_backcourt = (x < half_court_x) if basket_x > 0 else (x > half_court_x)

        # Check if the player's y position is within the range that includes the 3-point arc
        if abs(y) <= three_pt_line_transition_x:  # Within the corners where the line is straight
            distance_from_basket = np.sqrt((x - basket_x) ** 2 + y ** 2)
            in_zone_of_death = in_backcourt and distance_from_basket > corner_three_distance
        else:  # Within the arc
            distance_from_basket = np.sqrt((x - basket_x) ** 2 + y ** 2)
            in_zone_of_death = in_backcourt and distance_from_basket > top_key_three_distance

        return in_zone_of_death
    
    def is_leading_offensive_player(df, off_team_id, basket_x):
        """
        Determine if there is a leading offensive player who is closer to the basket than any defenders,
        taking into account both distance and momentum indicators such as speed and acceleration.

        Args:
        df (pd.DataFrame): DataFrame containing player positions, team IDs, speed, and acceleration.
        off_team_id (int): The team ID for the offensive team.
        basket_x (float): The x-coordinate of the basket towards which the offense is heading.

        Returns:
        bool: True if there is a leading offensive player, False otherwise.
        """
        # Filter offensive and defensive players
        offense = df[df['teamId'] == off_team_id]
        defense = df[df['teamId'] != off_team_id]

        # Calculate raw distances to the basket for all players
        offense['distance_to_basket'] = np.abs(offense['x'] - basket_x)
        defense['distance_to_basket'] = np.abs(defense['x'] - basket_x)

        # Incorporate speed and acceleration into the distance measure
        # Assuming higher speed and positive acceleration reduce the effective distance
        offense['dynamic_distance'] = offense['distance_to_basket'] - (offense['speed'] + 0.5 * offense['acceleration'])
        defense['dynamic_distance'] = defense['distance_to_basket'] - (defense['speed'] + 0.5 * defense['acceleration'])

        # Find the minimum dynamic distance to the basket for both teams
        min_off_dynamic_distance = offense['dynamic_distance'].min()
        min_def_dynamic_distance = defense['dynamic_distance'].min()

        # Determine if any offensive player is dynamically closer to the basket than all defenders
        return min_off_dynamic_distance < min_def_dynamic_distance
    
    def find_closest_defenders(df, off_id, timestamp, unique_defender=False):
        """
        Find the closest defender to each offensive player at a given moment, optimized to use squared distances for efficiency.
        Allows for ensuring that each defender is only assigned to one offensive player.

        Args:
        df (DataFrame): DataFrame containing columns 'playerId', 'x', 'y', 'teamId', and 'timestamp'.
        timestamp (int): The specific moment of the game to analyze.
        unique_defender (bool): If True, ensures each defender is only assigned once.

        Returns:
        DataFrame: A DataFrame with offensive players and their closest defenders.
        """
        # Filter the DataFrame for the given timestamp
        moment_df = df[df['wcTime'] == timestamp]
        
        # Separate offensive and defensive players
        offense = moment_df[moment_df['teamId'] == off_id]
        defense = moment_df[(moment_df['teamId'] != off_id) & (moment_df['teamId'] != "-1")]

        # Initialize a list to store the results and a set to track assigned defenders
        closest_defenders = []
        assigned_defenders = set()

        # Calculate the closest defender for each offensive player
        for offensive_player in offense.itertuples():
            # Calculate squared distances from the offensive player to all defenders
            distances = np.sum((np.array([offensive_player.x, offensive_player.y]) - defense[['x', 'y']].to_numpy())**2, axis=1)
            
            # Sort distances and get indices sorted by distance
            sorted_indices = np.argsort(distances)

            for idx in sorted_indices:
                defender_id = defense.iloc[idx]['playerId']
                if unique_defender and defender_id in assigned_defenders:
                    continue  # Skip if this defender is already assigned and unique assignment is required
                # Compute the actual minimum distance (sqrt) for the closest available defender
                min_distance = np.sqrt(distances[idx])
                # Assign defender
                assigned_defenders.add(defender_id)
                # Append the result
                closest_defenders.append({
                    'off_player_id': offensive_player.playerId,
                    'closest_defender_id': defender_id,
                    'distance': min_distance
                })
                break  # Exit after assigning the closest available defender

        # Convert the list of results into a DataFrame
        return pd.DataFrame(closest_defenders)
    
    def find_ball_moment(df, condition_function, basket_x):
        """
        Find the first moment when the ball meets a specified condition.

        Args:
        df (DataFrame): DataFrame containing the tracking data of the ball, which includes
                        'x', 'y', 'timestamp', and 'teamId' columns.
        condition_function (function): A function that takes x, y, basket_x and returns a boolean
                                    indicating whether the condition is met.
        basket_x (float): The x-coordinate of the basket which the offensive team is attacking.

        Returns:
        dict: A dictionary containing the timestamp and position ('x' and 'y') of the ball
            when it first meets the condition or None if it never meets the condition.
        """
        # Filter the DataFrame to include only the ball data
        ball_df = df[df['teamId'] == "-1"]

        # Loop through the ball data to check when it meets the condition
        for index, row in ball_df.iterrows():
            if condition_function(row['x'], row['y'], basket_x):
                return {
                    'timestamp': row['wcTime'],
                    'x': row['x'],
                    'y': row['y']
                }

        # Return None if the ball never meets the condition
        return None
    
    def find_ball_crossing_halfcourt(df, basket_x):
        return FeatureUtil.find_ball_moment(df, FeatureUtil.is_past_halfcourt, basket_x)
        
    def find_ball_crossing_far_three_point_line(df, basket_x):
        return FeatureUtil.find_ball_moment(df, FeatureUtil.is_past_far_three_point_line, basket_x)
    
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