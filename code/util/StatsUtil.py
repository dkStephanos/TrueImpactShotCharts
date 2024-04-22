import numpy as np
from scipy.spatial.distance import euclidean


class StatsUtil:
    def calculate_true_points(df):
        """
        Enhances the DataFrame with shot attempts to include a 'true points produced' column,
        which considers points from made shots and subsequent free throws correctly associated with fouls on those shots.

        Args:
        df (pd.DataFrame): DataFrame containing game event data.

        Returns:
        pd.DataFrame: Updated DataFrame with only shot attempts and an added 'true points produced' column.
        """
        # Filter to get only shot attempts
        shots_df = df[df["eventType"] == "SHOT"].copy()

        # Add a column to store the computed true points
        shots_df["true_points_produced"] = 0

        # Iterate through the shots DataFrame
        for index, row in shots_df.iterrows():
            points = 0
            if row["made"]:  # Check if the shot was made
                points += 3 if row["three"] else 2
            else:
                # Check for fouls resulting in free throws
                player_id = row["playerId"]

                # Identify free throws that directly follow the shot within the game events
                subsequent_events = df[
                    (df["wcTime"] > row["wcTime"]) & (df["gameId"] == row["gameId"])
                ]
                free_throws = subsequent_events[
                    (subsequent_events["eventType"] == "FT")
                    & (subsequent_events["fouledId"] == player_id)
                ]

                # Consider the first set of free throws after the shot until a different type of event occurs
                for _, ft in free_throws.iterrows():
                    if ft["made"]:
                        points += 1
                    # Stop adding points if we encounter an event that is not a free throw
                    if subsequent_events.loc[ft.name + 1, "eventType"] != "FT":
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
