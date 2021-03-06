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
    #SHOULDERHOZ = 7
    ELBOW = 8
    WRIST = 7
    HAND = 11
    maxRight = 1510 
    maxLeft = 7900
    currentScanDirection = 0 #start off scanning left
    previousState = 0
    previousPivot = 0
    previousCenterBody = ""
    headDown = False
    headCenter = False

    state =  0 # --- intial state is 0 for finding a face, state 1 is navigating to the approperate distance, state 2 is when the wheels no longer need to move but the head needs to move

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
        self.hand = 6000
        self.wrist = 5200
        self.elbow = 6000
        self.tango.setTarget(self.ELBOW, self.elbow)
        self.tango.setTarget(self.WRIST, self.wrist)
        self.tango.setTarget(self.HAND, self.hand)
        self.tango.setTarget(self.TURN, self.turn)
        self.tango.setTarget(self.MOTORS, self.motors) 
        self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.BODY, self.body)
        self.tango.setTarget(self.HEADTURN, self.headTurn)
        


    def resetMotors(self):
        self.headDown = False
        #re-center body and turn off motors
        self.motors = 6000
        self.turn = 6000
        self.body =6000
        self.tango.setTarget(self.BODY, self.body)
        self.tango.setTarget(self.MOTORS, self.motors)
        #self.tango.setTarget(self.HEADTILT, self.headTilt)
        self.tango.setTarget(self.TURN, self.turn)


    #state for being too close        
    def backwards(self):
        self.motors = 6500
        self.tango.setTarget(self.MOTORS, self.motors)
    # onclick event function for hsv window
    def onClick(self,event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # print out color values for current click x,y coords (to help figure out color thresholds)
            print(hsv[y, x])
            print("onclicl")

    def closeHand(self):
        print("closing hand")
        self.hand = 2000
        self.tango.setTarget(self.HAND, self.hand)

    def openHand(self):
        print("Opening hand")
        self.hand = 7000
        self.tango.setTarget(self.HAND, self.hand)

    def moveForward(self):
        if(self.previousState != 2):
            print("moving forward")
            self.motors = 5200 #5200 on slow robot
            self.tango.setTarget(self.MOTORS, self.motors)
        previousState = 2

    # at the start of grabbing for ice.
    def raiseElbow(self):
        self.elbow = 6000
        self.SHOULDERVER = 7000
        self.tango.setTarget(self.ELBOW, self.elbow)
        self.tango.setTarget(self.ELBOW, self.elbow)

    #raise head (used for human face detection)
    def raiseHead(self):
        if(self.headDown != True):
            self.headTilt = 7500 #7000
            self.tango.setTarget(self.HEADTILT, self.headTilt)
            headDown = True
    def centerHead(self):
        if(self.headCenter != True):
            self.headTilt = 5000
            self.tango.setTarget(self.HEADTILT, self.headTilt)
            headCenter = True

    def lowerHead(self):
        self.headTilt = 3000
        self.tango.setTarget(self.HEADTILT, self.headTilt)

    #pivot left for scanning
    def pivotLeft(self):
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

IP = '10.200.47.149' #phone IP
PORT = 5010
client = ClientSocket(IP, PORT)

camera = PiCamera()
camera.resolution = (640, 480) #reccomended at 256x256 started at 640, 480
camera.framerate = 20 #default =32
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
momentBufferLeft =220
momentBufferRight =260
headBufferLeft = 245
headBufferRight = 295   #head buffer is currently 150px
bufferTop = 160
bufferBottom = 300 #320
loseCount = 0  
elbowStatus = 0 # initially straight arm
state10Count = 0
state10CountMax = 10 #dropping into box state
state10PivotCount = 0
state10PivotCountMax = 8
state0Count = 0
state0CountMax = 5 #moving to first line counter
state0Seeline = False
state8Delay = 0

colorGoal = "pink" #current run color *CHANGEME*

#waiting variables for grabbing ice
waitCounter = 0
maxWait = 60


#filters for the colored lines
blueFilterMin = numpy.array([90,20,110]) 
blueFilterMax = numpy.array([145,48,255]) 

#orange values are good
orangeFilterMin = numpy.array([5,50,120]) 
orangeFilterMax = numpy.array([25,180,255])  

#pink filters 
pinkFilterMin = numpy.array([150,50,230])
pinkFilterMax = numpy.array([170,140,255])

#green filters 
greenFilterMin = numpy.array([40,190,120]) 
greenFilterMax = numpy.array([63,240,255])

#yellow filters inside test room
yellowFilterMin = numpy.array([25,140,175])
yellowFilterMax = numpy.array([60,215,240])

# #yellow filters for hallway
# yellowFilterMin = numpy.array([25,150,150])
# yellowFilterMax = numpy.array([40,200,190])


# main program

##client.start()         
time.sleep(1) #camera warmup
client.setup() #align head and body.

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    key = cv2.waitKey(1) & 0xFF
    image = frame.array
    #cv2.imshow("og", image)

    if(client.state ==0): #scan for blue line
        image = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        cv2.setMouseCallback('hsv', client.onClick)
        cv2.imshow("hsv 0 ", hsv)


        #cv2.imshow("hsv", hsv)

        #mask = cv2.inRange(hsv, blueFilterMin, blueFilterMax)
        #mask = cv2.inRange(hsv, orangeFilterMin, orangeFilterMax)
        mask = cv2.inRange(hsv, yellowFilterMin, yellowFilterMax)
        #erode and dialate to reduce white noise
        kernel = numpy.ones((5, 5), numpy.uint8)
        #erode
        #mask = cv2.erode(mask,kernel,iterations = 1)
        #dialate
        #mask = cv2.dilate(mask,kernel,iterations = 3)
        #cv2.setMouseCallback('hsv', client.onClick)
        cv2.imshow("state 0 mask", mask)

        client.lowerHead()
        h = OGHeight
        w = OGWidth
        wTotal = 0 
        hTotal = 0
        totalCounted = 0
        emptyState0 = False

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mask, contours, -1, (0,255,0), 3)

        # if(state0Seeline != True):
        #     client.lowerHead()
        #     client.moveForward()
        #     #cv2.circle(mask, (cogH, cogW), 5, (100, 100, 100), -1)
        #     #print(len(contours))
        #     #find extreame contours to determine COG 
        #     try:
        #         c = max(contours, key=cv2.contourArea)
        #         #min = min(contours, key=cv2.contourArea)
        #         #print("COGW " , min , " " , max)

        #         # determine the most extreme points along the contour
        #         extLeft = tuple(c[c[:, :, 0].argmin()][0])
        #         extRight = tuple(c[c[:, :, 0].argmax()][0])
        #         extTop = tuple(c[c[:, :, 1].argmin()][0])
        #         extBot = tuple(c[c[:, :, 1].argmax()][0])
        #         cogH = (extTop[1] + extBot[1]) / 2
        #     except:
        #         emptyState0 = True
        #     if(cogH >= 400):
        #         state0Seeline = True
        # else:
        #     print(state0Count)
        #     if(state0Count <= state0CountMax):
        #         #move forward
        #         client.moveForward()
        #         state0Count = state0Count + 1
        #     else:
        #         client.resetMotors()
        #         cv2.destroyAllWindows()
        #         #move to next state
        #         client.sendData("entered digging zone")
        #         client.state = 2
            

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
            client.pivotLeft()

    elif(client.state ==3): #grabbing ice
        client.lowerHead()
        #print("grabbing ice")
        #raise elbow if havent yet
        if(elbowStatus == 0):
            #client.raiseElbow()
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
        #cv2.imshow("hsv", hsv)
        #cv2.setMouseCallback('hsv', client.onClick)

        if(numpy.sum(mask == 255) > 10):
            print("correct ice detected")
            cv2.destroyAllWindows()
            client.sendData("that is the ice I want")
            client.state = 8

    elif(client.state ==4): #scan room for goal.
        client.centerHead()
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        #cv2.setMouseCallback('hsv', client.onClick)

        if(colorGoal == "yellow"):
            mask = cv2.inRange(hsv, yellowFilterMin, yellowFilterMax)
        elif(colorGoal =="green"):
            mask = cv2.inRange(hsv, greenFilterMin, greenFilterMax)
        elif(colorGoal =="pink"):
            mask = cv2.inRange(hsv, pinkFilterMin, pinkFilterMax)
        else:
            print("color goal errer in state 4")

        cv2.imshow("4 mask", mask)
        cv2.imshow("hsv 4", hsv)


        h = OGHeight
        w = OGWidth
        wTotal = 0 
        hTotal = 0
        totalCounted = 0
        emptyState4 = False

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mask, contours, -1, (0,255,0), 3)
        try:
            c = max(contours, key=cv2.contourArea)
            

            # determine the most extreme points along the contour
            extLeft = tuple(c[c[:, :, 0].argmin()][0])
            extRight = tuple(c[c[:, :, 0].argmax()][0])
            extTop = tuple(c[c[:, :, 1].argmin()][0])
            extBot = tuple(c[c[:, :, 1].argmax()][0])

            cogW = (extRight[0] +  extLeft[0]) / 2
            cogH = (extTop[1] + extBot[1]) / 2
        except:
            emptyState4 = True

        if(emptyState4):
            #keep pivoting
            #print("still scanning in 4")
            client.pivotLeft()
        else:
            #stop moving and proceed to state 6
            client.state = 6
            client.resetMotors()

    elif(client.state ==6):             
        #print("moving for the right goal")
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
        #cv2.imshow("hsv", hsv)
        if(colorGoal == "yellow"):
            mask = cv2.inRange(hsv, yellowFilterMin, yellowFilterMax)
        elif(colorGoal =="green"):
            mask = cv2.inRange(hsv, greenFilterMin, greenFilterMax)
        elif(colorGoal =="pink"):
            mask = cv2.inRange(hsv, pinkFilterMin, pinkFilterMax)
        else:
            print("color goal errer in state 6")

        h = OGHeight
        w = OGWidth
        wTotal = 0 
        hTotal = 0
        totalCounted = 0
        empty = False

        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(mask, contours, -1, (0,255,0), 3)

        #cv2.circle(mask, (cogH, cogW), 5, (100, 100, 100), -1)
        #print(len(contours))
        #find extreame contours to determine COG 
        try:
            c = max(contours, key=cv2.contourArea)
            #min = min(contours, key=cv2.contourArea)
            #print("COGW " , min , " " , max)

            # determine the most extreme points along the contour
            extLeft = tuple(c[c[:, :, 0].argmin()][0])
            extRight = tuple(c[c[:, :, 0].argmax()][0])
            extTop = tuple(c[c[:, :, 1].argmin()][0])
            extBot = tuple(c[c[:, :, 1].argmax()][0])

            # print(extLeft[0] , " left x") #x left
            # print(extRight[0] , " right x") # x right
            # print(extTop[1], " top y")
            # print(extBot[1], " bottom y")
            cogW = (extRight[0] +  extLeft[0]) / 2
            cogH = (extTop[1] + extBot[1]) / 2
            print("H " , cogH)
        except:
            empty = True
        if(cogH >=420): #close enough to end box
            client.resetMotors()
            client.state = 10 #move to dropping ice phase.
            client.sendData("entered goal area")

        if(empty): #if not found scan
            #scan
            client.pivotLeft()
            print("scanning")
        else:
            #move
            client.movement(cogW, bufferLeft, bufferRight)

        cv2.imshow("mask", mask)
        #if the robot is stopped for long enough, pivot and drop the ice.

    elif(client.state ==7):
        print("finished")
    elif(client.state ==8):
        #wait 3 seconds and close hand
        if(waitCounter >= maxWait):
            client.closeHand()
            if(state8Delay >= 10):
                client.state = 4 #find orange line next
            else:
                state8Delay = state8Delay + 1
        else:
            waitCounter = waitCounter + 1
            print("Wait counter " , waitCounter)

    elif(client.state ==9):#moving to human with ice.
        #print("moving to human")
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
            client.sendData("please give me ice")
        else:
            client.movement(cogW ,bufferLeft, bufferRight)
    elif(client.state ==10):
        #moving forward breifly
        state10Count = state10Count + 1
        print(state10Count)
        client.moveForward()
        if(state10Count >= state10CountMax):
            client.resetMotors()
            client.state =11 #move on to state 11
    elif(client.state ==11): #pivoting and dropping ice
        state10PivotCount = state10PivotCount + 1
        if(state10PivotCount <= state10PivotCountMax):
            client.pivotLeft()
        else:
            client.resetMotors()
            client.openHand()
            cv2.destroyAllWindows()
            client.state=100 #move onto final /end state


    elif(client.state ==100):
        print("end program")
    else:
        print(" phase error")

    # if the `q` key was pressed, break from the loop after destroying cv2 windows
    if key == ord("q"):
        client.resetMotors()
        cv2.destroyAllWindows()
        break
    rawCapture.truncate(0)
rawCapture.truncate(0)