import random
import sys

blacklist = []
random.seed()

def random_char():
	return chr(random.randint(1,255))

def padding(length,string=None):
	result = []
	while(len(result) < length):
		tmp = random_char()
		if tmp not in blacklist:
			result += tmp

	if string != None:
		if len(string) > length:
			print "[!] String is too long"
			sys.exit()
		for ch in blacklist:
			if ch in string:
				print "[!] String consists blacklisted character"
				print blacklist
				sys.exit()
		ran = random.randint(0,length-len(string))
		result[ran:(ran+len(string))] = string
	return "".join(result)
