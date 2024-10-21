import pandas as pd
from pybaseball import statcast, playerid_reverse_lookup
from datetime import datetime, timedelta

def get_filtered_daily_statcast_data(start_date, end_date):
    """
    Retrieve filtered daily Statcast data for the specified date range.
    
    :param start_date: Start date in 'YYYY-MM-DD' format
    :param end_date: End date in 'YYYY-MM-DD' format
    :return: DataFrame with filtered daily Statcast data
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    all_data = []
    current_date = start
    
    while current_date <= end:
        print(f"Fetching data for {current_date.strftime('%Y-%m-%d')}")
        
        try:
            df = statcast(start_dt=current_date.strftime('%Y-%m-%d'), end_dt=current_date.strftime('%Y-%m-%d'))
            if not df.empty:
                # Select only the required columns
                df = df[['game_date', 'batter', 'estimated_woba_using_speedangle', 'woba_value', 'woba_denom']]
                # Filter out rows where woba_denom is not equal to 1
                df = df[df['woba_denom'] == 1]
                df['game_date'] = pd.to_datetime(df['game_date'])
                all_data.append(df)
            else:
                print(f"No data available for {current_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"Error fetching data for {current_date.strftime('%Y-%m-%d')}: {e}")
        
        current_date += timedelta(days=1)
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

def add_player_names(df):
    """
    Add first name and last name to the DataFrame using playerid_reverse_lookup.
    
    :param df: DataFrame with 'batter' column containing MLBAM IDs
    :return: DataFrame with added 'first_name' and 'last_name' columns
    """
    unique_batters = df['batter'].unique()
    player_info = playerid_reverse_lookup(unique_batters, key_type='mlbam')
    
    # Create a dictionary for quick lookup
    name_dict = dict(zip(player_info['key_mlbam'], zip(player_info['name_first'], player_info['name_last'])))
    
    # Add first name and last name columns
    df['first_name'] = df['batter'].map(lambda x: name_dict.get(x, ('Unknown', 'Unknown'))[0])
    df['last_name'] = df['batter'].map(lambda x: name_dict.get(x, ('Unknown', 'Unknown'))[1])
    
    return df

def save_data_to_csv(df, filename):
    """
    Save the DataFrame to a CSV file.
    
    :param df: DataFrame to save
    :param filename: Name of the CSV file
    """
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

# Example usage
if __name__ == "__main__":
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")
    
    data = get_filtered_daily_statcast_data(start_date, end_date)
    
    if not data.empty:
        data = add_player_names(data)
        output_file = f"filtered_statcast_data_with_names_{start_date}_to_{end_date}.csv"
        save_data_to_csv(data, output_file)
        print(f"Total rows of data: {len(data)}")
        print(data.head())
    else:
        print("No data retrieved for the specified date range.")