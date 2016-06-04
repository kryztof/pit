#!/usr/bin/python3
"""
note: for this to work make sure to follow instructions found here:
https://www.raspberrypi.org/forums/viewtopic.php?f=108&t=120968&start=50
i.e.:
sudo vim /etc/udev/rules.d/backlight-permissions.rules
and add line:
SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/rpi_backlight/brightness /sys/class/backlight/rpi_backlight/bl_power"
save and reboot the rpi
now if you do 'ls -l /sys/class/backlight/rpi_backlight/bl_power'
you should see :
-rw-rw-rw- 1 root root 4096 Mar 17 22:08 /sys/class/backlight/rpi_backlight/bl_power
"""

import time, threading
from utils import *
import ft5406
from ft5406 import Touchscreen, TS_PRESS, TS_RELEASE, TS_MOVE

class DisplayManager:
  ##def __init__(self):
    #self.blpowerpath = "/sys/class/backlight/rpi_backlight/bl_power"
    ##self.fd = open(self.blpowerpath,'r+')
    ##self.lastaction = 0
    ##self.reset_timer()
    ##self.check_for_sleep()

  def __del__(self):
    #dbgprint("del dm")
    self.bl_on()
    self.fd.close()

  def check_for_sleep(self):
    now = time.time()
    #dbgprint("now", now, "last action:", self.lastaction)
    if now - self.lastaction > 7*60 :
      self.bl_off()

  def reset_timer(self):
    #dbgprint("reset timer", self.lastaction)
    self.lastaction =  time.time(); #-> returns time in seconds
    self.bl_on()

  def init_touchscreen(self):
    self.ts = ft5406.Touchscreen()
    for touch in self.ts.touches:
      touch.on_press = self.bl_on()

  def bl_on(self):
    self.fd.write('0'); 
    self.fd.flush()

  def bl_off(self):
    self.fd.write('1'); 
    self.fd.flush()

#if __name__ == '__main__':
#  displayManager = DisplayManager()
#  displayManager.bl_off()
#  time.sleep(10)
#  displayManager.bl_on()
