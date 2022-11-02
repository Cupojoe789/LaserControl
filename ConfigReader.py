import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
class ConfigReader():
    cfgFilePath = "InterpVals3.xlsx"
    AVCC1 = 3.55
    bitVal = 4095
    pdCount = 5
    def __init__(self):
        cfgData = pd.read_excel(self.cfgFilePath,sheet_name=None)
        wl = np.array(cfgData["InterpVals3"].iloc[:, 0])
        np.save("WavelengthIndices",wl)
        v = np.array(cfgData["PD4"].iloc[:,2])
        v = v[~np.isnan(v)]
        i = np.array(cfgData["PD4"].iloc[:,3])
        i = i[~np.isnan(i)]
        print(i)
        polys = np.polyfit(v,i,1)
        testPoints = np.linspace(v[0],v[-1],10)
        testVals = self.linear(polys[0],testPoints)
        print(polys)
        print(v)
        print(i)
        plt.plot(v,i)
        plt.plot(testPoints,testVals)
        plt.show()
    def linear(self,a,x):
        return a*x
configReader = ConfigReader()