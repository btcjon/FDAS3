const groupedData = data.trades.reduce((acc, curr) => {
    // Use curr.comment as the key
    const key = curr.comment && curr.comment.trim() !== '' ? curr.comment : 'No Comment';
  
    if (!acc[key]) {
      acc[key] = {
        comment: curr.comment,
        volume: 0,
        profit: 0
      };
    }
  
    // Sum up volume and profit
    acc[key].volume += curr.volume;
    acc[key].profit += curr.profit;
  
    return acc;
  }, {});
  
  // Convert the grouped data object to an array
  const groupedDataArray = Object.values(groupedData);
  
  return groupedDataArray; // Return the transformed data