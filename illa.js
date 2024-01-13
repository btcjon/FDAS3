const groupedData = positions.data.reduce((acc, curr) => {
  const key = `${curr.symbol}-${curr.type}`;
  if (!acc[key]) {
    acc[key] = {
      primaryKey: key,
      symbol: curr.symbol,
      type: curr.type === 'POSITION_TYPE_BUY' ? 'buy' : 'sell',
      volume: 0,
      uProfit: 0,
      swap: 0,
    };
  }
  acc[key].volume += curr.volume;
  acc[key].uProfit += curr.unrealizedProfit;
  acc[key].swap += curr.swap;

  return acc;
}, {});

const groupedDataArray = Object.values(groupedData);

return groupedDataArray;