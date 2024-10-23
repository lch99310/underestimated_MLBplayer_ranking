import pandas as pd
import numpy as np

def process_baseball_data(file_path):
    """
    Process baseball statistics data with the following steps:
    1. Reorganize name columns
    2. Calculate differential OBA (xwOBA - wOBA)
    3. Calculate 100 PA rolling statistics for each batter:
       - rolling diff_OBA
       - rolling xwOBA
       - rolling wOBA
       - diff_rolling_OBA (rolling_xwOBA - rolling_wOBA)
    
    Args:
        file_path (str): Path to the CSV file containing baseball data
    
    Returns:
        pandas.DataFrame: Processed baseball statistics
    """
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # 1. Move first_name and last_name next to batter
    # First, get all column names
    cols = df.columns.tolist()
    # Remove first_name and last_name from their current position
    cols.remove('first_name')
    cols.remove('last_name')
    # Insert them after 'batter'
    batter_idx = cols.index('batter')
    cols.insert(batter_idx + 1, 'first_name')
    cols.insert(batter_idx + 2, 'last_name')
    # Reorder the DataFrame
    df = df[cols]
    
    # 2. Calculate diff_OBA (xwOBA - wOBA)
    # Note: estimated_woba_using_speedangle is xwOBA
    df['diff_OBA'] = df['estimated_woba_using_speedangle'] - df['woba_value']
    
    # 3. Calculate rolling statistics for each batter
    # Sort by batter and date to ensure correct rolling calculation
    df = df.sort_values(['batter', 'game_date'])
    
    # Function to calculate rolling average
    def calculate_rolling_stats(group):
        # Calculate rolling diff_OBA
        group['rolling_100PA_diff_OBA'] = group['diff_OBA'].rolling(window=100, min_periods=1).mean()
        
        # Calculate rolling xwOBA
        group['rolling_100PA_xwOBA'] = group['estimated_woba_using_speedangle'].rolling(window=100, min_periods=1).mean()
        
        # Calculate rolling wOBA
        group['rolling_100PA_wOBA'] = group['woba_value'].rolling(window=100, min_periods=1).mean()
        
        # Calculate diff_rolling_OBA (difference between rolling xwOBA and rolling wOBA)
        group['diff_rolling_OBA'] = group['rolling_100PA_xwOBA'] - group['rolling_100PA_wOBA']
        
        return group
    
    # Apply rolling calculations for each batter
    df = df.groupby('batter', group_keys=False).apply(calculate_rolling_stats)
    
    return df

def main():
    """
    Main function to demonstrate usage of the baseball data processor
    """
    # Example usage
    file_path = 'sample.csv'  # Replace with actual file path
    
    try:
        # Process the data
        processed_df = process_baseball_data(file_path)
        
        # Display basic information about the processed data
        print("\nData Processing Summary:")
        print(f"Total number of PAs processed: {len(processed_df)}")
        print("\nUnique batters processed:")
        for batter in processed_df[['batter', 'first_name', 'last_name']].drop_duplicates().values:
            print(f"ID: {batter[0]}, Name: {batter[1]} {batter[2]}")
            
        # Display sample of rolling statistics for each batter
        print("\nSample of rolling statistics for each batter:")
        for batter in processed_df['batter'].unique():
            batter_name = f"{processed_df[processed_df['batter'] == batter]['first_name'].iloc[0]} {processed_df[processed_df['batter'] == batter]['last_name'].iloc[0]}"
            latest_stats = processed_df[processed_df['batter'] == batter].iloc[-1]
            print(f"\n{batter_name}:")
            print(f"Latest rolling 100PA diff_OBA: {latest_stats['rolling_100PA_diff_OBA']:.3f}")
            print(f"Latest rolling 100PA xwOBA: {latest_stats['rolling_100PA_xwOBA']:.3f}")
            print(f"Latest rolling 100PA wOBA: {latest_stats['rolling_100PA_wOBA']:.3f}")
            print(f"Latest diff_rolling_OBA: {latest_stats['diff_rolling_OBA']:.3f}")
        
        # Optional: Save the processed data to a new CSV file
        output_file = 'processed_baseball_stats.csv'
        processed_df.to_csv(output_file, index=False)
        print(f"\nProcessed data saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()