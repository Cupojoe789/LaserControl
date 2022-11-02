import time
import numpy as np

def intValToVoltage(data):
    AVCC1 = 3.55
    bitVal = 4095
    lowConv = 3.21535243e01
    highConv = 0.29010633
    pdIndicies = list(range(8)) + [10, 11]
    data[:, pdIndicies] = data[:, pdIndicies] * (AVCC1 / bitVal)
    data[:, 10] = data[:, 10] * lowConv / 1000
    data[:, 11] = data[:, 11] * highConv / 1000
    return data

def averageData(data):
    pointsPerSweep = 998
    startTime = time.time()
    averagedData = np.empty([pointsPerSweep,15])
    index = 1 #start at 1 because board indicies starts at 1 *yuck*
    count = 0
    tempRow = np.zeros(15)
    for i in range(0, len(data)-1):
        measurementIndex = data[i,14]
        if measurementIndex == index:
            tempRow = tempRow+data[i]
            count += 1
        elif measurementIndex > index:
            if count: #Only save if count !=0
                if tempRow[14] % count != 0:
                    raise RuntimeError("Incorrect averaging")
                averagedData[index-1] = tempRow/count
            index = measurementIndex
            tempRow = data[i]
            count = 1
        else:
            raise RuntimeError("Invalid Data Structure")
    if count: #save the last row
        averagedData[index-1] = tempRow/count
    print((time.time()-startTime)*1000)
    return(averagedData)
