import json

from requests_futures.sessions import FuturesSession
import requests


class State:
    __slots__ = [
        'challenges',
        'chall_id',
        'chall_teams',
        'regex_flag',
        'round_time',
        'username',
        'password',
        'submit_var',
        'chall_scriptlang',
        'team_flag',
        'log_file',
        'num_team',
        'my_team_id',
        'session',
        'monitoring',
        'attack_now',
        'stop'
    ]

    def __init__(self):
        self.monitoring = False
        self.attack_now = False
        self.stop = False

        s = json.loads(open('settings.json').read())
        SETTINGS = s

        self.challenges = list(map(lambda x: x['name'], SETTINGS['challenges']))
        self.chall_id = {
            chall['name']: chall['id'] for chall in SETTINGS['challenges']
        }
        self.chall_teams = s['challenges']
        self.regex_flag = s["flagfmt"]
        self.round_time = s["roundtime"]
        self.username = s['username']
        self.password = s['password']
        self.submit_var = s["submit"]
        self.log_file = s['logfile']
        self.num_team = s['num_team']
        self.my_team_id = s['teamid']

        try:
            self.chall_scriptlang = json.loads(open('CHALL_SCRIPTLANG.json').read())
        except FileNotFoundError:
            self.chall_scriptlang = dict.fromkeys(self.challenges, [])
            json.dump(self.chall_scriptlang, open('CHALL_SCRIPTLANG.json', 'w'), indent=4)

        # try:
        #     self.team_flag = json.loads(open('TEAM_FLAG.json').read())
        # except FileNotFoundError:
        #     self.setup_chall_port()


        self.session = requests.session()
        # self.session = FuturesSession()
        self.login()

    def login(self):
        SUBMIT = self.submit_var
        self.session.get(SUBMIT['scoreboard'])
        self.session.post(SUBMIT['signin'], data={
            "username": self.username,
            "password": self.password,
            "csrf_token": self.session.cookies["csrf_cookie"]
        })

    def submit(self, chall, team, flag):
        try:
            flag = flag.decode()
        except AttributeError:
            pass
        # lastflag = self.team_flag[chall][team][0]
        # print("{} {} {}".format(lastflag, flag, lastflag != flag))
        if lastflag == flag:
            return
        datafmt = self.submit_var['datafmt']
        data = {}
        for key, val in datafmt.items():
            data[key] = val
            if val == ':chall_id':
                data[key] = int(self.chall_id[chall])
            if val == ':flag':
                data[key] = flag
            if val == ':csrf':
                data[key] = self.session.cookies["csrf_cookie"]

        url = self.submit_var['url']
        r = self.session.post(url, data=data)
        if 'error_code' in r.text:
            self.login()
            r = self.session.post(url, data=data)

        msg = r.text
        # msg = "SUBMIT [{}] [{}] {}".format(chall, team, flag)
        # LOG.write(msg)
        if MONITORING:
            print(msg)
        return
        # self.team_flag[chall][team].insert(0, flag)
        # json.dump(self.team_flag, open('TEAM_FLAG.json', 'w'), indent=4)

    def team_chall_port(self, team_id):
        raise Error("Edit team service ip/port to send data here")
        return list(map(lambda x: {
            "name": team_id,
            "ip": x["ip"],
            "port": str(team_id) + x["port"]
        }, self.challenges))


    def setup_chall_port(self):
        # self.team_flag = {
        #     self.chall['name']: {
        #         tid: [""] for tid in range(1, self.num_team) if tid != self.my_team_id
        #     } for chall in s['challenges']
        # }
        # json.dump(self.team_flag, open('TEAM_FLAG.json', 'w'), indent=4)
        # raise Error("Write code to setup chall -> port here")
        pass
