const express = require("express");
const { Kafka, logLevel } = require("kafkajs");
const { client: esdb, jsonEvent } = require("./esdbClient");

const app = express();
const port = 3000;

const kafka = new Kafka({
  clientId: "action-node-service",
  brokers: ["kafka:9092"],
  logLevel: logLevel.INFO,
});

const consumer = kafka.consumer({ groupId: "node-consumer-group" });
const admin = kafka.admin();

const topics = ["autoCommand", "uiCommand"];

async function waitForTopic(topic, retries = 10, delay = 2000) {
  for (let i = 0; i < retries; i++) {
    try {
      const metadata = await admin.fetchTopicMetadata({ topics: [topic] });
      const topicData = metadata.topics.find(t => t.name === topic);
      if (topicData && topicData.partitions.length > 0) {
        return true;
      }
      console.log(`Topic '${topic}' exists but no partitions yet. Retrying...`);
    } catch (err) {
      if (err.type === 'UNKNOWN_TOPIC_OR_PARTITION') {
        console.log(`Topic '${topic}' not ready yet. Retry ${i + 1}/${retries}`);
      } else {
        console.error("Unexpected error while checking topic:", err);
        throw err;
      }
    }
    await new Promise(resolve => setTimeout(resolve, delay));
  }
  throw new Error(`Topic '${topic}' not available after ${retries} attempts`);
}

async function setupKafka() {
  await admin.connect();

  const existing = await admin.listTopics();

  for (const topic of topics) {
    if (!existing.includes(topic)) {
      await admin.createTopics({
        topics: [{ topic, numPartitions: 1, replicationFactor: 1 }],
        waitForLeaders: true,
      });
      console.log(`Topic '${topic}' created.`);
    } else {
      console.log(`Topic '${topic}' already exists.`);
    }

    await waitForTopic(topic);
  }

  await admin.disconnect();
}

async function startKafkaConsumer() {
  await setupKafka();
  await consumer.connect();

  for (const topic of topics) {
    await consumer.subscribe({ topic, fromBeginning: true });
  }

  await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
  console.log(`message obtained by action initializer from topic: ${topic}`)

  const rawValue = message.value.toString();
  let data;

  try {
    data = JSON.parse(rawValue);
  } catch (err) {
    console.error("Failed to parse Kafka message:", err);
    return;
  }

  try {
    const event = jsonEvent({
      type: topic,
      data: data,
    });

    await esdb.appendToStream(topic, event);
    console.log(`Event appended to EventStoreDB stream: ${topic}`);
  } catch (err) {
    console.error("Error writing to EventStoreDB:", err);
  }

  // 🚦 Обработка autoCommand
  if (topic === "autoCommand") {
    try {
      const fixedSteps = data.steps.replace(/'/g, '"');
      const steps = JSON.parse(fixedSteps);

      console.log("Running scenario steps...");
      steps.forEach(s =>
        console.log(`Automatization step ${s.order}: ${s.action} device ${s.deviceId} (${s.type})`)
      );
    } catch (err) {
      console.error("Failed to parse steps in autoCommand:", err);
    }
  }

  if (topic === "uiCommand") {
    console.log("uiCommand is obtained");
    console.log(`[${topic}] ${rawValue}`);
  }
}

});
}

startKafkaConsumer().catch(console.error);

app.get("/", (req, res) => {
  res.send("Kafka consumer is running");
});

app.listen(port, () => {
  console.log(`Express app on port ${port}`);
});
