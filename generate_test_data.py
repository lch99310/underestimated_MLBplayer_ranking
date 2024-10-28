import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_data():
    """Generate test baseball data for the 2024 season"""
    # Generate dates for 2024 season
    start_date = datetime(2024, 3, 20)
    end_date = datetime(2024, 9, 29)
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    # Create sample players
    players = [
        (660271, "Shohei", "Ohtani"),
        (641343, "Max", "Muncy"),
        (624413, "Mookie", "Betts"),
        (665487, "Trea", "Turner"),
        (514888, "Mike", "Trout"),
        (592450, "Marcus", "Semien"),
        (605141, "Manny", "Machado"),
        (621043, "Juan", "Soto"),
        (545361, "Mike", "Zunino"),
        (543939, "Kyle", "Tucker")
    ]

    # Generate sample data
    data = []
    for date in dates:
        for batter_id, first_name, last_name in players:
            # Generate random stats
            woba_value = np.random.normal(0.320, 0.050)
            estimated_woba = np.random.normal(woba_value, 0.030)
            woba_denom = np.random.randint(1, 5)

            data.append({
                'game_date': date,
                'batter': batter_id,
                'first_name': first_name,
                'last_name': last_name,
                'estimated_woba_using_speedangle': max(0, min(1, estimated_woba)),
                'woba_value': max(0, min(1, woba_value)),
                'woba_denom': woba_denom
            })

    # Create DataFrame
    df = pd.DataFrame(data)
    return df

def main():
    """Generate and save test data"""
    # Generate test data
    df = generate_test_data()
    
    # Save raw data
    raw_file = 'data/raw/statcast_2024-03-20_to_2024-09-29.csv'
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv(raw_file, index=False)
    print(f"Test data saved to {raw_file}")

if __name__ == "__main__":
    import os
    main()