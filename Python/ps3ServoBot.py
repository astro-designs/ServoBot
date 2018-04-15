#!/usr/bin/env python2.7

import RPi.GPIO as GPIO # Import the GPIO Library
import pygame
import time
import os
import sys
import wiringpi as wiringpi

# Define the PWM pins (these are fixed!)
PWM_PIN1 = 18
PWM_PIN2 = 19

# Define the left-right speed balance
BAL_Left = 1.0
BAL_Right = 1.0

# Define the initial Duty-Cycle for forwards & backwards
DC_forwards = 11
DC_backwards = 20
DC_Stop = 15

# Set variables for the line detector GPIO pin
pinLineFollower = 25

# pygame controller constants
JoyButton_Square = 0
JoyButton_X = 1
JoyButton_Circle = 2
JoyButton_Triangle = 3
JoyButton_L1 = 4
JoyButton_R1 = 5
JoyButton_L2 = 6
JoyButton_R2 = 7
JoyButton_Select = 8
JoyButton_Start = 9
JoyButton_L3 = 10
JoyButton_R3 = 11
JoyButton_Home = 12
axisUpDown = 1                          # Joystick axis to read for up / down position
axisUpDownInverted = False              # Set this to True if up and down appear to be swapped
axisLeftRight = 0                       # Joystick axis to read for left / right position
axisLeftRightInverted = False           # Set this to True if left and right appear to be swapped
interval = 0.00                         # Time between keyboard updates in seconds, smaller responds faster but uses more processor time


# Setup pygame and key states
global hadEvent
global LeftStickUp
global LeftStickDown
global LeftStickLeft
global LeftStickRight
global RightStickUp
global RightStickDown
global RightStickLeft
global RightStickRight
global HatStickUp
global HatStickDown
global HatStickLeft
global HatStickRight
global TriangleButton
global SquareButton
global CircleButton
global XButton
global HomeButton
global StartButton
global SelectButton
global R1Button
global R2Button
global R3Button
global L1Button
global L2Button
global L3Button
global moveQuit
hadEvent = True
LeftStickUp = False
LeftStickDown = False
LeftStickLeft = False
LeftStickRight = False
RightStickUp = False
RightStickDown = False
RightStickLeft = False
RightStickRight = False
HatStickUp = False
HatStickDown = False
HatStickLeft = False
HatStickRight = False
TriangleButton = False
SquareButton = False
CircleButton = False
XButton = False
HomeButton = False
StartButton = False
SelectButton = False
R1Button = False
R2Button = False
R3Button = False
L1Button = False
L2Button = False
L3Button = False
moveQuit = False

# Needed to allow PyGame to work without a monitor
os.environ["SDL_VIDEODRIVER"]= "dummy"

#Initialise pygame & controller(s)
pygame.init()
print 'Waiting for joystick... (press CTRL+C to abort)'
timeoutCount = 100
while True:
    try:
        try:
            pygame.joystick.init()
            # Attempt to setup the joystick
            if pygame.joystick.get_count() < 1:
                # No joystick attached, toggle the LED
                #ZB.SetLed(not ZB.GetLed())
                pygame.joystick.quit()
                time.sleep(0.1)
            else:
                # We have a joystick, attempt to initialise it!
                JoystickFound = False
                joystick = pygame.joystick.Joystick(0)
                break
        except pygame.error:
            # Failed to connect to the joystick
            pygame.joystick.quit()
            time.sleep(0.1)
        
        if timeoutCount < 1:
            print 'Cannot find joystick'
            JoystickFound = False
            break
        else:
            timeoutCount = timeoutCount - 1
            
    except KeyboardInterrupt:
        # CTRL+C exit, give up
        print '\nUser aborted'
        #ZB.SetLed(True)
        sys.exit()

if JoystickFound == True:
    print 'Joystick found'
    joystick.init()

    print 'Initialised Joystick : %s' % joystick.get_name()

    # Check number of joysticks in use...
    joystick_count = pygame.joystick.get_count()
    print("joystick_count")
    print(joystick_count)
    print("--------------")

    # Check number of axes on joystick...
    numaxes = joystick.get_numaxes()
    print("numaxes")
    print(numaxes)
    print("--------------")

    # Check number of buttons on joystick...
    numbuttons = joystick.get_numbuttons()
    print("numbuttons")
    print(numbuttons)

    # Pause for a moment...
    time.sleep(2)


# Turn all motors off
def StopMotors():
    wiringpi.pwmWrite(PWM_PIN1,DC_Stop)
    wiringpi.pwmWrite(PWM_PIN2,DC_Stop)
    
# Turn both motors backwards
def Backwards():
    wiringpi.pwmWrite(PWM_PIN1,DC_backwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_forwards)

# Turn both motors forwards
def Forwards():
    wiringpi.pwmWrite(PWM_PIN1,DC_forwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_backwards)

# Turn Right
def Right():
    wiringpi.pwmWrite(PWM_PIN1,DC_forwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_forwards)

def BLeft():
    global TurnDC
    
    wiringpi.pwmWrite(PWM_PIN1,DC_backwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_forwards * TurnDC)

def FLeft():
    global TurnDC
    
    wiringpi.pwmWrite(PWM_PIN1,DC_backwards * TurnDC)
    wiringpi.pwmWrite(PWM_PIN2,DC_forwards)

# Turn left
def Left():
    wiringpi.pwmWrite(PWM_PIN1,DC_backwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_backwards)

def BRight():
    global TurnDC
    
    wiringpi.pwmWrite(PWM_PIN1,DC_forwards * TurnDC)
    wiringpi.pwmWrite(PWM_PIN2,DC_backwards)

def FRight():
    global TurnDC
    
    wiringpi.pwmWrite(PWM_PIN1,DC_forwards)
    wiringpi.pwmWrite(PWM_PIN2,DC_backwards * TurnDC)

# Return True if the line detector is over a black line
def IsOverBlack():
    if GPIO.input(pinLineFollower) == 0:
        return True
    else:
        return False

# Search for the black line
def SeekLine():
    print("Seeking the line")
    # The direction the robot will turn - True = Left
    Direction = True
    
    SeekSize = 0.25 # Turn for 0.25s
    SeekCount = 1 # A count of times the robot has looked for the line 
    MaxSeekCount = 5 # The maximum time to seek the line in one direction
    # Turn the robot left and right until it finds the line
    # Or it has been searched for long enough
    while SeekCount <= MaxSeekCount:
        # Set the seek time
        SeekTime = SeekSize * SeekCount
        
        # Start the motors turning in a direction
        if Direction:
            print("Looking left")
            Left()
        else:
            print("Looking Right")
            Right()
        
        # Save the time it is now
        StartTime = time.time()
        
        # While the robot is turning for SeekTime seconds,
        # check to see whether the line detector is over black
        while time.time()-StartTime <= SeekTime:
            if IsOverBlack():
                StopMotors()
                # Exit the SeekLine() function returning
                # True - the line was found
                return True
                
        # The robot has not found the black line yet, so stop
        StopMotors()
        # Turn the LED off
        GPIO.output(pinLED1, False)

        
        # Increase the seek count
        SeekCount += 1
        
        # Change direction
        Direction = not Direction
        
    # The line wasn't found, so return False
    return False

def do_linefollower():
    global SpeedRamp

    #repeat the next indented block forever
    print("Following the line")
    KeepTrying = True
    while KeepTrying == True:
        # If the sensor is Low (=0), it's above the black line
        if IsOverBlack():
            SpeedRamp = SpeedRamp + 0.05
            if SpeedRamp > 1:
                SpeedRamp = 1
            Forwards()
            time.sleep(0.2)
            # If not (else), print the following
        else:
            StopMotors()
            if SeekLine() == False:
                StopMotors()
                print("The robot has lost the line")
                KeepTrying = False
            else:
                print("Following the line")
    print("Exiting the line-following routine")
    StopMotors()

def PygameHandler(events):
    # Variables accessible outside this function
    global hadEvent
    global LeftStickUp
    global LeftStickDown
    global LeftStickLeft
    global LeftStickRight
    global RightStickUp
    global RightStickDown
    global RightStickLeft
    global RightStickRight
    global HatStickUp
    global HatStickDown
    global HatStickLeft
    global HatStickRight
    global TriangleButton
    global SquareButton
    global CircleButton
    global XButton
    global HomeButton
    global StartButton
    global SelectButton
    global R1Button
    global R2Button
    global R3Button
    global L1Button
    global L2Button
    global L3Button
    global moveQuit

    # Handle each event individually
    for event in events:
        #print ("Event: ", event)
        if event.type == pygame.QUIT:
            print ("QUIT")
            # User exit
            hadEvent = True
            moveQuit = True
        elif event.type == pygame.JOYHATMOTION:
            # A key has been pressed, see if it is one we want
            hadEvent = True
            #print ("Hat Motion: ", event.value)
            hat = joystick.get_hat(0)
            # Hat up/down
            if hat[0] == -1:
                HatStickLeft = True
            elif hat[0] == 1:
                HatStickRight = True
            else:
                HatStickLeft = False
                HatStickRight = False
            # Hat left/right
            if hat[1] == -1:
                HatStickDown = True
            elif hat[1] == 1:
                HatStickUp = True
            else:
                HatStickDown = False
                HatStickUp = False
            
        elif event.type == pygame.JOYBUTTONDOWN:
            # A key has been pressed, see if it is one we want
            hadEvent = True
            #print ("Button Down: ", event.button)
            if event.button == JoyButton_Square:
                SquareButton = True
            elif event.button == JoyButton_X:
                XButton = True
            elif event.button == JoyButton_Circle:
                CircleButton = True
            elif event.button == JoyButton_Triangle:
                TriangleButton = True
            elif event.button == JoyButton_L1:
                L1Button = True
            elif event.button == JoyButton_R1:
                R1Button = True
            elif event.button == JoyButton_L2:
                L2Button = True
            elif event.button == JoyButton_R2:
                R2Button = True
            elif event.button == JoyButton_L3:
                L3Button = True
            elif event.button == JoyButton_R3:
                R3Button = True
            elif event.button == JoyButton_Select:
                SelectButton = True
            elif event.button == JoyButton_Start:
                StartButton = True
            elif event.button == JoyButton_Home:
                HomeButton = True
        elif event.type == pygame.JOYBUTTONUP:
            # A key has been released, see if it is one we want
            hadEvent = True
            #print ("Button Up: ", event.button)
            if event.button == JoyButton_Square:
                SquareButton = False
            elif event.button == JoyButton_X:
                XButton = False
            elif event.button == JoyButton_Circle:
                CircleButton = False
            elif event.button == JoyButton_Triangle:
                TriangleButton = False
            elif event.button == JoyButton_L1:
                L1Button = False
            elif event.button == JoyButton_R1:
                R1Button = False
            elif event.button == JoyButton_L2:
                L2Button = False
            elif event.button == JoyButton_R2:
                R2Button = False
            elif event.button == JoyButton_L3:
                L3Button = False
            elif event.button == JoyButton_R3:
                R3Button = False
            elif event.button == JoyButton_Select:
                SelectButton = False
            elif event.button == JoyButton_Start:
                StartButton = False
            elif event.button == JoyButton_Home:
                HomeButton = False
        elif event.type == pygame.JOYAXISMOTION:
            # A joystick has been moved, read axis positions (-1 to +1)
            hadEvent = True
            upDown = joystick.get_axis(axisUpDown)
            leftRight = joystick.get_axis(axisLeftRight)
            # Invert any axes which are incorrect
            if axisUpDownInverted:
                upDown = -upDown
            if axisLeftRightInverted:
                leftRight = -leftRight
            # Determine Up / Down values
            if upDown < -0.1:
                print ("LeftStickUp")
                LeftStickUp = True
                LeftStickDown = False
            elif upDown > 0.1:
                print ("LeftStickDown")
                LeftStickUp = False
                LeftStickDown = True
            else:
                LeftStickUp = False
                LeftStickDown = False
            # Determine Left / Right values
            if leftRight < -0.1:
                print ("LeftStickLeft")
                LeftStickLeft = True
                LeftStickRight = False
            elif leftRight > 0.1:
                print ("LeftStickRight")
                LeftStickLeft = False
                LeftStickRight = True
            else:
                LeftStickLeft = False
                LeftStickRight = False
        
try:
    print("Entering control loop...")

    print ("Setting up GPIO")
    wiringpi.wiringPiSetupGpio()

    print ("Setting mode to PWM")
    wiringpi.pinMode(PWM_PIN1,2)
    wiringpi.pinMode(PWM_PIN2,2)

    print ("Setting mode to MS mode")
    wiringpi.pwmSetMode(0)

    print ("Setting the divisor")
    wiringpi.pwmSetClock(1920)

    print ("Setting the range")
    wiringpi.pwmSetRange(200)

    print ("Setting DC to 0")
    wiringpi.pwmWrite(PWM_PIN1,0)
    wiringpi.pwmWrite(PWM_PIN2,0)
            
    # Allow module to settle
    time.sleep(0.5)    

    # Loop indefinitely
    while JoystickFound:
        # Get the currently pressed keys on the keyboard
        PygameHandler(pygame.event.get())
        if hadEvent:
            # Keys have changed, generate the command list based on keys
            hadEvent = False
            if moveQuit:
                break
            elif HomeButton and CircleButton: # Shutdown
                print ("Halting Raspberry Pi...")
                GPIO.cleanup()
                bashCommand = ("sudo halt")
                os.system(bashCommand)
                break
            elif HomeButton and XButton: # Exit
                break
            elif StartButton and CircleButton: 
                print ("Start Line-follower")
                do_linefollower()
            elif StartButton and SquareButton: 
                print ("Start Proximity")
                #do_proximity()
            elif StartButton and XButton: 
                print ("Start Avoidance")
                #do_proximity()
            elif SelectButton:
                print ("Select")
            elif SquareButton:
                print ("Square")
            elif XButton:
                print ("X")
            elif CircleButton:
                print ("Circle")
            elif TriangleButton:
                print ("Triangle")
            elif L1Button:
                print ("L1")
            elif R1Button:
                print ("R1")
            elif L2Button:
                print ("L2")
            elif R2Button:
                print ("R2")
            elif L3Button:
                print ("L3")
            elif R3Button:
                print ("R3")
            elif LeftStickLeft:
                Left()
            elif LeftStickRight:
                Right()
            elif LeftStickUp:
                Forwards()
            elif LeftStickDown:
                Backwards()
            elif RightStickLeft:
                print ("Right Stick Left")
            elif RightStickRight:
                print ("Right Stick Right")
            elif RightStickUp:
                print ("Right Stick Up")
            elif RightStickDown:
                print ("Right Stick Down")
            elif HatStickLeft:
                print ("Hat Left")
            elif HatStickRight:
                print ("Hat Right")
            elif HatStickUp:
                print ("Hat Up")
            elif HatStickDown:
                print ("Hat Down")
            if not LeftStickLeft and not LeftStickRight and not LeftStickUp and not LeftStickDown:
                StopMotors()
        time.sleep(interval)
    # Disable all drives
    if JoystickFound == False:
        print ("Start Line-follower")
        do_linefollower()
    
    StopMotors()    
# If you press CTRL+C, cleanup and stop
except KeyboardInterrupt:
    # Reset GPIO settings
    GPIO.cleanup()
            
