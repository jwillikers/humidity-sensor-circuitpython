import time
# import alarm
import board
import busio
import digitalio
from machine import Pin, I2C, SPI
from neopixel import NeoPixel
import adafruit_htu31d
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680  # pylint: disable=unused-import


NUMBER_OF_SAMPLES = 300


def disable_led(led_pin):
    neopixel = NeoPixel(led_pin, 1)
    pixel_off = bytearray([0, 0, 0])
    neopixel[0] = pixel_off
    neopixel.write()


def median(numbers):
    numbers.sort()
    return numbers[len(numbers) // 2]


def zero_values(values):
    return [None for i in range(len(values))]

def initialize_display():
    spi = busio.SPI(board.GP18, board.GP19, board.GP20)
    ecs = digitalio.DigitalInOut(board.D9)
    dc = digitalio.DigitalInOut(board.D10)
    srcs = digitalio.DigitalInOut(board.D6)  # can be None to use internal memory
    rst = None  # digitalio.DigitalInOut(board.D8)  # can be None to not use this pin
    busy = None  # digitalio.DigitalInOut(board.D7)  # can be None to not use this pin

    display = Adafruit_SSD1680(
        122,
        250,  # 2.13" HD mono display
        spi,
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


led_pin = Pin(16, Pin.OUT)
disable_led(led_pin)

# Temporary workaround for light sleep.
memory = [None for i in range(602)]

relative_humidity_values = memory[1:301]  # alarm.sleep_memory[1:301]
temperature_values = memory[302:602]  # alarm.sleep_memory[302:602]

relative_humidity_index = memory[0]  # alarm.sleep_memory[0]
temperature_index = memory[301]  # alarm.sleep_memory[301]

# Zero the memory if we haven't slept yet.
# if not alarm.wake_alarm:
(
    memory[0],
    relative_humidity_values,
    memory[301],
    temperature_values,
) = reset_sleep_memory(
    memory[0], relative_humidity_values, memory[301], temperature_values
)

display = initialize_display()
i2c = busio.I2C(Pin(3), Pin(2))
htu = adafruit_htu31d.HTU31D(i2c)

# Temporary workaround for light sleep.
first_run = True
while True:

    (
        temperature_values[memory[301]],
        relative_humidity_values[memory[0]],
    ) = htu.measurements

    # Display initial measurements so that we don't have to wait for a full collection of samples before getting a reading.
    if first_run:
        # if not alarm.wake_alarm:
        update_display(
            display,
            relative_humidity_values[memory[0]],
            temperature_values[memory[301]],
        )
        first_run = False

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

    # todo Deep sleep for 1 second.
    time.sleep(1)
    # al = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 1)
    # alarm.light_sleep_until_alarms(al)
