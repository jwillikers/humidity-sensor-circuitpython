import struct
import time
import alarm
import board
import digitalio
import microcontroller
import neopixel_write
import adafruit_fram
import adafruit_htu31d
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680  # pylint: disable=unused-import


NUMBER_OF_SAMPLES = 300
STRUCT_FORMAT = ("i" + "d" * 300) * 2
FIRST_WAKE = (
    alarm.wake_alarm
    is None
    # microcontroller.cpu.reset_reason != microcontroller.ResetReason.DEEP_SLEEP_ALARM
)


def disable_led(led_pin):
    pin = digitalio.DigitalInOut(led_pin)
    pin.direction = digitalio.Direction.OUTPUT
    pixel_off = bytearray([0, 0, 0])
    neopixel_write.neopixel_write(pin, pixel_off)


def median(numbers):
    numbers.sort()
    return numbers[len(numbers) // 2]


def zero_values(values):
    return [0 for i in range(len(values))]


def initialize_display(spi_bus, ecs):
    dc = digitalio.DigitalInOut(board.D10)
    srcs = digitalio.DigitalInOut(board.D6)  # can be None to use internal memory
    rst = None  # digitalio.DigitalInOut(board.D8)  # can be None to not use this pin
    busy = None  # digitalio.DigitalInOut(board.D7)  # can be None to not use this pin

    display = Adafruit_SSD1680(
        122,
        250,  # 2.13" HD mono display
        spi_bus,
        cs_pin=ecs,
        dc_pin=dc,
        sramcs_pin=srcs,
        rst_pin=rst,
        busy_pin=busy,
    )
    display.rotation = 1
    return display


def update_display(display, relative_humidity, temperature):
    display.fill(Adafruit_EPD.WHITE)
    display.pixel(10, 100, Adafruit_EPD.BLACK)
    display.text("Humble", 68, 8, Adafruit_EPD.BLACK, size=3)
    display.text("Humidity Sensor", 34, 40, Adafruit_EPD.BLACK, size=2)
    display.text(
        "Humidity {:.1f}%".format(relative_humidity), 8, 70, Adafruit_EPD.BLACK, size=2
    )
    display.text(
        "Temperature {:.1f} C".format(temperature), 8, 100, Adafruit_EPD.BLACK, size=2
    )
    display.display()


def reset_sleep_memory(
    relative_humidity_index,
    relative_humidity_values,
    temperature_index,
    temperature_values,
):
    return (
        0,
        zero_values(relative_humidity_values),
        0,
        zero_values(temperature_values),
    )


# print("Reset reason: ", microcontroller.cpu.reset_reason)
print("wake_alarm: ", alarm.wake_alarm)
disable_led(board.NEOPIXEL)

spi_bus = board.SPI()

cs = digitalio.DigitalInOut(board.D5)
fram = adafruit_fram.FRAM_SPI(spi_bus, cs)

assert struct.calcsize(STRUCT_FORMAT) <= len(fram)

memory = [0 for i in range(602)]
if not FIRST_WAKE:
    memory = list(
        struct.unpack(STRUCT_FORMAT, fram[0 : struct.calcsize(STRUCT_FORMAT) - 1])
    )

relative_humidity_values = memory[1:301]  # alarm.sleep_memory[1:301]
temperature_values = memory[302:602]  # alarm.sleep_memory[302:602]

relative_humidity_index = memory[0]  # alarm.sleep_memory[0]
temperature_index = memory[301]  # alarm.sleep_memory[301]

# Zero the memory if we haven't slept yet.
if FIRST_WAKE:
    (
        memory[0],
        relative_humidity_values,
        memory[301],
        temperature_values,
    ) = reset_sleep_memory(
        memory[0], relative_humidity_values, memory[301], temperature_values
    )

ecs = digitalio.DigitalInOut(board.D9)
display = initialize_display(spi_bus, ecs)

i2c = board.I2C()
htu = adafruit_htu31d.HTU31D(i2c)

(
    temperature_values[memory[301]],
    relative_humidity_values[memory[0]],
) = htu.measurements

# Display initial measurements so that we don't have to wait for a full collection of samples before getting a reading.
if FIRST_WAKE:
    update_display(
        display,
        relative_humidity_values[memory[0]],
        temperature_values[memory[301]],
    )

# Update the indices.
# alarm.sleep_memory[0] = relative_humidity_index + 1
# alarm.sleep_memory[301] = temperature_index + 1
memory[0] += 1
memory[301] += 1

# Update the display if finished taking samples.
if memory[0] >= NUMBER_OF_SAMPLES:
    median_relative_humidity = median(relative_humidity_values)
    median_temperature = median(temperature_values)

    print("Temperature: %0.1f C" % median_temperature)
    print("Humidity: %0.1f %%" % median_relative_humidity)
    print("")

    update_display(display, median_relative_humidity, median_temperature)
    (
        memory[0],
        relative_humidity_values,
        memory[301],
        temperature_values,
    ) = reset_sleep_memory(
        memory[0], relative_humidity_values, memory[301], temperature_values
    )

fram = struct.pack("i", memory[0])
fram += struct.pack("d" * 300, *memory[1:301])
fram += struct.pack("i", memory[301])
fram += struct.pack("d" * 300, *memory[302:601])

# todo Deep sleep for 1 second.
al = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 1)
alarm.exit_and_deep_sleep_until_alarms(al)
