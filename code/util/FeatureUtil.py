import pandas as pd
import numpy as np
from shapely.geometry import Point
from code.io.PossessionProcessor import PossessionProcessor
from code.util.ShotRegionUtil import ShotRegionUtil
from sklearn.metrics import brier_score_loss


class FeatureUtil:
    # Court location features
    # ----------------------------------------------------
    def is_in_region(x, y, region: ShotRegionUtil, basket_x):
        """
        Generic method to determine if a position (x, y) is in the given shot region.
        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        region (ShotRegionUtil): The region to check against.
        basket_x (float): The x-coordinate of the basket, determines which half of the court to consider.
        Returns:
        bool: True if the position is in the specified region, otherwise False.
        """
        point = Point(x if basket_x > 0 else -x, y)

        # Use intersects instead of contains to include boundary points
        return region.intersects(point)

    def is_in_close_range(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["CLOSE_RANGE"], basket_x
        )

    def is_in_left_corner_three(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["LEFT_CORNER_THREE"], basket_x
        )

    def is_in_right_corner_three(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["RIGHT_CORNER_THREE"], basket_x
        )

    def is_in_center_three(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["CENTER_THREE"], basket_x
        )

    def is_in_left_wing_three(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["LEFT_WING_THREE"], basket_x
        )

    def is_in_right_wing_three(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["RIGHT_WING_THREE"], basket_x
        )

    def is_in_left_baseline_mid(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["LEFT_BASELINE_MID"], basket_x
        )

    def is_in_right_baseline_mid(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["RIGHT_BASELINE_MID"], basket_x
        )

    def is_in_left_elbow_mid(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["LEFT_ELBOW_MID"], basket_x
        )

    def is_in_right_elbow_mid(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["RIGHT_ELBOW_MID"], basket_x
        )

    def is_beyond_halfcourt(x, y, basket_x):
        return FeatureUtil.is_in_region(
            x, y, ShotRegionUtil.regions["BEYOND_HALFCOURT"], basket_x
        )

    def is_in_paint(x, y):
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
        return (basket_x > 0 and x > far_three_point_line) or (
            basket_x < 0 and x < far_three_point_line
        )

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
        if (
            abs(y) <= three_pt_line_transition_x
        ):  # Within the corners where the line is straight
            distance_from_basket = np.sqrt((x - basket_x) ** 2 + y**2)
            in_zone_of_death = (
                in_backcourt and distance_from_basket > corner_three_distance
            )
        else:  # Within the arc
            distance_from_basket = np.sqrt((x - basket_x) ** 2 + y**2)
            in_zone_of_death = (
                in_backcourt and distance_from_basket > top_key_three_distance
            )

        return in_zone_of_death

    def is_in_paint(x, y, basket_x):
        """
        Determine if a position (x, y) is in the paint of an NBA basketball court, relative to a specific basket.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, used to determine which half of the court to consider.

        Returns:
        bool: True if the position is in the paint of the specified half of the court, otherwise False.
        """
        PAINT_WIDTH_HALF = 8  # The paint is 16 feet wide total
        PAINT_LENGTH = 19  # Length from baseline to free throw line

        # Determine which half of the court to consider based on basket_x
        if basket_x > 0:
            return -PAINT_WIDTH_HALF <= x <= PAINT_WIDTH_HALF and 0 <= y <= PAINT_LENGTH
        else:
            return (
                -PAINT_WIDTH_HALF <= x <= PAINT_WIDTH_HALF and -PAINT_LENGTH <= y <= 0
            )

    def is_under_basket(x, y, basket_x):
        """
        Determine if a position (x, y) is directly under the basket on a standard NBA basketball court, relative to a specific basket.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, determines which basket to consider.

        Returns:
        bool: True if the position is under the specified basket, otherwise False.
        """
        BASKET_RADIUS = 4  # The radius around the basket to consider 'under the basket'

        # Use basket_x to adjust y-coordinate range based on court half
        basket_y = 0  # Basket y-coordinate is always at the center line of the width
        return (x - basket_x) ** 2 + y**2 <= BASKET_RADIUS**2

    def is_out_of_bounds(x, y, basket_x):
        """
        Determine if a position (x, y) is out of bounds on a standard NBA basketball court, considering the relevant half.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, used to determine which half of the court to consider.

        Returns:
        bool: True if the position is out of bounds in the specified half of the court, otherwise False.
        """
        COURT_LENGTH = 94  # Length of the court in feet
        COURT_WIDTH = 50  # Width of the court in feet

        in_half_court = x > 0 if basket_x > 0 else x < 0
        in_court_bounds = (
            0 <= x <= COURT_LENGTH and -COURT_WIDTH / 2 <= y <= COURT_WIDTH / 2
        )

        return not in_half_court or not in_court_bounds

    def is_at_free_throw_line(x, y, basket_x):
        """
        Determine if a position (x, y) is at the free throw line on a standard NBA basketball court, relative to a specific basket.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket, used to determine which half of the court to consider.

        Returns:
        bool: True if the position is at the free throw line of the specified half of the court, otherwise False.
        """
        FREE_THROW_LINE_DISTANCE = (
            19  # Distance from the baseline to the free throw line
        )

        is_correct_half = (x > 0) if basket_x > 0 else (x < 0)

        return is_correct_half and -1 <= x <= 1 and y == -FREE_THROW_LINE_DISTANCE

    def is_near_sideline(x, y, basket_x):
        """
        Determine if a position (x, y) is near the sideline of a basketball court.

        Args:
        x (float): The x-coordinate of the position.
        y (float): The y-coordinate of the position.
        basket_x (float): The x-coordinate of the basket used to determine the relevance of the position.

        Returns:
        bool: True if the position is near the sideline, otherwise False.
        """
        COURT_WIDTH_HALF = 25  # Half the NBA court width
        SIDELINE_BUFFER = 3  # Define 'near' as within 3 feet of the sideline

        return abs(y) >= (COURT_WIDTH_HALF - SIDELINE_BUFFER)

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
        offense = df[df["teamId"] == off_team_id]
        defense = df[df["teamId"] != off_team_id]

        # Calculate raw distances to the basket for all players
        offense["distance_to_basket"] = np.abs(offense["x"] - basket_x)
        defense["distance_to_basket"] = np.abs(defense["x"] - basket_x)

        # Incorporate speed and acceleration into the distance measure
        # Assuming higher speed and positive acceleration reduce the effective distance
        offense["dynamic_distance"] = offense["distance_to_basket"] - (
            offense["speed"] + 0.5 * offense["acceleration"]
        )
        defense["dynamic_distance"] = defense["distance_to_basket"] - (
            defense["speed"] + 0.5 * defense["acceleration"]
        )

        # Find the minimum dynamic distance to the basket for both teams
        min_off_dynamic_distance = offense["dynamic_distance"].min()
        min_def_dynamic_distance = defense["dynamic_distance"].min()

        # Determine if any offensive player is dynamically closer to the basket than all defenders
        return min_off_dynamic_distance < min_def_dynamic_distance

    # Feature extractors
    # ----------------------------------------------------
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
        moment_df = df[df["wcTime"] == timestamp]

        # Separate offensive and defensive players
        offense = moment_df[moment_df["teamId"] == off_id]
        defense = moment_df[
            (moment_df["teamId"] != off_id) & (moment_df["teamId"] != "-1")
        ]

        # Initialize a list to store the results and a set to track assigned defenders
        closest_defenders = []
        assigned_defenders = set()

        # Calculate the closest defender for each offensive player
        for offensive_player in offense.itertuples():
            # Calculate squared distances from the offensive player to all defenders
            distances = np.sum(
                (
                    np.array([offensive_player.x, offensive_player.y])
                    - defense[["x", "y"]].to_numpy()
                )
                ** 2,
                axis=1,
            )

            # Sort distances and get indices sorted by distance
            sorted_indices = np.argsort(distances)

            for idx in sorted_indices:
                defender_id = defense.iloc[idx]["playerId"]
                if unique_defender and defender_id in assigned_defenders:
                    continue  # Skip if this defender is already assigned and unique assignment is required
                # Compute the actual minimum distance (sqrt) for the closest available defender
                min_distance = np.sqrt(distances[idx])
                # Assign defender
                assigned_defenders.add(defender_id)
                # Append the result
                closest_defenders.append(
                    {
                        "off_player_id": offensive_player.playerId,
                        "closest_defender_id": defender_id,
                        "distance": min_distance,
                    }
                )
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
        ball_df = df[df["teamId"] == "-1"]

        # Loop through the ball data to check when it meets the condition
        for index, row in ball_df.iterrows():
            if condition_function(row["x"], row["y"], basket_x):
                return {"timestamp": row["wcTime"], "x": row["x"], "y": row["y"]}

        # Return None if the ball never meets the condition
        return None

    def find_ball_crossing_halfcourt(df, basket_x):
        return FeatureUtil.find_ball_moment(
            df, FeatureUtil.is_beyond_halfcourt, basket_x
        )

    def find_ball_crossing_far_three_point_line(df, basket_x):
        return FeatureUtil.find_ball_moment(
            df, FeatureUtil.is_past_far_three_point_line, basket_x
        )

    # Shot classification
    # ----------------------------------------------------
    def classify_shot_region(x, y, basket_x):
        """
        Classify a shot based on its location on the court using detailed categories.
        NOTE: Due to shots that fall on boundary borders, order here is important. Check midrange first!

        Args:
        x (float): The x-coordinate of the shot.
        y (float): The y-coordinate of the shot.
        basket_x (float): The x-coordinate of the basket.

        Returns:
        shot region desc: str
        """
        if FeatureUtil.is_beyond_halfcourt(x, y, basket_x):
            return "BEYOND_HALFCOURT"

        if FeatureUtil.is_in_close_range(x, y, basket_x):
            return "CLOSE_RANGE"

        if FeatureUtil.is_in_left_baseline_mid(x, y, basket_x):
            return "LEFT_BASELINE_MID"
        if FeatureUtil.is_in_right_baseline_mid(x, y, basket_x):
            return "RIGHT_BASELINE_MID"

        if FeatureUtil.is_in_left_elbow_mid(x, y, basket_x):
            return "LEFT_ELBOW_MID"
        if FeatureUtil.is_in_right_elbow_mid(x, y, basket_x):
            return "RIGHT_ELBOW_MID"

        if FeatureUtil.is_in_left_corner_three(x, y, basket_x):
            return "LEFT_CORNER_THREE"
        if FeatureUtil.is_in_right_corner_three(x, y, basket_x):
            return "RIGHT_CORNER_THREE"

        if FeatureUtil.is_in_left_wing_three(x, y, basket_x):
            return "LEFT_WING_THREE"
        if FeatureUtil.is_in_right_wing_three(x, y, basket_x):
            return "RIGHT_WING_THREE"

        if FeatureUtil.is_in_center_three(x, y, basket_x):
            return "CENTER_THREE"

    def classify_shot_locations(shots_df, possession_df, classify_shot):
        """
        Classifies the locations of shots in the DataFrame using the basketX from the possession DataFrame
        based on the shot_time matching within the possession window.

        Args:
            shots_df (DataFrame): DataFrame containing shot locations and times.
            possession_df (DataFrame): DataFrame containing possession data with basketX values, start and end times.
            classify_shot (function): A function to classify shot locations based on x, y, and basketX.

        Returns:
            DataFrame: The input DataFrame augmented with a new column for shot classification.
        """
        # Create a temporary key for merging to avoid large Cartesian products
        shots_df = shots_df.copy()
        
        shots_df['basketX'] = shots_df['shot_time'].apply(
            lambda x: PossessionProcessor.extract_possession_by_timestamp(possession_df, x)['basketX']
        )

        # Apply the classification function
        shots_df["shot_classification"] = shots_df.apply(
            lambda row: classify_shot(row["shot_x"], row["shot_y"], row["basketX"]),
            axis=1,
        )

        return shots_df

    def calculate_brier_score_loss(shot_rebound_df):
        return brier_score_loss(
            shot_rebound_df["dReb"], shot_rebound_df["def_reb_chance"] / 100
        )

    def calculate_oreb_ppp(event_df, off_rebounds_df):
        # List to store points from the first shot attempt after each offensive rebound
        points_after_rebounds = []

        # Iterate over each offensive rebound
        for idx, rebound in off_rebounds_df.iterrows():
            # Find subsequent events in the same game and period
            subsequent_events = event_df.loc[
                (event_df["gameId"] == rebound["gameId"])
                & (event_df["period"] == rebound["period"])
                & (event_df["wcTime"] > rebound["wcTime"])
            ].sort_values(by="wcTime")

            # Filter to find the first shot attempt
            first_shot = subsequent_events.loc[
                subsequent_events["eventType"] == "SHOT"
            ].head(1)

            # Check if there is a shot and calculate points
            if not first_shot.empty:
                points = (
                    3
                    if (first_shot.iloc[0]["made"] and first_shot.iloc[0]["three"])
                    else (2 if first_shot.iloc[0]["made"] else 0)
                )
            else:
                # No shot was made after the rebound before possession ended
                points = 0

            points_after_rebounds.append(points)

        # Calculate average points per possession
        if points_after_rebounds:
            ppp = sum(points_after_rebounds) / len(points_after_rebounds)
        else:
            ppp = 0

        return ppp

    def calculate_fg_percentage_by_region(shot_data):
        """
        Calculate the field goal percentage (FG%) for each shot classification region.

        Args:
            shot_data (DataFrame): DataFrame containing shot data with columns 'shot_classification' and 'made'.

        Returns:
            DataFrame: DataFrame with FG% for each shot classification region.
        """
        # Group by shot classification and calculate the FG%
        fg_percentage_by_region = shot_data.groupby('shot_classification').apply(
            lambda x: pd.Series({
                'shots_attempted': len(x),
                'shots_made': x['made'].sum(),
                'fg_percentage': x['made'].mean() * 100
            })
        ).reset_index()

        return fg_percentage_by_region
    
    def calculate_shot_statistics_by_region(shot_data):
        """
        Calculate per-shot statistics for points produced, true points produced, and true impact points produced 
        for each shot classification region.

        Args:
            shot_data (DataFrame): DataFrame containing shot data with columns 'shot_classification', 
                                'points_produced', 'true_points_produced', and 'true_impact_points_produced'.

        Returns:
            DataFrame: DataFrame with per-shot statistics for each shot classification region.
        """
        # Group by shot classification and calculate statistics
        shot_statistics_by_region = shot_data.groupby('shot_classification').apply(
            lambda x: pd.Series({
                'shots_attempted': len(x),
                'points_produced_avg': x['points_produced'].mean(),
                'true_points_produced_avg': x['true_points_produced'].mean(),
                'true_impact_points_produced_avg': x['true_impact_points_produced'].mean(),
            })
        ).reset_index()

        return shot_statistics_by_region
    
    def calculate_rebound_statistics_by_region(rebound_data):
        """
        Calculate rebound statistics for each shot classification region, including the percentage of real defensive rebounds,
        as well as the projected offensive and defensive rebound chances.

        Args:
            rebound_data (DataFrame): DataFrame containing rebound data with columns 'shot_classification',
                                    'off_reb_chance', 'def_reb_chance', and 'dReb' (boolean indicating defensive rebound).

        Returns:
            DataFrame: DataFrame with rebound statistics for each shot classification region.
        """
        # Group by shot classification and calculate statistics
        rebound_statistics_by_region = rebound_data.groupby('shot_classification').apply(
            lambda x: pd.Series({
                'shots_attempted': len(x),
                'off_reb_chance_avg': x['off_reb_chance'].mean(),
                'def_reb_chance_avg': x['def_reb_chance'].mean(),
                'off_rebounds_percent_real': (1 - x['dReb']).mean() * 100,
                'def_rebounds_percent_real': x['dReb'].mean() * 100
            })
        ).reset_index()

        return rebound_statistics_by_region
    
    def calculate_player_rebound_statistics(rebound_data):
        """
        Calculate rebound statistics for each player, comparing expected to actual rebound percentages.
        """
        def process_rebound_opportunities(row):
            if row['player_rebound_chances'] is None:
                return pd.Series({
                    'total_opportunities': 0,
                    'expected_rebounds': 0,
                    'actual_rebounds': 0,
                    'expected_reb_percentage': 0,
                    'actual_reb_percentage': 0,
                    'rebounds_above_expected': 0
                })
            
            # Convert player chances to a list of dictionaries
            opportunities = [
                {
                    'player_id': player_id,
                    'rebound_chance': chance,
                    'got_rebound': player_id == row['rebounder_id']
                }
                for player_id, chance in row['player_rebound_chances'].items()
            ]
            
            # Convert to DataFrame for processing
            opp_df = pd.DataFrame(opportunities)
            if len(opp_df) == 0:
                return pd.Series({
                    'total_opportunities': 0,
                    'expected_rebounds': 0,
                    'actual_rebounds': 0,
                    'expected_reb_percentage': 0,
                    'actual_reb_percentage': 0,
                    'rebounds_above_expected': 0
                })
                
            # Group by player
            player_stats = opp_df.groupby('player_id').agg({
                'rebound_chance': ['count', 'sum'],
                'got_rebound': 'sum'
            }).reset_index()

            player_stats.columns = ['player_id', 'total_opportunities', 'expected_rebounds', 'actual_rebounds']
            
            # Normalize to per possession
            player_stats['expected_rebounds'] = player_stats['expected_rebounds'] / 100
            
            return player_stats
        
        # Process each row and concatenate results
        all_stats = []
        for _, row in rebound_data.iterrows():
            stats = process_rebound_opportunities(row)
            if isinstance(stats, pd.DataFrame) and len(stats) > 0:
                all_stats.append(stats)
        
        # Combine all stats and aggregate by player
        if all_stats:
            final_stats = pd.concat(all_stats, ignore_index=True)
            return final_stats.groupby('player_id').agg({
                'total_opportunities': 'sum',
                'expected_rebounds': 'sum',
                'actual_rebounds': 'sum'
            }).assign(
                expected_reb_percentage=lambda x: x['expected_rebounds'] / x['total_opportunities'],
                actual_reb_percentage=lambda x: x['actual_rebounds'] / x['total_opportunities'],
                rebounds_above_expected=lambda x: (
                    x['actual_rebounds'] / x['total_opportunities'] - 
                    x['expected_rebounds'] / x['total_opportunities']
                )
            ).reset_index()
        else:
            return pd.DataFrame(columns=[
                'player_id', 'total_opportunities', 'expected_rebounds', 
                'actual_rebounds', 'expected_reb_percentage', 
                'actual_reb_percentage', 'rebounds_above_expected'
            ])
    
    def calculate_net_gains(shot_statistics_by_region):
        """
        Calculate the net gains for true points produced and points produced based on true impact points produced.

        Args:
            shot_statistics_by_region (DataFrame): DataFrame containing per-shot statistics for each shot classification region.

        Returns:
            DataFrame: DataFrame with net gains for each shot classification region.
        """
        shot_statistics_by_region = shot_statistics_by_region.copy()
        shot_statistics_by_region['net_gain_true_points'] = (
            shot_statistics_by_region['true_points_produced_avg'] - shot_statistics_by_region['points_produced_avg']
        )
        shot_statistics_by_region['net_gain_true_impact_points'] = (
            shot_statistics_by_region['true_impact_points_produced_avg'] - shot_statistics_by_region['points_produced_avg']
        )

        return shot_statistics_by_region