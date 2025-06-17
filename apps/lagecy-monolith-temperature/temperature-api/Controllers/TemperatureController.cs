using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using temperature_api.Services;

namespace temperature_api.Controllers
{
	[ApiController]
	[ApiVersion("1.0")]
	[Route("/api/v{version:apiVersion}/[controller]")]
	public class TemperatureController : ControllerBase
	{
		private readonly IServiceScopeFactory _serviceScopeFactory;
		public TemperatureController(IServiceScopeFactory factory)
		{
			_serviceScopeFactory = factory;
		}

		[HttpGet]
		public async Task<IActionResult> GetTemperature([FromQuery] string? location)
		{

			if (string.IsNullOrEmpty(location))
			{
				location = "Average home temperature";
			}

			if (location.Length is > 100)
			{
				return BadRequest("Location name shouldn't be longer than 100");
			}

			var random = new Random();

			if (string.IsNullOrEmpty(location))
			{
				return BadRequest("Location parameter is required.");
			}

			var temperature = random.Next(-30, 50); // Temperature between -30 and 50 degrees Celsius
			using var scope = _serviceScopeFactory.CreateScope();
			var temperatureSender = scope.ServiceProvider.GetService<TemperatureSender>();

			await temperatureSender.ProduceAsync(new Models.SendTemperatureCommand
			{
				Location = location,
				Temperature = temperature
			});
			return Ok(new { Location = location, Temperature = temperature });
		}
	}
}
