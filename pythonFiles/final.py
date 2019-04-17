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
    SHOULDERVER = 6
    SHOULDERHOZ = 7
    ELBOW = 8
    WRIST = 10
    HAND = 11
    maxRight = 1510 
    maxLeft = 7900
    currentScanDirection = 0 #start off scanning left
    currentHeadTurn = 6000 #initially centered
    currentHeadTilt = 500
    previousState = 0
    previousPivot = 0
    previousCenterBody = ""

    state = 2 #intial state is 0 for finding a face, state 1 is navigating to the approperate distance, state 2 is when the wheels no longer need to move but the head needs to move

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
        self.shoulderhoz = 6000
        self.hand = 1000
        self.wrist = 5200
        self.elbow = 2000
        self.tango.setTarget(self.ELBOW, self.elbow)
        self.tango.setTarget(self.WRIST, self.wrist)
        self.tango.setTarget(self.HAND, self.hand)
        self.tango.setTarget(self.TURN, self.turn)
        self.tango.setTarget(self.SHOULDERHOZ, self.shoulderhoz)
        self.tango.setTarget(self.MOTORS, self.motors) 
        self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.BODY, self.body)
        self.tango.setTarget(self.HEADTURN, self.headTurn)
        


    def resetMotors(self):
        #re-center body and turn off motors
        self.motors = 6000
        #self.headTilt = 5000
        self.turn = 6000
        #re-center head
        self.tango.setTarget(self.MOTORS, self.motors)
        #self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.TURN, self.turn)



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

    def closeHand(self):
        print("closing hand")
        self.hand = 7500
        self.tango.setTarget(self.HAND, self.hand)

    def openHand(self):
        print("Opening hand")
        self.hand = 1000
        self.tango.setTarget(self.HAND, self.hand)

    # at the start of grabbing for ice.
    def raiseElbow(self):
        self.elbow = 7000
        self.tango.setTarget(self.ELBOW, self.elbow)

    #raise head (used for human face detection)
    def raiseHead(self):
        self.headTilt = 7000
        self.tango.setTarget(self.HEADTILT, self.headTilt)

    def pivotRight(self):
        if(self.previousPivot == 0):
            self.previousPivot =1
            self.turn = 7000
            self.tango.setTarget(self.TURN, self.turn)

    #robot movement for approaching human
    def movement(self,cogW,xBufferMin, xBufferMax):
        #base motor control on COG's 
        if(cogW < xBufferMax and cogW > xBufferMin):        #straight
            if(self.previousState != 2):
                self.motors = 6000
                self.turn = 6000
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                print("straight")
                self.motors = 5200 #5200 on slow robot
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
                self.turn = 7000
                self.tango.setTarget(self.TURN, self.turn)
                self.tango.setTarget(self.MOTORS, self.motors) 
                previousState = 1
        else:
            print("stoped/error")                           #stopped


print("program start")
globalVar = ""

IP = '10.200.13.125' #phone IP
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
comfortableDistance = 120 #100
comfortableDistanceMax = 130

bufferLeft = 215
bufferRight = 425
headBufferLeft = 245
headBufferRight = 295   #head buffer is currently 150px
bufferTop = 160
bufferBottom = 300 #320
loseCount = 0  
elbowStatus = 0 # initially straight arm

colorGoal = "yellow" #current run color *CHANGEME*

#waiting variables for grabbing ice
waitCounter = 0
maxWait = 60


#blue filter
blueFilterMin = numpy.array([90,20,110]) 
blueFilterMax = numpy.array([145,48,255]) 

#orange filter
orangeFilterMin = numpy.array([5,50,120]) 
orangeFilterMax = numpy.array([25,110,255]) 

#pink filters 
pinkFilterMin = numpy.array([150,50,230])
pinkFilterMax = numpy.array([170,140,255])

#green filters 
greenFilterMin = numpy.array([45,140,190])
greenFilterMax = numpy.array([55,175,255])

#yellow filters 
yellowFilterMin = numpy.array([25,105,190])
yellowFilterMax = numpy.array([40,145,240])


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
    elif(client.state ==2): #finding human (scan only)
        print("finding human")
        client.raiseHead()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.5, 2) #1.3 , 3 has fewer

        if(faces != ()):
            #navigate to human move to state 9
            client.resetMotors()
            client.state = 9
        else:
            #continue to pivot if no face found
            client.pivotRight()

    elif(client.state ==3): #grabbing ice?
        print("grabbing ice")
        #raise elbow if havent yet
        if(elbowStatus == 0):
            client.raiseElbow()
            elbowStatus == 1
        #get all of the masks 
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if(colorGoal == "yellow"):
            mask = cv2.inRange(hsv, yellowFilterMin, yellowFilterMax)
        elif(colorGoal =="green"):
            mask = cv2.inRange(hsv, greenFilterMin, greenFilterMax)
        elif(colorGoal =="pink"):
            mask = cv2.inRange(hsv, pinkFilterMin, pinkFilterMax)
        else:
            print("color goal errer in state 3")
        cv2.imshow("mask", mask)

        if(numpy.sum(mask == 255) > 10):
            print("yellow ice detected")
            cv2.destroyAllWindows()
            client.sendData("that is the ice I want")
            client.state = 8



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
    elif(client.state ==8):
        print("closing hand")
        #wait 3 seconds and close hand
        if(waitCounter >= maxWait):
            client.closeHand()
            client.state = 4 #find orange line next
        else:
            waitCounter = waitCounter + 1
            print("Wait counter " , waitCounter)

    elif(client.state ==9):#moving to human with ice.
        print("moving to human")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.5, 2) #1.3 , 3 has fewer
        canvas = numpy.zeros((OGHeight -1,OGWidth -1,3,),dtype=numpy.uint8) #canvas to draw rectangles on
        for (x,y,w,h) in faces:
            cv2.rectangle(canvas,(x,y),(x+w,y+h),(255,255,255),-1)
            cogW= (x + (w/2))
            cogH =(y + (h/2))
            boxWidth = w
        cv2.imshow("face", canvas)

        if(boxWidth >= comfortableDistance): #if within the comfortable distance
            client.resetMotors()
            client.state = 3
            cv2.destroyAllWindows()
        else:
            client.movement(cogW,bufferLeft, bufferRight)
    else:
        print(" phase error")

    # if the `q` key was pressed, break from the loop after destroying cv2 windows
    if key == ord("q"):
        client.resetMotors()
        cv2.destroyAllWindows()
        break
    rawCapture.truncate(0)
rawCapture.truncate(0)