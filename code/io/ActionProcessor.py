import pandas as pd


class ActionProcessor:
    """
    Class for identifying/extracting game actions using a combnination of event, possesssion and tracking data
    """

    def extract_shots_and_rebounds(event_df, tracking_df):
        """
        Extracts missed shots and their corresponding rebounds, mapping the shot location to the rebound location using tracking data.
        Includes the teamId of the team that secured the rebound to compare against calculated rebound chances.
        Now also includes the basketX position and the shot outcome from possessions data for each shot based on the timestamp.

        Args:
            event_df (DataFrame): DataFrame containing all game events.
            tracking_df (DataFrame): DataFrame containing tracking data for ball and players.

        Returns:
            DataFrame: Contains matched shot and rebound locations, times, rebounding teamId, etc.
        """
        # Extract ball locations where teamId is '-1'
        tracking_df = tracking_df[tracking_df["teamId"] == "-1"].copy()

        # Filter for shots and rebounds
        shots_df = (
            event_df[event_df["eventType"] == "SHOT"].drop(columns=["dReb"]).copy()
        )
        rebounds_df = event_df[event_df["eventType"] == "REB"][
            ["gameId", "teamId", "period", "wcTime", "dReb"]
        ].copy()

        # Merging shots and rebounds on 'gameId' and 'period', then filtering and deduplicating
        merged_df = pd.merge(
            rebounds_df, shots_df, on=["gameId", "period"], suffixes=("_reb", "_shot")
        )
        valid_pairs = merged_df[merged_df["wcTime_shot"] < merged_df["wcTime_reb"]]
        valid_pairs = valid_pairs.sort_values(
            by=["gameId", "period", "wcTime_reb", "wcTime_shot"],
            ascending=[True, True, True, False],
        )
        valid_pairs = valid_pairs.drop_duplicates(
            subset=["gameId", "period", "wcTime_shot"]
        )
        valid_pairs = valid_pairs.drop_duplicates(
            subset=["gameId", "period", "wcTime_reb"]
        )

        # Merge with tracking data for positions
        valid_pairs = pd.merge(
            valid_pairs,
            tracking_df[["gameId", "wcTime", "x", "y"]],
            left_on=["gameId", "wcTime_shot"],
            right_on=["gameId", "wcTime"],
            how="left",
            suffixes=("", "_shot"),
        )
        valid_pairs = valid_pairs.rename(columns={"x": "shot_x", "y": "shot_y"})
        valid_pairs = valid_pairs.drop(columns=["wcTime"])

        valid_pairs = pd.merge(
            valid_pairs,
            tracking_df[["gameId", "wcTime", "x", "y"]],
            left_on=["gameId", "wcTime_reb"],
            right_on=["gameId", "wcTime"],
            how="left",
            suffixes=("_shot", "_reb"),
        )
        valid_pairs = valid_pairs.rename(columns={"x": "rebound_x", "y": "rebound_y"})
        valid_pairs = valid_pairs.drop(columns=["wcTime"])

        # Prepare the final DataFrame
        result_df = valid_pairs.rename(
            columns={
                "wcTime_shot": "shot_time",
                "wcTime_reb": "rebound_time",
                "teamId_reb": "rebound_teamId",
                "teamId_shot": "teamId",
            }
        )
        result_df = result_df.dropna(
            subset=["shot_x", "shot_y"]
        )

        # Combine made and missed shot data, ensuring that rebound data for made shots is filled with nulls
        made_shots = pd.merge(
            shots_df.loc[shots_df["made"] == True],
            tracking_df[["gameId", "wcTime", "x", "y"]],
            left_on=["gameId", "wcTime"],
            right_on=["gameId", "wcTime"],
            how="left",
            suffixes=("", "_shot"),
        )
        made_shots = made_shots.rename(
            columns={"x": "shot_x", "y": "shot_y", "wcTime": "shot_time"}
        )

        return pd.concat(
            [
                made_shots,  # Made shots, already included in shots_with_pos
                result_df,  # Missed shots merged with rebound data
            ],
            ignore_index=True,
        )
