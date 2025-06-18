using Asp.Versioning;
using temperature_api.Data;
using temperature_api.Options;
using temperature_api.Services;
namespace temperature_api
{
	public class Program
	{
		public static void Main(string[] args)
		{
			var builder = WebApplication.CreateBuilder(args);
			// Add services to the container.

			builder.Services.AddControllers();
			builder.Services.AddHealthChecks();
			builder.Services.AddSingleton<NewSystemIntegrationEventSender>();
			//var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
			builder.Services.AddScoped(_ => new PostgresSensorRepository("Host=legacy-monolith-db;Port=5432;Database=smarthome;Username=postgres;Password=postgres;"));

			builder.Services.Configure<KafkaSettings>(builder.Configuration.GetSection("Kafka"));

			builder.Services.AddApiVersioning(options =>
			{
				options.DefaultApiVersion = new ApiVersion(1, 0);
				options.AssumeDefaultVersionWhenUnspecified = true;
				options.ReportApiVersions = true;
				options.ApiVersionReader = new UrlSegmentApiVersionReader();
			});

			var app = builder.Build();

			// Configure the HTTP request pipeline.

			//app.UseHttpsRedirection();

			app.UseAuthorization();

			app.MapControllers();

			app.MapHealthChecks("/health");

			app.Run();
		}
	}
}
