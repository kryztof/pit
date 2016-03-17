#!/usr/bin/python
import subprocess
import string
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from histelement import *
from histelementcontainer import *
from utils import *


class SmsReader:
  def __init__(self,historycontainer):
    self.token = -1
    self.smses = -1
    self.histcontainer = historycontainer
    self.reading = 0

  def fetch_smses(self):
    if self.reading == 1 :
      dbgprint("Already busy reading sms messages")
      return
    dbgprint("TTTTTTTTTTTTTTTTTTTTTTTTTTTTT")
    dbgprint("Fetching sms!")
    self.reading = 1
    self.get_token()
    if self.token != -1:
      self.get_smses()
      self.parse_sms_answer()
    self.reading = 0
    dbgprint("Fetching sms done!")
    dbgprint("TTTTTTTTTTTTTTTTTTTTTTTTTTTTT")

  def get_token(self):
    dbgprint("GETTING TOKEN")
    #self.token = subprocess.check_output(['curl', '-s',
    #'http://192.168.8.1/api/webserver/token'])
    try: 
      url='http://192.168.8.1/api/webserver/token'
      request  = urllib.request.Request(url)
      response = urllib.request.urlopen(request)
      root = ET.fromstring(response.read())
      self.token = root.find('token').text
      #dbgprint(self.token)
    except:
      dbgprint("ERROR reading token")
      self.token = -1

  """
  Next was copied from the chome browser when opening the page SMS
  and looking into de debug console under network filtering with
  sms-list. Then you can right click on it and copy as cUrl. Then
  the url was simplified (unnecessary stuff was removed).
  curl 'http://192.168.8.1/api/sms/sms-list' -H '__RequestVerificationToken: 1185367643' --data '<?xml version="1.0" encoding="UTF-8"?><request><PageIndex>1</PageIndex><ReadCount>20</ReadCount><BoxType>1</BoxType><SortType>0</SortType><Ascending>0</Ascending><UnreadPreferred>0</UnreadPreferred></request>'
  """
  def get_smses(self):
    dbgprint("GETTING SMSES")
    if self.token == -1:
      dbgprint ("ERROR invalid token")
      return -1
    #try:
    xml = '<?xml version="1.0" encoding="UTF-8"?><request><PageIndex>{:d}</PageIndex><ReadCount>10</ReadCount><BoxType>1</BoxType><SortType>0</SortType><Ascending>0</Ascending><UnreadPreferred>0</UnreadPreferred></request>'
    url = 'http://192.168.8.1/api/sms/sms-list'
    headers = {'__RequestVerificationToken': self.token ,
              'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8'}

    page = 1
    maxpages = 100
    self.smses = []
    while True:
      xmlp = xml.format(page)
      data = xmlp.encode('utf-8')
      req = urllib.request.Request(url, data, headers)
      response = urllib.request.urlopen(req)
      response = response.read().decode('utf-8')
      if "error" in response:
        dbgprint("Error reading smses: ",response)
        break
      if "<Count>0</Count>" in response:
        break
      self.smses.append(response)
      #dbgprint(response)
      page += 1
      if page == maxpages:
        break
    #except Exception as e:
      #dbgprint(e)
      #self.smses = -1


  def parse_sms_answer(self):
    dbgprint("PARSING SMS ANSWER")
    if len(self.smses) == 0 :
      dbgprint("ERROR: len(self.smses) == 0")
      return -1

    for page in self.smses:
      #dbgprint(page)
      root = ET.fromstring(page)
      for msg in root.iter('Messages'):
        for child in msg:
          nr = child.find('Phone').text
          content = child.find('Content').text
          date = child.find('Date').text
          #dbgprint("sms date:", date)
          index = child.find('Index').text
          #smstype = child.find('SmsType').text
          self.histcontainer.add_element_from_sms(nr,index,content,date)
          #dbgprint (nr,index,smstype,content, date)
    return 0

#if __name__ == '__main__':
#  smsReader = SmsReader()
#  smsReader.fetch_smses()
