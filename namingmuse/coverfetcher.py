#!/usr/bin/python

import os,re,sys,types,urllib2,urllib
from xml.dom import minidom

class CoverFetcher:

    amazonLicense = "D1URM11J3F2CEH";


    def getCover(self, artist, album, mode="lite", size="1", albumonly="False"):

        """    fetcher->getCover( artist, album, keyword, CoverFetcher::heavy, edit, 2, false );
        """

        keyword = ""

        if artist == album:
            keyword = album
        else:
            keyword = artist + " - " + album

        #url =  "http://xml-eu.amazon.com/onca/xml3?t=webservices-20&dev-t=%s&KeywordSearch=%s&mode=music&type=%s&page=1&f=xml" %(
        url = "http://xml-eu.amazon.com/onca/xml3?f=xml"
        url += "&t=%s" % "webservices-20"
        url += "&dev-t=%s" % self.amazonLicense
        url += "&type=%s" % mode 
        #if _supportedLocales[locale][0]:
        #url += "&locale=%s" % _supportedLocales[locale][0]
        #if page:
        #url += "&page=%s" % page
        #if product_line:
        url += "&mode=%s" % "music"
        url += "&%s=%s" % ("KeywordSearch", urllib.quote(keyword))

        urlobj = urllib2.urlopen(url)
        self.xmldoc = minidom.parse(urlobj)
        imageurl = self._getImageUrl()
        imagedata = self._getImage(imageurl)
        return imagedata

    def _getImageUrl(self, imagesize=1):
        if imagesize == 0:
            imageurlnodes = self.xmldoc.getElementsByTagName('ImageUrlSmall')
        if imagesize == 2:
            imageurlnodes = self.xmldoc.getElementsByTagName('ImageUrlMedium')
        else:
            imageurlnodes = self.xmldoc.getElementsByTagName('ImageUrlLarge')
        for imageurl in imageurlnodes:
            print imageurl.firstChild.data
            return imageurl.firstChild.data
            #print imageurl.toprettyxml()

    def _getImage(self, imageurl):
        urlobj = urllib2.urlopen(imageurl)
        return urlobj.read()

if __name__== "__main__":
    cf = CoverFetcher()
    cf.getCover("Turboneger", "Scandinavian", "lite",1,False)
