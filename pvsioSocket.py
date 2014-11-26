# Python library to connect to a pvsio-web server
# (available from https://github.com/thehogfather/pvsio-web)
# - Sends commands to pvsio-web device model
# - Parses and displays results from pvsio-web server
#
# Copyright (C) 2014  Swansea University
# Author: Gerrit Niezen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from websocket import create_connection
import json
from fractions import Fraction

debug = False

command = ""

def convert(s):
    try:
        return int(s)
    except ValueError:
        return float(Fraction(s))

def parseOutput(output):
    if debug:
        print "boutput ", output
    if not isinstance(output, basestring):
        output = output[0]

    if debug:
        print "aoutput ", output
    s = output.strip("(##)")
    d = dict(item.split(":=") for item in s.split(",")) # Generate dictionary
    return { k.strip():convert(v.strip()) for k, v in d.iteritems()} # Remove whitespace in dictionary

def sendCommand(ws, command, state):
    state['command'] = command
    cmdstate = '{command}((# left_display:={left_display}, step:={step}, timer:={timer} #));'.format(**state);
    d = {"type":"sendCommand", "data":{'command':cmdstate}}
    if debug:
        print "Sending:", d
    ws.send(json.dumps(d))

    message = waitForType(ws,"commandResult")
    #message = waitForType(ws, "pvsoutput")
    #message = json.loads(ws.recv())
    if debug:
        print "Message: ", message
    return message


def waitForType(ws,reqType):

    msg= json.loads(ws.recv())
    if debug:
        print "Msg:", msg
    state = msg['type']

    if debug:
        print "Message: ", msg
        print "Type: ", state

    while( state != reqType):
        msg = json.loads(ws.recv())
        state = msg['type']

    return msg


def pvsCommand(cmd):
        if(cmd == -1):
            return "press_dn"
        if(cmd == 10):
            return "press_UP"
        if(cmd == -10):
            return "press_DN"
        if(cmd == 1):
            return "press_up"
        if(cmd == 0):
            return "release_key"


def getDisplay(ws,button,prev):

    command = pvsCommand(button)
    if debug:
        print command

    message = sendCommand(ws,command,prev)

    result = message['data']
    output = parseOutput(result)
    if debug:
        print 'Output: ', output

    ldisplay = output['left_display']

    #print "ldisplay: ", ldisplay

    return output


def connect(firstCommand):
    ws = create_connection("ws://localhost:8082/")
    ws.send('{"type":"startProcess","data":{"projectName":"AlarisGH_AsenaCC", "fileName": "alarisGH_AsenaCC"}}')

    waitForType(ws,"processReady")

    if debug:
        print "Connected, sending first command.."

    command = pvsCommand(firstCommand)

    ws.send('{"type":"sendCommand","data":{"command":"'+command+'((# left_display := 0, step := 1, timer := 5 #));"}}')

    msg = waitForType(ws,'commandResult')
    if debug:
        print msg

    result = msg['data']
    output = parseOutput(result)
    if debug:
        print 'Output: ', output

    return ws, output

def disconnect(ws):
    ws.close()

if __name__ == "__main__":
    ws, prev = connect(1)

    for i in range (0,20):
        prev = getDisplay(ws,10,prev)

    for i in range (0,20):
        prev = getDisplay(ws,1,prev)
