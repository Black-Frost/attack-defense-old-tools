import re
from base64 import b64decode

# TODO: Merge this into ProxyChall Class

def _IsValidOutput(chall):
    def check(data):
        # chall is closure in here
        return True
    return check


def IsValidOutput(chall, data):
    return any(map(_IsValidOutput(chall), [ data, data[::-1] ]))


def IsValidInput(chall, data):
    return True
