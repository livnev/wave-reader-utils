import asyncio

# pip install rich
from rich.console import Console
from rich.table import Table

from wave_reader import WaveDevice
from wave_reader.data import WaveProduct


class MyWaveDevice(WaveDevice):
    def __init__(self):
        self.name: str = "Airthings Wave+"
        self.address: str = "80:6F:B0:A0:E0:00"
        self.serial_number: int = 2930000000
        self.product: WaveProduct = WaveProduct(self.name)


def data_table(data: dict, serial: int) -> Table:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("SERIAL", style="dim", width=12)
    column_data = []
    for k, v in data.items():
        table.add_column(str(k).upper())
        column_data.append(str(v))
    table.add_row(str(serial), *column_data)
    return table


if __name__ == "__main__":
    device = MyWaveDevice()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(device.get_sensor_values())

    console = Console()
    console.print(data_table(device.sensors.as_dict(), device.serial_number))

# Prints the following output:
#
# ┏━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━┓
# ┃ SERIAL       ┃ HUMIDITY ┃ RADON_STA ┃ RADON_LTA ┃ TEMPERATURE ┃ PRESSURE ┃ CO2   ┃ VOC  ┃
# ┡━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━┩
# │ 2930000000   │ 26.0     │ 128       │ 115       │ 20.74       │ 987.66   │ 647.0 │ 72.0 │
# └──────────────┴──────────┴───────────┴───────────┴─────────────┴──────────┴───────┴──────┘