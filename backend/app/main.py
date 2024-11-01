from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
from baseball_data_processor import process_baseball_data
from baseball_ranking import analyze_player_estimations
from baseball_plotting import plot_baseball_stats_final
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = FastAPI()

@app.get("/api/baseball-stats")
async def get_baseball_stats():
    try:
        # Process the baseball data
        df = process_baseball_data('your_input_file.csv')
        
        # Get the underestimated players
        underestimated, _ = analyze_player_estimations(df)
        
        # Get the latest date's top 5 players
        latest_date = underestimated['game_date'].max()
        top_5_players = underestimated[underestimated['game_date'] == latest_date]
        
        # Format the response
        players_list = []
        for _, player in top_5_players.iterrows():
            player_data = {
                'player_id': hash(player['player_name']),  # Create a unique ID
                'player_name': player['player_name'],
                'rolling_woba': player['rolling_100PA_wOBA'],
                'diff_rolling_OBA': player['diff_rolling_OBA']
            }
            players_list.append(player_data)
            
        return players_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/baseball-plot/{player_id}")
async def get_player_plot(player_id: str):
    try:
        # Get the player's data
        df = process_baseball_data('your_input_file.csv')
        
        # Filter for the specific player
        player_data = df[df['player_id'] == player_id]
        
        # Create the plot
        fig = plot_baseball_stats_final(player_data)
        
        # Save plot to bytes
        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format='png', bbox_inches='tight')
        plt.close(fig)
        img_bytes.seek(0)
        
        return FileResponse(img_bytes, media_type='image/png')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)