#!/usr/bin/env python3

import sys
import imaplib
import getpass
import email
from email import policy
from email.message import EmailMessage
from email.contentmanager import ContentManager, raw_data_manager
from email.parser import BytesParser
import datetime
import os
import glob
import time
from histelement import *
from histelementcontainer import *
from utils import *
import pygame

import traceback


class EmailReader:

  def __init__(self,historycontainer):
    self.imap = 0;
    self.histcontainer = historycontainer
    self.fetching_mail = 0
    self.pw = ""
    self.email = ""
    self.read_email_pw()


  def read_email_pw(self):
    path = "/etc/pit.conf"
    fd = open(path,'r')
    fd.seek(0)
    for line in fd:
      l = line.split(" ")
      if len(line) > 0 and line[0]!='#' and len(l) == 2:
        self.email = l[0]
        self.pw = l[1]
        break;
    fd.close()

  def fetch_mail(self):
    if self.fetching_mail == 0:
      self.fetching_mail = 1
      dbgprint("#############################")
      dbgprint("Fetching emails!")
      self.post_progress(10)
      try:
        if self.login() == 0 :
          self.post_progress(30)
          self.open_mailbox()
          self.post_progress(80)
          self.logout()
      except:
        try:
          self.logout()
        except:
          pass
        dbgprint("EXCEPTION DURING FETCHING EMAILS:");
        dbgprint(sys.exc_info()[0])
        dbgprint(sys.exc_info()[1])
        dbgprint(sys.exc_info()[2])
        traceback.print_stack()

      self.post_progress(100)
      dbgprint("Fetching emails done!")
      dbgprint("#############################")
      self.fetching_mail = 0

  def login(self):
    self.imap = imaplib.IMAP4_SSL('imap.gmail.com')
    try:
      self.imap.login(self.email, self.pw);
      return 0
    except imaplib.IMAP4.error:
      dbgprint("LOGIN FAILED!!! ")
      return -1

  def logout(self):
    self.imap.logout()

  def open_mailbox(self):
    rv, mailboxes = self.imap.list()
    #if rv == 'OK': dbgprint( "Mailboxes:", mailboxes)
    rv, data = self.imap.select("INBOX",1) ; #true = readonly
    self.post_progress(40)
    if rv == 'OK':
        dbgprint("Processing mailbox...")
        self.process_mailbox()
        self.imap.close()
    else:
      dbgprint("Error opening INBOX!")

  def process_body(self,body,el):
    if el != -1 :
      el.create_body(body)
  
  def process_attachments(self,msg,el):
    #dbgprint("Content main type:", msg.get_content_maintype())
    if msg.get_content_maintype() != 'multipart':
      return
  
    for part in msg.walk():
      #dbgprint("part:", part.get_content_maintype())
      if part.get_content_maintype() == 'multipart':
        continue
      #dbgprint('Content-disposition',part.get('Content-Disposition'))
      #dbgprint("payload:",part.get_payload(decode=True),"------------")
      if part.get('Content-Disposition') is None:
        continue
  
      attfn= part.get_filename()
      #dbgprint("Filename:", attfn)
      if el != -1:
        el.create_attachment(part.get_payload(decode=True),attfn)
      else:
        dbgprint("ERROR: Not Creating attachment!")
  
  def add_msg_to_history(self,uid,msg):
    dbgprint("Adding email message to history")
    self.histcontainer.add_element_from_message(uid,msg)

  def remove_deleted_msgs_from_history(self, existing_msguids):
    dbgprint("Removing existing email message")
    msguids_int = list(map(int,existing_msguids))
    for el in self.histcontainer.get_elements('email'):
      if el.get_uid() not in msguids_int:
        self.histcontainer.delete_element(el.get_uid())
      
  def mark_msg_as_read(self,msguid):
    #doesn't work...
    self.imap.uid('store', str(msguid), '+FLAGS', '\Seen')

  def process_mailbox(self):
    rv, data = self.imap.uid('search',None, "ALL")
    if rv != 'OK':
      dbgprint("No messages found!")
      return

    #delete removed messages
    self.remove_deleted_msgs_from_history(data[0].split())
    self.post_progress(50)
      
    #get last history uid
    lastmessage=0
    if self.histcontainer.get_nr_elements('email') > 0:
      lastmessage = self.histcontainer.get_last_element('email').get_uid()

    #lastmessage = 35
    dbgprint("last element uid: " + str(lastmessage))

    #loop over all messages and download new ones
    if (int(data[0].split()[-1])-lastmessage) > 0 :
      progressstep = 30/(int(data[0].split()[-1])-lastmessage)
      progressactual = 50
      for uid in data[0].split():
        if int(uid) <= lastmessage:
          continue
        rv, data = self.imap.uid('fetch', uid, '(RFC822)')
        if rv != 'OK':
          dbgprint("ERROR getting message " + uid)
          continue
        #dbgprint("New message UID: "+ str(int(uid))) 
        msg = email.message_from_bytes(data[0][1])
        msg2 = BytesParser(policy=policy.default).parsebytes(data[0][1])
        #dbgprint("BODY:",msg2.get_body(),"------------------")
        body = msg2.get_body(preferencelist=('plain', 'html'))

        el = self.histcontainer.make_element_from_message(int(uid),msg)
        self.process_body(str(body),el)
        self.process_attachments(msg,el)
        self.histcontainer.add_element(el)

        self.mark_msg_as_read(int(uid))
        progressactual+=progressstep
        self.post_progress(progressactual)

  def body_test(self,msg):
    text = ""
    if msg.is_multipart():
      html = None
      for part in msg.get_payload():
        print (part.get_content_type(), part.get_content_charset())
        if part.get_content_charset() is None:
        # We cannot know the character set, so return decoded "something"
          text = part.get_payload(decode=True)
          print("text: ", text)
          continue
        charset = part.get_content_charset()
        print("charset",charset)

        if part.get_content_type() == 'text/plain':
          text = part.get_payload(decode=True).decode('utf8', 'replace')

        if part.get_content_type() == 'text/html':
          html = part.get_payload(decode=True).decode('utf8', 'replace')

      if text is not None:
        return text.strip()
      else:
        return html.strip()
    else:
      text = msg.get_payload(decode=True).decode('utf8', 'replace')
      return text.strip()

  def print_msg(self,msg):
    if 0 == 1 :
      dbgprint("type:" + str(type(msg)))
      dbgprint("body:" + str(body));
      dbgprint('Message:', msg['Subject'])
      dbgprint('Message-ID:', msg['Message-ID'])
      dbgprint('FROM:', msg['From'])
      dbgprint('Subject:', msg['Subject'])
      dbgprint('Content-Type:', msg['Content-Type'])
      date_tuple = email.utils.parsedate_tz(msg['Date'])
      if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        dbgprint("Local Date:", local_date.strftime("%a, %d %b %Y %H:%M:%S"))
      dbgprint("\n")

    if 1==1 :
      for key in msg:
        dbgprint("key:" + str(key)); 
        #print(str(key) + ": " + str(msg[key])); 
    dbgprint("_________________________"); 

  def post_progress(self, percentage):
    emailprogressevent = pygame.event.Event(pygame.USEREVENT+3, progress=percentage)
    pygame.event.post(emailprogressevent)

#if __name__ == '__main__':
#  emailReader = EmailReader()
#  emailReader.fetch_mail()
