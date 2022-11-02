import time
import tkinter as tk
from tkinter.colorchooser import askcolor
import sys
import cv2
import numpy as np
from PIL import ImageTk, Image
from pypylon import pylon
import Communication
import LaserControlGUI

board = Communication.Communication()
board.connect()
sweepData = board.runSweep()
print(sweepData.shape)
root = tk.Tk()
LaserControlGUI.LaserControlGUI(root, "Window")
root.mainloop()