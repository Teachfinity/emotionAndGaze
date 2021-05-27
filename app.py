

from flask import Flask
import glob
import os
# ******
from real_time_video import emotionRecog 




from et import ET
import imutils
import cv2

# from eyeTracker import eyeTracker
from eyeTracker import eyeTrack

app = Flask(__name__)

@app.route('/')
def hello():
    # return {"happy":"Happy"}

# import pathlib
# from fer import FER
# import matplotlib.pyplot as plt 
    
    folder_path = r'C:\\Users\\ajeel\\Desktop\\Faces\\*'
    
    files = glob.glob(folder_path)
    # max file will store the file name with latest creation time
    max_file = max(files, key=os.path.getctime)
    # add .png extension to that file
    new_name = max_file + ".png"
    
    # max_file.rename(folder_path, new_name)
    print("this is new for ajeel")
    os.rename(r'{}'.format(max_file),r'{}'.format(new_name))
    print(max_file )

    # **********************************
    # emotion recog starts here
    # ************************************

    currEmotion = emotionRecog(new_name)

    print("this is new for ajeel")

    # return {"currEmotion": currEmotion}
    return currEmotion

@app.route('/eyeTrack')
def hello2():
    folder_path = r'C:\\Users\\ajeel\\Desktop\\Faces\\*'
    
    files = glob.glob(folder_path)
    # max file will store the file name with latest creation time
    max_file = max(files, key=os.path.getctime)
    # add .png extension to that file
    new_name = max_file + ".png"
    
    # max_file.rename(folder_path, new_name)
    print("this is new for ajeel")
    os.rename(r'{}'.format(max_file),r'{}'.format(new_name))
    print(max_file )

    currDirection = eyeTrack(new_name)
    return currDirection
