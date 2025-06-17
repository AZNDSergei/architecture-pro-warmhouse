namespace net_device_metrics
{
	public class Sensor
	{
		public int Id { get; set; }
		public string Name { get; set; } = "";
		public string Type { get; set; } = "";
		public string? Location { get; set; }
		public double? Value { get; set; }
		public string? Unit { get; set; }
		public string? Status { get; set; }
		public DateTime Timestamp { get; set; } = DateTime.UtcNow;
	}
}
