from websocket import create_connection
import json
from fractions import Fraction

debug = True

command = ""

def convert(s):
    try:
        return int(s)
    except ValueError:
        return float(Fraction(s))

def parseOutput(output):
    print "boutput ", output
    if not isinstance(output, basestring):
        output = output[0]

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
    
    message = waitForType(ws, "pvsoutput")
    #message = json.loads(ws.recv())    
    print "Message: ", message
    return message


def waitForType(ws,reqType):

    msg= json.loads(ws.recv())
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
    #if(state == "hold"):
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

#    if(state == "click"):
#        if(cmd == -1):
#            return "click_dn"
#        if(cmd == 1):
#            return "click_up"
#        if(cmd == -10):
#            return "click_DN"
#        if(cmd == 10):
#            return "click_UP"


#def getDisplay(ws, state,button,prev):
def getDisplay(ws,button,prev):

    #command = pvsCommand(state,button)
    command = pvsCommand(button)    
    print command

    message = sendCommand(ws,command,prev)
   
    result = message['data']
    output = parseOutput(result)
    print 'Output: ', output

    ldisplay = output['left_display']

    #print "ldisplay: ", ldisplay

    return output


def connect(firstCommand):
    ws = create_connection("ws://localhost:8082/")
    ws.send('{"type":"startProcess","data":{"fileName":"public/projects/AlarisGH_AsenaCC/alarisGH_AsenaCC"}}')

    waitForType(ws,"processReady")

    print "Connected, sending first command.."

    command = pvsCommand(firstCommand)

    ws.send('{"type":"sendCommand","data":{"command":"'+command+'((# left_display := 0, step := 1, timer := 5 #));"}}')

    #msg = json.loads(ws.recv())
    msg = waitForType(ws,'pvsoutput')
    print msg
    
    result = msg['data']
    output = parseOutput(result)
    print 'Output: ', output
    
    print "sent."

    return ws, output

def disconnect(ws):
    ws.close()

if __name__ == "__main__":
    ws, prev = connect(1)

    for i in range (0,20):
        prev = getDisplay(ws,10,prev)

    for i in range (0,20):
        prev = getDisplay(ws,1,prev)

