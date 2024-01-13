const groupedData = getmeta_api_positions.data.reduce((acc, curr) => {
    // Define the comments that should be considered as 'B'
    const commentsToGroup = ['AW Recovery Average', '7-0-30', '"7-0-30"', '6-4-30'];
    
    // Check if the current comment is in the list or contains 'PineConnector' or 'from'
    const comment = curr.comment && (commentsToGroup.includes(curr.comment) || curr.comment.includes('PineConnector') || curr.comment.includes('from')) ? 'B' : curr.comment;
    
    const key = `${curr.symbol}-${curr.type}-${comment}`; // Use the modified comment
    if (!acc[key]) {
      acc[key] = {
        primaryKey: key,
        symbol: curr.symbol,
        type: curr.type === 'POSITION_TYPE_BUY' ? 'buy' : 'sell',
        comment: comment, // Use the modified comment
        volume: 0,
        uProfit: 0,
        swap: 0,
        BE: curr.openPrice,
        time: curr.time,
        currentPrice: curr.currentPrice,
      };
    }
    acc[key].volume += curr.volume;
    acc[key].uProfit += curr.unrealizedProfit; // renamed from unrealizedProfit
    acc[key].swap += curr.swap;
    acc[key].BE = (acc[key].BE * acc[key].volume + curr.openPrice * curr.volume) / (acc[key].volume + curr.volume); // calculate average openPrice
    acc[key].currentPrice = curr.currentPrice; // Update currentPrice with the current item's currentPrice
    acc[key]['%diff'] = acc[key].type === 'sell' ? 
      (acc[key].currentPrice - acc[key].BE) / acc[key].BE : 
      -(acc[key].currentPrice - acc[key].BE) / acc[key].BE;
  
    // Update time if the current item's time is older
    if (new Date(curr.time) < new Date(acc[key].time)) {
      acc[key].time = curr.time;
    }
  
    // Add other aggregations as needed
    return acc;
  }, {});
  
  // Calculate 'Days' for each group
  const currentDate = new Date();
  for (let key in groupedData) {
    const groupTime = new Date(groupedData[key].time);
    const timeDiff = Math.abs(currentDate - groupTime);
    groupedData[key].Days = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)); // Convert time difference from milliseconds to days
  }
  
  // Convert the grouped data object to an array
  const groupedDataArray = Object.values(groupedData);
  
  return groupedDataArray;