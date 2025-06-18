namespace temperature_api
{
    public class RandomValueGenerator
    {
        public static double GenerateRandomTemperatureValue()
        {
            var random = new Random();

            return random.Next(-30, 50);

        }
    }
}
