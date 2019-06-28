#!/usr/bin/env python3

from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from threading import Thread
from subprocess import Popen, PIPE, DEVNULL
from datetime import datetime

import shutil
import os
import json
import re
import time
import requests


class FILE:
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


SETTINGS            = None
CHALLENGES          = None
CHALL_ID            = None
CHALL_TEAMS         = None
REGEX_FLAG          = None
ROUND_TIME          = None
SCOREBOARD_USERNAME = None
SCOREBOARD_PASSWORD = None
SUBMIT              = None
CHALL_SCRIPTLANG    = None
TEAM_FLAG           = None
LOG_FILE            = None


def loadSetting():
    global SETTINGS
    global CHALLENGES
    global CHALL_ID
    global CHALL_TEAMS
    global REGEX_FLAG
    global ROUND_TIME
    global SCOREBOARD_USERNAME
    global SCOREBOARD_PASSWORD
    global SUBMIT
    global CHALL_SCRIPTLANG
    global TEAM_FLAG
    global LOG_FILE

    SETTINGS = json.loads(open('settings.json').read())

    CHALLENGES = list(map(lambda x: x['name'], SETTINGS['challenges']))
    CHALL_ID = {chall['name']: chall['id'] for chall in SETTINGS['challenges']}
    CHALL_TEAMS = SETTINGS['challenges']
    REGEX_FLAG = SETTINGS["flagfmt"]
    ROUND_TIME = SETTINGS["roundtime"]
    SCOREBOARD_USERNAME = SETTINGS['username']
    SCOREBOARD_PASSWORD = SETTINGS['password']
    SUBMIT = SETTINGS["submit"]
    LOG_FILE = SETTINGS['logfile']
    try:
        CHALL_SCRIPTLANG = json.loads(open('CHALL_SCRIPTLANG.json').read())
    except FileNotFoundError:
        CHALL_SCRIPTLANG = dict.fromkeys(CHALLENGES, [])
    try:
        TEAM_FLAG = json.loads(open('TEAM_FLAG.json').read())
    except FileNotFoundError:
        TEAM_FLAG = {
            chall['name']: {
                team['name']: [""] for team in chall['teams']
            } for chall in SETTINGS['challenges']
        }


loadSetting()
LOG = FILE(LOG_FILE)
STOP = False
MONITORING = False
LASTATTACK = datetime.now()


def submit(chall, team, flag):
    global LOG
    global MONITORING
    global TEAM_FLAG
    try:
        flag = flag.decode()
    except AttributeError:
        pass
    lastflag = TEAM_FLAG[chall][team][0]
    # print("{} {} {}".format(lastflag, flag, lastflag != flag))
    if lastflag == flag:
        return
    datafmt = SUBMIT['datafmt']
    data = {}
    for key, val in datafmt.items():
        data[key] = val
        if val == ':CHALL_ID':
            data[key] = CHALL_ID[chall]
        if val == ':flag':
            data[key] = flag
            data[key] = "HELLO WORLD 2ac376481ae546cd689d5b91275d324e"
    url = SUBMIT['url'].replace(':chall_name', chall)
    # r = s.post(url, data=data)
    # msg = r.text
    msg = "SUBMIT [{}] [{}] {}".format(chall, team, flag)
    LOG.write(msg)
    if MONITORING:
        print(msg)
    return
    TEAM_FLAG[chall][team].insert(0, flag)
    json.dump(TEAM_FLAG, open('TEAM_FLAG.json', 'w'), indent=4)


def attack_thread(chall, script, lang, name, ip, port):
    global LOG
    global MONITORING
    process = Popen([lang, script, ip, port], stdout=PIPE, stderr=DEVNULL)
    (output, err) = process.communicate()
    try:
        exit_code = process.wait(timeout=120)
    except TimeoutError:
        process.terminate()
    result = "SUCCESS"
    try:
        output = output.decode()
    except AttributeError:
        pass
    flag = re.findall(REGEX_FLAG, output)
    if exit_code != 0 or len(flag) == 0:
        result = "FAILED"
    msg = "[{}] [{}.{}] [{}:{}] [{}] {} {}".format(
            chall, script, lang, ip, port, name, result, flag
        )
    LOG.write(msg)
    if len(flag) > 0:
        submit(chall, name, flag[0])
    if MONITORING:
        print(msg)


def attack_chall(chall, teams):
    for f, lang in enumerate(CHALL_SCRIPTLANG[chall], 1):
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
    global LOG
    global LASTATTACK
    for x in CHALL_TEAMS:
        chall = x["name"]
        teams = x["teams"]
        attack_chall(chall, teams)
    LASTATTACK = datetime.now()


def get_payload(chall, file, lang):
    if not os.path.exists(chall):
        os.makedirs(chall)
    if not os.path.exists(file):
        print("File not exists")
        return
    CHALL_SCRIPTLANG[chall].append(lang)
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
    global STOP
    global CHALLENGES
    global CHALL_SCRIPTLANG
    global MONITORING
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
            attack()
            MONITORING = True

        if answers == 'Reload settings.json':
            loadSetting()

        if answers == 'Reload CHALL_SCRIPTLANG.json':
            CHALL_SCRIPTLANG = json.loads(open('CHALL_SCRIPTLANG.json').read())

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
                'choices': CHALL_TEAMS
              }
            ]
            answers = prompt(questions)
            get_payload(answers['chall'], answers['file'], answers['lang'])


def auto():
    global STOP
    global LASTATTACK
    while not STOP:
        deltatime = datetime.now() - LASTATTACK
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
    LOG.close()
