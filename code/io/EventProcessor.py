import pandas as pd
from code.io.PossessionProcessor import PossessionProcessor
class EventProcessor:
    """
    csv cols: 
        gameId,
        eventType,
        playerId,
        playerName,
        teamId,
        teamAbbr,
        period,
        wcTime,
        wcTimeEnd,
        gcTime,
        scTime,
        fouledId,
        fouledName,
        foulType,
        made,
        three,
        fouled,
        assisted,
        receiverId,
        receiverName,
        distance,
        dReb,
        defenderProximity,
        defenderId,
        defenderName
    """
    def load_game(game_id):
        event_df = pd.read_csv('data/src/events.csv', dtype={'gameId': str, 'teamId': str, 'playerId': str, 'fouledId': str,})
        return event_df.loc[event_df['gameId'] == game_id].reset_index(drop=True)
    
    def load_games(game_ids: list = "all"):
        event_df = pd.read_csv('data/src/events.csv', dtype={'gameId': str, 'teamId': str, 'playerId': str, 'fouledId': str,})
        if game_ids != "all":
            event_df = event_df.loc[event_df['gameId'].isin(game_ids)].reset_index(drop=True)
        
        return event_df
    
    def extract_shots(event_df):
        # Initialize an empty list to hold the indices of offensive rebounds
        return event_df.loc[event_df['eventType'] == 'SHOT']

    def extract_off_rebounds(event_df):
        # Filter the DataFrame for offensive rebounds -- we exclude team rebounds here
        return event_df.loc[(event_df['eventType'] == 'REB') & (event_df['dReb'] == False) & (event_df['playerId'].notnull())]
    
    def extract_transition_opportunities(event_df):
        # Find rows where 'dReb' is not null
        drebs = event_df[(event_df['dReb'].notna()) & (event_df['playerId'].notna())].index.tolist()
        
        # List to hold transition opportunities
        transition_opportunities = []
        
        # Find events following each dReb that match the same teamId until a condition breaks the sequence
        for start_index in drebs:
            team_id = event_df.at[start_index, 'teamId']

            # Get the slice of the dataframe from the dReb event to the end of the dataframe
            subsequent_events = event_df.loc[start_index:]

            # Find where the team ID changes or an event type signals a new play
            break_condition = subsequent_events['teamId'] != team_id

            # Get the index of the first event where this condition is true
            if break_condition.any():
                end_index = subsequent_events[break_condition].index[0]
            else:
                end_index = event_df.index[-1]

            # Append the slice from the dReb to the event before the condition breaks
            transition_opportunities.append(event_df.loc[start_index:end_index - 1])
        
        return transition_opportunities

    def get_start_end_time_of_event(event):
        start_moment = event.iloc[0]
        end_moment = event.iloc[-1]
        
        return start_moment['wcTime'], end_moment['wcTime']
        
    def extract_shots_and_rebounds(event_df, tracking_df, possession_df):
        """
        Extracts shots and their corresponding rebounds, mapping the shot location to the rebound location using tracking data.
        Includes the teamId of the team that secured the rebound to compare against calculated rebound chances.
        Now also includes the basketX position from possessions data for each shot based on the timestamp.

        Args:
            event_df (DataFrame): DataFrame containing all game events.
            tracking_df (DataFrame): DataFrame containing tracking data for ball and players.
            possession_df (DataFrame): DataFrame containing possession data with basketX values.

        Returns:
            DataFrame: Contains matched shot and rebound locations, times, rebounding teamId, and basketX.
        """
        # Extract the ball locations from the tracking_df
        tracking_df = tracking_df[tracking_df["teamId"] == "-1"].copy()
        
        # Filter for shots and rebounds
        shots_df = event_df[event_df['eventType'] == 'SHOT'].copy()
        rebounds_df = event_df[event_df['eventType'] == 'REB'].copy()

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

        # Apply possession data for basketX based on the shot time
        valid_pairs['basketX'] = valid_pairs['wcTime_shot'].apply(
            lambda x: PossessionProcessor.extract_possession_by_timestamp(possession_df, x)['basketX']
        )

        # Select and rename relevant columns for the result, including the rebounding teamId
        result_df = valid_pairs[['shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'wcTime_shot', 'wcTime_reb', 'teamId_reb', 'basketX']]
        result_df.columns = ['shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'shot_time', 'rebound_time', 'rebound_teamId', 'basketX']

        return result_df






