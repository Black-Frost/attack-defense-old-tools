import random
import time
#from pwn import *
from threading import *
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'obfuscate'))
import obfuscate
import requests


HOST = "serveradmin.890m.com"
random.seed(time.time())

fport = open("list_port","r")
LIST_PORT = fport.read().splitlines()
for port in LIST_PORT:
	port = int(port)
fport.close()

fword = open("word_list","r")
WORD_LIST = fword.read().splitlines()
fword.close()


#Load web target
f = open('web_target', 'r')
WEB_TARGET = f.read().splitlines()
f.close()

#Load web key word
f = open('web_word', 'r')
WEB_WORD = f.read().splitlines()
f.close()

#Spam web payload
def webPayload():
	global WEB_WORD
	
	ret = {}
	ret['method'] = random.choice(['GET', 'POST'])
	
	part = random.randint(1, 5)
	path = ''
	body = {}
	for i in range(1, part):
		path = path + '/' + random.choice(WEB_WORD)
		body[random.choice(WEB_WORD)] = random.choice(WEB_WORD)
	
	ret['path'] = path
	ret['body'] = body
	
	return ret
	
#SPAM
def sendRequest():
	global WEB_TARGET
	
	while 1:
		for target in WEB_TARGET:
			try:
				payload = webPayload()
				payload['path'] = target + payload['path']
				
				if payload['method'] == 'GET':
					r = requests.get(payload['path'], headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
				elif payload['method'] == 'POST':
					r = requests.post(payload['path'], data = payload['body'], headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'})
				else:
					pass
					
			except:
				print(':(')
				
		time.sleep(3)



def spamPayload():
	len_of_payload = randint(30,100)
	string = random.choice(WORD_LIST)
	while (len(string) > len_of_payload):
		string = random.choice(WORD_LIST)
	return obfuscate.padding(len_of_payload,string)


def sendPayload():
	global LIST_PORT
	while True:
		for port in LIST_PORT:
			try:
				r = remote(HOST,port)
				payload = spamPayload()
				print payload 
				r.send(payload)
				r.close()
			except:
				pass
		time.sleep(2)


def reload():
	global WORD_LIST, LIST_PORT, WEB_WORD, WEB_TARGET
	while True:
		fport = open("list_port","r")
		LIST_PORT_TMP = fport.read().splitlines()
		for port in LIST_PORT_TMP:
			port = int(port)
		fport.close()
		if (len(LIST_PORT_TMP) != len(LIST_PORT)):
			LIST_PORT = LIST_PORT_TMP
			print '[+] LIST_PORT updated'

		fword = open("word_list","r")
		WORD_LIST_TMP = fword.read().splitlines()
		fword.close()
		if (len(WORD_LIST_TMP) != len(WORD_LIST)):
			WORD_LIST = WORD_LIST_TMP
			print "[+] WORD_LIST updated"
			
		#Reload web spam word
		f = open('web_word', 'r')
		temp = f.read().splitlines()
		f.close()
		if len(WEB_WORD) != len(temp):	#??
			WEB_WORD = temp
			print('[+] WEB_WORD updated')
			
		#Reload web target
		f = open('web_target', 'r')
		temp = f.read().splitlines()
		f.close()
		if len(WEB_TARGET) != len(temp):	#??
			WEB_TARGET = temp
			print('[+] WEB_TARGET updated')
			
		time.sleep(3)

if __name__ == '__main__':
	thread_reload = Thread(target = reload)
	thread_reload.daemon = True
	thread_reload.start()
	
	thread_pwn = Thread(target = sendPayload)
	thread_pwn.daemon = True
	thread_pwn.start()
	
	thread_web = Thread(target = sendRequest)
	thread_web.daemon = True
	thread_web.start()

	try:
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		print('Closing ...')



