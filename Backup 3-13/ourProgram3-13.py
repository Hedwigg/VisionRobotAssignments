#ssh -x pi@<ip>
#DISPLAY=:0 python3 <programname>
from picamera import PiCamera
from time import sleep
import tkinter as tk
import maestro     
import cv2             
from picamera.array import PiRGBArray           
import time     
import numpy     

MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3
camera = PiCamera()
camera.resolution = (256, 256) #reccomended at 256x256 started at 640, 480
camera.framerate = 25 #default =32
rawCapture = PiRGBArray(camera, size=(256, 256))
cropAmount = 120    #pixels to crop from the top of the image
OGHeight = 256 #setting initial height and width based on camera resulution
OGWidth = 256

time.sleep(1) #camera warmup

class KeyControl():
    def __init__(self,win):
        self.root = win
        self.tango = maestro.Controller()
        self.body = 6000
        self.headTurn = 6000
        self.headTilt = 6000
        self.motors = 6000
        self.turn = 6000


    def head(self,key):
        print(key.keycode)
        if key.keycode == 38:
            self.headTurn += 200
            if(self.headTurn > 7900):
                self.headTurn = 7900
            self.tango.setTarget(HEADTURN, self.headTurn)
        elif key.keycode == 40:
            self.headTurn -= 200
            if(self.headTurn < 1510):
                self.headTurn = 1510
            self.tango.setTarget(HEADTURN, self.headTurn)
        elif key.keycode == 25:
            self.headTilt += 200
            if(self.headTilt > 7900):
                self.headTilt = 7900
            self.tango.setTarget(HEADTILT, self.headTilt)
        elif key.keycode == 39:
            self.headTilt -= 200
            if(self.headTilt < 1510):
                self.headTilt = 1510
            self.tango.setTarget(HEADTILT, self.headTilt)
            
            
            
    def program(self, key):
        print(key.keycode)
        if key.keycode == 33: #p = prep camera position
            print("align head")
            self.headTilt = 1510
            self.headTurn = 6000
            self.body = 6000
            self.tango.setTarget(HEADTILT, self.headTilt)
            self.tango.setTarget(BODY, self.body)
            self.tango.setTarget(HEADTURN, self.headTurn)

        elif key.keycode == 32: #start program key 'o'
            previousState = 0 # holding state to avoid overloading motor controllers (see motor logic below)

            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                key = cv2.waitKey(1) & 0xFF 
                
                image = frame.array

                #crop image to focus on whats right in front of the robot's wheels 
                height, width, c = image.shape
                #cropped = image[cropAmount:height, 0:width]


                lower = numpy.uint8([100, 235, 245]) #110 240 250
                upper = numpy.uint8([255, 255, 255]) #255 255 255
                roi = image[cropAmount:height, 0:width]
                # color mask
                mask = cv2.inRange(roi, lower, upper)
                output = cv2.bitwise_and(roi, roi, mask=mask)

                #normalize
                normalized = numpy.zeros((600,600))
                normalized = cv2.normalize(output, normalized, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX) #alpha and beta values to adjust #100,200?
                #grayscale
                gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
                #blur
                blur = cv2.GaussianBlur(normalized, (5,5), 0)
                #canny edges
                canny = cv2.Canny(blur, 100, 150) #100,170

                # show the frames for DEBUGGING
                cv2.imshow("Frame", canny)
                og = frame.array
                #cv2.imshow("OG", og)

            
                h = OGHeight-cropAmount
                w = OGWidth
                wTotal = 0
                hTotal = 0
                totalCounted = 0
                for i in range(0,h-1):
                    for j in range(0,w-1):
                        if(canny[i,j] == 255):
                            wTotal = wTotal + i
                            hTotal = hTotal + j
                            totalCounted = totalCounted + 1
                try:
                    cogH = int(round(wTotal / totalCounted)) # yes we know its backwards but we double checked with camera
                    cogW = int(round(hTotal / totalCounted))
                except:
                    print("divide by 0 error - no white")
                    cogH = 0
                    cogW = 0

                #base motor control on COG's 
                middleBuffer = 30 #"stright"  (half of total zone)
                middlex = w/2
                middley = h/2
                xBufferMax = middlex + middleBuffer
                xBufferMin = middlex - middleBuffer

                if(cogW < xBufferMax and cogW > xBufferMin):        #straight
                    if(previousState != 2):
                        self.motors = 6000
                        self.turn = 6000
                        self.tango.setTarget(TURN, self.turn)
                        self.tango.setTarget(MOTORS, self.motors) 
                        print("straight")
                        self.motors = 5200
                        self.tango.setTarget(MOTORS, self.motors)
                        previousState = 2

                elif(cogW > xBufferMax):                            #right
                    if(previousState !=3):
                        self.motors = 6000
                        self.turn = 6000
                        self.tango.setTarget(TURN, self.turn)
                        self.tango.setTarget(MOTORS, self.motors) 
                        print("right")
                        self.turn = 5200
                        self.tango.setTarget(TURN, self.turn)
                        self.tango.setTarget(MOTORS, self.motors) 
                        previousState = 3

                elif(cogW < xBufferMin):                            #left
                    if(previousState !=1):
                        self.motors = 6000
                        self.turn = 6000
                        self.tango.setTarget(TURN, self.turn)
                        self.tango.setTarget(MOTORS, self.motors) 
                        print("left")
                        self.turn = 6800
                        self.tango.setTarget(TURN, self.turn)
                        self.tango.setTarget(MOTORS, self.motors) 
                        previousState = 1
                else:
                    print("stoped/error")                           #stopped
                    #print(cogW , " w")

                

                # if the `q` key was pressed, break from the loop after turning off motors & servos thus ending the program
                if key == ord("q"):
                    cv2.destroyAllWindows()
                    #re-center body and turn off motors
                    self.motors = 6000
                    self.turn = 6000
                    #re-center head

                    self.headTilt = 6000
                    self.headTurn = 6000

                    self.tango.setTarget(MOTORS, self.motors)
                    self.tango.setTarget(HEADTURN, self.headTurn)
                    self.tango.setTarget(HEADTILT, self.headTilt)
                    self.tango.setTarget(TURN, self.turn)
                    break
                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)
            exit() # end program when loop is broken


win = tk.Tk()
keys = KeyControl(win)

win.bind('<w>', keys.head)
win.bind('<s>', keys.head)
win.bind('<a>', keys.head)
win.bind('<d>', keys.head)
win.bind('<p>', keys.program)
win.bind('<o>', keys.program)
win.mainloop()
keys = KeyControl(win)



