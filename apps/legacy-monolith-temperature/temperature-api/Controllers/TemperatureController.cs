using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;

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


			return Ok(new { Location = location, Temperature = temperature });
		}
	}
}
