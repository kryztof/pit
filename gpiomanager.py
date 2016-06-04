#!/usr/bin/python

import RPi.GPIO as GPIO
import pygame


class GpioManager:
  def __init__(self):
    self.channels = [24,26]
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(self.channels, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    self.make_callbacks()

  def make_callbacks(self):
    GPIO.add_event_detect(self.channels[0], GPIO.FALLING, callback = self.callback, bouncetime=100)
    GPIO.add_event_detect(self.channels[1], GPIO.FALLING, callback = self.callback, bouncetime=100)

  def callback(self,channel):
    if channel == 24 :
      buttonevent = pygame.event.Event(pygame.USEREVENT+4)
      pygame.event.post(buttonevent)
    elif channel == 26 :
      buttonevent = pygame.event.Event(pygame.USEREVENT+5)
      pygame.event.post(buttonevent)

  #def leds_on(self):
  #  GPIO.output(self.channels, 1)

  #def leds_off(self):
  #  GPIO.output(self.channels, 0)

