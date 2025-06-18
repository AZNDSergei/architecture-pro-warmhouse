namespace temperature_api.Options
{
	public class KafkaSettings
	{
		public string BootstrapServers { get; set; } = default!;
		public string Topic { get; set; } = default!;
	}
}
