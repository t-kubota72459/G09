from machine import Pin, PWM
from time import sleep

def blink():
    led = Pin(8, Pin.OUT)
    for _ in range(5):
        led.value(1)
        sleep(0.5)
        led.value(0)
        sleep(0.5)
