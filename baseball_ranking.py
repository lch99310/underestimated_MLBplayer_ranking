import pandas as pd
import numpy as np
from typing import Tuple, List
import glob
import os

def analyze_player_estimations(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze baseball players' estimation accuracy based on diff_rolling_OBA.
    
    Args:
        df (pandas.DataFrame): DataFrame containing baseball statistics with columns:
            - game_date
            - first_name
            - last_name
            - diff_rolling_OBA
    
    Returns:
        Tuple[pandas.DataFrame, pandas.DataFrame]: Two DataFrames containing:
            1. Daily top 5 most underestimated players (highest diff_rolling_OBA)
            2. Daily top 5 most overestimated players (lowest diff_rolling_OBA)
    """
    # Create full player names
    df['player_name'] = df['first_name'] + ' ' + df['last_name']
    
    # Calculate average diff_rolling_OBA for each player on each game date
    daily_player_stats = df.groupby(['game_date', 'player_name'])['diff_rolling_OBA'].mean().reset_index()
    
    def get_daily_rankings(data: pd.DataFrame, ascending: bool) -> pd.DataFrame:
        # Group by date and get top/bottom 5 players
        ranked_players = []
        
        for date in data['game_date'].unique():
            date_data = data[data['game_date'] == date].copy()
            # Sort and get top/bottom 5
            sorted_players = date_data.nlargest(5, 'diff_rolling_OBA') if not ascending else date_data.nsmallest(5, 'diff_rolling_OBA')
            sorted_players['rank'] = range(1, len(sorted_players) + 1)
            ranked_players.append(sorted_players)
        
        # Combine all rankings
        ranked_df = pd.concat(ranked_players, ignore_index=True)
        
        # Format the diff_rolling_OBA as percentage
        ranked_df['diff_rolling_OBA'] = ranked_df['diff_rolling_OBA'].multiply(100).round(2)
        
        return ranked_df

    # Get underestimated (highest diff_rolling_OBA) and overestimated (lowest diff_rolling_OBA) players
    underestimated = get_daily_rankings(daily_player_stats, ascending=False)
    overestimated = get_daily_rankings(daily_player_stats, ascending=True)
    
    # Add estimation type labels
    underestimated['estimation_type'] = 'Underestimated'
    overestimated['estimation_type'] = 'Overestimated'
    
    # Sort by date and rank
    underestimated = underestimated.sort_values(['game_date', 'rank'])
    overestimated = overestimated.sort_values(['game_date', 'rank'])
    
    return underestimated, overestimated

def format_results(df: pd.DataFrame) -> str:
    """
    Format the analysis results into a readable string.
    
    Args:
        df (pandas.DataFrame): DataFrame containing ranked players
        
    Returns:
        str: Formatted string of results
    """
    output = []
    for date in df['game_date'].unique():
        date_data = df[df['game_date'] == date]
        output.append(f"\nDate: {date}")
        output.append("-" * 50)
        
        for _, row in date_data.iterrows():
            output.append(f"Rank {row['rank']}: {row['player_name']} ({row['diff_rolling_OBA']:+.2f}%)")
    
    return "\n".join(output)

def get_latest_processed_file() -> str:
    """
    Find the most recent processed baseball stats file.
    
    Returns:
        str: Path to the most recent processed_baseball_stats.csv file
    """
    try:
        # Look for processed_baseball_stats.csv file
        if os.path.exists('processed_baseball_stats.csv'):
            return 'processed_baseball_stats.csv'
        else:
            raise FileNotFoundError("Cannot find processed_baseball_stats.csv")
    except Exception as e:
        print(f"Error finding input file: {str(e)}")
        raise

def main():
    """
    Main function to run the player estimation analysis.
    """
    try:
        # Get the latest processed file
        input_file = get_latest_processed_file()
        print(f"\nUsing input file: {input_file}")
        
        # Read the data
        df = pd.read_csv(input_file)
        
        # Analyze player estimations
        underestimated, overestimated = analyze_player_estimations(df)
        
        # Print results
        print("\n=== Most Underestimated Players ===")
        print(format_results(underestimated))
        
        print("\n\n=== Most Overestimated Players ===")
        print(format_results(overestimated))
        
        # Save results to CSV files
        underestimated.to_csv('underestimated_players.csv', index=False)
        overestimated.to_csv('overestimated_players.csv', index=False)
        print("\nResults have been saved to 'underestimated_players.csv' and 'overestimated_players.csv'")
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")

if __name__ == "__main__":
    main()