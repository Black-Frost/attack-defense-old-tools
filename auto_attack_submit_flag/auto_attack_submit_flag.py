import mysql.connector
from pwn import *
import re
import datetime

REGEX_FLAG = "MATESCTF\{.*\}"
LOG_FILE = "./log"

SCOREBOARD_LOGIN = ""
SCOREBOARD_SUBMIT = ""

mydb = mysql.connector.connect(
  host="localhost",
  user="efiens",
  passwd="conbocuoi",
  database="matesctf",
)

def write_log(error):
	f = open(LOG_FILE,"w")
	f.write("[%s] %s" %(datetime.datetime.now(),error))
	f.close()

def get_flag_from_output(out):
	return re.findall(REGEX_FLAG,out)

def attack(challenge_name=None,team_name=None):
	global mydb
	mycursor = mydb.cursor()
	if (challenge_name == None):
		mycursor.execute("SELECT * FROM challenges")
	else:
		mycursor.execute("SELECT * FROM challenges WHERE challenge_name='%s' AND team_name='%s'" % (challenge_name,team_name))
	
	myresult = mycursor.fetchall()
	columns = [col[0] for col in mycursor.description]
        print columns
        
	rows = [dict(zip(columns,row)) for row in myresult]
	for row in rows:
                print row
	  	ip = row["ip"];
	  	port = row["port"]
	  	payload_dir = row["payload_dir"]
	  	r = process(executable=payload_dir,argv=[ip,str(port)])
	  	out = r.recvall()
	  	flag = get_flag_from_output(out)
	  	if len(flag) == 0:
	  		write_log("[ERROR] Exploit failed. Output %s" % out)
	  		continue
	  	#submit_flag(flag)
	  	r.close()

def submit_flag(flag):


