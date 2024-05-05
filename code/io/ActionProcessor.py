import pandas as pd
from code.io.PossessionProcessor import PossessionProcessor

class ActionProcessor:
    """
    Class for identifying/extracting game actions using a combnination of event, possesssion and tracking data
    """
    
    def extract_shots_and_rebounds(event_df, tracking_df, possession_df):
        """
        Extracts missed shots and their corresponding rebounds, mapping the shot location to the rebound location using tracking data.
        Includes the teamId of the team that secured the rebound to compare against calculated rebound chances.
        Now also includes the basketX position and the shot outcome from possessions data for each shot based on the timestamp.

        Args:
            event_df (DataFrame): DataFrame containing all game events.
            tracking_df (DataFrame): DataFrame containing tracking data for ball and players.
            possession_df (DataFrame): DataFrame containing possession data with basketX values and shot outcomes.

        Returns:
            DataFrame: Contains matched shot and rebound locations, times, rebounding teamId, and basketX.
        """
        # Extract the ball locations from the tracking_df
        tracking_df = tracking_df[tracking_df["teamId"] == "-1"].copy()
        
        # Filter for shots and rebounds
        shots_df = event_df[event_df['eventType'] == 'SHOT'].copy()
        rebounds_df = event_df[event_df['eventType'] == 'REB'].copy()

        # Include outcome and basketX by applying a function to extract data from possession_df based on timestamp
        shots_df['outcome'] = shots_df['wcTime'].apply(
            lambda x: PossessionProcessor.extract_possession_by_timestamp(possession_df, x)['outcome']
        )
        shots_df['basketX'] = shots_df['wcTime'].apply(
            lambda x: PossessionProcessor.extract_possession_by_timestamp(possession_df, x)['basketX']
        )

        # Filter shots_df further for only missed shots (FGX)
        shots_df = shots_df[shots_df['outcome'] == 'FGX']

        # Reverse the merge direction: start with rebounds and find the last shot before each
        merged_df = pd.merge(rebounds_df, shots_df, on=['gameId', 'period'], suffixes=('_reb', '_shot'))

        # Filter to ensure that only valid shot-rebound pairs are considered
        valid_pairs = merged_df[merged_df['wcTime_shot'] < merged_df['wcTime_reb']].copy()

        # Sort to get the latest shot before each rebound
        valid_pairs.sort_values(by=['gameId', 'period', 'wcTime_reb', 'wcTime_shot'], ascending=[True, True, True, False], inplace=True)
        
        # Drop duplicates to keep only the most recent shot for each rebound
        valid_pairs = valid_pairs.drop_duplicates(subset=['gameId', 'period', 'wcTime_reb'])

        # Merge tracking data for the positions
        valid_pairs = pd.merge(valid_pairs, tracking_df[['gameId', 'wcTime', 'x', 'y']], left_on=['gameId', 'wcTime_shot'], right_on=['gameId', 'wcTime'], how='left', suffixes=('', '_shot'))
        valid_pairs.rename(columns={'x': 'shot_x', 'y': 'shot_y'}, inplace=True)
        valid_pairs.drop(columns=['wcTime'], inplace=True)

        valid_pairs = pd.merge(valid_pairs, tracking_df[['gameId', 'wcTime', 'x', 'y']], left_on=['gameId', 'wcTime_reb'], right_on=['gameId', 'wcTime'], how='left', suffixes=('_shot', '_reb'))
        valid_pairs.rename(columns={'x': 'rebound_x', 'y': 'rebound_y'}, inplace=True)
        valid_pairs.drop(columns=['wcTime'], inplace=True)

        # Select and rename relevant columns for the result, including the rebounding teamId
        result_df = valid_pairs[['shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'wcTime_shot', 'wcTime_reb', 'teamId_reb', 'basketX']]
        result_df.columns = ['shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'shot_time', 'rebound_time', 'rebound_teamId', 'basket_x']

        # Drop rows where essential coordinates are missing
        return result_df.dropna(subset=['shot_x', 'shot_y', 'rebound_x', 'rebound_y'])


