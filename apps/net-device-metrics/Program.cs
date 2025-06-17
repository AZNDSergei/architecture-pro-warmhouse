using System.Text.Json;
using Confluent.Kafka;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using net_device_metrics;
using Prometheus;
using Serilog;
using Serilog.Formatting.Compact;

var builder = Host.CreateApplicationBuilder(args);

Log.Logger = new LoggerConfiguration()
	.Enrich.FromLogContext()
	.WriteTo.Console()
	.WriteTo.DurableHttpUsingFileSizeRolledBuffers(
		requestUri: "http://loki:3111/loki/api/v1/push",
		textFormatter: new RenderedCompactJsonFormatter()
	)
	.CreateLogger();

builder.Logging.ClearProviders();
builder.Logging.AddSerilog();

// === Запуск метрик-сервера Prometheus ===
builder.Services.AddHostedService<PrometheusMetricServer>();
builder.Services.AddHostedService<KafkaSensorProcessor>();

var host = builder.Build();
await host.RunAsync();

// === Sensor.cs ===

// === Prometheus endpoint service ===
public class PrometheusMetricServer : BackgroundService
{
	protected override async Task ExecuteAsync(CancellationToken stoppingToken)
	{
		var server = new KestrelMetricServer(port: 5000);
		server.Start();
		Log.Information("Prometheus metrics server running on :5000");
		await Task.Delay(Timeout.Infinite, stoppingToken);
	}
}

// === Kafka Consumer Service ===
public class KafkaSensorProcessor : BackgroundService
{
	private static readonly Counter _messageCounter = Metrics
		.CreateCounter("sensor_kafka_messages_total", "Total Kafka messages received");

	private static readonly Gauge _lastSensorValue = Metrics
		.CreateGauge("sensor_last_value", "Last value per sensor", new[] { "sensor_name" });

	protected override async Task ExecuteAsync(CancellationToken stoppingToken)
	{
		var config = new ConsumerConfig
		{
			BootstrapServers = "kafka:9092",
			GroupId = "dotnet-consumer-group",
			AutoOffsetReset = AutoOffsetReset.Earliest
		};

		using var consumer = new ConsumerBuilder<Ignore, string>(config).Build();
		consumer.Subscribe("sensorData");

		Log.Information("Kafka consumer started and subscribed to 'sensorData'");

		while (!stoppingToken.IsCancellationRequested)
		{
			try
			{
				var result = consumer.Consume(stoppingToken);
				Log.Information("Received Kafka message: {Message}", result.Message.Value);
				_messageCounter.Inc();

				Sensor? sensor = null;
				try
				{
					sensor = JsonSerializer.Deserialize<Sensor>(result.Message.Value);
				}
				catch (Exception ex)
				{
					Log.Warning("Deserialization failed: {Error}", ex.Message);
					continue;
				}

				if (sensor?.Name != null && sensor.Value.HasValue)
				{
					_lastSensorValue.WithLabels(sensor.Name).Set(sensor.Value.Value);
				}
			}
			catch (ConsumeException e)
			{
				Log.Warning("Kafka consume error: {Error}", e.Message);
			}
			catch (OperationCanceledException)
			{
				break;
			}
		}

		consumer.Close();
		Log.Information("Kafka consumer stopped.");
	}
}
