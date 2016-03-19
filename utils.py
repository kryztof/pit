#!/usr/bin/python
import time
from threading import Event, Thread
import os

dbgfile="pit_dbg.log"
try: 
  os.remove(dbgfile)
except:
  pass

def call_repeatedly(interval, func, *args):
  stopped = Event()
  def loop():
    while not stopped.wait(interval): # the first call is in `interval` secs
      func(*args)
  Thread(target=loop).start()    
  return stopped.set

dbgfp = open(dbgfile,'a+')
def dbgprint(*arg):
  s = ' '.join(map(str,arg))
  print(s)
  dbgfp.write(s+'\n')
  #dbgfp.close()

def get_screen_size(real = 0):
  debug = 1
  if debug == 1 and real == 0 : 
    return (400,220)
  else:
    return (800,480)

def get_aspect_scale(width,height,maxwidth,maxheight):
  """ Scales 'img' to fit into box maxwidth/maxheight.
   This method will retain the original image's aspect ratio """
  if width > height:
    # fit to width
    scale_factor = maxwidth/float(width)
    new_h = scale_factor * height
    if new_h > maxheight:
      scale_factor = maxheight/float(height)
      new_w = scale_factor * width
      new_h = maxheight
    else:
      new_w = maxwidth
  else:
    # fit to height
    scale_factor = maxheight/float(height)
    new_w = scale_factor * width
    if new_w > maxwidth:
      scale_factor = maxwidth/float(width)
      new_w = maxwidth
      new_h = scale_factor * height
    else:
      new_h = maxheight
  #dbgprint(" new scale: "+str(new_w) + " " + str(new_h))
  return (int(new_w), int(new_h))


##The event is used to stop the repetitions:
#cancel_future_calls = call_repeatedly(5, print, "Hello, World")
## do something else here...
#counter=0
#while True:
#  print("zaza");
#  time.sleep(1);
#  counter+=1
#  if counter > 20: break
#cancel_future_calls() # stop future calls
