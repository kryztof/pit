#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pygame
from pygame import *
from pygame.locals import *
import time
import ft5406
from ft5406 import Touchscreen, TS_PRESS, TS_RELEASE, TS_MOVE
import sys
import os
#import exifread
from emailread import *
from utils import *
from histelementcontainer import *
from histelement import *
from smsread import *
from gpiomanager import *
from displaymanager import *

class PIT:
  def __init__(self, historycontainer, displaymanager):
    self.presspos = (0,0);
    self.releasepos = (0,0);
    self.background_color = (255,255,255)
    self.linecolor = (150,150,150)
    self.histcontainer = historycontainer
    self.displaymanager = displaymanager
    self.w,self.h = get_screen_size()
    self.roundboxmargin = (45,10)
    #the contentmargin is for left and write, to and bottom
    self.contentmargin = (55,25)
    #the offset below the y margin
    self.lineyoffset = 45
    #the offset below the y margin
    self.imageyoffset = 60
    self.buttonsize = (40, 70)
    self.gpioManager = GpioManager()
    self.gpioManager.leds_off()

  def start_screen(self):
    self.init_pygame_and_screen()
    self.init_touchscreen()
    self.get_next_previous_item(0)

    self.start_timer_from_new_items_check()
    self.start_endless_touch_loop()

  def init_pygame_and_screen(self):
    pygame.init()
    pygame.mouse.set_visible(False)

    #self.screen = pygame.display.set_mode(get_screen_size())
    ss = get_screen_size()
    if ss[0] == 400 : 
      self.screen = pygame.display.set_mode(ss)
    else:
      self.screen = pygame.display.set_mode(ss,pygame.FULLSCREEN) 
    #c = pygame.time.Clock() # create a clock object for timing
    self.draw_full_background()
    self.draw_surrounding_rect()
    self.draw_line_below_top()

  def init_touchscreen(self):
    self.ts = ft5406.Touchscreen()
    for touch in self.ts.touches:
      touch.on_press = self.touch_handler
      touch.on_release = self.touch_handler
      #touch.on_move = touch_handler
    self.ts.run()

  def touch_handler(self, event, touch):
    if event == TS_PRESS:
      self.presspos=(touch.x,touch.y)
      self.displaymanager.reset_timer()
    if event == TS_RELEASE:
      self.releasepos=(touch.x,touch.y)
      res = self.check_swipe()
      if res != 0:
        self.get_next_previous_item(res)
      #button pushed
      else :
        backbutton = pygame.Rect(
          (0,self.h/2-self.buttonsize[1]/2),
          self.buttonsize)
        if backbutton.collidepoint(self.releasepos):
          self.get_next_previous_item(-1)
        else:
          nextbutton = pygame.Rect(
            (self.w-self.buttonsize[0],self.h/2-self.buttonsize[1]/2),
            self.buttonsize)
          if nextbutton.collidepoint(self.releasepos):
            self.get_next_previous_item(1)
            
  
  def check_swipe(self):
    #dbgprint (self.presspos, self.releasepos)
    #go back
    if self.releasepos[0] - self.presspos[0] > 20:
      return -1
    #go further
    if self.presspos[0] - self.releasepos[0] > 20:
      return 1
    return 0

  def start_endless_touch_loop(self):
    while True:
      for event in pygame.event.get():
        if event.type == KEYDOWN:
          if event.key == K_ESCAPE:
            self.ts.stop()
            sys.exit()
        if event.type == USEREVENT + 1:
          self.draw_left_right_buttons_if_needed()

  def start_timer_from_new_items_check(self):
    pygame.time.set_timer(USEREVENT+1, 2000)

  def draw_full_background(self):
    self.screen.fill(self.background_color) 
    pygame.display.flip()

  def draw_surrounding_rect(self):
    margin = self.roundboxmargin
    surf_rect = pygame.Rect((margin[0],margin[1], self.w-2*margin[0], self.h-2*margin[1]))
    self.AAfilledRoundedRect(self.screen,surf_rect,self.linecolor,0.1)
    #pygame.display.update(surf_rect)
    self.clear_rounded_rect()
    
  def clear_rounded_rect(self):
    margin2 = (self.roundboxmargin[0]+1,self.roundboxmargin[1]+1)
    surf_rect2 = pygame.Rect((margin2[0],margin2[1], self.w-2*margin2[0], self.h-2*margin2[1]))
    self.AAfilledRoundedRect(self.screen,surf_rect2,(255,255,255),0.1)
    pygame.display.update()
    #set the background image
    self.background_color = self.screen.get_at((200,200))

  def AAfilledRoundedRect(self,surface,rect,color,radius=0.4):
    """
      AAfilledRoundedRect(surface,rect,color,radius=0.4)

      surface : destination
      rect    : rectangle
      color   : rgb or rgba
      radius  : 0 <= radius <= 1
    """

    rect         = Rect(rect)
    color        = Color(*color)
    alpha        = color.a
    color.a      = 0
    pos          = rect.topleft
    rect.topleft = 0,0
    rectangle    = Surface(rect.size,SRCALPHA)
    circle       = Surface([min(rect.size)*3]*2,SRCALPHA)
    draw.ellipse(circle,(0,0,0),circle.get_rect(),0)
    circle       = transform.scale(circle,[int(min(rect.size)*radius)]*2)

    radius              = rectangle.blit(circle,(0,0))
    radius.bottomright  = rect.bottomright
    rectangle.blit(circle,radius)
    radius.topright     = rect.topright
    rectangle.blit(circle,radius)
    radius.bottomleft   = rect.bottomleft
    rectangle.blit(circle,radius)

    rectangle.fill((0,0,0),rect.inflate(-radius.w,0))
    rectangle.fill((0,0,0),rect.inflate(0,-radius.h))

    rectangle.fill(color,special_flags=BLEND_RGBA_MAX)
    rectangle.fill((255,255,255,alpha),special_flags=BLEND_RGBA_MIN)

    return surface.blit(rectangle,pos)


  def draw_infos(self, fromm,time,subject,page,totalpages):
    offset = self.contentmargin
    txt = "De: " + fromm
    if subject.strip() != "":
      txt+="\nSujet: "+ subject;
    font = pygame.font.Font(None, 24)
    height = font.size("g")[1]*2+1
    rect = pygame.Rect((0,0, 600, height))
    text_surface = self.render_textrect(txt, font, rect, (0, 0, 0), 0)
    self.screen.blit(text_surface,(offset[0],offset[1]))
    
    txt = "Reçu le " + time + "\npage " + str(page) + "/" + str(totalpages)
    rect2 = pygame.Rect((0,0, 350, height))
    text_surface = self.render_textrect(txt, font, rect2, (0, 0, 0), 2)
    self.screen.blit(text_surface,(self.w-offset[0]-350,offset[1]))
    display.update(offset[0],offset[1],self.w-2*offset[0],height)

  def draw_line_below_top(self):
    offset = self.contentmargin
    pygame.draw.line(self.screen, self.linecolor,
      (offset[0],offset[1]+self.lineyoffset),
      (self.w-offset[0], offset[1]+self.lineyoffset),1)
    display.update(offset[0],offset[1]+self.lineyoffset,self.w-offset[0],3)

  def render_textrect(self, string, font, rect, text_color, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
           text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
            1 horizontally centered
            2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """
    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    for requested_line in requested_lines:
      if font.size(requested_line)[0] > rect.width:
        words = requested_line.split(' ')
        # if any of our words are too long to fit, return.
        for word in words:
          if font.size(word)[0] >= rect.width:
            #raise TextRectException, "The word " + word + " is too long to fit in the rect passed."
            dbgprint("ERROR line length1!");
        # Start a new line
        accumulated_line = ""
        for word in words:
          test_line = accumulated_line + word + " "
          # Build the line while the words fit.  
          if font.size(test_line)[0] < rect.width:
            accumulated_line = test_line 
          else: 
            final_lines.append(accumulated_line) 
            accumulated_line = word + " " 
        final_lines.append(accumulated_line)
      else: 
        final_lines.append(requested_line) 

    # Let's try to write the text out on the surface.
    surface = Surface(rect.size) 
    surface.fill(self.background_color)

    accumulated_height = 0 
    for line in final_lines: 
      if accumulated_height + font.size(line)[1] >= rect.height:
        #raise TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect."
        dbgprint("ERROR line length 2:",accumulated_height + font.size(line)[1],rect.height)
      #sometime rendering a line fails due to strange characters -> skip htat line
      try:
        if line != "":
          tempsurface = font.render(line, 1, text_color)
          if justification == 0:
            surface.blit(tempsurface, (0, accumulated_height))
          elif justification == 1:
            surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
          elif justification == 2:
            surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
          #else:
            #raise TextRectException, "Invalid justification argument: " + str(justification)
        accumulated_height += font.size(line)[1]
      except:
        pass

    return surface

  def clear_image_and_body(self):
    offset = self.contentmargin
    rect  = pygame.Rect(offset[0],offset[1]+self.imageyoffset,
      self.w-2*offset[0],
      self.h-offset[1]-self.imageyoffset-offset[1])
    surface = Surface(rect.size) 
    surface.fill(self.background_color)
    self.screen.blit(surface,rect.topleft)
    pygame.display.update(rect)

  def show_body (self,txt):
    offset = self.contentmargin
    self.clear_image_and_body()
    font = pygame.font.Font(None, 24)
    rect  = pygame.Rect(offset[0],self.imageyoffset+offset[1],
      self.w-offset[0]-offset[0],
      self.h-self.imageyoffset-offset[1]-offset[1])
    rendered_text = self.render_textrect(txt, font, rect, (0, 0, 0), 0)
    self.screen.blit(rendered_text, rect.topleft)
    pygame.display.update(offset[0],self.imageyoffset+offset[1],
      self.w-2*offset[0],
      self.h-self.imageyoffset-offset[1]-offset[1]) # update the display

  def show_image(self,path):
    self.clear_image_and_body()
    dbgprint("show path: " + path)
    offset = self.contentmargin
    img=pygame.image.load(path) 
  
    #rotate if needed
    #rotate = get_image_orientation(path)
    #if rotate != 0 :
    #  img = pygame.transform.rotate(img,rotate)
  
    #scale if needed
    new_w, new_h = get_aspect_scale(img.get_size()[0], img.get_size()[1],self.w-2*offset[0],self.h-offset[1]-self.imageyoffset-offset[1]);
    img = pygame.transform.scale(img, (int(new_w),int(new_h)))

    self.screen.blit(img,(offset[0],offset[1]+self.imageyoffset))
    pygame.display.update((offset[0],offset[1]+self.imageyoffset),(img.get_size())) # update the display

  def draw_left_right_buttons_if_needed(self):
    s1 = ""
    if self.histcontainer.has_previous_item():
      s1 = self.draw_button(1)
    else:
      s1 = self.clear_button(1)
      #dbgprint("clearing left")

    self.screen.blit(s1,(0,self.h/2-s1.get_size()[1]/2))
    pygame.display.update((0,self.h/2-s1.get_size()[1]/2),s1.get_size())

    s2 = ""
    if self.histcontainer.has_next_item():
      if self.histcontainer.has_unread_items():
        self.gpioManager.leds_on()
        s2 = self.draw_button(0,(255,0,0))
      else:
        self.gpioManager.leds_off()
        s2 = self.draw_button(0)
    else:
      #dbgprint("clearing right")
      if not self.histcontainer.has_unread_items():
        self.gpioManager.leds_off()
      s2 = self.clear_button(0)

    self.screen.blit(s2,(self.w-s2.get_size()[0],self.h/2-s2.get_size()[1]/2))
    pygame.display.update((self.w-s2.get_size()[0],self.h/2-s2.get_size()[1]/2),s2.get_size())

  def clear_button(self,left):
    surface = Surface(self.buttonsize)
    surface.fill((255,255,255))
    return surface

  def draw_button(self,left,color=(100,200,50)):
    #dbgprint("drawing button")
    surface = Surface(self.buttonsize)
    surface.fill((255,255,255))
    if left:
      pygame.draw.polygon(surface,color,
        ((0,self.buttonsize[1]/2),(self.buttonsize[0],0),(self.buttonsize[0],self.buttonsize[1])))
    else:
      pygame.draw.polygon(surface,color,
        ((self.buttonsize[0],self.buttonsize[1]/2),(0,0),(0,self.buttonsize[1])))
    return surface

  #np can be +1 or -1 or 0
  def get_next_previous_item(self, np):
    res = -1
    if np == -1:
      res = self.histcontainer.get_previous_item()
    elif np == 1:
      res = self.histcontainer.get_next_item()
    else:
      res = self.histcontainer.get_actual_element()
      if res != -1 :
        res = self.histcontainer.get_actual_element().get_actual_item()

    if res != -1 :
      fromm=self.histcontainer.get_actual_element().get_from_better()
      #date=self.histcontainer.get_actual_element().get_date()
      time=self.histcontainer.get_actual_element().get_time_locale_fr()
      subject=self.histcontainer.get_actual_element().get_subject()
      items=self.histcontainer.get_actual_element().get_nr_items()
      itemnr=self.histcontainer.get_actual_element().get_actual_item_nr()+1
      self.draw_infos(fromm,time,subject,itemnr,items)

      if "_body" in res:
        txt =self.histcontainer.get_actual_element().get_body_txt()
        self.show_body(txt)
      else:
        self.show_image(res)
      self.draw_left_right_buttons_if_needed()
    else:
      dbgprint("No email to show!")
    dbgprint("---------------------------")
  


# main routine
if __name__ == '__main__':
  
  historycontainer = HistElementContainer()
  displaymanager   = DisplayManager()

  emailReader = EmailReader(historycontainer)
  #emailReader.fetch_mail()

  smsReader = SmsReader(historycontainer)
  #smsReader.fetch_smses()

  stop_fetch_mail = call_repeatedly(5*60,emailReader.fetch_mail)
  stop_fetch_sms  = call_repeatedly(60,smsReader.fetch_smses)
  stop_check_bl = call_repeatedly(10, displaymanager.check_for_sleep)
  try:
    pit = PIT(historycontainer, displaymanager)
    #next doesn't return until escape is pressed
    pit.start_screen()
  finally:
    stop_check_bl()
    stop_fetch_mail() 
    stop_fetch_sms()
    del displaymanager


