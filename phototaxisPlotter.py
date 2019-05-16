import sys
import numpy as np
import scipy.signal as signal
import matplotlib
matplotlib.use("PS")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plotData(sample, progress, lock, data, datasheet, outputDirectory, dataNumber, minutePoint, dataPerMeasurement, dataMinutePoints, timePointIndices, sgFilter, windowSize, polyOrder, period, startingPoint, pointSize, label):
        
    timePoints = np.unique(data["h"] // 1 + startingPoint).astype(float)
    timePointLabels = None
    days = np.arange(0, timePoints[-1], 24)
    if(label == "Days"):
        timePointLabels = np.unique((timePoints // 24).astype(int))
    elif(label == "Hours"):
        timePointLabels = days
        
    minuteIndices = None
    if(minutePoint != "None"):
        minuteIndex = np.where(dataMinutePoints == minutePoint)[0][0]
        minuteIndices = np.arange(minuteIndex, len(data["h"]), dataPerMeasurement)
        
    minimumPhaseList = list()
    maximumPhaseList = list()
    minimumPeriodList = list()
    maximumPeriodList = list()
    maxVoltage = np.amax(data[sample])
    minVoltage = np.amin(data[sample])
    sampleData_invertMean = None
    if(minutePoint != "None"):
        sampleData_mean = np.take(np.array(data[sample]), minuteIndices)
        sampleData_invertMean = (maxVoltage + minVoltage) - sampleData_mean
    else:
        sampleData_invert = np.array(np.split((maxVoltage+minVoltage)-data[sample], timePointIndices))
        sampleData_invertMean = np.mean(sampleData_invert[:,-dataNumber:], axis=1)
    
    if(sgFilter == "On"):
        dataPoints = signal.savgol_filter(sampleData_invertMean, windowSize, polyOrder)
    elif(sgFilter == "Off"):
        dataPoints = sampleData_invertMean
    
    figure = plt.figure()
    plot = plt.plot(timePoints, dataPoints, marker="o", markersize=pointSize, color="k", linestyle="-")
    plt.title(sample + "\n" + datasheet.split("/")[-1])
    plt.xticks(days, timePointLabels)
    plt.xlabel(label)
    plt.ylabel("mV")
    threshold = (maxVoltage - minVoltage) * 0.05
    lastValley = None
    lastPeak = None
    points = 1
    for day in days:
        dayStart = day - (2 * points)
        dayEnd = day + (22 + (2 * points))
        if(day == 0):
            dayStart = int(startingPoint)
        else:
            if(period == "Minimum"):
                plt.axvline(day, ymin=0.1, color="k", linestyle=":")
            elif(period == "Maximum"):
                plt.axvline(day, ymax=0.9, color="k", linestyle=":")
            elif(period == "Both"):
                plt.axvline(day, ymin=0.1, ymax=0.9, color="k", linestyle=":")

        if(not dayEnd in timePoints):
            dayEnd = timePoints[-1]

        timeIndexStart = np.where(timePoints == dayStart)[0][0]
        timeIndexEnd = np.where(timePoints == dayEnd)[0][0]
        daySample = dataPoints[timeIndexStart:timeIndexEnd+1]
        dayTimePoints = timePoints[timeIndexStart:timeIndexEnd+1]
        valleys, peaks = findPeaksAndValleys(daySample, points)
        if(len(valleys) and (period == "Minimum" or period == "Both")):
            if(dayEnd != timePoints[-1]):
                valley = None
                smallestValley = sys.float_info.max
                for i in valleys:
                    if(daySample[i] <= smallestValley):
                        smallestValley = daySample[i]
                        valley = i
                
                meanTime = None
                meanValley = None
                if(day == 0):
                    meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints[:-points], daySample[:-points], valley, threshold, "min")
                elif(dayEnd == timePoints[-1]):
                    meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints[points:], daySample[points:], valley-points, threshold, "min")
                else:
                    meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints[points:-points], daySample[points:-points], valley-points, threshold, "min")
                if(lastValley != None):
                    bottomLine = minVoltage - (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastValley], [bottomLine, bottomLine], color="k", linestyle="-")
                    plt.annotate(str(meanTime-lastValley).replace(".", ",") + "h", xy=((meanTime+lastValley)/2, 0.04), xycoords=("data","axes fraction"), size=10, ha="center")
                    minimumPeriodList.append(str(meanTime-lastValley).replace(".", ","))
                    
                top = minVoltage - (maxVoltage - minVoltage) * 0.15
                bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="k", linestyle="-")
                minimumPhaseList.append(str(meanTime%24).replace(".", ",") + ";" + str(meanValley).replace(".", ","))
                lastValley = meanTime
        if(len(peaks) and (period == "Maximum" or period == "Both")):
            if(day != 0):
                peak = None
                highestPeak = 0
                for i in peaks:
                    if(daySample[i] > highestPeak):
                        highestPeak = daySample[i]
                        peak = i
                
                meanTime = None
                meanPeak = None
                if(day == 0):
                    meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints[:-points], daySample[:-points], peak, threshold, "max")
                elif(dayEnd == timePoints[-1]):
                    meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints[points:], daySample[points:], peak-points, threshold, "max")
                else:
                    meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints[points:-points], daySample[points:-points], peak-points, threshold, "max")
                if(lastPeak != None):
                    topLine = maxVoltage + (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastPeak], [topLine, topLine], color="k", linestyle="-")
                    plt.annotate(str(meanTime-lastPeak).replace(".", ",") + "h", xy=((meanTime+lastPeak)/2, 0.93), xycoords=("data","axes fraction"), size=10, ha="center")
                    maximumPeriodList.append(str(meanTime-lastPeak).replace(".", ","))
                    
                top = maxVoltage + (maxVoltage - minVoltage) * 0.15
                bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="k", linestyle="-")
                maximumPhaseList.append(str(meanTime%24).replace(".", ",") + ";" + str(meanPeak).replace(".", ","))
                lastPeak = meanTime
            
    figure.savefig(outputDirectory + "tmp/" + sample + ".pdf", bbox_inches="tight")
    plt.close()
    with lock:
        progress.value += 1
        
    return {sample: [[timePoints, dataPoints], outputDirectory + "tmp/" + sample + ".pdf", minimumPhaseList, maximumPhaseList, minimumPeriodList, maximumPeriodList]}



def plotComparePlots(sampleList, progress, lock, plotList, data, datasheet, outputDirectory, startingPoint, pointSize, label):
    
    colorList = ("k", "b", "g", "r", "c", "m", "y")
    samples = sampleList.split(" - ")
    patches = list()
    colorIndex = 0
    firstPlot = True
    timePoints = np.unique(data["h"] // 1 + startingPoint).astype(int)
    timePointLabels = None
    days = np.arange(0, timePoints[-1], 24)
    if(label == "Days"):
        timePointLabels = np.unique((timePoints // 24).astype(int))
    elif(label == "Hours"):
        timePointLabels = days
        
    figure = plt.figure()
    for sample in samples:
        plot = next(list(page.values()) for page in plotList if sample == list(page.keys())[0])[0][0]
        x = plot[0]
        y = plot[1]
        legendPatch, = plt.plot(x, y, label=sample, marker="o", markersize=pointSize, color=colorList[colorIndex], linestyle="-")
        patches.append(legendPatch)
        if(firstPlot):
            plt.title(sampleList + "\n" + datasheet.split("/")[-1])
            plt.xticks(days, timePointLabels)
            plt.xlabel(label)
            plt.ylabel("mV")
            for day in days:
                if(day in timePoints):
                    plt.axvline(day, color="k", linestyle=":")

            firstPlot = False

        if(colorIndex == len(colorList)-1):
            colorIndex = 0
        else:
            colorIndex += 1

    plt.legend(handles=patches, bbox_to_anchor=(1.05,0.5))
    figure.savefig(outputDirectory + "tmpCompare/" + sampleList + ".pdf", bbox_inches="tight")
    plt.close()
    
    del patches[:]
    with lock:
        progress.value += 1
        
    return {sampleList: outputDirectory + "tmpCompare/" + sampleList + ".pdf"}



def findPeaksAndValleys(y, points):
    
    valleys = list()
    peaks = list()
    if(len(y) > points*2):
        for i in range(points, len(y)-points, 1):
            valleyFound = True
            for j in range(1, points+1, 1):
                if(y[i] > y[i-j] or y[i] > y[i+j]):
                    valleyFound = False
                    break
            
            if(valleyFound):
                valleys.append(i)
                
            peakFound = True
            for j in range(1, points+1, 1):
                if(y[i] < y[i-j] or y[i] < y[i+j]):
                    peakFound = False
                    break
                
            if(peakFound):
                peaks.append(i)

    return (valleys, peaks)



def calculatePeakAndValleyMean(x, y, point, threshold, mode):

    valueList = list()
    indexList = list()
    leftY = y[:point]
    for i in range(len(leftY)-1, -1, -1):
        if(mode == "min"):
            if(leftY[i] > y[point]+threshold):
                break
            elif(y[point] <= leftY[i] <= y[point]+threshold):
                valueList.append(leftY[i])
                indexList.append(i)
        elif(mode == "max"):
            if(leftY[i] < y[point]-threshold):
                break
            elif(y[point] >= leftY[i] >= y[point]-threshold):
                valueList.append(leftY[i])
                indexList.append(i)
    
    indexList = list(reversed(indexList))
    valueList.append(y[point])
    indexList.append(point)
    rightY = y[point:]
    for i in range(1, len(rightY), 1):
        if(mode == "min"):
            if(rightY[i] > y[point]+threshold):
                break
            elif(y[point] <= rightY[i] <= y[point]+threshold):
                valueList.append(rightY[i])
                indexList.append(point+i)
        elif(mode == "max"):
            if(rightY[i] < y[point]-threshold):
                break
            elif(y[point] >= rightY[i] >= y[point]-threshold):
                valueList.append(rightY[i])
                indexList.append(point+i)
    
    meanX = int(np.mean(np.take(x, indexList)))
    meanY = np.mean(np.array(valueList))
    return (meanX, meanY)
