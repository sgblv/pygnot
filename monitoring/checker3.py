#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
try:
  from xml.etree import ElementTree # for Python 2.5 users
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import string
import time
import urllib2,ConfigParser
import logging,logging.handlers
import sys
import os
def log2mail(mess,level="DEBUG"):
    ##################### send logs to mail describe here #########################################
    logger = logging.getLogger('myapp')
    hldr = logging.handlers.SMTPHandler('localhost','buylov@b.urg','buylov.sergey@corpguru.ru','monitoring')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hldr.setFormatter(formatter)
    logger.addHandler(hldr)
    logger.setLevel(logging.DEBUG)
    try : logger.info(mess)
    except : sys.stderr.write(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())+"Logger works incorrect")
    mess=mess+time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    return mess
    

class Sites:
    def __init__(self, url, keyword, maxfailed):
        self.url = url
        self.keyword = keyword
        self.maxfailed = maxfailed
        failedcnt = 0
        self.failedcnt=failedcnt
 #   def status(self):
 #       print "debug",self.failedcnt,self.maxfailed
 #       a=self.failedcnt>self.maxfailed
 #       print "debug",a
 #       return a
    def checker(self):
        req = urllib2.Request(self.url)
        try:
            resp = urllib2.urlopen(req)
        except Exception, e:
            sys.stdout.write(str(log2mail(str(self.url)+str(e))))
            return 1
        page=resp.read()
        headers=resp.headers.dict
        if  resp.code<>200:
            sys.stdout.write(log2mail(str(self.url)+" response code " +str(resp.code) + " " + str(headers) +" debug "))
            return 1
        if  self.keyword not in page:            
            sys.stdout.write(str(log2mail(str(self.url)+" no such keyword here " +str(resp.headers.dict)+str(page))))
            return 1
        return 0
    def check(self):
        self.failedcnt=self.failedcnt+self.checker()
        return self.failedcnt-self.maxfailed

class Notifications:
    def __init__(self,login,password):
        self.mess = 'test'
        self.lastnotificationtime=time.time()
        self.login = login
        self.password = password
    def _mayisent(self):
        if (time.time()-self.lastnotificationtime)<120:
            return False
        return True
    def smsfromcalendar(self,mess):
        if self._mayisent():
            self.mess = mess
            self._calendar()
            self.lastnotificationtime=time.time()
            return True
        return False
    def _calendar(self):
        try:
            #authorization##############################################
            calendar_service = gdata.calendar.service.CalendarService()
            calendar_service.email = self.login
            calendar_service.password = self.password
            calendar_service.source = 'Google-Calendar_GURU_WEBSITE_CHECKER-3.0'
            calendar_service.ProgrammaticLogin()
        #################################################################
            #create event################################################
            event = gdata.calendar.CalendarEventEntry()
            event.title = atom.Title(text=self.mess)
            event.content = atom.Content(text=self.mess)
            start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() +900))
            end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() +1200))
            event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))
            new_event = calendar_service.InsertEvent(event, '/calendar/feeds/default/private/full')
        #############################################################
            #create sms-notification#####################################
            new_event.when[0].reminder.append(gdata.calendar.Reminder(minutes=5))
            calendar_service.UpdateEvent(new_event.GetEditLink().href, new_event)
        except Exception,e:
            sys.stderr.write(log2mail(str(e)))

def main():
    #create pid file
    if os.path.exists('/tmp/checker3.pid'):
        sys.stderr.write(str(log2mail("pid file exists")))
        sys.exit("pid file exists")
    pid=open('/tmp/checker3.pid',"w")
    pid.write(str(os.getpid()))
    pid.close()
    ###create object for create events in google calendar
    mainconfig = ConfigParser.RawConfigParser()
    mainconfig.read(sys.argv[1])
    sms = Notifications(mainconfig.get('auth','email'),mainconfig.get('auth','password'))
    ######################################################################################
    #create dict which contain items objects
    itemconfig = ConfigParser.RawConfigParser()
    itemconfig.read(sys.argv[2])
    ITEMS={}.fromkeys(itemconfig.sections())
    for i  in ITEMS:
        ITEMS[i]=Sites(itemconfig.get(i,'url'),itemconfig.get(i,'keyword'),int(mainconfig.get('main','maxfailed')))
    ###########################################################################################################
    ###########main checker cycle################3
    count=0
    while True:
        count=count+1
        print count
        for i  in ITEMS:
            if ITEMS[i].check()>0:
                mess = str(i)+str("in status failed now")
                #print mess
                sms.smsfromcalendar(mess)
        time.sleep(0.1)
    
     

if __name__ == "__main__":
    main()

