using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using temperature_api.Data;
using temperature_api.Models;
using temperature_api.Services;

namespace temperature_api.Controllers
{
	[ApiController]
	[ApiVersion("1.0")]
	[Route("/api/v{version:apiVersion}/[controller]")]
	public class SensorsController : ControllerBase
	{

		private readonly PostgresSensorRepository _repo;
		private readonly IServiceScopeFactory _serviceScopeFactory;
		public SensorsController(PostgresSensorRepository repo, IServiceScopeFactory serviceScopeFactory)
		{
			_repo = repo;
			_serviceScopeFactory = serviceScopeFactory;
		}

		[HttpGet]
		public async Task<IActionResult> GetSensors() => Ok(await _repo.GetAllSensorsAsync());

		[HttpPost]
		public async Task<IActionResult> AddSensors([FromBody] Sensor sensor)
		{
			var result = await _repo.AddSensorAsync(sensor);

			using var scope = _serviceScopeFactory.CreateScope();
			var bridgeToNewSystem = scope.ServiceProvider.GetService<NewSystemIntegrationEventSender>();

			await bridgeToNewSystem.ProduceAsync(new Models.Sensor
			{
				Location = result.Location,
				Name = result.Name,
				Value = result.Value,
				Type = result.Type,
				Unit = result.Unit,
				Status = result.Status
			});

			return Ok(result);
		}

		[HttpPut("{sensorId}")]
		public async Task<IActionResult> UpdateSensor([FromRoute] int sensorId, [FromBody] Sensor sensor)
		{
			if (sensor == null)
			{
				return BadRequest("Sensor ID is required.");
			}

			var updatedSensor = await _repo.UpdateSensorAsync(sensorId, sensor);

			if (updatedSensor == null)
			{
				return NotFound("There is no sensor by this Id");
			}

			return Ok(updatedSensor);
		}

		[HttpPatch("{sensorId}")]
		public async Task<IActionResult> PatchSensor([FromRoute] int sensorId, [FromBody] SensorPatchModel patch)
		{
			if (sensorId == 0)
			{
				return BadRequest("Sensor ID is required.");
			}

			if (string.IsNullOrEmpty(patch.Status))
			{
				return BadRequest("Sensor status should be specified");
			}

			var updatedSensor = await _repo.PatchSensorAsync(sensorId, patch);

			if (updatedSensor == null)
			{
				return NotFound("There is no sensor by this Id");
			}

			using var scope = _serviceScopeFactory.CreateScope();
			var bridgeToNewSystem = scope.ServiceProvider.GetService<NewSystemIntegrationEventSender>();

			await bridgeToNewSystem.ProduceAsync(new Models.SensorPatchModel
			{
				Status = updatedSensor.Status,
				Value = updatedSensor.Value
			});

			return Ok(updatedSensor);
		}

		[HttpDelete("{sensorId}")]
		public async Task<IActionResult> Remove([FromRoute] int? sensorId)
		{
			if (sensorId == null)
			{
				return BadRequest("Sensor ID is required.");
			}

			var sensor = await _repo.RemoveSensorAsync(sensorId.Value);

			if (sensor == null)
			{
				return NotFound("There is no sensor by this Id");
			}

			using var scope = _serviceScopeFactory.CreateScope();
			var bridgeToNewSystem = scope.ServiceProvider.GetService<NewSystemIntegrationEventSender>();

			await bridgeToNewSystem.ProduceAsync(sensorId.Value);

			return Ok(sensor);
		}

		[HttpGet("{sensorId}")]
		public async Task<IActionResult> GetSensor([FromRoute] int? sensorId)
		{
			if (sensorId == null)
			{
				return BadRequest("Sensor ID is required.");
			}

			var sensor = await _repo.GetSensorByIdAsync(sensorId.Value);

			if (sensor == null)
			{
				return NotFound("There is no sensor by this Id");
			}

			return Ok(sensor);
		}
	}
}
