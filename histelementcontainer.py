import glob
import os
import datetime
import time
from email.message import EmailMessage
from histelement import *
from utils import *

class HistElementContainer:
  def __init__(self):
    self.histelements = []
    self.outputdir = "/home/pi/.pit"
    self.historyfilename = "history.txt"
    self.historypath = os.path.join(self.outputdir,self.historyfilename)
    self.actualelement = -1
    self.counteritemsread = -1
    self.read_history()

  def do_history_save_when_item_set_to_read(self):
    counter=0
    for el in self.histelements:
      if el.is_read() == 0:
        counter+=1
    if counter != self.counteritemsread:
      self.counteritemsread = counter
      self.save_history()

  def get_next_item(self):
    self.do_history_save_when_item_set_to_read()
    if self.actualelement == -1:
      return -1
    #next can happen when element is deleted (from browser f.e.)
    if self.actualelement >= len(self.histelements) :
      self.actualelement = len(self.histelements)-1
      item = self.histelements[self.actualelement].get_first_item()
    else:
      item = self.histelements[self.actualelement].get_next_item()
    if item != -1:
      return item
    else:
      #no next element in container
      if self.actualelement == len(self.histelements) -1:
        return -1
      else:
        self.actualelement +=1
        return self.histelements[self.actualelement].get_first_item()

  def get_previous_item(self):
    self.do_history_save_when_item_set_to_read()
    if self.actualelement == -1:
      return -1
    #next can happen when element is deleted (from browser f.e.)
    if self.actualelement >= len(self.histelements) :
      self.actualelement = len(self.histelements)-1
      item = self.histelements[self.actualelement].get_first_item()
    else:
      item = self.histelements[self.actualelement].get_previous_item()
    if item != -1:
      return item
    else:
      if self.actualelement == 0 :
        return -1
      else:
        self.actualelement -= 1
        return self.histelements[self.actualelement].get_last_item()

  def has_next_item(self):
    # can happen when element gets deleted
    if self.actualelement >= len(self.histelements):
      self.actualelement = len(self.histelements)-1

    if len(self.histelements) > 0:
      el = self.histelements[self.actualelement]
      if len(self.histelements)-1 == self.actualelement and el.get_actual_item_nr() == el.get_nr_items()-1:
        return False
      return True
    return False

  def has_previous_item(self):
    # can happen when element gets deleted
    if self.actualelement >= len(self.histelements):
      self.actualelement = len(self.histelements)-1

    if len(self.histelements) > 0:
      el = self.histelements[0]
      if 0 == self.actualelement and el.get_actual_item_nr() == 0:
        return False
      return True
    return False

  def get_actual_element(self):
    if self.actualelement == -1:
      return -1
    if len(self.histelements) == 0:
      return -1
    # can happen when element gets deleted
    if self.actualelement >= len(self.histelements):
      self.actualelement = len(self.histelements)-1
    return self.histelements[self.actualelement]

  def read_history(self):
    if os.path.exists(self.outputdir) == False:
      os.makedirs(self.outputdir)

    fd = open(self.historypath,'a+')
    fd.seek(0)
    for line in fd:
      if len(line) > 0:
        histEl = HistElement(self.outputdir)
        res = histEl.from_history_no_items(line)
        if res != -1 :
          self.histelements.append(histEl)
        else:
          dbgprint("ERROR in history file, skipping element: '" + line + "'")
      self.sort_history()
    self.actualelement=len(self.histelements)-1
    fd.close()

  def sort_history(self):
    self.histelements.sort(key=lambda x:x.time, reverse=False)

  def save_history(self):
    fd = open(self.historypath,'w'); #will truncate the file
    dbgprint("saving history:")
    counter = 0
    for el in self.histelements:
      dbgprint("saving line",counter, ":", el.to_string(True).strip())
      fd.write(el.to_string(True))
      counter +=1
    fd.close()
    
  def get_element(self,uid,typeke=''):
    for el in self.histelements:
      if typeke == '' :
        if el.get_uid() == uid:
          return el
      else :
        #dbgprint("into else",uid,typeke,":",el.get_type(), str(el.get_uid()))
        if el.get_type() == typeke and el.get_uid() == int(uid):
          #dbgprint("returning an element")
          return el
    return -1

  def get_elements(self, typeke):
    if typeke == '' :
      return self.histelements
    else:
      res = []
      for el in self.histelements:
        if el.get_type() == typeke:
          res.append(el)
      return res

  def get_nr_elements(self,typeke=''):
    if typeke == '' :
      return len(self.histelements)
    counter = 0
    for el in self.histelements:
      if el.get_type() == typeke:
        counter +=1
    return counter

  #typeke can be 'email' or 'sms'
  def get_last_element(self,typeke):
    if len(self.histelements) > 0:
      for el in reversed(self.histelements):
        if el.get_type() == typeke:
          return el
    return -1

  def make_element_from_message(self,uid,msg):
    #dbgprint("Adding element " + str(uid))
    #do not add element if it already exists
    #if self.get_element(uid,'email') == -1 :
    el = HistElement(self.outputdir)
    el.from_message_no_items(uid,msg)
    return el

  def add_element(self,el):
    #if the element exists in list -> delete it
    # body and attachemnt is not deleted as these are overwritten
    for ele in self.histelements:
      if ele.get_uid() == el.uid :
        self.histelements.remove(ele)
    #now add the element
    self.histelements.append(el)
    self.sort_history()
    self.save_history()
    if self.actualelement == -1:
      self.actualelement=len(self.histelements)-1
    #else:
      #dbgprint("Not adding email with uid", uid, ". Element already exists.")

  def add_element_from_sms(self, smsgsm, smsid, smscontent, smsdate):
    #do not add element if it already exists
    if self.get_element(smsid,'sms') == -1 :
      el = HistElement(self.outputdir)
      res = el.from_sms(smsgsm, smsid, smscontent, smsdate)
      if res == 1:
        self.histelements.append(el)
        self.sort_history()
        self.save_history()
        if self.actualelement == -1:
          self.actualelement=len(self.histelements)-1
      #else :
        #dbgprint("Not adding sms with uid", smsid, ". Element already exists.")

  def delete_element(self,uid):
    for el in self.histelements:
      if el.get_uid() == uid :
        self.histelements.remove(el)
    for filename in glob.glob(self.outputdir + "/" + str(uid)+ "_*"):
      os.remove(filename)
    self.save_history()

  def has_unread_items(self):
    for el in self.histelements:
      if el.is_read() == 0:
        return True
    return False

  def to_string(self):
    dbgprint("History Container:")
    for el in self.histelements:
      el.to_string(False)
    dbgprint("---------------")
