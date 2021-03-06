# USAGE
# python eyetracking.py --face cascades/haarcascade_frontalface_default.xml --eye cascades/haarcascade_eye.xml --video video/adrian_eyes.mov
# python eyetracking.py --face cascades/haarcascade_frontalface_default.xml --eye cascades/haarcascade_eye.xml

# import the necessary packages
from et import ET
import imutils
import cv2
#import numpy as np #need if converting input for OTSU
import json

#replace parameters with file location of recognition libraries if different
et = ET("cascades/haarcascade_frontalface_default.xml", "cascades/haarcascade_eye.xml") #recognition libraries
# camera = cv2.VideoCapture(0) #initializes camera

calibrated = False
position = ""


# direction = ""

#function that identifies eye and resizes frame to only one eye
def resizeFrame(new_name):
	# grab the current frame
	filename = new_name
    
	#	 	frame = cv2.imread('C://Users//ajeel//Desktop//Faces//FZKmwbkp.png')
	frame = cv2.imread(filename)
	# resize the frame and convert it to grayscale
	frame = imutils.resize(frame, width = 300)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# use tracking function to get the dimensions and locations of where to put the rectangles for eyes and face
	rects_f, rects_e = et.track(gray)


	# draw the face rectangles in the full sized camera view
	for r in rects_f:
		cv2.rectangle(frame, (r[0], r[1]), (r[2], r[3]), (0, 255, 0), 2)
	#for r in rects_e:
		#cv2.rectangle(frame, (r[0], r[1]), (r[2], r[3]), (0, 255, 0), 2)
		#commented out drawing bounding box for eyes bc box showed up in frame when using rolling avg

	#makes a copy of the frame to manipulate and resize
	frameClone = frame.copy()

	eye1 = []
	#if it identifies and tracks eyes, collapse the box to only include the first eye
	# if there is an eye detected
	if len(rects_e) > 0:
		#try to use the second eye to avoid complications in switching eyes
		try:
			eye1 = rects_e[1]
		#if only one eye detected, rects_e[1] --> error --> use the first eye detected
		except:
			eye1 = rects_e[0]
		#toggle commenting out line below to bring back/take out rolling average
		eye1 = rolling_average(eye1, "eye") #rolling average makes the box smoother but runs into issues when "eye1" switches between right and left
		# if the height and width of the first eye is greater than 0 (aka exists)
		if eye1[3] > 0 and eye1[2] > 0:
			#resize frame to just the dimensions of eye tracking box
			#adding and subtracting percentage of frame reduce the frame to include as little area around the eye as possible
			ypercent = int((eye1[3] - eye1[1]) * .30)
			xpercent = int((eye1[2] - eye1[0]) * .17)
			frameClone = frameClone[eye1[1]+ypercent:eye1[3]-ypercent, eye1[0]+xpercent:eye1[2]-xpercent]

			width = int(frameClone.shape[1] * 2)
			height = int(frameClone.shape[0] * 2)
			dim = (width, height)
			# resize image
			frameClone = cv2.resize(frameClone, dim, interpolation=cv2.INTER_AREA)

	#otherwise show the whole face
	else:
		frameClone = []

	#continuously show entire frame in separate window
	# cv2.imshow("Whole camera", frame)
	#returns the frame cropped to only one eye

	return frameClone, eye1 #returns resized frame



recentsEye = []
recentsPupil = []
#takes in a list of integers (x, y, width, and height) and computes a rolling average for the previous 5 frames
def rolling_average(current, eyeOrPupil):
	#for making the rolling avg of the eye frame dimensions
	if eyeOrPupil == "eye":
		#add the current frame onto the end of the list
		recentsEye.append(current)
		if len(recentsEye) > 5:
			#limit the list length to the previous 5 frames
			recentsEye.pop(0)
		avg_vals = [0, 0, 0, 0]
		#adds all the x values, y values, etc in one list (avg_vals)
		for l in recentsEye:
			for i in range(0, 4):
				avg_vals[i] += l[i]

		#computes the average and makes it an acceptable type (a rounded integer)
		for i in range(0, len(avg_vals)):
			avg_vals[i] = int(round(avg_vals[i]/len(recentsEye)))

	#for making the rolling avg of the pupil box dimensions
	elif eyeOrPupil == "pupil":
		#add the current frame onto the end of the list
		recentsPupil.append(current)
		if len(recentsPupil) > 2:
			#limit the list length to the previous 2 frames
			recentsPupil.pop(0)

		avg_vals = [0, 0, 0, 0]
		#adds all the x values, y values, etc in one list (avg_vals)
		for l in recentsPupil:
			for i in range(4):
				avg_vals[i] += l[i]

		#computes the average and makes it an acceptable type (a rounded integer)
		for i in range(0, len(avg_vals)):
			avg_vals[i] = int(round(avg_vals[i]/len(recentsPupil)))

	#print(avg_vals)
	return avg_vals


def calculatePosition(rect_eye, pupil):
	print("calculating position")
	eyeX, eyeY, eyeW, eyeH = rect_eye[0], rect_eye[1], rect_eye[2], rect_eye[3]  #dimensions of eye bounding box (x and y of top right corner)
	pupilX, pupilY, pupilW, pupilH = pupil[0], pupil[1], pupil[2], pupil[3]  #dimensions of pupil bounding box (x and y of top right corner)

	eyeCenter = ((eyeX + int(eyeW/2)), (eyeY + int(eyeH/2))) #(x,y) of center of eye bounding box
	global adjustedCenter #from calibration
	pupilCenter = ((pupilX + int(pupilW / 2)), (pupilY + int(pupilH / 2)))  #(x,y) of center of pupil bounding box

	Xdifference = pupilCenter[0] - adjustedCenter[0] #difference in x's of adjustedCenter vs pupilCenter, - means pupil is left of center
	Ydifference = adjustedCenter[1] - pupilCenter[1] #difference in y's of adjustedCenter vs pupilCenter, - means pupil is below center
	print(Xdifference)
	print(Ydifference)

	#determining which of 9 areas gaze is placed in (areas split like tic tac toe board)

	xMargin, yMargin = int(eyeW/26), int(eyeH/26) #not sure why the margins have to be divided so much, maybe issue with calc of xdiff and ydiff
	print(xMargin)
	print(yMargin)

	#fairly inaccurate at this point, but getting there
	if (Xdifference > 0) & (abs(Xdifference) > xMargin):
		xdirection = "right"

	elif (Xdifference < 0) & (abs(Xdifference) > xMargin):
		xdirection = "left"

	elif abs(Xdifference) <= xMargin:
		xdirection = "center"

	else:
		xdirection = "invalid"


	if (Ydifference > 0) & (abs(Ydifference) > yMargin):
		ydirection = "upper"

	elif (Ydifference < 0) & (abs(Ydifference) > yMargin):
		ydirection = "lower"

	elif abs(Ydifference) <= yMargin:
		ydirection = "center"

	else:
		ydirection = "invalid"

	
	direction = ydirection + " " + xdirection

	return direction #returns description of area gaze is in (ex: upper right)



# indentifies and tracks pupil
def findPupil(new_name):
    # pupilDims="ajeel"
	#function that resizes frame from original to just one eye
	pupilDims=[0,0,0,0]
	eyeFrame, rect_e = resizeFrame(new_name)
	
    
    

	#maybe use value as a percentage of the highest so it adjusts for high and low light conditions
	#if an eye is detected, try to find the pupil
	if len(eyeFrame) > 0:
		#converts eye frame to grayscale and applies Gaussian blur to reduce noise
		gray_eye = cv2.cvtColor(eyeFrame, cv2.COLOR_BGR2GRAY)
		gray_eye = cv2.GaussianBlur(gray_eye, (15,15), 0) #(7,7) #(9,9) #(11,11)

		#gray_eye = cv2.Canny(gray_eye, 30, 150) #get rid of if not using OTSU

		rows, cols, _ = eyeFrame.shape

		#only identifies darkest parts of frame (trying to find pupil)
		#threshold = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 3, 2)  #good w blur (11, 11) or (9,9)
		#threshold = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 5, 1) #good w blur (13, 13)
		threshold = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 5, 2) #clear pupil but eyelid, blur (7,7), super noisy but good pupil blob w blur (15,15)
		#threshold = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 5, 3) # good, blur (11,11)
		#threshold = cv2.adaptiveThreshold(gray_eye,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,3,1) #higher threshhold, counts eyelid instead of pupil
		#threshold = cv2.threshold(gray_eye, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) #doesn't work w current gray_eye input type

		#finds the contours of the threshold
		contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

		#sorts the contours by area with largest area first
		contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse = True)

		'''
		#this code commented out determined the pupil from the contours based on the one closest to the ratio of width/height = 1
		#Which would mean a square-like shape (or circle-like shape)
		#but the contours didn't group well enough for it to work
		#get the dimensions for each contour and put them into cntDimensions[]
		cntDimensions = []
		for cnt in contours:
			#epsilon = 0.1 * cv2.arcLength(cnt, True)
			#approx = cv2.approxPolyDP(cnt, epsilon, True)
			x, y, w, h = cv2.boundingRect(cnt)
			cntDimensions.append([x,y,w,h])

			#only takes the contours w the top 3 biggest areas 
			if len(cntDimensions) == 3:
				break

		#have to put in a try/except bc will give error (at ratios.index(min(ratios))) if no contours to make ratios with
		try:
			#get the ratios of width/height for each contour and add how far it is from 1 to ratios[]
			ratios = []
			for dim in cntDimensions:
				#ratio = width of contour bounding box/height of contour bounding box
				ratio = dim[2]/dim[3]
				#how far it is from 1 (pupil is circle so it should be height = width --> ratio of 1)
				ratios.append(abs(1 - ratio))

			pupilCntIndex = ratios.index(min(ratios)) #the index of the contour closest to a ratio of 1 for height vs width

			#draws the contours on the original color eye
			#cv2.drawContours(eyeFrame, [cnt], -1, (0, 0, 255), 1)
			#x and y coordinates of top right corner of bounding box, width and height of bounding box
			(x, y, w, h) = cv2.boundingRect(cnt)

			#draws rectangle + horizontal line and vertical line down center of rectangle
			cv2.rectangle(eyeFrame, (x, y), (x + w, y + h), (255, 255, 0), 1)
			cv2.line(eyeFrame, (x + int(w / 2), 0), (x + int(w / 2), rows), (0, 255, 0), 1)
			cv2.line(eyeFrame, (0, y + int(h / 2)), (cols, y + int(h / 2)), (0, 255, 0), 1)
		except:
			continue



		'''	
		#different method for determining pupil from contours:  the "pupil" is determined by largest area
		for cnt in contours:
			#draws the contours on the original color eye
			#cv2.drawContours(eyeFrame, [cnt], -1, (0, 0, 255), 1)
			#x and y coordinates of top right corner of bounding box, width and height of bounding box
			(x, y, w, h) = cv2.boundingRect(cnt)

			#computes the rolling avg for the previous 2 frames for the pupil bounding box dimensions
			#must be compatible with the rolling_average method + code below these 3 lines (which is why it seems repetitive)
			pupilDims = [x,y,w,h]
			pupilDims = rolling_average(pupilDims, "pupil")
			x,y,w,h = pupilDims[0], pupilDims[1], pupilDims[2], pupilDims[3]

			cv2.rectangle(eyeFrame, (x,y), (x + w, y + h), (255, 255, 0), 1)
			cv2.line(eyeFrame, (x + int(w/2), 0), (x + int(w/2), rows), (0, 255, 0), 1)
			cv2.line(eyeFrame, (0, y + int(h/2)), (cols, y + int(h/2)), (0, 255, 0), 1)

			#stops the loop after the first one so only the contour with the biggest area is drawn
			#using a loop bc no errors if no eyes detected (if nothing in the list contours)
			# break


		# cv2.imshow("Only eye", eyeFrame)
		# cv2.imshow("grayscale eye", gray_eye)
		# cv2.imshow("threshold", threshold)
		cv2.waitKey(1)


	
	position = "default position"
	if calibrated == True:
		try:
			# global position 
			position = calculatePosition(rect_e, pupilDims)
			print("position variable in findPupil() is ")
			print(position)
		# it comes in here, I dont want it here
		except: #will give error if no eyes detected (bc no pupilDims to pass in --> pass if no eyes detected)
			print("no eyes")
	print("these are pupilDims")
	print(pupilDims)
	print("this is pos")
	print(position)
	dictPupil = {
		"pupilPosition":position, 
		"pupilDimension":pupilDims
	}
	return dictPupil


# calibrate() adjusts the eye's center reference point to where the pupil is when user looking at the center of the screen
# need to make it dynamic adjusting for position of light source so user can move positions without issue
adjustedCenter = []
def calibrate(new_name):
	print("Please look roughly at the center of the screen for 3 seconds")
	cv2.waitKey(1500)  #give them 1.5 seconds to look at the center of the screen
	pupilDict = findPupil(new_name)
	pupil = pupilDict.get("pupilDimension")

	pupilX, pupilY, pupilW, pupilH = pupil[0], pupil[1], pupil[2], pupil[3]  #dimensions of pupil bounding box (x and y of top right corner)
	pupilCenter = ((pupilX + int(pupilW / 2)), (pupilY + int(pupilH / 2)))  #(x,y) of center of pupil bounding box
	print("Your center point has been adjusted.")
	print("Your center point is " + str(pupilCenter))
	global calibrated
	calibrated = True

	global adjustedCenter
	adjustedCenter = pupilCenter  #this is the adjusted reference point for where the eye is looking at the center of the screen

#running the functions
def eyeTrack(new_name):
    # calibrate(new_name)
	calibrate(new_name)
    
    # while True:
    # 	# position = findPupil(new_name)
	# 	# return position
	# 	positionDICT = {"position":position}
	# 	positionJSON = json.dumps(positionDICT)
	# 	print("bye")
    
	# 	return positionJSON

	# while True: 
		
	pupilDict2= findPupil(new_name)
	somePosition=pupilDict2.get("pupilPosition")
	print("somePosiition is")
	print(somePosition)
	# print(somePosition)
	# print("position is" + position)
	positionDICT ={"position": somePosition}
	positionJSON = json.dumps(positionDICT)
	print(positionJSON)
	return positionJSON
	
	# calculatePosition(new_name)
		
	

# def eyeTracker(new_name):
# 	eyeTrack(new_name)
# 	print("hello")
# 	positionDICT = {"position":position}
# 	positionJSON = json.dumps(positionDICT)
# 	print("bye")
    
# 	return positionJSON
	


		
	

# def eyeTrack2():


# cleanup the camera and close any open windows
#line
# camera.release()
# cv2.destroyAllWindows()

