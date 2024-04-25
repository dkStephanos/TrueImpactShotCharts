import pandas as pd

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
    
    def extract_shots_and_rebounds(event_df, tracking_df):
        """
        Extracts shots and their corresponding rebounds, mapping the shot location to the rebound location with tracking data.
        
        Args:
            event_df (pd.DataFrame): DataFrame containing game events.
            tracking_df (pd.DataFrame): DataFrame containing tracking data with coordinates.

        Returns:
            pd.DataFrame: DataFrame with columns ['shot_x', 'shot_y', 'rebound_x', 'rebound_y', 'shot_time', 'rebound_time']
        """
        # Filter for shots and rebounds in the event data
        shots_df = event_df[event_df['eventType'] == 'SHOT']
        rebounds_df = event_df[event_df['eventType'] == 'REB']

        # Mapping of shots to their subsequent rebounds with coordinates
        shot_rebound_mapping = []

        # Iterate over rebounds to find the preceding shot
        for rebound_index, rebound_row in rebounds_df.iterrows():
            # Get the latest shot before the rebound within the same game and period
            possible_shots = shots_df[(shots_df['wcTime'] < rebound_row['wcTime']) & (shots_df['gameId'] == rebound_row['gameId']) & (shots_df['period'] == rebound_row['period'])]
            
            if not possible_shots.empty:
                latest_shot = possible_shots.iloc[-1]  # Get the last shot entry before the rebound
                
                # Get tracking data for shot and rebound moments
                shot_tracking = tracking_df[(tracking_df['wcTime'] == latest_shot['wcTime']) & (tracking_df['playerId'] == latest_shot['playerId'])]
                rebound_tracking = tracking_df[(tracking_df['wcTime'] == rebound_row['wcTime']) & (tracking_df['playerId'] == rebound_row['playerId'])]
                
                if not shot_tracking.empty and not rebound_tracking.empty:
                    shot_rebound_mapping.append({
                        'shot_x': shot_tracking.iloc[0]['x'],
                        'shot_y': shot_tracking.iloc[0]['y'],
                        'rebound_x': rebound_tracking.iloc[0]['x'],
                        'rebound_y': rebound_tracking.iloc[0]['y'],
                        'shot_time': latest_shot['wcTime'],
                        'rebound_time': rebound_row['wcTime']
                    })

        return pd.DataFrame(shot_rebound_mapping)