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
import os
from utils import *
try:
  import ft5406
  from ft5406 import Touchscreen, TS_PRESS, TS_RELEASE, TS_MOVE
except:
  pass

class DisplayManager:
  def __init__(self):
    self.ft = True ; # TRUE IF TOUCH SCREEN 
    self.blpowerpath = "/sys/class/backlight/rpi_backlight/bl_power"
    try:
      self.fd = open(self.blpowerpath,'r+')
    except:
      self.ft = False
    self.lastaction = 0
    self.displaystate = 1 ; #1 in on, 0 is off

    self.reset_timer()
    self.check_for_sleep()


  def __del__(self):
    #dbgprint("del dm")
    #self.display_on() -> generate exception ...
    if self.ft:
      self.fd.close()

  def check_for_sleep(self):
    now = time.time()
    #dbgprint("now", now, "last action:", self.lastaction)
    if now - self.lastaction > 7*60 :
      self.display_off()

  def reset_timer(self):
    #dbgprint("reset timer", self.lastaction)
    self.lastaction =  time.time(); #-> returns time in seconds
    if self.displaystate == 0 :
      self.display_on()

  def init_touchscreen(self):
    if self.ft :
      self.ts = ft5406.Touchscreen()
      for touch in self.ts.touches:
        touch.on_press = self.display_on()

  def display_on(self):
    #dbgprint("display on")
    self.displaystate = 1
    if self.ft:
      self.fd.write('0'); 
      self.fd.flush()
    else:
      os.system("/opt/vc/bin/tvservice -p")
      os.system("chvt 9")
      os.system("chvt 7")

  def display_off(self):
    #dbgprint("display off")
    self.displaystate = 0
    if self.ft:
      self.fd.write('1'); 
      self.fd.flush()
    else:
      os.system("/opt/vc/bin/tvservice -o")

#if __name__ == '__main__':
#  displayManager = DisplayManager()
#  displayManager.display_off()
#  time.sleep(10)
#  displayManager.display_on()
