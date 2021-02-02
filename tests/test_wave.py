from copy import deepcopy
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from wave_reader import wave

from .mocks import MockedBleakClient, MockedBLEDevice


class TestReaderUtils(TestCase):
    def test_parse_serial_number(self):
        """Validate Wave Plus manufacturer data parsing."""
        valid_data = {820: [13, 25, 160, 170, 9, 0]}
        valid_serial = wave.WaveDevice.parse_serial_number(valid_data)
        self.assertEqual(valid_serial, 2862618893)

        invalid_data = [
            {},
            None,
            {120: []},
            {120: None},
            {820: [10, 20]},
            {120: [13, 25, 160, 170, 9, 0]},
        ]
        for i in invalid_data:
            self.assertRaises(
                wave.UnknownDevice, wave.WaveDevice.parse_serial_number, i
            )


class TestWave(IsolatedAsyncioTestCase):
    def setUp(self):
        # A device that is a valid Wave profile.
        self.BLEDevice = MockedBLEDevice()
        self.WaveDevice = wave.WaveDevice(self.BLEDevice, 2862618893)
        self.DeviceSensors = wave.DeviceSensors.from_bytes(
            (1, 65, 0, 0, 136, 143, 2063, 48984, 692, 114, 0, 1564),
            self.WaveDevice.product,
        )

    @patch("wave_reader.wave._logger.debug")
    @patch("wave_reader.wave.discover")
    async def test_discover_wave_devices(self, mocked_discover, mocked_logger):
        # A device that should raise an UnknownDevice exception.
        BLEUnknownDevice = deepcopy(self.BLEDevice)
        BLEUnknownDevice.metadata["manufacturer_data"] = {420: [69]}
        # A device that should be ignored because it lacks manu_data.
        BLEIgnoredDevice = deepcopy(self.BLEDevice)
        BLEIgnoredDevice.metadata["manufacturer_data"] = {}

        mocked_discover.return_value = [
            self.BLEDevice,
            BLEUnknownDevice,
            BLEIgnoredDevice,
        ]
        expected_result = [self.WaveDevice]
        devices = await wave.discover_devices()
        self.assertTrue((devices == expected_result))
        self.assertTrue(mocked_logger.called)

    def test_wave_device__str__(self):
        self.assertEqual(str(self.WaveDevice), "WaveDevice (2862618893)")

    @patch("wave_reader.wave.BleakClient", autospec=True)
    async def test_get_sensor_values(self, mocked_client):
        device = [self.WaveDevice]
        mocked_client.return_value = MockedBleakClient(device[0])
        await device[0].get_sensor_values()
        self.assertEqual(device[0].sensors, self.DeviceSensors)

    def test_sensors__str__(self):
        self.assertEqual(
            str(self.DeviceSensors),
            "DeviceSensors (humidity: 32.5, radon_sta: 136, radon_lta: 143, "
            "temperature: 20.63, pressure: 979.68, co2: 692.0, voc: 114.0)",
        )

    def test_create_valid_product(self):
        device = wave.WaveDevice.create("Airthings Wave", "foo_address", 123)
        self.assertEqual(device.name, "Airthings Wave")
        self.assertEqual(device.address, "foo_address")
        self.assertEqual(device.serial_number, 123)

    def test_create_invalid_product(self):
        with self.assertRaises(ValueError):
            wave.WaveDevice.create("Unsupported", "foo_address", 123)

    @patch("wave_reader.wave._logger.error")
    def test_invalid_version(self, mocked_logger):
        device = wave.WaveDevice.create('Airthings Wave', 'foo', 123)
        device._raw_gatt_values = b"\x01A\x00\x00"
        with self.assertRaises(wave.UnsupportedVersionError):
            device._map_sensor_values()
        self.assertTrue(mocked_logger.called)
