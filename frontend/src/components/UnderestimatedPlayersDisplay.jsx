import React, { useEffect, useState } from 'react';

const UnderestimatedPlayersDisplay = () => {
  const [playersData, setPlayersData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBaseballData = async () => {
      try {
        // Log the fetch attempt
        console.log('Fetching data from API...');
        
        const response = await fetch('https://lch99310.github.io/underestimated_MLBplayer_ranking/api/baseball-stats');
        console.log('Response received:', response);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Data received:', data);
        
        if (!data || !data.players) {
          throw new Error('Invalid data format received');
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

  // Rest of your component remains the same...
};

export default UnderestimatedPlayersDisplay;