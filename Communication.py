import serial
import numpy as np
import time
import threading
TEC_ENABLE = [b"TE", [29779, 25185, 25964,0,0,0,0,0,0,0,0,0,0,0,0]]
LASER_ENABLE = [b"LE", [29779, 25185, 25964,0,0,0,0,0,0,0,0,0,0,0,0]]
SINGLE_SWEEP = [b"SS", [28484, 25966, 0,0,0,0,0,0,0,0,0,0,0,0,0]]

class Threaded_Comms(threading.Thread):
    def __init__(self, serialObject, toWrite, commList):
        threading.Thread.__init__(self)
        self.ser = serialObject
        self.toWrite = toWrite
        self.commList = commList
        self.receivedValue = None
    def run(self):
        print("Thread Beginning")
        command = self.commList[0]
        expResp = self.commList[1]
        startTime = time.time()
        self.ser.write(command)
        self.ser.flush()  # it is buffering. required to get the data out *now*
        time.sleep(.3)  # Wait for any initialization and then for data
        #### Create Initial array
        rec = self.ser.read(30)
        parsed = np.frombuffer(rec, np.uint16)
        values = np.array([parsed])
        #### Keep reading and appending until .01s without any recieved data
        while True:
            # Pull chunks of 30 from the buffer and append
            while self.ser.in_waiting:
                rec = self.ser.read(30)
                parsed = np.frombuffer(rec, np.uint16)
                values = np.append(values, [parsed], axis=0)
            # Buffer empty, give time to fill again
            time.sleep(.01)
            if np.array_equal(values[-1], expResp):
                print("Thread Success")
                self.receivedValue = values
                return
            elif time.time() - startTime >= 10:
                print("Receiving Timed Out")
                self.receivedValue = values
                return


class Communication:

    def __init__(self, baudRate=9600, portNum=10):
        self.ser = serial.Serial()
        self.ser.baudrate = baudRate
        self.ser.port = "COM" + str(portNum)

    def connect(self):
        try:
            self.ser.open()
            return self.ser.isOpen()
        except serial.SerialException:
            print("Connection Failed")
            return False


    def getConnection(self):
        return str(self.ser)

    def verifyConnection(self):
        #TODO: create identification command
        pass
    def runSweep(self):
        self.ser.write(b"SS")
        self.ser.flush()  # it is buffering. required to get the data out *now*
        time.sleep(.3)  # Wait for any initialization and then for data
        #### Create Initial array
        readIn = self.ser.read(30)
        parsed = np.frombuffer(readIn, np.uint16)
        values = np.array([parsed])
        #### Keep reading and appending until .01s without any recieved data
        while True:
            # Pull chunks of 30 from the buffer and append
            while self.ser.in_waiting:
                readIn = self.ser.read(30)
                parsed = np.frombuffer(readIn, np.uint16)
                values = np.append(values, [parsed], axis=0)
            # Buffer empty, give time to fill again
            time.sleep(.01)
            # Quit if still empty after .01s
            if self.ser.in_waiting == 0:
                break
        return values
    def commandAndRead(self,commList):
        command = commList[0]
        expResp = commList[1]
        startTime = time.time()
        self.ser.write(command)
        self.ser.flush()  # it is buffering. required to get the data out *now*
        time.sleep(.3)  # Wait for any initialization and then for data
        #### Create Initial array
        rec = self.ser.read(30)
        parsed = np.frombuffer(rec, np.uint16)
        values = np.array([parsed])
        #### Keep reading and appending until .01s without any recieved data
        while True:
            # Pull chunks of 30 from the buffer and append
            while self.ser.in_waiting:
                rec = self.ser.read(30)
                parsed = np.frombuffer(rec, np.uint16)
                values = np.append(values, [parsed], axis=0)
            # Buffer empty, give time to fill again
            time.sleep(.01)
            if np.array_equal(values[-1], expResp):
                print("Success")
                return values
            elif time.time()-startTime >= 15:
                print("Timeout Receiving")
                return None
    def asyncCommand(self, toWrite, commList):
        commsThread = Threaded_Comms(self.ser, toWrite, commList)
        commsThread.start()
        return commsThread
    def endConnection(self):
        self.ser.write(b"SR")
