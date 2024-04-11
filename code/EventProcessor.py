import pandas as pd

class EventProcessor:
    def extract_shots(event_df):
        # Initialize an empty list to hold the indices of offensive rebounds
        return event_df.loc[event_df['eventType'] == 'SHOT']
    
    def tag_off_rebounds(event_df):
        # Add an 'off_reb' column initialized to False
        event_df['off_reb'] = False
        
        # Iterate over the DataFrame
        for i in range(1, len(event_df)):
            # Check if current row is a rebound and previous row is a shot by the same team
            if event_df.iloc[i]['eventType'] == 'REB' and event_df.iloc[i - 1]['eventType'] == 'SHOT' and event_df.iloc[i - 1]['teamId'] == event_df.iloc[i]['teamId']:
                # Mark the previous shot row as followed by an offensive rebound
                event_df.at[i - 1, 'off_reb'] = True
        
        # Return the modified DataFrame
        return event_df

    def extract_off_rebounds(event_df):
        # Initialize an empty list to hold the indices of offensive rebounds
        offensive_rebounds = []

        # Iterate over the DataFrame using .iterrows()
        for i, row in event_df.iterrows():
            # Check if current row is a rebound
            if row['eventType'] == 'REB':
                # Check if the previous row is a shot by the same team
                if i > 0 and event_df.iloc[i - 1]['eventType'] == 'SHOT' and event_df.iloc[i - 1]['teamId'] == row['teamId']:
                    offensive_rebounds.append(i)

        # Filter the DataFrame for offensive rebounds
        return event_df.loc[offensive_rebounds]