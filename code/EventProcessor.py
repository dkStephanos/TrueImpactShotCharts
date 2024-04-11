import pandas as pd

class EventProcessor:
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