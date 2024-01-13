const groupedData = data.reduce((acc, curr) => {
  // Define the comments that should be considered as 'B'
  const commentsToGroup = ['AW Recovery Average', '7-0-30', '"7-0-30"', '6-4-30', 'P2-1'];
  
  // Check if the current comment is in the list or contains 'PineConnector', 'from', 'B', or is null/undefined/empty
  const comment = (!curr.comment || 
                   commentsToGroup.includes(curr.comment) || 
                   curr.comment.includes('PineConnector') || 
                   curr.comment.includes('from') ||
                   curr.comment.includes('B')) ? 'B' : curr.comment;
  
  const key = `${curr.symbol}-${curr.type}-${comment}`; // Use the modified comment
  if (!acc[key]) {
    // Remove '.PRO' from the symbol and generate the URL
    const symbolWithoutPro = curr.symbol.replace('.PRO', '');
    let url;
  
    if (curr.symbol === 'EURAUD.PRO' && comment === 'B') {
      url = `https://www.tradingview.com/chart/3wMgwNbG/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.symbol === 'NZDJPY.PRO' && comment === 'B') {
      url = `https://www.tradingview.com/chart/AxMGqmD8/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.symbol === 'AUDCAD.PRO' && comment === 'B') {
      url = `https://www.tradingview.com/chart/EVWCVx6R/?symbol=PEPPERSTONE:${symbolWithoutPro}`;  
    } else if (curr.symbol === 'AUDNZD.PRO' && comment === 'B') {
      url = `https://www.tradingview.com/chart/o0ZgIGtv/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.comment && curr.comment.includes('7-1')) {
      url = `https://www.tradingview.com/chart/LeiDEXcK/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.comment && curr.comment.includes('7-3')) {
      url = `https://www.tradingview.com/chart/FqN1nxSD/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.comment && curr.comment.includes('L2L')) {
      url = `https://www.tradingview.com/chart/IRxIFKHd/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else if (curr.comment && curr.comment.includes('L2S')) {
      url = `https://www.tradingview.com/chart/8RukpZhB/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    } else {
      url = `https://www.tradingview.com/chart/C7Pl8ZeK/?symbol=PEPPERSTONE:${symbolWithoutPro}`;
    }



    acc[key] = {
      primaryKey: key,
      symbol: curr.symbol,
      type: curr.type === 'POSITION_TYPE_BUY' ? 'long' : 'short',
      comment: comment, // Use the modified comment
      volume: 0,
      Net: curr.unrealizedProfit + curr.unrealizedSwap, 
      profit: curr.profit, // Added 'profit' field
      uProfit: 0,
      rProfit: curr.realizedProfit, // Added 'rProfit' (realizedProfit) field
      swap: 0,
      uSwap: curr.unrealizedSwap, // Added 'uSwap' (unrealizedSwap) field
      rSwap: curr.realizedSwap, // Added 'rSwap' (realizedSwap) field
      BE: curr.openPrice,
      time: curr.time,
      currentPrice: curr.currentPrice,
      url: url,
    };
  }
  acc[key].volume += curr.volume;
  acc[key].Net += curr.unrealizedProfit + curr.unrealizedSwap; 
  acc[key].profit += curr.profit; // Added 'profit' field
  if (typeof curr.unrealizedProfit === 'number') {
    acc[key].uProfit += curr.unrealizedProfit; // renamed from unrealizedProfit
  }
  acc[key].rProfit += curr.realizedProfit; // Added 'rProfit' (realizedProfit) field
  acc[key].swap += curr.swap;
  acc[key].uSwap += curr.unrealizedSwap; // Added 'uSwap' (unrealizedSwap) field
  acc[key].rSwap += curr.realizedSwap; // Added 'rSwap' (realizedSwap) field
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

console.log(groupedData); // Log the output of the reduce function

// Convert the grouped data object to an array
const groupedDataArray = Object.values(groupedData);

console.log(groupedDataArray); // Log the final output

return groupedDataArray;
