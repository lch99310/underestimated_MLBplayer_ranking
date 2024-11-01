# baseball_workflow.py
import os
import pandas as pd
from datetime import datetime, date
import argparse
import logging
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

# Import the functions from other scripts
from get_daily_statcast_data import get_filtered_daily_statcast_data, add_player_names
from baseball_data_processor import process_baseball_data
from baseball_plotting import plot_baseball_stats_final
from baseball_ranking import analyze_player_estimations

class BaseballDataWorkflow:
    def __init__(self):
        """Initialize the workflow with web-oriented directory structure"""
        # Setup directory structure
        self.base_dir = Path(__file__).parent
        self.raw_dir = self.base_dir / "data/raw"
        self.processed_dir = self.base_dir / "data/processed"
        self.plots_dir = self.base_dir / "data/plots"
        self.rankings_dir = self.base_dir / "data/rankings"
        self.frontend_dir = self.base_dir / "frontend"
        self.docs_dir = self.base_dir / "docs"
        self.docs_api_dir = self.docs_dir / "api"
        self.docs_plots_dir = self.docs_dir / "plots"
        
        # Create directories if they don't exist
        for directory in [self.raw_dir, self.processed_dir, self.plots_dir, 
                         self.rankings_dir, self.frontend_dir, 
                         self.docs_dir, self.docs_api_dir, self.docs_plots_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize latest processed file path
        self.latest_processed_file = None

    def fetch_data(self, start_date, end_date, force_refresh=False):
        """Fetch Statcast data for the specified date range"""
        try:
            output_file = self.raw_dir / f"statcast_{start_date}_to_{end_date}.csv"
            
            if output_file.exists() and not force_refresh:
                self.logger.info(f"Using existing data file: {output_file}")
                return output_file
            
            self.logger.info(f"Fetching data from {start_date} to {end_date}")
            data = get_filtered_daily_statcast_data(start_date, end_date)
            
            if isinstance(data, pd.DataFrame) and not data.empty:
                data = add_player_names(data)
                data.to_csv(output_file, index=False)
                self.logger.info(f"Data saved to {output_file}")
                return output_file
            else:
                self.logger.error("No data retrieved or invalid data format")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in fetch_data: {e}")
            raise

    def process_data(self, input_file):
        """Process the raw baseball data"""
        try:
            output_file = self.processed_dir / f"processed_{Path(input_file).name}"
            
            self.logger.info(f"Processing data from {input_file}")
            
            # Read the input file
            if not Path(input_file).exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
                
            # Convert Path to string for pd.read_csv
            input_file_str = str(input_file)
            processed_df = process_baseball_data(input_file_str)
            
            # Save processed data
            processed_df.to_csv(output_file, index=False)
            self.logger.info(f"Processed data saved to {output_file}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Error in process_data: {e}")
            raise

    def analyze_rankings(self, processed_file):
        """Analyze player rankings from processed data"""
        try:
            self.logger.info(f"Analyzing player rankings from {processed_file}")
            
            # Read processed data
            if not Path(processed_file).exists():
                raise FileNotFoundError(f"Processed file not found: {processed_file}")
                
            df = pd.read_csv(processed_file)
            underestimated, overestimated = analyze_player_estimations(df)
            
            return underestimated, overestimated
            
        except Exception as e:
            self.logger.error(f"Error in analyze_rankings: {e}")
            raise

    def save_static_data(self):
        """Save data as static JSON and plots for GitHub Pages"""
        if self.latest_processed_file:
            try:
                self.logger.info("Generating static data for GitHub Pages...")
                
                # Read processed data
                df = pd.read_csv(self.latest_processed_file)
                
                # Log available columns for debugging
                self.logger.info(f"Available columns: {df.columns.tolist()}")
                
                underestimated, _ = analyze_player_estimations(df)
                
                # Get latest date's top 5 players
                latest_date = underestimated['game_date'].max()
                top_5_players = underestimated[
                    underestimated['game_date'] == latest_date
                ].head(5)
                
                # Create static data structure
                static_data = {
                    'date': latest_date,
                    'players': []
                }
                
                # Process each player
                for _, player in top_5_players.iterrows():
                    # Generate unique filename for plot
                    plot_filename = f"player_{hash(player['player_name'])}.png"
                    plot_path = self.docs_plots_dir / plot_filename
                    
                    # Get player data and create plot
                    player_df = df[
                        (df['first_name'] + ' ' + df['last_name']) == player['player_name']
                    ]
                    
                    if not player_df.empty:
                        # Create and save plot
                        fig = plot_baseball_stats_final(player_df)
                        fig.savefig(plot_path, bbox_inches='tight')
                        plt.close(fig)
                        
                        # Add player data to static data
                        player_data = {
                            'player_id': hash(player['player_name']),
                            'player_name': player['player_name'],
                            'rolling_woba': float(player_df['woba_value'].iloc[-1]),  # Using last value
                            'diff_rolling_OBA': float(player['diff_rolling_OBA'])
                        }
                        static_data['players'].append(player_data)
                
                # Save JSON data
                json_path = self.docs_api_dir / 'baseball-stats.json'
                with open(json_path, 'w') as f:
                    json.dump(static_data, f, indent=2)
                
                self.logger.info(f"Static data saved to {self.docs_dir}")
                self.logger.info(f"JSON data saved to {json_path}")
                self.logger.info(f"Plots saved to {self.docs_plots_dir}")
                
            except Exception as e:
                self.logger.error(f"Error saving static data: {e}")
                raise

    def process_and_save_data(self, start_date, end_date, force_refresh=False):
        """Process data and save results"""
        try:
            # Fetch and process data
            raw_data_file = self.fetch_data(start_date, end_date, force_refresh)
            if raw_data_file:
                processed_file = self.process_data(raw_data_file)
                if processed_file:
                    self.latest_processed_file = processed_file
                    # Analyze rankings
                    underestimated, overestimated = self.analyze_rankings(processed_file)
                    
                    # Save rankings
                    rankings_date = end_date.replace('-', '')
                    underestimated_path = self.rankings_dir / f'underestimated_players_{rankings_date}.csv'
                    overestimated_path = self.rankings_dir / f'overestimated_players_{rankings_date}.csv'
                    
                    underestimated.to_csv(underestimated_path, index=False)
                    overestimated.to_csv(overestimated_path, index=False)
                    
                    # Save static data for GitHub Pages
                    self.save_static_data()
                    
                    self.logger.info(f"Data processing completed. Results saved in {self.rankings_dir}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error in process_and_save_data: {e}")
            raise

    def initialize_api(self):
            """Initialize FastAPI application"""
            app = FastAPI()
            
            # Add CORS middleware
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Mount static files directory for plots
            app.mount("/plots", StaticFiles(directory=str(self.plots_dir)), name="plots")
            
            @app.get("/api/baseball-stats")
            async def get_baseball_stats():
                try:
                    if not self.latest_processed_file:
                        return {"error": "No processed data available"}
                        
                    df = pd.read_csv(self.latest_processed_file)
                    underestimated, _ = analyze_player_estimations(df)
                    
                    latest_date = underestimated['game_date'].max()
                    top_5_players = underestimated[
                        underestimated['game_date'] == latest_date
                    ].head(5)
                    
                    players_list = []
                    for _, player in top_5_players.iterrows():
                        # Generate plot
                        plot_filename = f"player_{hash(player['player_name'])}.png"
                        plot_path = self.plots_dir / plot_filename
                        
                        # Get player data and create plot
                        player_df = df[
                            (df['first_name'] + ' ' + df['last_name']) == player['player_name']
                        ]
                        
                        if not player_df.empty:
                            # Create and save plot
                            fig = plot_baseball_stats_final(player_df)
                            fig.savefig(plot_path, bbox_inches='tight')
                            plt.close(fig)
                        
                        player_data = {
                            'player_id': str(hash(player['player_name'])),
                            'player_name': player['player_name'],
                            'rolling_woba': float(player_df['woba_value'].iloc[-1]),
                            'diff_rolling_OBA': float(player['diff_rolling_OBA'])
                        }
                        players_list.append(player_data)
                    
                    return {
                        "date": latest_date,
                        "players": players_list
                    }
                
                except Exception as e:
                    self.logger.error(f"Error in get_baseball_stats: {e}")
                    print(f"Detailed error: {str(e)}")  # Add detailed error logging
                    return {"error": str(e)}
            
            @app.get("/")
            async def root():
                return {"message": "Baseball Stats API is running"}
                
            return app

def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(description="Baseball Data Analysis Workflow")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh existing data")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    
    args = parser.parse_args()
    
    try:
        # Initialize workflow
        workflow = BaseballDataWorkflow()
        
        # Process data
        success = workflow.process_and_save_data(
            args.start_date, 
            args.end_date,
            args.force_refresh
        )
        
        if success:
            # Initialize and start the API server
            app = workflow.initialize_api()
            
            # Start the server
            uvicorn.run(app, host="0.0.0.0", port=args.port)
        else:
            workflow.logger.error("Data processing failed")
            
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()