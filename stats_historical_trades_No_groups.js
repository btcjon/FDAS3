// Get the current date and time
let now = new Date();

// Subtract 7 hours from the current time to adjust for the server time
now.setHours(now.getHours() - 7);

// Create a new date for 5PM on the previous day in server time
let start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 22, 0, 0); // 22:00:00 is 5PM server time

// Convert the start and end times to ISO strings and remove the milliseconds
let startISO = start.toISOString().split('.')[0] + 'Z';
let nowISO = now.toISOString().split('.')[0] + 'Z';

// Generate the URL
let url = `https://metastats-api-v1.new-york.agiliumtrade.ai/users/current/accounts/28c98cc1-cc61-4220-8a39-e4896ad746a5/historical-trades/${startISO}/${nowISO}`;

return url;