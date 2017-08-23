#!/usr/bin/python

try:
  import RPi.GPIO as GPIO
except:
  pass
import pygame
from utils import *
from time import sleep 


class GpioManager:
  def __init__(self):
    try:
      self.channels = [24,26]
      GPIO.setwarnings(False)
      GPIO.setmode(GPIO.BOARD)
      GPIO.setup(self.channels, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      self.make_callbacks()
    except:
      print("No module RPi.GPIO")

  def __del__(self):
    GPIO.remove_event_detect(self.channels[0])
    GPIO.remove_event_detect(self.channels[1])
    GPIO.cleanup()

  def make_callbacks(self):
    GPIO.add_event_detect(self.channels[0], GPIO.FALLING, callback = self.callback, bouncetime=200)
    GPIO.add_event_detect(self.channels[1], GPIO.FALLING, callback = self.callback, bouncetime=200)

  def callback(self,channel):
    #dbgprint("gettting button input")
    time.sleep(0.1)
    if GPIO.input(24) == 0 and GPIO.input(26) == 0:
      buttonevent = pygame.event.Event(pygame.USEREVENT+6)
    elif channel == 26 :
      buttonevent = pygame.event.Event(pygame.USEREVENT+4)
    elif channel == 24 :
      buttonevent = pygame.event.Event(pygame.USEREVENT+5)

    pygame.event.post(buttonevent)

  #def leds_on(self):
  #  GPIO.output(self.channels, 1)

  #def leds_off(self):
  #  GPIO.output(self.channels, 0)

