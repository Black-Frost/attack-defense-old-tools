#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
# from pprint import pprint
from PyInquirer import prompt
from threading import Thread
from subprocess import Popen, PIPE
from datetime import datetime

import shutil
import os
import json
import re
import time


class LOG:
    def __init__(self, f):
        self.f = open(f, "a+", 1)
        self.access = 0

    def close(self):
        self.f.close()

    def write(self, content):
        while self.access >= 1:
            continue
        self.access += 1
        self.f.write("[%s] %s\n" % (datetime.now(), content))
        self.access -= 1


SETTINGS = json.loads(open('settings.json').read())

challenges = list(map(lambda x: x['name'], SETTINGS['challenges']))
chall_teams = SETTINGS['challenges']
REGEX_FLAG = SETTINGS["flagfmt"]
ROUND_TIME = SETTINGS["roundtime"]
SCOREBOARD_USERNAME = SETTINGS['username']
SCOREBOARD_PASSWORD = SETTINGS['password']
try:
    chall_id = json.loads(open('chall_id.json').read())
except FileNotFoundError:
    chall_id = dict.fromkeys(challenges, [])

LOG_FILE = SETTINGS['logfile']
log = LOG(LOG_FILE)
stop = False
isMonitoring = False
lastattack = datetime.now()


def submit(flag):
    global log
    log.write("Submited {}".format(flag))
    pass


def send_payload(chall, teams):
    for f, lang in enumerate(chall_id[chall], 1):
        for t in teams:
            name = t["name"]
            ip = t["ip"]
            port = t["port"]
            script = "{}/{}".format(chall, f, lang)
            process = Popen([lang, script, ip, port], stdout=PIPE)
            (output, err) = process.communicate()
            exit_code = process.wait()
            result = "SUCCESS"
            flag = re.findall(REGEX_FLAG, str(output))
            if exit_code != 0 or len(flag) == 0:
                result = "FAILED"
            msg = "[{}] [{}.{}] [{}:{}] [{}] {} {}".format(
                    chall, f, lang, ip, port, name, result, flag
                )
            log.write(msg)
            if len(flag) > 0:
                submit(flag[0])
            if isMonitoring:
                print(msg)


def attack():
    # TODO:
    #   Create threads to run
    #   Return result or pass to submit_flag
    global log
    global lastattack
    for x in chall_teams:
        chall = x["name"]
        teams = x["teams"]
        send_payload(chall, teams)
    lastattack = datetime.now()


def submit_flag(flag):
    return


def get_payload(chall, file, lang):
    if not os.path.exists(chall):
        os.makedirs(chall)
    if not os.path.exists(file):
        print("File not exists")
        return
    chall_id[chall].append(lang)
    shutil.copy2(file, "{}/{}".format(chall, len(chall_id[chall]), lang))
    json.dump(chall_id, open('chall_id.json', 'w'), indent=4)


def monitor():
    global isMonitoring
    isMonitoring = True
    while True:
        q = input()
        if q == 'q':
            isMonitoring = False
            return


def menu():
    global stop
    global challenges
    global chall_id
    while True:
        questions = [
            {
                'type': 'list',
                'name': 'action',
                'message': 'What do you want to do?',
                'choices': [
                    'Add a payload',
                    'Attack now',
                    'Manual attack',
                    'Reload chall_id.json',
                    'Switch to Monitor mode',
                    'Exit',
                ]
            },
        ]
        answers = prompt(questions)['action']
        if answers == 'Exit':
            stop = True
            return

        if answers == 'Switch to Monitor mode':
            monitor()

        if answers == 'Attack now':
            attack()

        if answers == 'Reload chall_id.json':
            chall_id = json.loads(open('chall_id.json').read())

        if answers == 'Add a payload':
            questions = [
              {
                'type': 'list',
                'name': 'lang',
                'message': 'Payload language',
                'choices': [
                  'python3',
                  'python2',
                  'sage'
                ]
              },
              {
                'type': 'input',
                'name': 'file',
                'message': 'Payload file path'
              },
              {
                'type': 'list',
                'name': 'chall',
                'message': 'The challenge for this payload',
                'choices': challenges
              }
            ]
            answers = prompt(questions)
            get_payload(answers['chall'], answers['file'], answers['lang'])


def auto():
    global stop
    global lastattack
    while not stop:
        deltatime = datetime.now() - lastattack
        if deltatime.seconds < ROUND_TIME:
            time.sleep(1)
            continue
        attack()


if __name__ == '__main__':
    t1 = Thread(target=menu)
    t2 = Thread(target=auto)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    log.close()
