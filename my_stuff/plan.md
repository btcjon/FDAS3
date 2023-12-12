use retool.com to build dashboard from various metaapi data (API)

-positions table data from API data source in retool 'getmeta_api_positions'

-made "run js code" as data soure to manipulate data
/////
const groupedData = getmeta_api_positions.data.reduce((acc, curr) => {
  const key = `${curr.symbol}-${curr.type}`;
  if (!acc[key]) {
    acc[key] = {
      primaryKey: key,
      symbol: curr.symbol,
      type: curr.type === 'POSITION_TYPE_BUY' ? 'buy' : 'sell',
      volume: 0,
      uProfit: 0, // renamed from unrealizedProfit
      swap: 0,
      BE: curr.openPrice, // added openPrice and renamed to BE
      time: curr.time, // Initialize time with the current item's time
      currentPrice: curr.currentPrice, // Initialize currentPrice with the current item's currentPrice
      // Add other fields as needed
    };
  }
  acc[key].volume += curr.volume;
  acc[key].uProfit += curr.unrealizedProfit; // renamed from unrealizedProfit
  acc[key].swap += curr.swap;
  acc[key].BE = (acc[key].BE * acc[key].volume + curr.openPrice * curr.volume) / (acc[key].volume + curr.volume); // calculate average openPrice
  acc[key].currentPrice = curr.currentPrice; // Update currentPrice with the current item's currentPrice
  acc[key]['%diff'] = acc[key].type === 'buy' ? 
    -((acc[key].currentPrice - acc[key].BE) / acc[key].currentPrice) * 100 : 
    ((acc[key].currentPrice - acc[key].BE) / acc[key].currentPrice) * 100; // calculate %diff based on type

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
////

-metric components

statistic
    - today: % gain