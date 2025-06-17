const {
  EventStoreDBClient,
  jsonEvent,
} = require("@eventstore/db-client");

const endpoint   = process.env.ESDB_ENDPOINT || "eventstore:2113";
const insecure   = process.env.ESDB_TLS === "false";
const client     = EventStoreDBClient.connectionString`esdb://${endpoint}?tls=${!insecure}`;

module.exports   = { client, jsonEvent };
