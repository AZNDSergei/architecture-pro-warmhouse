namespace temperature_api.Models
{
    public class Sensor
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Type { get; set; }
        public string Location { get; set; }
        public string Unit { get; set; }
        public string Status { get; set; } = "inactive";
        public double Value { get; set; } = 0.0;

    }

    public class SensorPatchModel
    {
        public string Status { get; set; }
        public double Value { get; set; }
    }
}
