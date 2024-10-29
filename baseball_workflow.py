# baseball_workflow.py
import os
import pandas as pd
from datetime import datetime, date
import argparse
import logging
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
import matplotlib.pyplot as plt

# Import the functions from other scripts
from get_daily_statcast_data import get_filtered_daily_statcast_data, add_player_names
from baseball_data_processor import process_baseball_data
from baseball_plotting import plot_baseball_stats_final
from baseball_ranking import analyze_player_estimations
from baseball_email_report import BaseballReportEmailer, MLBSeasonSchedule

class BaseballDataWorkflow:
# Update the email_config in baseball_workflow.py's __init__ method:

    def __init__(self):
        """Initialize the workflow with simplified directory structure"""
        # Setup directory structure
        self.raw_dir = Path("data/raw")
        self.processed_dir = Path("data/processed")
        self.plots_dir = Path("data/plots")
        self.rankings_dir = Path("data/rankings")
        
        # Create directories if they don't exist
        for directory in [self.raw_dir, self.processed_dir, self.plots_dir, self.rankings_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize season schedule
        self.season = MLBSeasonSchedule(datetime.now().year)
        
        # Email configuration (Postmark)
        self.email_config = {
            'smtp_server': 'smtp.postmarkapp.com',
            'smtp_port': 587,
            'sender_email': '2eef09f5-6e2d-4b31-a034-0b33b7754e10',  # API Token as username
            'sender_password': '2eef09f5-6e2d-4b31-a034-0b33b7754e10',  # API Token as password
            'from_address': 'chunghao_lee@wistron.com',  # Your verified sender address
            'recipients': ['lch99310@gmail.com']  # Where you want to receive the reports
        }
    
    def validate_email_config(self):
        """Validate email configuration"""
        required_keys = ['smtp_server', 'smtp_port', 'sender_email', 
                        'sender_password', 'recipients']
        
        missing_keys = [key for key in required_keys 
                       if not self.email_config.get(key)]
        
        if missing_keys:
            raise ValueError(f"Missing required email configuration: {missing_keys}")
        
        if not isinstance(self.email_config['recipients'], list):
            raise ValueError("Recipients must be a list of email addresses")
    
    def validate_data(self, df, stage=""):
        """Validate that DataFrame has required columns"""
        required_columns = {
            'raw': ['game_date', 'batter', 'estimated_woba_using_speedangle', 'woba_value', 'woba_denom'],
            'processed': ['game_date', 'batter', 'first_name', 'last_name', 'estimated_woba_using_speedangle', 
                         'woba_value', 'rolling_100PA_xwOBA', 'rolling_100PA_wOBA', 'diff_rolling_OBA']
        }
        
        if stage in required_columns:
            missing_cols = [col for col in required_columns[stage] if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns for {stage} data: {missing_cols}")
    
    def fetch_data(self, start_date, end_date, force_refresh=False):
        """Fetch Statcast data for the specified date range"""
        output_file = self.raw_dir / f"statcast_{start_date}_to_{end_date}.csv"
        
        if output_file.exists() and not force_refresh:
            self.logger.info(f"Using existing data file: {output_file}")
            data = pd.read_csv(output_file)
            self.validate_data(data, "raw")
            return output_file
        
        self.logger.info(f"Fetching data from {start_date} to {end_date}")
        data = get_filtered_daily_statcast_data(start_date, end_date)
        
        if not data.empty:
            data = add_player_names(data)
            self.validate_data(data, "raw")
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
            self.validate_data(processed_df, "processed")
            processed_df.to_csv(output_file, index=False)
            self.logger.info(f"Processed data saved to {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")
            return None
    
    def analyze_rankings(self, processed_file):
        """Analyze player rankings from processed data"""
        self.logger.info(f"Analyzing player rankings from {processed_file}")
        try:
            df = pd.read_csv(processed_file)
            underestimated, overestimated = analyze_player_estimations(df)
            return underestimated, overestimated
        except Exception as e:
            self.logger.error(f"Error analyzing rankings: {e}")
            raise
    
    def prepare_email_report(self, processed_df, underestimated_players):
        """Prepare data for email report"""
        latest_date = underestimated_players['game_date'].max()
        today_top_players = underestimated_players[
            underestimated_players['game_date'] == latest_date
        ].sort_values('rank')
        
        players_data = []
        for _, row in today_top_players.iterrows():
            player_df = processed_df[
                (processed_df['first_name'] + ' ' + processed_df['last_name']) == row['player_name']
            ].copy()
            
            if not player_df.empty:
                # Create plot
                plot_bytes = BaseballReportEmailer(
                    None, None, None, None
                ).create_player_plot(player_df)
                
                players_data.append({
                    'name': row['player_name'],
                    'rolling_woba': player_df['rolling_100PA_wOBA'].iloc[-1],
                    'diff_oba': row['diff_rolling_OBA'] / 100,  # Convert back from percentage
                    'plot_bytes': plot_bytes
                })
            else:
                self.logger.warning(f"No data found for player: {row['player_name']}")
        
        return players_data, latest_date
    
    def send_email_report(self, processed_file, underestimated_players):
        """Send email report with top underestimated players"""
        self.logger.info("Preparing and sending email report")
        try:
            self.validate_email_config()
            
            # Read processed data
            processed_df = pd.read_csv(processed_file)
            
            # Prepare report data
            players_data, report_date = self.prepare_email_report(
                processed_df, underestimated_players
            )
            
            if not players_data:
                self.logger.warning("No player data to report")
                return
            
            # Initialize emailer and send report
            emailer = BaseballReportEmailer(
                self.email_config['smtp_server'],
                self.email_config['smtp_port'],
                self.email_config['sender_email'],
                self.email_config['sender_password'],
                self.email_config['from_address']  # Add this line
            )
            
            emailer.send_report(
                self.email_config['recipients'],
                players_data,
                report_date
            )
            
            self.logger.info(f"Email report sent successfully for {report_date}")
            
        except Exception as e:
            self.logger.error(f"Error sending email report: {e}")
            raise

def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(description="Baseball Data Analysis Workflow")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh existing data")
    parser.add_argument("--skip-email", action="store_true", help="Skip sending email report")
    parser.add_argument("--test-email", action="store_true",
                      help="Send test email regardless of game day")
    
    args = parser.parse_args()
    
    try:
        # Initialize and run workflow
        workflow = BaseballDataWorkflow()
        
        # Check if it's a game day (if end_date is today)
        today = date.today().strftime('%Y-%m-%d')
        is_game_day = args.test_email or (
            args.end_date == today and workflow.season.is_game_day(date.today())
        )
        
        # Execute workflow steps
        raw_data_file = workflow.fetch_data(
            args.start_date, args.end_date, args.force_refresh
        )
        
        if raw_data_file:
            processed_file = workflow.process_data(raw_data_file)
            if processed_file:
                # Analyze rankings
                underestimated, overestimated = workflow.analyze_rankings(processed_file)
                
                # Save rankings
                rankings_date = args.end_date.replace('-', '')
                underestimated.to_csv(
                    f'data/rankings/underestimated_players_{rankings_date}.csv', 
                    index=False
                )
                overestimated.to_csv(
                    f'data/rankings/overestimated_players_{rankings_date}.csv', 
                    index=False
                )
                
                # Send email report if it's a game day and email is not skipped
                if is_game_day and not args.skip_email:
                    workflow.send_email_report(processed_file, underestimated)
                elif not is_game_day:
                    workflow.logger.info("Skipping email report - not a game day")
                else:
                    workflow.logger.info("Skipping email report - --skip-email flag set")
                
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()