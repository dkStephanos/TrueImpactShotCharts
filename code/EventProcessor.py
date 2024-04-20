import pandas as pd

class EventProcessor:
    def load_game(game_id):
        event_df = pd.read_csv('data/src/events.csv', dtype={'gameId': str, 'teamId': str, 'playerId': str})
        return event_df.loc[event_df['gameId'] == game_id]
    
    def extract_shots(event_df):
        # Initialize an empty list to hold the indices of offensive rebounds
        return event_df.loc[event_df['eventType'] == 'SHOT']

    def extract_off_rebounds(event_df):
        # Filter the DataFrame for offensive rebounds -- we exclude team rebounds here
        return event_df.loc[(event_df['eventType'] == 'REB') & (event_df['dReb'] == False) & (event_df['playerId'].notnull())]
    
    def extract_transition_events(event_df):
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
