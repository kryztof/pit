import glob
import os
import datetime
import time
import email
from email.message import EmailMessage
from email.header import decode_header
from utils import *
import PIL
from PIL import Image
import exifread
import base64
import locale
import quopri

class HistElement:
  gsmdict = dict()
  def __init__(self,outputdir):
    self.uid = -1;
    self.time = -1;
    self.typeke= -1;
    self.date = -1;
    self.fromm = -1;
    self.subject = -1;
    self.historydelim = "@@@@"
    self.outputdir = outputdir
    self.items = []
    self.actualitem = 0
    self.gsm_path = os.path.join(self.outputdir,'gsm_ref.txt')
    self.get_gsm_numbers()

  def get_previous_item(self):
    if len(self.get_items()) == 0:
      return -1
    if self.actualitem == 0:
      return -1
    self.actualitem -= 1
    return self.get_items()[self.actualitem]

  def get_next_item(self):
    if len(self.get_items()) == 0:
      return -1
    if self.actualitem+1 == len(self.get_items()):
      return -1
    self.actualitem +=1
    return self.get_items()[self.actualitem]

  def get_first_item(self):
    if len(self.get_items()) == 0:
      return -1
    self.actualitem = 0
    return self.get_items()[self.actualitem]
    
  def get_last_item(self):
    if len(self.get_items()) == 0:
      return -1
    self.actualitem = len(self.get_items())-1
    return self.get_items()[self.actualitem]

  # possibly the element has no items (ie body or pictures!)
  # the return -1
  def get_actual_item(self):
    self.get_items()
    if len(self.items) == 0 :
      return -1
    return self.get_items()[self.actualitem]

  def get_actual_item_nr(self):
    return self.actualitem

  def set_outputdir(self, odir):
    self.outputdir = odir

  def get_nr_items(self):
    return len(self.get_items())

  def from_message_no_items(self,uid,msg):
    self.uid    = int(uid)
    self.typeke = 'email'
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
      local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    self.time    = int(time.mktime(local_date.timetuple()))
    self.date    = msg['Date']
    self.fromm   = msg['From']
    #self.subject = str(quopri.decodestring(msg['Subject']).decode('utf-8')).strip()
    try:
      self.subject = decode_header(msg['Subject'])[0][0].decode('utf-8')
    except:
      self.subject = msg['Subject'].strip()
    #dbgprint("ssubject",msg['From'] )


  def from_history_no_items(self, histstring):
    strings = histstring.split(self.historydelim)
    if len(strings) != 6 :
      dbgprint("ERROR: length histstings is "+str(len(strings))+": " + histstring )
      return -1
    self.typeke  = strings[0]
    self.time    = int(strings[1])
    self.date    = strings[2]
    self.uid     = int(strings[3])
    self.fromm   = strings[4]
    self.subject = strings[5]
    return 0

  def from_sms(self, smsgsm, smsid, smscontent, smsdate):
    self.uid = int(smsid)
    self.typeke = 'sms'
    self.date = smsdate
    self.time = int(time.mktime(datetime.datetime.strptime(smsdate,'%Y-%m-%d %H:%M:%S').timetuple()))
    self.fromm = smsgsm
    self.subject = ""
    res = self.create_body(smscontent)
    return res

  def create_body(self,body):
    #dbgprint("body is" , body)
    new_body = ""
    decode=False
    #this base 64 is important to interprete accents!
    for line in body.splitlines(True):
      #dbgprint("line is", line)
      if "Content-" in line and "base64" in line:
        #dbgprint("decode true")
        decode=True
      #as long as there is more header info: clear the new_body
      if "Content-" in line:
        #dbgprint("clearing")
        new_body = ""
      if not "Content-" in line:
        #dbgprint("adding line", line,"--")
        new_body+=line
    #dbgprint("New_body is", new_body,"--")
    new_body = new_body.strip()
    if decode:
      new_body = str(base64.b64decode(new_body),'utf-8')
    else :
      try:
        #new_body = decode_header(new_body)[0][0].decode('utf-8')
        new_body = str(quopri.decodestring(new_body).decode('utf-8')).strip()
      except:
        pass

    new_body = new_body.strip()
    #dbgprint("New_body 2 is",len(new_body), ":", new_body,"--")
    if new_body != "":
      #dbgprint("new_body:",new_body, "-")
      filename = ""+str(self.uid)+"_body.txt"
      path = os.path.join(self.outputdir, filename )
      if os.path.isfile(path):
        os.remove(path)
      fp = open( path ,'a+',encoding='utf-8')
      fp.write(new_body)
      fp.close()
      self.get_items(True)
      return 1
    return -1

  """
  #rotate image if needed
  #        1: 'Horizontal (normal)',
  #        2: 'Mirrored horizontal',
  #        3: 'Rotated 180',
  #        4: 'Mirrored vertical',
  #        5: 'Mirrored horizontal then rotated 90 CCW',
  #        6: 'Rotated 90 CCW',
  #        7: 'Mirrored horizontal then rotated 90 CW',
  #        8: 'Rotated 90 CW'
  """
  @staticmethod
  def get_image_orientation(path):
    f = open(path,'rb')
    tags = exifread.process_file(f,stop_tag='Orientation')
    rotate = 0
    for tag in tags.keys():
      if "Image Orientation" in tag:
        if str(tags[tag]) == "Rotated 180":
          rotate = 180
        elif str(tags[tag]) == "Rotated 90 CCW": 
          rotate = 90
        elif str(tags[tag]) == "Rotated 90 CW": 
          rotate = -90
        break
    return rotate

  def create_attachment(self,attstr,attfilename):
    filename = ""+str(self.uid)+"_" + attfilename
    path = os.path.join(self.outputdir, filename )
    if os.path.isfile(path):
      os.remove(path)
    fp = open( path ,'ab+')
    fp.write(attstr)
    fp.close()
    #scale image if needed
    try:
      rotate = HistElement.get_image_orientation(path)
      img = Image.open(path)
      screenw,screenh = get_screen_size(1)
      new_w, new_h = get_aspect_scale(img.size[0], img.size[1],screenw,screenh)
      img = img.resize((new_w, new_h),PIL.Image.ANTIALIAS)
      img = img.rotate(rotate)
      img.save(path)
    except:
      dbgprint("ERROR in scaling img: " + path)
      pass
    self.get_items(True)

  def get_uid(self):     return self.uid
  def get_time(self):    return self.time
  def get_time_locale_fr(self):    
    locale.setlocale(locale.LC_TIME,'fr_BE')
    t = time.localtime(self.time)
    return time.strftime("%d %b %Y à %Hh%M",t)
  def get_type(self):    return self.typeke
  def get_date(self):    return self.date
  def get_from(self):    return self.fromm
  def get_from_better(self):
    if self.typeke == 'sms':
      name = self.find_name_of_gsmnummer(self.fromm)
      if name != -1:
        return name
      return self.fromm
    else:
      return self.fromm.split('<')[0]
  def get_subject(self): return self.subject

  def to_string(self,compact):
    line  = self.typeke     + self.historydelim 
    line += str(self.time)  + self.historydelim 
    line += self.date       + self.historydelim 
    line += str(self.uid)   + self.historydelim 
    line += self.fromm      + self.historydelim 
    line += self.subject.strip()    
    if not compact:
      line += "items: "
      for item in self.get_items():
        line += item + " " 
    line += "\n"
    #dbgprint("to_string " + line)
    return line

  def get_items(self, forcereread = False):
    if self.items == [] or forcereread:
      self.items = glob.glob(self.outputdir + "/" + str(self.uid)+ "_*")

      #now make sure the body comes first in the item list
      items = []
      for item in self.items:
        if str(self.uid)+"_body" in item:
          items.append(item)
      for item in self.items:
        if str(self.uid)+"_body" not in item:
          items.append(item)
      self.items=items
    return self.items

  def get_body_path(self):
    for item in self.get_items():
      if str(self.uid)+"_body" in item:
        return item
    return -1

  def get_body_txt(self):
    path = self.get_body_path()
    txt=""
    with open(path, 'r',encoding='utf-8') as fd:
      txt = fd.read()
    return txt

  def get_attachments_path(self):
    res = []
    for item in self.get_items():
      if str(uid)+"_body" not in item:
        res.append(item)
    return res

  def get_nr_attachments(self):
    return len(self.get_attachments())

  def get_attachment_path(self,nr):
    if nr < len(self.get_attachments()):
      return self.get_attachments()[nr]
    return -1
  
  def get_gsm_numbers(self):
    if len(HistElement.gsmdict) >0 :
      return
    txt = ""
    #dbgprint("self.gms_path", self.gsm_path)
    with open(self.gsm_path,'a+') as fd:
      for line in fd:
        strs = line.split(" ")
        gsm = strs[0].strip()
        del strs[0]
        name = " ".join(strs)
        if name.strip() != "":
          HistElement.gsmdict[name]=gsm

  def find_name_of_gsmnummer(self,gsmstr):
    for name,gsm in HistElement.gsmdict.items():
      if gsm == gsmstr:
        return name
    return -1
