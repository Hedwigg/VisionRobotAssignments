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
        self.headTurn = 3968
        self.headTilt = 6000
        self.motors = 6000
        self.turn = 6000
        self.tango.setTarget(TURN, self.turn)
        self.tango.setTarget(MOTORS, self.motors) 
        self.tango.setTarget(HEADTILT, self.headTilt)
        self.tango.setTarget(BODY, self.body)
        self.tango.setTarget(HEADTURN, self.headTurn)
    
    def getHeadTurnPos(self):
        return self.tango.getPosition(HEADTURN)
        ##7900 is left, 3968 is right

    # 0 = left 1 = right scan has access to currentScanDirection and currentHeadTurn
    def scan(x):
        print(currentScanDirection , currentHeadTurn, " plus")
        # if(currentScanDirection == 0): 
        #     if(currentHeadTurn <= 1510):
        #         #change directions and set global head turn value
        #         currentHeadTurn = null #changeme
        #     #keep turning left if not at the max.
        #     print("scanning left")
        

        

IP = '10.200.4.71'
PORT = 5010
client = ClientSocket(IP, PORT)
##client.start()

#example send text to voice
# for i in ["start"]:
#     time.sleep(1)
#     client.sendData(i)            
# print("Exiting Sends")


MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3
camera = PiCamera()
camera.resolution = (640, 480) #reccomended at 256x256 started at 640, 480
camera.framerate = 32 #default =32
rawCapture = PiRGBArray(camera, size=(640, 480))
face_cascade= cv2.CascadeClassifier('/home/pi/opencv/data/haarcascades/haarcascade_frontalface_default.xml')
maxRight = 1510 
maxLeft = 7900
currentScanDirection = 0 #start off scanning left
currentHeadTurn = 6000


time.sleep(1) #camera warmup


client.setup() #align head and body.

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    key = cv2.waitKey(1) & 0xFF
    image = frame.array
    
    #cv2.imshow("Image", image) #show orig capture

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.5, 3) #1.3 , 2 has a few false positives
    #print(faces)

    
    #if faces is empty, continue to scan for face.
    if(faces == ()):
        client.scan()

    canvas = numpy.zeros((600,600,3,),dtype=numpy.uint8) #canvas to draw rectangles on
    for (x,y,w,h) in faces:
        cv2.rectangle(canvas,(x,y),(x+w,y+h),(255,255,255),-1)
    cv2.imshow("gray", gray)
    #cv2.imshow("canvas", canvas)

    # if the `q` key was pressed, break from the loop after destroying cv2 windows
    if key == ord("q"):
        cv2.destroyAllWindows()
        break
    rawCapture.truncate(0)
