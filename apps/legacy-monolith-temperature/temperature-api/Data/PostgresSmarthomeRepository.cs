namespace temperature_api.Data
{
    using Dapper;
    using Npgsql;
    using System.Data;
    using temperature_api.Models;

    public class PostgresSensorRepository
    {
        private readonly string _connectionString;

        public PostgresSensorRepository(string configuration)
        {
            _connectionString = configuration;
        }

        private IDbConnection CreateConnection() => new NpgsqlConnection(_connectionString);

        public async Task<Sensor> AddSensorAsync(Sensor sensor)
        {
            var sql = @"
            INSERT INTO sensors (name, type, location, value, unit, status)
            VALUES (@Name, @Type, @Location, @Value, @Unit, @Status)
            RETURNING *;";

            using var connection = CreateConnection();
            return await connection.QuerySingleAsync<Sensor>(sql, sensor);
        }

        public async Task<Sensor?> GetSensorByIdAsync(int id)
        {
            var sql = "SELECT * FROM sensors WHERE id = @Id";
            using var connection = CreateConnection();
            var sensor = await connection.QueryFirstOrDefaultAsync<Sensor>(sql, new { Id = id });
            if (sensor != null)
            {
                sensor.Value = RandomValueGenerator.GenerateRandomTemperatureValue();
            }

            return sensor;
        }

        public async Task<IEnumerable<Sensor>> GetAllSensorsAsync()
        {
            var sql = "SELECT * FROM sensors ORDER BY id";
            using var connection = CreateConnection();
            var sensorList = await connection.QueryAsync<Sensor>(sql);
            if (sensorList.Any())
            {
                sensorList = sensorList.Select(s => { s.Value = RandomValueGenerator.GenerateRandomTemperatureValue(); return s; });
            }

            return sensorList;
        }

        public async Task<Sensor?> RemoveSensorAsync(int id)
        {
            var sensor = await GetSensorByIdAsync(id);
            if (sensor == null)
            {
                return null;
            }

            var sql = "DELETE FROM sensors WHERE id = @Id";
            using var connection = CreateConnection();
            await connection.ExecuteAsync(sql, new { Id = id });
            return sensor;
        }

        public async Task<Sensor?> UpdateSensorAsync(int id, Sensor updated)
        {
            var sql = @"
            UPDATE sensors
            SET name = @Name,
                type = @Type,
                location = @Location,
                unit = @Unit,
                status = @Status
            WHERE id = @Id
            RETURNING *;";
            using var connection = CreateConnection();
            return await connection.QueryFirstOrDefaultAsync<Sensor>(sql, new { updated.Name, updated.Type, updated.Location, updated.Unit, Id = id });
        }

        public async Task<Sensor?> PatchSensorAsync(int id, SensorPatchModel patch)
        {
            var sql = @"
            UPDATE sensors
            SET value = @Value,
                status = @Status,
                last_updated = NOW()
            WHERE id = @Id
            RETURNING *;";
            using var connection = CreateConnection();
            return await connection.QueryFirstOrDefaultAsync<Sensor>(sql, new { patch.Value, patch.Status, Id = id });
        }
    }
}
