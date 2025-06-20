package mapper

import (
	"encoding/json"

	"github.com/google/uuid"
)

type Sensor struct {
	ID       int     `json:"id"`
	Name     string  `json:"name"`
	Type     string  `json:"type"`
	Location string  `json:"location"`
	Unit     string  `json:"unit"`
	Status   string  `json:"status"`
	Value    float64 `json:"value"`
}

type Device struct {
	ID              uuid.UUID `json:"id"`
	Name            string    `json:"name"`
	Type            string    `json:"type"`
	Model           string    `json:"model"`
	FirmwareVersion string    `json:"firmware_version"`
	Status          string    `json:"status"`
}

const (
	defaultFirmware = "legacy-1.0"
	defaultModel    = "legacy-sensor"
)

func SensorJSONToDevice(payload []byte) (Device, error) {
	var s Sensor
	if err := json.Unmarshal(payload, &s); err != nil {
		return Device{}, err
	}
	return mapSensorToDevice(s), nil
}

func mapSensorToDevice(s Sensor) Device {
	return Device{
		ID:              uuid.New(),
		Name:            s.Name,
		Type:            s.Type,
		Model:           firstNonEmpty(s.Unit, s.Location, defaultModel),
		FirmwareVersion: defaultFirmware,
		Status:          firstNonEmpty(s.Status, "inactive"),
	}
}

func firstNonEmpty(vals ...string) string {
	for _, v := range vals {
		if v != "" {
			return v
		}
	}
	return ""
}
