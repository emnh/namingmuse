"""
Simple library speaking CDDBP to CDDB servers.
$Id: cddb.py,v 1.24 2004/09/10 22:21:33 emh Exp $
"""

import socket,string
socket.socket
import getpass
import re
from exceptions import *

#defaultserver = "bash.no"
#defaultport = 1863
defaultserver = "freedb.freedb.org"
defaultport = 8880
defaultprotocol = 6
version="0.20"

# cddb read replies
READ_OK = 210
CDDB_CONNECTION_TIMEOUT = 530
CDDB_ALREADY_READ = "502"

class CDDBPException(Exception):

    def __init__(self,code,resp):
        Exception.__init__(self)
        self.code=code
        self.resp=resp

    def __str__(self):
        return "CDDBP exception: %d %s" % (self.code, self.resp)

class SmartSocket:
    """Simple socket-like class with some extra intelligence for telnet-based
    protocols."""

    def __init__(self,dbg=0,recvsize=1024):
        self.dbg = dbg
        self.recvsize = recvsize
        self.sock = None

    def connect(self, server, port):
        "Connects to the server at the given port."
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((server, port))
        except socket.error, (errno, errstr):
            raise NamingMuseError(errstr)
            

    def flush(self):
        flushed = self.sock.recv(self.recvsize)
        if self.dbg:
            print "Trashing data:",flushed

    def send(self, message, term):
        """Sends a string to the server, returning the response terminated
        by 'term'."""
        if not self.sock:
            raise CDDBException("trying to use smartsocket with no connection")
	self.sock.send(message+"\n")
	if self.dbg:
	    print "Send: "+message

        return self.receive(term)

    
    def receive(self,term):
        """Receives a string from the server. Blocks until 'term' has been
        received."""
        data=""
        while 1:
            newdata = self.sock.recv(self.recvsize)
            data = data + newdata
            if data[-len(term):]==term or data.startswith('230 ') \
                    or data.startswith('401 ') \
                    or data.startswith(CDDB_ALREADY_READ + " "):
                # 230 means that we did something nasty and the server is
                # hanging up on us. It doesn't provide the needed terminator
                # then.
                # 401 means a CD read failed. It doesn't provide terminator.
                break
            
	if self.dbg:
	    print "Recv: "+data
	return data

    def disconnect(self):
        "Disconnects from the remote server."
        self.sock.close()

    def __del__(self):
        if self.sock: 
            self.disconnect()

class CDDBP(object):
    "This class can speak the CDDBP protocol, level 6."
    __connected = False

    def __init__(self, user='nmuse', localhost='localhost'):
        self.sock = SmartSocket(0,8192)
        self.user = getpass.getuser()
        self.localhost = socket.gethostname()
        self.client = "PyCDDBPlib"
        
    def __decode(self,resp):
        code = int(resp[:3])
        result = resp[4:]
        return (code,result)

    def __getattribute__(self, name):
        if name in ("lscat", "sites", "query", "setproto", 
                    "getRecord", "motd", "stat", "ver", "whom"):
            if not self.__connected:
                self.connect()
        return super(CDDBP, self).__getattribute__(name)
        
    def connect(self, server=defaultserver, port=defaultport):
        "Connects to the server and does the initial handshake."
        self.server=server
        self.port=port
        self.sock.connect(self.server,self.port)
        self.__connected = True
        (code,resp)=self.__decode(self.sock.receive("\r\n"))
        if code>399:
            raise CDDBPException(code,resp)

        (code,resp)=self.__decode(self.sock.send("cddb hello %s %s %s %s" % \
                                                 (self.user,self.localhost,
                                                  self.client,version),
                                                 "\r\n"))
        if code>399:
            raise CDDBPException(code,resp)

        #set the server proto
        self.setproto()

    def reconnect(self, server=defaultserver, port=defaultport):
        self.sock.disconnect()
        self.connect(server, port)

    def setproto(self,proto=defaultprotocol):
        '''Sets the proto level on the server.
           5 is the goodest
           6 is the goodest with UTF8 strings
        '''
        
        (code,resp)=self.__decode(self.sock.send("proto %d "%proto, "\r\n"))

        if code>399:
            raise CDDBPException(code,resp)

    def lscat(self):
        "Returns a list of the CDDB music categories."
        (code,resp)=self.__decode(self.sock.send("cddb lscat","\r\n.\r\n"))
        if code>399:
            raise CDDBPException(code,resp)
        return string.split(resp,"\r\n")[1:-2]

    def sites(self):
        """Returns a list of the public CDDB servers, as (server, port,
        latitude, longitude, description) tuples."""
        (code,resp)=self.__decode(self.sock.send("sites","\r\n.\r\n"))
        if code>399:
            raise CDDBPException(code,resp)       

        res=[]
        for item in string.split(resp,"\r\n")[1:-2]:
            items=string.split(item)
            res.append((items[0],items[1],items[2],items[3],
                        string.join(items[4:])))

        return res

    def query(self, query):
        cddbid = query[0]
        num_tracks = query[1]

        query_str = (('%08lx %d ') % (cddbid, num_tracks))
        for i in query[2:]:
            query_str = query_str + ('%d ' % i)

        decodeable =self.sock.send("cddb query %s" %query_str, "\r\n")
        (code,resp)=self.__decode(decodeable)

        if code == 202:
            return (code,resp)
        
        if code>399:
            raise CDDBPException(code,resp)

        res=[]
        for item in resp.split("\r\n")[1:-2]:
            splitted = item.split() 
            genreid = splitted[0]
            cddbid = splitted[1]
            title = string.join(splitted[2:])
            res.append({
                    "genreid": genreid,
                    "cddbid": cddbid,
                    "title": title
                    })

        return code,res

    def getRecord(self, genre, cddbid):
        '''
        Read raw freedb record from database
        '''
        (code,resp)=self.__decode(self.sock.send("cddb read %s %s" \
                %(genre, cddbid), "\r\n.\r\n"))
        if code > 399:
            raise CDDBPException(code,resp)
        elif code == READ_OK:
            # get rid of first line (server header)
            freedbrecord = resp.split("\r\n", 1)[1]
        else:
            raise NotImplementedException("cddb read: code %u" % code)
        return freedbrecord.decode('UTF-8').encode(self.encoding, 'replace')
        
    def motd(self):
        "Returns the message of the day from the server."
        (code,resp)=self.__decode(self.sock.send("motd","\r\n.\r\n"))
        if code>399:
            raise CDDBPException(code,resp)

        pos=string.find(resp,"\n")
        return resp[pos+1:-3]

    def stat(self):
        "Returns a hash table of the different server properties."
        (code,resp)=self.__decode(self.sock.send("stat","\r\n.\r\n"))
        if code>399:
            raise CDDBPException(code,resp)

        res={}
        for item in string.split(resp,"\r\n")[1:-2]:
            items=string.split(item,":")
            if len(items)>=2:
                item1=string.strip(items[1])
                if item1!="":
                    res[string.strip(items[0])]=item1

        return res

    def ver(self):
        "Returns a (servername, version, copyright) tuple."
        (code,resp)=self.__decode(self.sock.send("ver","\r\n"))
        if code>399:
            raise CDDBPException(code,resp)

        items=string.split(resp)
        return (items[0],items[1],string.join(items[2:]))

    def flush(self):
        return self.sock.flush()

    def whom(self):
        "Returns a list of (pid, client, user, ip) tuples."
        (code,resp)=self.__decode(self.sock.send("whom","\r\n.\r\n"))
        if code>399:
            raise CDDBPException(code,resp)
        
        res=[]
        for item in string.split(resp,"\r\n")[2:-2]:
            items=string.split(item)
            if len(items)>3:
                res.append((items[0],items[1],items[2],items[3][1:-1]))

        return res
        
    def quit(self):
        self.sock.send("quit","\r\n")

    def __del__(self):
        try:
            self.sock.disconnect()
        except:
            pass

    # Missing: update, write
