require('dotenv').config();
const WebSocket = require('ws');
const express = require('express');
const { logger } = require('./utils/logger');
const { saveToBigQuery } = require('./utils/storage');

// Express app for health checks
const app = express();
const PORT = process.env.PORT || 8080;

// Configuration from environment variables
const MT5_SERVER_URL = process.env.MT5_SERVER_URL || 'ws://34.87.87.53:8765';
const FOREX_SYMBOLS = (process.env.FOREX_SYMBOLS || 'EURUSD,GBPUSD,USDJPY').split(',');
const STORAGE_TYPE = (process.env.STORAGE_TYPE || 'bigquery').toLowerCase();
const BQ_DATASET_ID = process.env.BQ_DATASET_ID;
const BQ_TABLE_ID = process.env.BQ_TABLE_ID || 'forex_prices';

// Flag to control the running state
let running = true;
let wsConnection = null;
let reconnectTimeout = null;

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    connectionStatus: wsConnection && wsConnection.readyState === WebSocket.OPEN ? 'connected' : 'disconnected',
    serverUrl: MT5_SERVER_URL,
    symbols: FOREX_SYMBOLS,
    storageType: STORAGE_TYPE
  });
});

// Start HTTP server for health checks
const server = app.listen(PORT, () => {
  logger.info(`HTTP server listening on port ${PORT}`);
});

// Function to handle process termination
function handleTermination() {
  logger.info('Received termination signal. Starting graceful shutdown...');
  running = false;
  
  // Clear any pending reconnect
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
  }
  
  // Close WebSocket connection if it exists
  if (wsConnection) {
    try {
      // Send unsubscribe message if connection is open
      if (wsConnection.readyState === WebSocket.OPEN) {
        const unsubscribeMessage = {
          type: 'subscription',
          action: 'unsubscribe',
          symbols: FOREX_SYMBOLS
        };
        wsConnection.send(JSON.stringify(unsubscribeMessage));
        logger.info('Unsubscribed from symbols');
      }
      
      // Close the connection
      wsConnection.close();
    } catch (err) {
      logger.error(`Error during WebSocket shutdown: ${err.message}`);
    }
  }
  
  // Close HTTP server
  server.close(() => {
    logger.info('HTTP server closed');
    process.exit(0);
  });
  
  // Force exit if not closed within 3 seconds
  setTimeout(() => {
    logger.warn('Forcing exit after timeout');
    process.exit(1);
  }, 3000);
}

// Register signal handlers
process.on('SIGINT', handleTermination);
process.on('SIGTERM', handleTermination);

// Function to subscribe to forex symbols
function subscribeToSymbols(ws) {
  const subscriptionMessage = {
    type: 'subscription',
    action: 'subscribe',
    symbols: FOREX_SYMBOLS
  };
  
  ws.send(JSON.stringify(subscriptionMessage));
  logger.info(`Subscribed to symbols: ${FOREX_SYMBOLS.join(', ')}`);
}

// Function to process price updates
async function processPriceUpdate(data) {
  const symbol = data.symbol;
  const timestamp = data.timestamp;
  const bid = data.bid;
  const ask = data.ask;
  const spread = data.spread || (ask - bid);
  
  if (STORAGE_TYPE === 'bigquery' && BQ_DATASET_ID) {
    // Prepare data for BigQuery
    const bqRecord = {
      timestamp: timestamp,
      symbol: symbol,
      bid: bid,
      ask: ask,
      spread: spread
    };
    
    try {
      await saveToBigQuery(bqRecord, BQ_DATASET_ID, `${BQ_TABLE_ID}_${symbol.toLowerCase()}`);
      logger.debug(`Saved ${symbol} price data to BigQuery ${BQ_DATASET_ID}.${BQ_TABLE_ID}_${symbol.toLowerCase()}`);
    } catch (err) {
      logger.error(`Error saving to BigQuery: ${err.message}`);
    }
  } else {
    logger.warn(`Storage type ${STORAGE_TYPE} not configured or supported`);
  }
}

// Function to connect to MT5 WebSocket server
function connectToMT5Server() {
  if (!running) return;
  
  logger.info(`Connecting to MT5 WebSocket server at ${MT5_SERVER_URL}`);
  
  // Create new WebSocket connection
  const ws = new WebSocket(MT5_SERVER_URL);
  wsConnection = ws;
  
  // Initial reconnect delay in milliseconds
  let reconnectDelay = 5000;
  const maxReconnectDelay = 60000;
  
  // WebSocket event handlers
  ws.on('open', () => {
    logger.info('Connected to MT5 WebSocket server');
    // Reset reconnect delay on successful connection
    reconnectDelay = 5000;
    // Subscribe to symbols
    subscribeToSymbols(ws);
  });
  
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      // Handle different types of messages
      if (data.type === 'price_update') {
        await processPriceUpdate(data);
      } else if (data.type === 'subscription_confirmation') {
        logger.info(`Subscription confirmed for: ${data.symbols.join(', ')}`);
      } else if (data.type === 'error') {
        logger.error(`Server error: ${data.message}`);
      } else {
        logger.debug(`Received other message: ${JSON.stringify(data)}`);
      }
    } catch (err) {
      logger.error(`Error processing message: ${err.message}`);
    }
  });
  
  ws.on('error', (error) => {
    logger.error(`WebSocket error: ${error.message}`);
  });
  
  ws.on('close', (code, reason) => {
    logger.warn(`WebSocket connection closed. Code: ${code}, Reason: ${reason}`);
    wsConnection = null;
    
    // Attempt to reconnect if still running
    if (running) {
      logger.info(`Reconnecting in ${reconnectDelay / 1000} seconds...`);
      
      // Set timeout for reconnection
      reconnectTimeout = setTimeout(() => {
        // Implement exponential backoff with maximum value
        reconnectDelay = Math.min(reconnectDelay * 1.5, maxReconnectDelay);
        connectToMT5Server();
      }, reconnectDelay);
    }
  });
}

// Validate required environment variables and start the client
async function main() {
  try {
    // Validate required environment variables
    if (STORAGE_TYPE === 'bigquery' && !BQ_DATASET_ID) {
      logger.error('BQ_DATASET_ID is required when STORAGE_TYPE is "bigquery"');
      process.exit(1);
    }
    
    // Log startup information
    logger.info(`Starting MT5 WebSocket client in ${STORAGE_TYPE} mode`);
    logger.info(`Server URL: ${MT5_SERVER_URL}`);
    logger.info(`Forex symbols: ${FOREX_SYMBOLS.join(', ')}`);
    
    // Start the connection
    connectToMT5Server();
    
  } catch (err) {
    logger.error(`Unhandled exception: ${err.message}`);
    process.exit(1);
  }
}

// Start the application
main().catch(err => {
  logger.error(`Fatal error: ${err.message}`);
  process.exit(1);
});