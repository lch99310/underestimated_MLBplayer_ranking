import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_baseball_stats_final(data):
    """
    Create baseball stats visualization for a player's data.
    
    Args:
        data (pd.DataFrame): DataFrame containing player statistics
    
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    # Create sequential PA index
    data = data.reset_index(drop=True)
    data['PA_number'] = range(1, len(data) + 1)
    
    # Get player name for title
    player_name = f"{data['first_name'].iloc[0].title()} {data['last_name'].iloc[0].title()}"
    
    # Get date range
    start_date = pd.to_datetime(data['game_date'].min()).strftime('%Y-%m-%d')
    end_date = pd.to_datetime(data['game_date'].max()).strftime('%Y-%m-%d')
    
    # Create figure with two subplots sharing x-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
    fig.subplots_adjust(hspace=0.1)  # Reduce space between subplots
    
    # Plot rolling statistics in top subplot
    ax1.plot(data['PA_number'], data['rolling_100PA_xwOBA'], 
             color='black', label='Rolling xwOBA (100PAs)', linewidth=2)
    ax1.plot(data['PA_number'], data['rolling_100PA_wOBA'], 
             color='#2775B6', label='Rolling wOBA (100PAs)', linewidth=2, alpha=0.6)
    
    # Customize top subplot
    ax1.set_title(player_name, pad=20)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_xticklabels([])  # Remove x-axis labels from top subplot
    
    # Set y-axis limits and ticks for top subplot
    ax1.set_ylim(0.000, 0.900)
    ax1.set_yticks(np.arange(0.000, 0.901, 0.100))
    ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
    
    # Plot diff_OBA bars in bottom subplot
    pos_mask = data['diff_OBA'] >= 0
    neg_mask = data['diff_OBA'] < 0
    
    ax2.bar(data.loc[pos_mask, 'PA_number'], 
            data.loc[pos_mask, 'diff_OBA'],
            color='red', alpha=0.6)
    ax2.bar(data.loc[neg_mask, 'PA_number'],
            data.loc[neg_mask, 'diff_OBA'],
            color='green', alpha=0.6)
    
    # Plot rolling diff_OBA
    ax2.plot(data['PA_number'], data['rolling_100PA_diff_OBA'], 
             color='orange', alpha=0.8, linewidth=1.5)
    
    # Customize bottom subplot
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel('Plate Appearances')
    
    # Add date range to bottom subplot
    ax2.text(data['PA_number'].min(), -1.2, start_date, 
             ha='left', va='top', rotation=45)
    ax2.text(data['PA_number'].max(), -1.2, end_date, 
             ha='right', va='top', rotation=45)
    
    # Set y-axis limits for bottom subplot
    ax2.set_ylim(-1, 1)
    
    # Ensure x-axis limits are the same for both subplots
    ax1.set_xlim(data['PA_number'].min(), data['PA_number'].max())
    ax2.set_xlim(data['PA_number'].min(), data['PA_number'].max())
    
    plt.tight_layout()
    
    return fig

# Only run this if the script is run directly (not imported)
if __name__ == "__main__":
    # Example usage for testing
    test_data = pd.read_csv('processed_baseball_stats.csv')
    fig = plot_baseball_stats_final(test_data)
    plt.show()