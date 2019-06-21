#!/usr/bin/python
import logging
 
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count
# import libemu
from cachetools import LRUCache
from scapy.layers.all import TCP, UDP, Raw
from scapy.all import sniff
import Queue
from termcolor import colored
import sys, os
from threading import *
import time
 
MAIN_LOG = None
PORTS = map(int,open("LISTPORT").read().splitlines())
print PORTS
LIST_CONNECT = {}
 
BLACKLIST_KEYWORDS = {}
for port in PORTS:
    if not os.path.exists(str(port)):
        os.makedirs(str(port))
    if not os.path.exists(str(port)+"_blacklist"):
        open("%s_blacklist" % port,"wb")
   
    BLACKLIST_KEYWORDS[port] = open("global_blacklist").read().splitlines()+open("%s_blacklist" % port).read().splitlines()
# BLACKLIST_KEYWORDS = []
 
stream_cache = LRUCache(1024)
BUFFER_SIZE = 1024 * 1024
USE_SLIDING_WINDOW = True
THREADS = cpu_count()
thread_pool = None
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
 
def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.INFO)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    streamHandler.setLevel(logging.ERROR)
    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
    # lhStdout = l.handlers[0]
    # l.removeHandler(lhStdout)
    return l
class LimitedPool(ThreadPool):
    def __init__(self, processes=None, initializer=None, initargs=(), max_queue_size=10000):
        self._max_queue_size = max_queue_size
        ThreadPool.__init__(self, processes, initializer, initargs)
 
    def _setup_queues(self):
        self._inqueue = Queue.Queue(self._max_queue_size)
        self._outqueue = Queue.Queue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get
 
 
'''def generate_key(packet):
    k = "{0}:{1}-{2}:{3}".format(packet.payload.src, packet.payload.payload.sport, packet.payload.dst, packet.payload.payload.dport)
    if packet.haslayer(TCP):
        return "tcp://{0}".format(k)
    if packet.haslayer(UDP):
        return "udp://{0}".format(k)
'''
 
def test_for_shellcode((appPort, attackPort, direction, payload, file_path)):
    try:
        str_port = str(appPort)+"_"+str(attackPort)
        if str_port not in LIST_CONNECT:
            LIST_CONNECT[str_port] = {'logger':setup_logger(str(appPort), "./"+str(appPort)+'/'+str(attackPort)+".log"),'time':time.time()}
        LIST_CONNECT[str_port]['time'] = time.time()
        current_log = LIST_CONNECT[str_port]['logger']
        current_log.info(direction+":\n\t"+payload.encode("hex")+"\n====\n\t"+repr(payload).replace("\\n","\n")+"\n=============================\n")
        for port in PORTS:
            for keyword in BLACKLIST_KEYWORDS[port]:
                if keyword in payload:
                    # print colored(("Detect %s in payload, check %s\%s.log\n" % (keyword, str(appPort), str(attackPort))),'red')
                    MAIN_LOG.info("Detect %s in payload, check %s/%s.log\n" % (keyword, str(appPort), str(attackPort)))
    except Exception as e:
        print e
 
def process_packet(pkt, file_path):
    global thread_pool
    try:
        if pkt.haslayer(Raw) and len(pkt[Raw].original) > 0:
            sport = pkt.payload.payload.sport
            dport = pkt.payload.payload.dport
            if sport in PORTS:
                appPort = sport
                attackPort = dport
                direction = "OUT"
            else:
                appPort = dport
                attackPort = sport
                direction = "IN"
            #k = generate_key(pkt)
            payload = pkt[Raw].original
            thread_pool.apply_async(test_for_shellcode, [(appPort, attackPort, direction, payload, file_path)])
    except Exception as e:
        print e
 
def reloadBacklist():
    global BLACKLIST_KEYWORDS
    while 1:
        for port in PORTS:
            BLACKLIST_KEYWORDS_TMP = open("global_blacklist").read().splitlines()+open("%s_blacklist" % port).read().splitlines()
            if len(BLACKLIST_KEYWORDS_TMP)!=len(BLACKLIST_KEYWORDS[port]):
                BLACKLIST_KEYWORDS[port] = BLACKLIST_KEYWORDS_TMP
                print colored("Updated blacklist port %s!"% port,"red")
                print port, BLACKLIST_KEYWORDS[port]
        time.sleep(3)
 
def closeLog():
    global LIST_CONNECT
    while True:
        current_time = time.time()
		#fout.write("current_time: %s\n" % str(current_time))
        for str_port in LIST_CONNECT.keys():
	    	#fout.write(str(str_port)+ ": %s\n" % LIST_CONNECT[str_port]['time'])
            if (current_time - LIST_CONNECT[str_port]['time'] > 20):
                handlers = LIST_CONNECT[str_port]['logger'].handlers
                for handler in handlers:
                    handler.close()
                    LIST_CONNECT[str_port]['logger'].removeHandler(handler)
                #print "Close %s log\n"% str_port
                del LIST_CONNECT[str_port]
        time.sleep(5)
	#fout.write("=========\n")
 
if __name__ == "__main__":
    #fout=open('debug','a')
    thread = Thread(target = reloadBacklist)
    thread.start()
    thread2 = Thread(target = closeLog)
    thread2.start()
    # thread.join()
   
    MAIN_LOG = setup_logger("main_log", "main.log")
    logging.basicConfig(level=logging.DEBUG)
   
    thread_pool = LimitedPool(processes=THREADS, max_queue_size=200)
    sniff(store=0, filter="tcp and (port "+" or port ".join(map(str,PORTS))+")", prn=lambda x: process_packet(x, "live"))
   
    thread_pool.close()
    thread_pool.join()
