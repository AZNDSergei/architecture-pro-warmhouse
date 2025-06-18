namespace temperature_api.Models
{
	public class SendTemperatureCommand
	{
		public string Location { get; set; } = string.Empty;
		public double Temperature { get; set; } = 0.0;
	}
}
