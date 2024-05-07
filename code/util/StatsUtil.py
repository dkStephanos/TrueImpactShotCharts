import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial.distance import euclidean
from shapely.geometry import Point, Polygon
from code.io.TrackingProcessor import TrackingProcessor
from code.util.VisUtil import VisUtil

class StatsUtil:
    def calculate_true_points(df):
        """
        Enhances the DataFrame with shot attempts to include a 'true points produced' column,
        which accounts for points from made shots and subsequent free throws following fouls on those shots,
        using TOUCH events to determine the end of a free throw sequence.
        """
        # Ensure the DataFrame is sorted by wcTime if not already sorted
        df = df.sort_values(by="wcTime")

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
            if index + 1 < len(df):
                next_event = df.iloc[index + 1]
                # Check if the next event is a FOUL related to this SHOT
                if (
                    next_event["eventType"] == "FOUL"
                    and next_event["fouledId"] == row["playerId"]
                ):
                    # Find free throws directly related to this foul
                    free_throws = df[
                        (df["eventType"] == "FT")
                        & (df["wcTime"] > next_event["wcTime"])
                        & (df["playerId"] == row["playerId"])
                        & (df["gameId"] == row["gameId"])
                    ].sort_values(by="wcTime")

                    for ft in free_throws.itertuples():
                        if ft.made:
                            points += 1
                        # Look for the next event after this free throw
                        ft_index = df.index.get_loc(ft.Index)
                        if ft_index + 1 < len(df):
                            next_ft_event = df.iloc[ft_index + 1]
                            if next_ft_event["eventType"] != "FT":
                                break

            # Store the total points produced in the DataFrame
            shots_df.at[index, "true_points_produced"] = points

        return shots_df[
            [
                "gameId",
                "playerId",
                "playerName",
                "teamId",
                "period",
                "wcTime",
                "points_produced",
                "true_points_produced",
            ]
        ]

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

    def calculate_rebound_chances(tracking_df, timestamp, hexbin_data, basket_x):
        """
        Calculates the rebound chances for each player based on Voronoi regions and precomputed hexbin densities.
        Additionally, computes rebound chances by team ID.

        Args:
            moments_df (DataFrame): DataFrame containing player positions and team IDs.
            hexbin_data (DataFrame): DataFrame containing precomputed hexbin centers and density values.
            basket_x (float): X-coordinate of the basket to determine court side for Voronoi.

        Returns:
            tuple: 
                - dict keyed by player ID with the percentage chance of rebound.
                - dict keyed by team ID with the percentage chance of rebound.
        """
        # Calculate Voronoi regions for players
        player_positions = tracking_df.loc[(tracking_df['teamId'] != "-1") & (tracking_df['wcTime'] == timestamp), ['playerId', 'x', 'y', 'teamId']]
        
        # Use the modified Voronoi method to retrieve Voronoi polygons instead of plotting
        vis = VisUtil(tracking_df)
        team_regions = vis.plot_voronoi_at_timestamp(timestamp, basket_x, return_data=True)

        # Map team IDs to Voronoi polygons
        player_teams = dict(zip(player_positions['playerId'], player_positions['teamId']))
        player_regions = {player_id: team_regions[team_id] for player_id, team_id in player_teams.items() if team_id in team_regions}

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

        
    def _calculate_rebound_for_row(row, tracking_df, hexbin_region_data):
        # Identify the hexbin data for the shot's classified region
        region_data = hexbin_region_data[hexbin_region_data['region'] == row['shot_classification']]

        # Calculate the rebound chances
        _, team_rebound_chances = StatsUtil.calculate_rebound_chances(
            tracking_df.copy().loc[tracking_df['gameId'] == row['gameId']], row['rebound_time'], region_data, row["basket_x"]
        )

        # Return rebound chances for defensive and offensive teams
        off_team_id = row['teamId']
        def_team_id = row['rebound_teamId']
        
        return team_rebound_chances.get(off_team_id, 0), team_rebound_chances.get(def_team_id, 0)

    def assign_rebound_chances_to_shots(shot_rebound_df, tracking_df, hexbin_region_data):
        # Apply the function row-wise using apply and pass additional args
        result = shot_rebound_df.apply(StatsUtil._calculate_rebound_for_row, axis=1, result_type='expand', args=(tracking_df, hexbin_region_data))
        
        # Assign results to new columns in the DataFrame
        shot_rebound_df['off_reb_chance'], shot_rebound_df['def_reb_chance'] = result[0], result[1]
        
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
