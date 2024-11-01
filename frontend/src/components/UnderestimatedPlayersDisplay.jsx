import React, { useEffect, useState } from 'react';

const UnderestimatedPlayersDisplay = () => {
  const [playersData, setPlayersData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBaseballData = async () => {
      try {
        console.log('Attempting to fetch data...');
        const response = await fetch('http://localhost:8000/api/baseball-stats');
        console.log('Response:', response);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch data: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        if (data.error) {
          throw new Error(data.error);
        }
        
        if (!data.players || !Array.isArray(data.players)) {
          throw new Error('Invalid data format: players array not found');
        }
        
        setPlayersData(data.players);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchBaseballData();
  }, []);

  const renderPlayerStats = (player, index) => {
    return (
      <div key={index} className="mb-8 p-6 bg-white rounded-lg shadow-lg">
        <div className="mb-4">
          <h2 className="text-xl font-bold">
            {index + 1}. Player name: {player.player_name}
          </h2>
        </div>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">100PA rolling wOBA</p>
            <p className="text-2xl font-bold">
              {typeof player.rolling_woba === 'number' 
                ? player.rolling_woba.toFixed(3) 
                : 'N/A'}
            </p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">diff_rolling_OBA</p>
            <p className="text-2xl font-bold">
              {typeof player.diff_rolling_OBA === 'number'
                ? player.diff_rolling_OBA.toFixed(3)
                : 'N/A'}%
            </p>
          </div>
        </div>
        {player.player_id && (
          <div className="w-full">
            <img 
              src={`http://localhost:8000/plots/player_${player.player_id}.png`}
              alt={`Statistics for ${player.player_name}`}
              className="w-full h-auto"
              onError={(e) => {
                console.error('Error loading image:', e);
                e.target.style.display = 'none';
              }}
            />
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-xl">Loading baseball statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-xl text-red-600">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-100 min-h-screen">
      <h1 className="text-4xl font-bold mb-2 text-center">
        Top 5 Most MLB Underestimated Players
      </h1>
      <h2 className="text-xl mb-8 text-center">
        November 1 - 2024
      </h2>
      <div className="space-y-6">
        {playersData && playersData.length > 0 ? (
          playersData.map((player, index) => renderPlayerStats(player, index))
        ) : (
          <p className="text-center text-gray-600">No player data available</p>
        )}
      </div>
    </div>
  );
};

export default UnderestimatedPlayersDisplay;