import serial

import Communication
import LaserControlGUI
class Controller():
    def __init__(self):
        self.board = Communication.Communication()
        self.isConnected = self.board.connect()
        win = LaserControlGUI.App()
    def enableTEC(self):
        pass
