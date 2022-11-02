import tkinter.filedialog

import Communication
import DataProcessing
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)
import time
from enum import Enum
import tkinter as tk
import tkinter.ttk as ttk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import os.path

matplotlib.use('TkAgg')


TEXT_ERROR = "Something went wrong. Try again. "
TEXT_ENABLE_TEC = "Connected. TEC ready to be enabled."
TEXT_TEC_STABILIZING = "TEC stabilizing..."
TEXT_ENABLE_LASER = "Laser ready to be enabled."
TEXT_TEC_STABILIZING_LASER = "Laser on. TEC stabilizing..."
TEXT_ENABLE_SWEEP = "Laser on. Ready for sweep."
TEXT_SWEEPING = "Sweeping..."


class CommStruct(Enum):
    PD0LO = 0   # stage 2 amplification, lowest powers.
    PD0HI = 1   # stage 1 amplification, highest powers.
    PD1LO = 2
    PD1HI = 3
    PD2LO = 4
    PD2HI = 5
    PD3LO = 6
    PD3HI = 7
    THERM1 = 8
    MUX = 9
    PD4LO = 10
    PD4HI = 11
    THERM0 = 12
    MUXSPAN = 13
    CSIND = 14

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Laser Control V0.1')
        self.board = Communication.Communication()
        self.board.connect()
        self.textOutput = tk.Label(self, text=TEXT_ENABLE_TEC)
        self.textOutput.pack()
        self.lastFrameTime=time.time()
        self.frameTimeOutput = tk.Label(self, text = str(0))
        self.frameTimeOutput.pack()
        self.currThread = None
        self.rawData = None
        self.lastData = None
        controller = None
        self.constantSweeping = False
        self.workingDir = os.path.abspath(os.getcwd())
        self.otherFrame = Main_Controls(self,controller)
        self.otherFrame.pack()
        self.selectedPlot = tk.StringVar(self)
        self.wavelengths = np.load("WavelengthIndices.npy")
        self.yLimits = None
        self.lockScale = tk.IntVar()
        plotOptions = [selection.name for selection in CommStruct]
        plotSelect = ttk.OptionMenu(
            self,
            self.selectedPlot,
            plotOptions[0],
            *plotOptions,
            command=self.optionChanged
        )
        self.lockButton = tk.Checkbutton(
            self,
            text = "Lock Scale",
            variable = self.lockScale,
            command=self.lockAxes
            )
        plotSelect.pack()
        self.lockButton.pack()
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self)

        self.figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH,
                                                expand=1)
        self.after(10, self.loop)

    def loop(self):
        self.checkForData()
        currTime = time.time()
        frameTime = (currTime - self.lastFrameTime)*1000
        self.frameTimeOutput.config(text="%d"%frameTime)
        self.lastFrameTime = currTime
        self.after(10, self.loop)

    def checkForData(self):
        if self.currThread is not None and not self.currThread.is_alive():
            print("Thread Finished")
            receivedValue = self.currThread.receivedValue
            self.currThread = None
            if receivedValue is not None:
                self.lastData = DataProcessing.averageData(receivedValue)
                self.lastData = DataProcessing.intValToVoltage(self.lastData)
                self.plot()
                successMSG = ""
            else:
                successMSG = TEXT_ERROR
            if self.constantSweeping:
                self.otherFrame.runSweepThreaded()
            else:
                self.otherFrame.enableSweep(successMSG)

    def optionChanged(self, command):
        if self.lastData is not None:
            self.plot()
    def lockAxes(self):
        if self.lockScale.get():
            self.yLimits = None
        self.optionChanged(None)
    def plot(self):
        self.figure.clf()
        self.axes = self.figure.add_subplot()
        valueIdx = CommStruct[self.selectedPlot.get()].value
        # transformedData = self.lastData[:,valueIdx]
        transformedData = 10*np.log10(self.lastData[:,valueIdx])
        self.axes.plot(self.wavelengths,transformedData,linewidth=0.75)
        self.axes.set_ylabel('Optical Power (dBm)')
        self.axes.set_xlabel('Wavelength (nm)')
        if self.lockScale.get():
            if self.yLimits is not None:
                self.axes.set_ylim(np.add(self.yLimits,(-3,+3)))
            else:
                self.axes.autoscale()
                self.yLimits = self.axes.get_ylim() #Gets limits from autolimit
                self.axes.set_ylim(np.add(self.yLimits, (-3, +3)))
        else:
            print("Hello")
            self.axes.autoscale()
        self.figure_canvas.get_tk_widget().pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand=1)
        self.figure_canvas.draw()
        self.toolbar.update()


class Main_Controls(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(
            self,
            parent,
            relief=tk.RAISED,
            borderwidth=1)
        self.parent=parent
        self.controller = controller

        self.TECButton = StandardButton(
            self,
            text="Enable TEC",
            command=self.enableTEC)
        self.LaserButton = tk.Button(
            self,
            text="Enable Laser",
            command=self.enableLaser,
            state=tk.DISABLED)

        self.SweepButton = StandardButton(
            self,
            text="Run Sweep",
            command=self.runSweepThreaded,
            state=tk.DISABLED)

        self.StopButton = StandardButton(
            self,
            text="Turn Off",
            command=self.parent.board.endConnection,
            state=tk.NORMAL)

        self.RepeatButton = StandardButton(
            self,
            text="Repeat Sweep",
            command=self.repeatSweep,
            state = tk.DISABLED
            )
        # self.ConstantButton = StandardButton(
        #     self,
        #     text="Constant Wavelength",
        #     state=tk.DISABLED
        # )
        self.SaveButton = StandardButton(
            self,
            text="Save Data",
            command=self.saveData,
        )
        self.TECButton.grid(column=1, row=1, padx=3, pady=3)
        self.LaserButton.grid(column=2, row=1, padx=3, pady=3)
        self.SweepButton.grid(column=3, row=1, padx=3, pady=3)
        self.StopButton.grid(column=4, row=1, padx=3, pady=3)
        self.RepeatButton.grid(column=5, row=1, padx=3, pady=3)
        self.SaveButton.grid(column=6, row=1, padx=3, pady=3)

    def enableTEC(self):
        self.parent.textOutput.config(text=TEXT_TEC_STABILIZING)
        self.TECButton.config(state=tk.DISABLED)
        self.update()
        command = Communication.TEC_ENABLE
        response = self.parent.board.commandAndRead(command)
        if response is not None:
            self.parent.textOutput.config(text=TEXT_ENABLE_LASER)
            self.LaserButton.config(state=tk.NORMAL)
        else:
            self.parent.textOutput.config(text=TEXT_ERROR + TEXT_ENABLE_TEC)
            self.TECButton.config(state=tk.NORMAL)

    def enableLaser(self):
        self.parent.textOutput.config(text=TEXT_TEC_STABILIZING_LASER)
        self.LaserButton.config(state=tk.DISABLED)
        self.StopButton.config(state=tk.NORMAL)
        self.update()
        command = Communication.LASER_ENABLE
        response = self.parent.board.commandAndRead(command)
        if response is not None:
            self.parent.textOutput.config(text=TEXT_ENABLE_SWEEP)
            self.SweepButton.config(state=tk.NORMAL)
            self.RepeatButton.config(state=tk.NORMAL)
        else:
            self.parent.textOutput.config(text=TEXT_ERROR + TEXT_ENABLE_LASER)
            self.LaserButton.config(state=tk.NORMAL)

    def runSweep(self):
        self.parent.textOutput.config(text=TEXT_SWEEPING)
        self.SweepButton.config(state=tk.DISABLED)
        self.update()
        command = Communication.SINGLE_SWEEP
        response = self.parent.board.commandAndRead(command)
        self.parent.rawData = response
        if response is not None:
            self.parent.textOutput.config(text=TEXT_ENABLE_SWEEP)
            self.SweepButton.config(state=tk.NORMAL)
            self.parent.lastData = self.parent.averageData(response)
            self.parent.lastData = self.parent.intValToVoltage(
                self.parent.lastData)
            self.parent.plot()
        else:
            self.parent.textOutput.config(text=TEXT_ERROR + TEXT_ENABLE_SWEEP)
            self.SweepButton.config(state=tk.NORMAL)

    def singleSweepCommand(self):
        self.parent.textOutput.config(text=TEXT_SWEEPING)
        self.SweepButton.config(state=tk.DISABLED)
        self.RepeatButton.config(state=tk.DISABLED)
        self.update()

    def runSweepThreaded(self):
        command = Communication.SINGLE_SWEEP
        self.parent.rawData = None # TODO: Make rawData thread safe
        currentThread = self.parent.board.asyncCommand(self.parent.rawData,
                                                       command)
        self.parent.currThread = currentThread

    def enableSweep(self, text):
        self.parent.textOutput.config(text= text + TEXT_ENABLE_SWEEP)
        self.StopButton.config(state=tk.NORMAL)
        self.SweepButton.config(state=tk.NORMAL)
        self.RepeatButton.config(state=tk.NORMAL)

    def repeatSweep(self):
        self.SweepButton.config(state=tk.DISABLED)
        self.StopButton.config(state=tk.DISABLED)
        self.RepeatButton.config(text="Stop Repeat", command = self.stopRepeat)
        self.parent.constantSweeping = True
        self.runSweepThreaded()

    def stopRepeat(self):
        self.RepeatButton.config(
            text="Repeat Sweep",
            command=self.repeatSweep,
            state=tk.DISABLED)
        self.parent.constantSweeping = False

    def saveData(self):
        if self.parent.lastData is not None:
            toSave = np.hstack((self.parent.lastData,
                                np.array([self.parent.wavelengths]).T))
            path = tkinter.filedialog.asksaveasfilename(
                initialdir=self.parent.workingDir,
                filetypes=[("Numpy Files", ".npy")],
                defaultextension=".npy"
            )
            if path is not None:
                print(path)
                np.save(path,toSave)
        else:
            raise ValueError("No value to save.")



class StandardButton(tk.Button):
    def init(self, parent, **kwargs):
        padding = 5
        kwargs["padx"] = padding
        kwargs["pady"] = padding
        super.__init__(parent, kwargs)
if __name__ == '__main__':
    print(os.path.abspath(os.getcwd()))
    app = App()
    app.mainloop()
