import os
import pandas as pd
from datetime import datetime
import argparse
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt

# Import the functions from other scripts
from get_daily_statcast_data import get_filtered_daily_statcast_data, add_player_names
from baseball_data_processor import process_baseball_data
from baseball_plotting import plot_baseball_stats_final

class BaseballDataWorkflow:
    def __init__(self):
        """Initialize the workflow with simplified directory structure"""
        # Setup directory structure
        self.raw_dir = Path("data/raw")
        self.processed_dir = Path("data/processed")
        self.plots_dir = Path("data/plots")
        
        # Create directories if they don't exist
        for directory in [self.raw_dir, self.processed_dir, self.plots_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_data(self, start_date, end_date, force_refresh=False):
        """Fetch Statcast data for the specified date range"""
        output_file = self.raw_dir / f"statcast_{start_date}_to_{end_date}.csv"
        
        if output_file.exists() and not force_refresh:
            self.logger.info(f"Using existing data file: {output_file}")
            return output_file
        
        self.logger.info(f"Fetching data from {start_date} to {end_date}")
        data = get_filtered_daily_statcast_data(start_date, end_date)
        
        if not data.empty:
            data = add_player_names(data)
            data.to_csv(output_file, index=False)
            self.logger.info(f"Data saved to {output_file}")
            return output_file
        else:
            self.logger.error("No data retrieved")
            return None
    
    def process_data(self, input_file):
        """Process the raw baseball data"""
        output_file = self.processed_dir / f"processed_{input_file.name}"
        
        self.logger.info(f"Processing data from {input_file}")
        try:
            processed_df = process_baseball_data(input_file)
            processed_df.to_csv(output_file, index=False)
            self.logger.info(f"Processed data saved to {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return None
    
    def generate_plots(self, processed_file):
        """Generate plots for each player"""
        self.logger.info(f"Generating plots from {processed_file}")
        
        try:
            df = pd.read_csv(processed_file)
            player_groups = df.groupby('batter')
            
            for batter, player_data in player_groups:
                player_name = f"{player_data['first_name'].iloc[0]}_{player_data['last_name'].iloc[0]}"
                plot_file = self.plots_dir / f"{player_name}_stats.png"
                
                self.logger.info(f"Generating plot for {player_name}")
                fig = plot_baseball_stats_final(player_data)
                fig.savefig(plot_file, dpi=300, bbox_inches='tight')
                plt.close(fig)
        
        except Exception as e:
            self.logger.error(f"Error generating plots: {e}")

def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(description="Baseball Data Analysis Workflow")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh existing data")
    
    args = parser.parse_args()
    
    # Initialize and run workflow
    workflow = BaseballDataWorkflow()
    
    # Execute workflow steps
    raw_data_file = workflow.fetch_data(args.start_date, args.end_date, args.force_refresh)
    if raw_data_file:
        processed_file = workflow.process_data(raw_data_file)
        if processed_file:
            workflow.generate_plots(processed_file)

if __name__ == "__main__":
    main()