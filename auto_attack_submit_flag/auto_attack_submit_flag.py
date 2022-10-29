#!/usr/bin/env python3
from __future__ import print_function, unicode_literals
import json
import os
import re
import requests
import shutil
import time

from datetime import datetime
from threading import Thread
from subprocess import Popen, PIPE, DEVNULL
from PyInquirer import prompt

from State import State


class File:
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


STATE = State()
LOG = File(STATE.log_file)
STOP = False


def attack_thread(chall, script, lang, name, ip, port):
    global LOG
    global STATE
    process = Popen([lang, script, ip, port], stdout=PIPE, stderr=DEVNULL)
    (output, err) = process.communicate()
    try:
        exit_code = process.wait(timeout=20)
    except TimeoutError:
        process.terminate()
    result = "SUCCESS"
    try:
        output = output.decode()
    except AttributeError:
        pass
    flag = re.findall(STATE.regex_flag, output)
    if exit_code != 0 or len(flag) == 0:
        result = "FAILED"
    msg = "[{}] [{}.{}] [{}:{}] {} {}".format(
            chall, script, lang, ip, port, result, flag
        )
    LOG.write(msg)
    if len(flag) > 0:
        STATE.submit(chall, name, flag[0])
    if STATE.monitoring:
        print(msg)


def attack_chall(chall, teams):
    for f, lang in enumerate(STATE.chall_scriptlang[chall], 1):
        for t in teams:
            name = t["name"]
            ip = t["ip"]
            port = t["port"]
            script = "{}/{}".format(chall, f)
            Thread(
                target=attack_thread,
                args=(chall, script, lang, name, ip, port)
            ).start()


def attack():
    global STATE
    global LOG
    for x in STATE.chall_teams:
        chall = x["name"]
        teams = [{
            "name": tid,
            "ip": x["ip"],
            "port": str(tid) + x["port"]
        } for tid in range(1, STATE.num_team) if tid != STATE.my_team_id]
        attack_chall(chall, teams)


def get_payload(chall, file, lang):
    global CHALL_SCRIPTLANG
    if not os.path.exists(chall):
        os.makedirs(chall)
    if not os.path.exists(file):
        print("File not exists")
        return
    print("{} {} {}".format(chall, file, lang))
    for key, val in CHALL_SCRIPTLANG.items():
        if key == chall:
            CHALL_SCRIPTLANG[key] = val + [lang]
        else:
            CHALL_SCRIPTLANG[key] = val
    print(CHALL_SCRIPTLANG)
    shutil.copy2(file, "{}/{}".format(chall, len(CHALL_SCRIPTLANG[chall])))
    json.dump(CHALL_SCRIPTLANG, open('CHALL_SCRIPTLANG.json', 'w'), indent=4)


def monitor():
    global MONITORING
    MONITORING = True
    while True:
        q = input()
        if q == 'q':
            MONITORING = False
            return


def menu():
    # XXX: Change from PyInquirer to Questionary
    # PyInquirer's upgrade to prompt-tools is too slow,
    # This is optional, we may wait
    #global STOP
    #global CHALLENGES
    #global CHALL_SCRIPTLANG
    #global MONITORING
    #global ATTACK_NOW
    global STATE
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
                    'Reload settings.json',
                    'Reload CHALL_SCRIPTLANG.json',
                    'Switch to Monitor mode',
                    'Exit',
                ]
            },
        ]
        answers = prompt(questions)['action']
        if answers == 'Exit':
            STOP = True
            return

        if answers == 'Switch to Monitor mode':
            monitor()

        if answers == 'Attack now':
            ATTACK_NOW = True
            monitor()

        if answers == 'Reload settings.json':
            STATE = State()

        if answers == 'Reload CHALL_SCRIPTLANG.json':
            CHALL_SCRIPTLANG = json.loads(open('CHALL_SCRIPTLANG.json').read())

        if answers == 'Add a payload':
            questions = [
              {
                'type': 'list',
                'name': 'chall',
                'message': 'The challenge for this payload',
                'choices': STATE.challenges
              },
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
              }
            ]
            answers = prompt(questions)
            get_payload(answers['chall'], answers['file'], answers['lang'])


def auto():
    global STOP
    #global LASTATTACK
    #global ATTACK_NOW
    while not STOP:
        #deltatime = datetime.now() - LASTATTACK
        #if deltatime.seconds < ROUND_TIME and not ATTACK_NOW:
        #    time.sleep(1)
        #    continue
        #ATTACK_NOW = False
        attack()
        time.sleep(2)


if __name__ == '__main__':
    t1 = Thread(target=menu)
    t2 = Thread(target=auto)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    LOG.close()
