import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi
from scipy.spatial.distance import euclidean
from shapely.geometry import Point, Polygon
from code.io.TrackingProcessor import TrackingProcessor

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
                            print(
                                f"Adding point for free throw at {ft.wcTime} by {ft.playerId}"
                            )
                        # Look for the next event after this free throw
                        ft_index = df.index.get_loc(ft.Index)
                        if ft_index + 1 < len(df):
                            next_ft_event = df.iloc[ft_index + 1]
                            if next_ft_event["eventType"] != "FT":
                                print(
                                    f"Stopping at {next_ft_event['eventType']} at {next_ft_event['wcTime']}"
                                )
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

    def calculate_rebound_chances(moments_df, shot_rebound_df, timestamp, basket_x):
        """
        Calculates the rebound chances for each player based on Voronoi regions and dynamically created hexbin densities
        at a specific timestamp. Additionally, computes rebound chances by team ID.

        Args:
            moments_df (DataFrame): DataFrame containing player positions and team IDs.
            shot_rebound_df (DataFrame): DataFrame containing shot and rebound locations. (Used as context for rebound distribution stats)
            timestamp (float): Specific game time moment for which player positions are considered.
            basket_x (float): X-coordinate of the basket to determine court side for Voronoi.

        Returns:
            tuple: 
                - dict keyed by player ID with the percentage chance of rebound.
                - dict keyed by team ID with the percentage chance of rebound.
        """
        # Filter moments data to the specific timestamp
        moments_df = moments_df[moments_df['wcTime'] == timestamp]

        # Create a new figure and axes for hexbin plot
        fig, ax = plt.subplots(figsize=(12, 8))

        # Mirror rebound data points across half court for plotting
        shot_rebound_df = TrackingProcessor.mirror_court_data(shot_rebound_df, 'rebound_x', basket_x)

        # Plotting the data using hexbin for rebounds
        hexbin = ax.hexbin(
            shot_rebound_df['rebound_x'], shot_rebound_df['rebound_y'],
            gridsize=int((47 / 1.5) / 2),  # based on court dimensions and desired hex radius
            cmap='viridis',  # visually distinct colormap
            edgecolors='black',
            linewidth=0.5,
            extent=[0 if basket_x > 0 else -47, 47 if basket_x > 0 else 0, -25, 25]  # Set the extent to match the half-court dimensions
        )

        # Calculate Voronoi regions for players at the given timestamp
        player_positions = moments_df.loc[moments_df['teamId'] != "-1"][['playerId', 'x', 'y', 'teamId']].values
        vor = Voronoi(player_positions[:, 1:3])

        # Map each Voronoi region to its player and team
        player_regions = {}
        player_teams = {}
        for player_id, team_id, region_index in zip(player_positions[:, 0], player_positions[:, 3], vor.point_region):
            region = vor.regions[region_index]
            if all(v >= 0 for v in region):  # Check if all vertices indices are non-negative
                polygon = Polygon(vor.vertices[region])
                player_regions[int(player_id)] = polygon
                player_teams[int(player_id)] = int(team_id)

        # Collect hexbin centers and their counts
        rebound_densities = hexbin.get_array()
        hexbin_centers = hexbin.get_offsets()

        # Calculate total potential rebounds per player and team
        player_rebound_potentials = {int(player_id): 0 for player_id in player_regions.keys()}
        team_rebound_potentials = {}
        total_rebound_potential = 0

        for center, density in zip(hexbin_centers, rebound_densities):
            point = Point(center[0], center[1])
            for player_id, region in player_regions.items():
                if region.contains(point):
                    player_rebound_potentials[player_id] += density
                    team_id = player_teams[player_id]
                    if team_id in team_rebound_potentials:
                        team_rebound_potentials[team_id] += density
                    else:
                        team_rebound_potentials[team_id] = density
                    total_rebound_potential += density

        # Normalize to get probabilities
        rebound_chances = {player_id: (potential / total_rebound_potential) * 100
                        for player_id, potential in player_rebound_potentials.items() if total_rebound_potential > 0}
        team_rebound_chances = {team_id: (potential / total_rebound_potential) * 100
                                for team_id, potential in team_rebound_potentials.items() if total_rebound_potential > 0}

        plt.close(fig)  # Close the plot as it's not needed for visualization

        return rebound_chances, team_rebound_chances

