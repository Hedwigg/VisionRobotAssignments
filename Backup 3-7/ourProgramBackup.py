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
camera.framerate = 20 #default =32
rawCapture = PiRGBArray(camera, size=(256, 256))

time.sleep(0.1) #camera warmup

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
            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                image = frame.array

                lower = numpy.uint8([110, 240, 250])
                upper = numpy.uint8([255, 255, 255])
                image = cv2.inRange(image, lower, upper)

                normalized = cv2.normalize(image, None, alpha=100, beta=200, norm_type=cv2.NORM_MINMAX) #alpha and beta values to adjust
                
                canny = cv2.Canny(normalized, 100, 170)

                #TODO canny edges found, need to calculate COG and program motor logic based on COG.
                #possibly dialating canny edges before calculating COG to make sure robot doesnt lose the yellow cards????



                # show the frame/(s)
                cv2.imshow("Frame", canny)
                cv2.imshow("orig",image)

                key = cv2.waitKey(1) & 0xFF ##NEED THIS LINE OR BUFFER RESOLUTION ERROR
                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)


                # if the `q` key was pressed, break from the loop 
                if key == ord("q"):
                    cv2.destroyAllWindows()
                    break

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


