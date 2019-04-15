## Joel Lechman
## Taylor Koth
## Robot Vision - Final Project


#DISPLAY=:0 python3 final.py

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
    currentHeadTilt = 500
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
        self.headTilt = 5000
        self.motors = 6000
        self.turn = 6000
        self.tango.setTarget(self.TURN, self.turn)
        self.tango.setTarget(self.MOTORS, self.motors) 
        self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.BODY, self.body)
        self.tango.setTarget(self.HEADTURN, self.headTurn)


    def resetMotors(self):
        #re-center body and turn off motors
        self.motors = 6000
        self.headTilt = 5000
        #re-center head
        self.tango.setTarget(self.MOTORS, self.motors)
        self.tango.setTarget(self.HEADTILT, self.headTilt)



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


    #center body on head
    def centerBody(self):
        print(self.headTurn , " --")
        if(self.headTurn > 6100):
            #motor left, head right
            self.headTurn = self.headTurn - 100
            self.tango.setTarget(self.HEADTURN, self.headTurn)
            if(self.previousCenterBody != "left"):
                print("left")
                self.turn = 6900 #6800
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

    #state for being too close        
    def backwards(self):
        self.motors = 6500
        self.tango.setTarget(self.MOTORS, self.motors)
    # onclick event function for hsv window
    def onClick(self,event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # print out color values for current click x,y coords (to help figure out color thresholds)
            print(hsv[y, x])  

print("program start")
globalVar = ""

IP = '10.200.27.7'
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
comfortableDistance = 110 #100
comfortableDistanceMax = 130

bufferLeft = 215
bufferRight = 425
headBufferLeft = 245
headBufferRight = 295   #head buffer is currently 150px
bufferTop = 160
bufferBottom = 300 #320
loseCount = 0  

#filters for the colored lines
blueFilterMin = numpy.array([90,20,110]) 
blueFilterMax = numpy.array([145,48,255]) 

#orange values are good
orangeFilterMin = numpy.array([5,50,120]) 
orangeFilterMax = numpy.array([25,110,255]) 


# main program

##client.start()         
time.sleep(1) #camera warmup
client.setup() #align head and body.

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    key = cv2.waitKey(1) & 0xFF
    image = frame.array
    #cv2.imshow("og", image)

    

    if(client.state == 0): #scan for blue line
        image = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        cv2.imshow("hsv", hsv)
        mask = cv2.inRange(hsv, blueFilterMin, blueFilterMax)
        #erode and dialate to reduce white noise
        kernel = numpy.ones((5, 5), numpy.uint8)
        #erode
        mask = cv2.erode(mask,kernel,iterations = 1)
        #dialate
        mask = cv2.dilate(mask,kernel,iterations = 3)
        cv2.setMouseCallback('hsv', client.onClick)
        cv2.imshow("blue mask", mask)


    elif(client.state == 1): #approach the blue line
        print("approaching blue line")
    elif(client.state ==2): #finding human
        print("finding human")
    elif(client.state ==3): #grabbing ice?
        print("grabbing ice")
    elif(client.state ==4): #find orange line
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        cv2.imshow("hsv", hsv)
        cv2.setMouseCallback('hsv', client.onClick)
        maskO = cv2.inRange(hsv, orangeFilterMin, orangeFilterMax)
        cv2.imshow("orange mask", maskO)

    elif(client.state ==5):
        print("approaching orange line")
    elif(client.state ==6):
        print("depositing in goal")
    elif(client.state ==7):
        print("finished")
    else:
        print(" phase error")

    # if the `q` key was pressed, break from the loop after destroying cv2 windows
    if key == ord("q"):
        client.resetMotors()
        cv2.destroyAllWindows()
        break
    rawCapture.truncate(0)