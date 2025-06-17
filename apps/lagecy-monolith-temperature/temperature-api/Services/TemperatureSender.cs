using System.Text.Json;
using Confluent.Kafka;
using Microsoft.Extensions.Options;
using temperature_api.Models;
using temperature_api.Options;

namespace temperature_api.Services
{
	public class TemperatureSender
	{
		private readonly IProducer<Null, string> _producer;
		private readonly string _topic;

		public TemperatureSender(IOptions<KafkaSettings> settings)
		{
			_topic = settings.Value.Topic;
			var config = new ProducerConfig
			{
				BootstrapServers = settings.Value.BootstrapServers
			};
			_producer = new ProducerBuilder<Null, string>(config).Build();
		}

		public async Task ProduceAsync(SendTemperatureCommand command)
		{
			try
			{
				var deliveryResult = await _producer.ProduceAsync(
					_topic,
					new Message<Null, string> { Value = JsonSerializer.Serialize(command) });

				Console.WriteLine($"[Kafka] Delivered message to '{deliveryResult.TopicPartitionOffset}': {deliveryResult.Value}");
			}
			catch (ProduceException<Null, string> ex)
			{
				Console.WriteLine($"[Kafka] Delivery failed: {ex.Error.Reason}");
			}
		}
	}
}
