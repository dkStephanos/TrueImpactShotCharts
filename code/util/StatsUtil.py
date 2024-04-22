import numpy as np
from scipy.spatial.distance import euclidean


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
