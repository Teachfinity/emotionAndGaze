from typing import Optional



# from flask import Flask
import glob
import os
# ******
from real_time_video import emotionRecog 

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    folder_path = r'C:\\Users\\ajeel\\Desktop\\Faces\\*'
    
    files = glob.glob(folder_path)
    # max file will store the file name with latest creation time
    max_file = max(files, key=os.path.getctime)
    # add .png extension to that file
    new_name = max_file + ".png"
    
    # max_file.rename(folder_path, new_name)
    os.rename(r'{}'.format(max_file),r'{}'.format(new_name))
    print(max_file )

    emotionRecog()