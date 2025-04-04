const { BigQuery } = require('@google-cloud/bigquery');
const { logger } = require('./logger');

// Initialize BigQuery client
const bigquery = new BigQuery();

// Cache for created tables
const createdTables = new Set();

/**
 * Create BigQuery table if it doesn't exist
 * 
 * @param {string} datasetId BigQuery dataset ID 
 * @param {string} tableId BigQuery table ID
 */
async function ensureTableExists(datasetId, tableId) {
  // Check if we've already created this table in this session
  const tableKey = `${datasetId}.${tableId}`;
  if (createdTables.has(tableKey)) {
    return;
  }
  
  const dataset = bigquery.dataset(datasetId);
  const table = dataset.table(tableId);
  
  try {
    // Check if table exists
    const [exists] = await table.exists();
    
    if (!exists) {
      // Define table schema
      const schema = [
        { name: 'timestamp', type: 'TIMESTAMP' },
        { name: 'symbol', type: 'STRING' },
        { name: 'bid', type: 'FLOAT' },
        { name: 'ask', type: 'FLOAT' },
        { name: 'spread', type: 'FLOAT' }
      ];
      
      // Create table with time partitioning
      const options = {
        schema: schema,
        timePartitioning: {
          type: 'DAY',
          field: 'timestamp'
        }
      };
      
      logger.info(`Creating BigQuery table ${datasetId}.${tableId}`);
      await dataset.createTable(tableId, options);
      logger.info(`Created BigQuery table ${datasetId}.${tableId}`);
    }
    
    // Add to cache
    createdTables.add(tableKey);
    
  } catch (error) {
    logger.error(`Error creating BigQuery table: ${error.message}`);
    throw error;
  }
}

/**
 * Save data to BigQuery
 * 
 * @param {Object} data Record to insert
 * @param {string} datasetId BigQuery dataset ID
 * @param {string} tableId BigQuery table ID
 */
async function saveToBigQuery(data, datasetId, tableId) {
  try {
    // Ensure table exists
    await ensureTableExists(datasetId, tableId);
    
    // Format timestamp if it's an ISO string
    if (typeof data.timestamp === 'string') {
      data.timestamp = new Date(data.timestamp);
    }
    
    // Insert data
    const rows = [data];
    await bigquery.dataset(datasetId).table(tableId).insert(rows);
    
    return true;
  } catch (error) {
    logger.error(`BigQuery insert error: ${error.message}`);
    throw error;
  }
}

module.exports = {
  saveToBigQuery
};