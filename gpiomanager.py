#!/usr/bin/python

import RPi.GPIO as GPIO


class GpioManager:
  def __init__(self):
    self.channels = [24,26]
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.channels, GPIO.OUT)
    GPIO.output(self.channels, 0)

  def leds_on(self):
    GPIO.output(self.channels, 1)

  def leds_off(self):
    GPIO.output(self.channels, 0)

