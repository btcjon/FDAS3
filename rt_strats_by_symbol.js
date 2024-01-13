const groupedData = data.trades.reduce((acc, curr) => {
    // Transform type
    const type = curr.type === 'DEAL_TYPE_BUY' ? 'long' : 'short';
    
    // If curr.comment is a non-empty string, include it in the key, otherwise group by symbol and type only
    const key = curr.comment && curr.comment.trim() !== '' ? `${curr.comment}-${curr.symbol}-${type}` : `${curr.symbol}-${type}`;
  
    if (!acc[key]) {
      acc[key] = {
        symbol: curr.symbol,
        type: type,
        comment: curr.comment,
        volume: 0,
        profit: 0,
        durationInMinutes: 0,
        closeTime: curr.closeTime // Initialize closeTime
      };
    } else if (new Date(curr.closeTime) > new Date(acc[key].closeTime)) {
      // If the current closeTime is newer, update it
      acc[key].closeTime = curr.closeTime;
    }
  
    // Sum up volume, durationInMinutes, and profit
    acc[key].volume += curr.volume;
    acc[key].durationInMinutes += curr.durationInMinutes;
    acc[key].profit += curr.profit;
  
    return acc;
  }, {});
  
  // Convert the grouped data object to an array
  const groupedDataArray = Object.values(groupedData);

  // Sort the array by closeTime in descending order
  groupedDataArray.sort((a, b) => new Date(b.closeTime) - new Date(a.closeTime));
  
  return groupedDataArray; // Return the sorted data
