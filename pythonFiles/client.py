#ssh -x pi@<ip>
#DISPLAY=:0 python3 client.py
#

import socket, time
import threading
import queue
from picamera import PiCamera
from time import sleep
import tkinter as tk
import maestro     
import cv2             
from picamera.array import PiRGBArray           
import time     
import numpy  



globalVar = ""

class ClientSocket(threading.Thread):
    MOTORS = 1
    TURN = 2
    BODY = 0
    HEADTILT = 4
    HEADTURN = 3
    maxRight = 1510 
    maxLeft = 7900
    currentScanDirection = 0 #start off scanning left
    currentHeadTurn = 6000 #initially centered
    currentHeadTilt = 6000
    previousState = 0
    previousCenterBody = ""

    state = 0 #intial state is 0 for finding a face, state 1 is navigating to the approperate distance, state 2 is when the wheels no longer need to move but the head needs to move

    def __init__(self, IP, PORT):
        super(ClientSocket, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
  
        print ('connected')
        self.alive = threading.Event()
        self.alive.set()

    def recieveData(self):
        global globalVar
        try:
            data = self.s.recv(105)
            print (data)
            globalVar = data
        except IOError as e:
            if e.errno == errno.EWOULDBLOCK:
                pass

    def sendData(self, sendingString):
        print ('sending')
        sendingString += "\n"
        self.s.send(sendingString.encode('UTF-8'))
        print ('done sending')

    def run(self):
        global globalVar
        while self.alive.isSet():
            data = self.s.recv(105)
            print (data)
            globalVar = data
            if(data == "0"):
                self.killSocket()
            
           
            
    def killSocket(self):
        self.alive.clear()
        self.s.close()
        print("Goodbye")
        exit()
    
    def setup(self):
        self.tango = maestro.Controller()
        self.body = 6000
        self.headTurn = 6000
        self.headTilt = 6700
        self.motors = 6000
        self.turn = 6000
        self.tango.setTarget(self.TURN, self.turn)
        self.tango.setTarget(self.MOTORS, self.motors) 
        self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.BODY, self.body)
        self.tango.setTarget(self.HEADTURN, self.headTurn)
    
    def getHeadTurnPos(self):
        return self.tango.getPosition(HEADTURN)
        ##7900 is left, 3968 is right


    def resetMotors(self):
        #re-center body and turn off motors
        self.motors = 6000
        #re-center head
        self.tango.setTarget(self.MOTORS, self.motors)



    # 0 = left 1 = right scan has access to currentScanDirection and currentHeadTurn
    def scan(self):
        if(self.currentHeadTurn <= 1510):
            self.currentScanDirection = 0
            self.currentHeadTurn = 1510
            print("scan direction is now LEFT")

        if(self.currentHeadTurn >= 7900): 
            self.currentScanDirection = 1
            self.currentHeadTurn = 7900
            print("scan direction is now RIGHT")

        if(self.currentScanDirection == 0):
            self.currentHeadTurn = self.currentHeadTurn + 200

        if(self.currentScanDirection == 1):
            self.currentHeadTurn = self.currentHeadTurn - 200

        self.headTurn = self.currentHeadTurn
        self.tango.setTarget(self.HEADTURN, self.headTurn)


    def movement(self,cogW,xBufferMin, xBufferMax):
        #base motor control on COG's 
        if(cogW < xBufferMax and cogW > xBufferMin):        #straight
            if(self.previousState != 2):
                self.motors = 6000
                self.turn = 6000
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                print("straight")
                self.motors = 5200
                self.tango.setTarget(self.MOTORS, self.motors)
                previousState = 2

        elif(cogW > xBufferMax):                            #right
            if(self.previousState !=3):
                self.motors = 6000
                self.turn = 6000
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                print("right")
                self.turn = 5200
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                previousState = 3

        elif(cogW < xBufferMin):                            #left
            if(self.previousState !=1):
                self.motors = 6000
                self.turn = 6000
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                print("left")
                self.turn = 6800
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                previousState = 1
        else:
            print("stoped/error")                           #stopped


    def trackHead(self,cogW,cogH,bufferTop,bufferBottom,bufferLeft,bufferRight):
        if(cogW <= bufferLeft): # left
            self.currentHeadTurn = self.currentHeadTurn + 150
        elif(cogW >= bufferRight): #right
            self.currentHeadTurn = self.currentHeadTurn - 150
        if(cogH > bufferBottom): # down
            self.currentHeadTilt = self.currentHeadTilt - 200
        elif(cogH < bufferTop): # up
            self.currentHeadTilt = self.currentHeadTilt + 200
        self.tango.setTarget(self.HEADTURN, self.currentHeadTurn)
        self.tango.setTarget(self.HEADTILT, self.currentHeadTilt)

    #center body on head before movement
    def centerBody(self):
        print(self.headTurn , " --")
        if(self.headTurn > 6100):
            #motor left, head right
            self.headTurn = self.headTurn - 100
            self.tango.setTarget(self.HEADTURN, self.headTurn)
            if(self.previousCenterBody != "left"):
                print("left")
                self.turn = 6800
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
            previousCenterBody = "left"
            return False
        elif(self.headTurn < 5900):
            #motor right, head left
            self.headTurn = self.headTurn + 100           
            self.tango.setTarget(self.HEADTURN, self.headTurn)
            if(self.previousCenterBody != "right"): #right
                print("centering right")
                self.turn = 5200
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
            previousCenterBody = "right"
            return False
        else:
            self.turn = 6000
            self.motors = 6000
            self.tango.setTarget(self.TURN, self.turn)
            self.tango.setTarget(self.MOTORS, self.motors)
            this.state = 1 #movement state
            return True

        

        

IP = '10.200.11.130'
PORT = 5010
client = ClientSocket(IP, PORT)


camera = PiCamera()
camera.resolution = (640, 480) #reccomended at 256x256 started at 640, 480
camera.framerate = 32 #default =32
rawCapture = PiRGBArray(camera, size=(640, 480))
face_cascade= cv2.CascadeClassifier('/home/pi/opencv/data/haarcascades/haarcascade_frontalface_default.xml')
OGHeight = 480
OGWidth = 640
cogW = 330
cogH = 240
boxWidth = 0
comfortableDistance = 100 #max

bufferLeft = 215
bufferRight = 425
headBufferLeft = 245
headBufferRight = 295   #head buffer is currently 150px
bufferTop = 160
bufferBottom = 320

##client.start()         


time.sleep(1) #camera warmup


client.setup() #align head and body.

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    key = cv2.waitKey(1) & 0xFF
    image = frame.array
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.5, 2) #1.3 , 3 has fewer
    #print(faces)


    

    canvas = numpy.zeros((OGHeight -1,OGWidth -1,3,),dtype=numpy.uint8) #canvas to draw rectangles on
    for (x,y,w,h) in faces:
        cv2.rectangle(canvas,(x,y),(x+w,y+h),(255,255,255),-1)
        cogW= (x + (w/2))
        cogH =(y + (h/2))
        boxWidth = w
        #TODO if boxWidth is greater than a certain number, call a method to back straight up a bit.
    cv2.line(canvas, (bufferLeft, 0), (bufferLeft, OGHeight), (255,255,255))
    cv2.line(canvas, (bufferRight, 0), (bufferRight, OGHeight), (255,255,255))
    cv2.imshow("canvas", canvas)    

    if(client.state == 0): #scan to find face
        if (faces == () and client.state == 0):
            print(client.state) 
            client.scan()
        else:
            print("moving to state 3")
            client.state = 3 # if there is a face, move on to the next phase
            client.sendData("Hello Human")

    elif(client.state == 1): #movement phase
        #check size of box first to kick into next state
        if(boxWidth >= comfortableDistance): #if within the comfortable distance
            client.state = 2
            client.resetMotors()
        else:
            if(faces != ()): #only calculate movement when there is a face recgonized
                client.movement(cogW,bufferLeft, bufferRight)


    elif(client.state ==2):  #head tracking phase (body is not moving)
        print("face tracking")
        if(faces != ()):
            client.trackHead(cogW,cogH,bufferTop,bufferBottom,headBufferLeft,headBufferRight)
        
    elif(client.state == 3): #center body on found face
        if(client.headTurn < 5900 or client.headTurn > 6100):
            print("centering BOdy")
            client.centerBody()
        else:
            client.state = 1
            client.resetMotors()
            print("moving to state 1 movement state")


    else:
        print(" phase error")

    # if the `q` key was pressed, break from the loop after destroying cv2 windows
    if key == ord("q"):
        client.resetMotors()
        cv2.destroyAllWindows()
        break
    rawCapture.truncate(0)
