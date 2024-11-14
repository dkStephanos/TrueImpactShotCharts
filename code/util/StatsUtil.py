import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.spatial.distance import euclidean
from shapely.geometry import Point
from code.io.TrackingProcessor import TrackingProcessor
from code.io.EventProcessor import EventProcessor
from code.util.FeatureUtil import FeatureUtil
from code.util.VisUtil import VisUtil


class StatsUtil:
    def calculate_true_points(df):
        """
        Enhances the DataFrame with shot attempts to include a 'true points produced' column,
        which accounts for points from made shots and subsequent free throws following fouls on those shots.
        """
        # Filter to get only shot attempts
        shots_df = df[df["eventType"] == "SHOT"].copy()

        # Add columns to store the computed true points
        shots_df["points_produced"] = 0
        shots_df["true_points_produced"] = 0

        # Iterate through the shots DataFrame
        for index, row in shots_df.iterrows():
            points = 0
            if row["made"]:  # Check if the shot was made
                points += 3 if row["three"] else 2
            shots_df.at[index, "points_produced"] = points

            # Find the immediate next event in the DataFrame
            shot_index = df.index.get_loc(index)
            if shot_index + 1 < len(df):
                next_event = df.iloc[shot_index + 1]
                # Check if the next event is a FOUL related to this SHOT
                if next_event["eventType"] == "FOUL" and next_event["fouledId"] == row["playerId"]:
                    # Find free throws directly related to this foul
                    free_throws = df[
                        (df["eventType"] == "FT") &
                        (df["wcTime"] > next_event["wcTime"]) &
                        (df["playerId"] == row["playerId"]) &
                        (df["gameId"] == row["gameId"])
                    ].sort_values(by="wcTime")

                    for ft in free_throws.itertuples():
                        if ft.made:
                            points += 1
                        # Look for the next event after this free throw
                        ft_index = df.index.get_loc(ft.Index)
                        if ft_index + 1 < len(df):
                            next_ft_event = df.iloc[ft_index + 1]
                            # Break if next event is not a FT and it's not a team rebound after a missed FT (happens if you miss the first in a sequence)
                            if next_ft_event["eventType"] != "FT" and not (next_ft_event["eventType"] == "REB" and pd.isna(next_ft_event["playerId"]) and not ft.made):
                                break

            # Store the total points produced in the DataFrame
            shots_df.at[index, "true_points_produced"] = points

        return shots_df

    def map_shot_data_to_true_points(true_points_df, shot_classification_df):
        shot_classification_df = shot_classification_df.rename(columns={"shot_time": "wcTime"})
        merged_df = true_points_df.merge(
            shot_classification_df[['gameId', 'playerId', 'wcTime', 'shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'shot_classification']],
            on=['gameId', 'playerId', 'wcTime'],
            how='left'
        )
        return merged_df.dropna(subset=["shot_classification"])


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
            (
                euclidean(player_a.iloc[i][["x", "y"]], player_b.iloc[i][["x", "y"]]),
                player_a.iloc[i]["wcTime"],
            )
            for i in range(player_range)
        ]
        
    def assign_oreb_expected_points_to_shots(true_points_df, reb_chances_df, event_df=None, oreb_ppp=None):
        """_summary_

        Args:
            true_points_df (_type_): _description_
            reb_chances_df (_type_): _description_
            event_df (_type_, optional):  Used for the full context oreb_ppp arg, can also pass that as a scalar. Defaults to None.
            oreb_ppp (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        # Allows for progress bar on pd.apply
        tqdm.pandas()
        
        if not oreb_ppp and not event_df:
            # Can't proceed unless one is provided
            raise Exception('One of oreb_ppp or event_df must be provided!')
        elif oreb_ppp:
            # Don't interpret if oreb_ppp provided (might be from another context)
            pass
        elif event_df:
            # Use the full event_df to generate average ppp on shots following orebs
            off_rebounds_df = EventProcessor.extract_off_rebounds(event_df)
            oreb_ppp = FeatureUtil.calculate_oreb_ppp(event_df, off_rebounds_df)

        # Apply the function row-wise using apply and pass additional args
        return true_points_df.apply(StatsUtil.calculate_oreb_expected_points, args=(oreb_ppp, reb_chances_df), axis=1)
                
    def calculate_oreb_expected_points(row, oreb_ppp, reb_chances_df):
        if row['made']:
            row['expected_oreb_points'] = 0
            row['true_impact_points_produced'] = row['true_points_produced']
            return row
            
        # Fetch the closest rebound chance based on timestamp
        rebound_chance = reb_chances_df.loc[
            (reb_chances_df['gameId'] == row['gameId']) & 
            (reb_chances_df['shot_time'] <= row['wcTime']),  # Assuming rebound happens before shot completion
            ['off_reb_chance', 'shot_time']
        ].nlargest(1, 'shot_time')  # Get the closest entry before the shot
        
        if not rebound_chance.empty:
            # Calculate additional points from offensive rebounds
            row['expected_oreb_points'] = rebound_chance['off_reb_chance'].iloc[0] * oreb_ppp / 100
        else:
            row['expected_oreb_points'] = 0
            
        row['true_impact_points_produced'] = row['true_points_produced'] + row['expected_oreb_points']

        return row

    def calculate_rebound_chances(moment_df, timestamp, moment_basket_x, hexbin_data, hexbin_basket_x):
        """
        Calculates the rebound chances for each player based on Voronoi regions and precomputed hexbin densities.
        Additionally, computes rebound chances by team ID.

        Args:
            moment_df (DataFrame): DataFrame containing player positions and team IDs.
            hexbin_data (DataFrame): DataFrame containing precomputed hexbin centers and density values.
            basket_x (float): X-coordinate of the basket to determine court side for Voronoi.

        Returns:
            tuple: 
                - dict keyed by player ID with the percentage chance of rebound.
                - dict keyed by team ID with the percentage chance of rebound.
        """
        # Collect on-court players Id's/teamId's
        player_info = moment_df.loc[(moment_df['teamId'] != "-1") & (moment_df['wcTime'] == timestamp), ['playerId', 'teamId']]
        
        # Use the modified Voronoi method to retrieve Voronoi polygons instead of plotting
        if moment_basket_x != hexbin_basket_x:
            moment_df = TrackingProcessor.mirror_court_data(moment_df, 'x', 'y', hexbin_basket_x)
        vis = VisUtil(moment_df)
        player_regions = vis.plot_voronoi_at_timestamp(timestamp, hexbin_basket_x, return_data=True)

        # Map team IDs to Voronoi polygons
        player_teams = dict(zip(player_info['playerId'], player_info['teamId']))
        
        # Initialize dictionaries to store rebound potentials
        player_rebound_potentials = {player_id: 0 for player_id in player_regions}
        team_rebound_potentials = {team_id: 0 for team_id in player_teams.values()}

        total_rebound_potential = 0
        # Calculate rebound potentials using precomputed hexbin data
        for center, density in zip(hexbin_data[['x', 'y']].itertuples(index=False), hexbin_data['density']):
            point = Point(center)
            for player_id, region in player_regions.items():
                if region.contains(point):
                    player_rebound_potentials[player_id] += density
                    team_id = player_teams[player_id]
                    team_rebound_potentials[team_id] += density
                    total_rebound_potential += density

        # Normalize to get probabilities
        rebound_chances = {player_id: (potential / total_rebound_potential) * 100
                        for player_id, potential in player_rebound_potentials.items() if total_rebound_potential > 0}
        team_rebound_chances = {team_id: (potential / total_rebound_potential) * 100
                                for team_id, potential in team_rebound_potentials.items() if total_rebound_potential > 0}

        return rebound_chances, team_rebound_chances

        
    def _calculate_team_rebound_chances_for_row(row, tracking_df, hexbin_region_data, hexbin_basket_x, shot_region_specific=False):
        if row['made'] == True:
            # If the shot was made, just return NA
            return pd.NA, pd.NA
        
        # Identify the hexbin data for the shot's classified region (if prompted)
        region_data = hexbin_region_data[hexbin_region_data['region'] == row['shot_classification']] if shot_region_specific else hexbin_region_data

        # Calculate the rebound chances
        _, team_rebound_chances = StatsUtil.calculate_rebound_chances(
            tracking_df.copy().loc[tracking_df['gameId'] == row['gameId']], row['shot_time'], row["basketX"], region_data, hexbin_basket_x
        )

        # Return rebound chances for defensive and offensive teams
        off_team_id = row['teamId']
        def_team_id = row['rebound_teamId']
        
        return team_rebound_chances.get(off_team_id, 0), team_rebound_chances.get(def_team_id, 0)

    def assign_rebound_chances_to_shots(shot_rebound_df, tracking_df, hexbin_region_data):
        # Allows for progress bar on pd.apply
        tqdm.pandas()
        
        # Determine the basket location used in the hexbin plots (important data is mirrored to this side pre-calculations)
        hexbin_basket_x = 41.75 if hexbin_region_data['x'].sum() > 0 else -41.75
        
        # Apply the function row-wise using apply and pass additional args
        result = shot_rebound_df.progress_apply(StatsUtil._calculate_team_rebound_chances_for_row, axis=1, result_type='expand', args=(tracking_df, hexbin_region_data, hexbin_basket_x))
        
        # Assign results to new columns in the DataFrame
        shot_rebound_df.loc[:, 'off_reb_chance'] = result[0]
        shot_rebound_df.loc[:, 'def_reb_chance'] = result[1]
        
        return shot_rebound_df
    
    def _calculate_player_rebound_chances_for_row(row, tracking_by_game, hexbin_region_data, hexbin_basket_x, shot_region_specific=False):
        if row['made']:
            return pd.Series({'player_rebound_chances': None})
        
        # Use pre-filtered game data
        game_tracking = tracking_by_game.get(row['gameId'])
        if game_tracking is None:
            return pd.Series({'player_rebound_chances': None})
        
        # Identify the hexbin data for the shot's classified region (if prompted)
        region_data = hexbin_region_data[hexbin_region_data['region'] == row['shot_classification']] if shot_region_specific else hexbin_region_data

        # Calculate the rebound chances
        player_rebound_chances, team_chances = StatsUtil.calculate_rebound_chances(
            game_tracking.copy(),
            row['shot_time'],
            row['basketX'],
            region_data, 
            hexbin_basket_x
        )
        
        return pd.Series({'player_rebound_chances': player_rebound_chances})
    
    def assign_player_rebound_chances_to_shots(shot_rebound_df, tracking_df, hexbin_region_data):
        """
        Assigns player-specific rebound chances to each missed shot attempt.
        """
        # Allows for progress bar
        tqdm.pandas()
        
        # Determine the basket location used in the hexbin plots
        hexbin_basket_x = 41.75 if hexbin_region_data['x'].sum() > 0 else -41.75
        
        # Group tracking data by gameId for faster lookup
        tracking_by_game = dict(tuple(tracking_df.groupby('gameId')))
        
        # Process each row with progress_apply
        filtered_df = shot_rebound_df[shot_rebound_df["rebounder_id"].notnull()]
        result = filtered_df.progress_apply(
            StatsUtil._calculate_player_rebound_chances_for_row,
            axis=1, result_type='expand', args=(tracking_by_game, hexbin_region_data, hexbin_basket_x)
        )
        
        # Add the player rebound chances to the original DataFrame
        shot_rebound_df['player_rebound_chances'] = None
        shot_rebound_df.loc[filtered_df.index, 'player_rebound_chances'] = result['player_rebound_chances']
        
        return shot_rebound_df
    
    def generate_region_hexbin_data(shot_rebound_df, regions):
        """
        Generates and saves hexbin data for multiple court regions based on rebound locations.

        Args:
            shot_rebound_df (DataFrame): DataFrame containing rebound locations.
            regions (dict): A dictionary where keys are region names and values are functions that filter shot_rebound_df for each specific region.

        Returns:
            DataFrame: A DataFrame containing rebound density data for each specified court region.
        """
        all_data = []

        for region_name, _ in regions.items():
            # Filter data for the current region
            region_data = shot_rebound_df.loc[shot_rebound_df['shot_classification'] == region_name]
            # Generate hexbin data for the region
            hexbin_df = VisUtil.plot_court_hexmap(region_data, 'rebound_x', 'rebound_y', label='Density (log scale)', return_data=True)
            hexbin_df['region'] = region_name  # Add region name to the DataFrame
            
            # Append to the list
            all_data.append(hexbin_df)
        
        # Concatenate all region data into a single DataFrame
        return pd.concat(all_data, ignore_index=True)