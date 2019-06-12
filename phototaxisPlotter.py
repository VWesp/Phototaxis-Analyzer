import sys
import numpy as np
import scipy.signal as signal
import matplotlib
matplotlib.use("PS")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def plotData(sample, progress, lock, data, datasheet, outputDirectory, dataNumber, informationOfTime,
             timePointIndices, plotColor, sgFilter, sgPlotColor, windowSize, polyOrder, period, startingPoint, pointSize, label):

    timePoints = informationOfTime[0]
    timePointLabels = informationOfTime[1]
    days = informationOfTime[2]
    minuteIndices = informationOfTime[3]
    minimumPhaseList = list()
    maximumPhaseList = list()
    minimumPeriodList = list()
    maximumPeriodList = list()
    maxVoltage = np.amax(data[sample])
    minVoltage = np.amin(data[sample])
    sampleData_invertMean = None
    if(minuteIndices != None):
        sampleData_mean = np.take(np.array(data[sample]), minuteIndices)
        sampleData_invertMean = (maxVoltage + minVoltage) - sampleData_mean
    else:
        sampleData_invert = np.array(np.split((maxVoltage+minVoltage)-data[sample], timePointIndices))
        sampleData_invertMean = np.mean(sampleData_invert[:,-dataNumber:], axis=1)

    dataPoints = sampleData_invertMean
    dataPoints_smoothed = signal.savgol_filter(sampleData_invertMean, windowSize, polyOrder)

    figure = plt.figure()
    plt.plot(timePoints, dataPoints, marker="o", markersize=pointSize, color=plotColor, linestyle="-",
             label="raw data")
    if(sgFilter):
        plt.plot(timePoints, dataPoints_smoothed, color=sgPlotColor, linestyle="-", label="smoothed data")
        plt.legend(bbox_to_anchor=(1.05,0.5))

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
            dayStart = startingPoint
        else:
            if(period == "Minimum"):
                plt.axvline(day, ymin=0.1, color="black", linestyle=":")
            elif(period == "Maximum"):
                plt.axvline(day, ymax=0.9, color="black", linestyle=":")
            elif(period == "Both"):
                plt.axvline(day, ymin=0.1, ymax=0.9, color="black", linestyle=":")

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
                valleys.reverse()
                for i in valleys:
                    if(daySample[i] < smallestValley):
                        smallestValley = daySample[i]
                        valley = i

                meanTime = None
                meanValley = None
                if(day == 0):
                    meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints[:-points], daySample[:-points],
                                                                      valley, threshold, "min")
                else:
                    meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints[points:-points],
                                                                      daySample[points:-points], valley-points,
                                                                      threshold, "min")
                if(lastValley != None):
                    bottomLine = minVoltage - (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastValley], [bottomLine, bottomLine], color="black", linestyle="-")
                    plt.annotate(str(meanTime-lastValley).replace(".", ",") + "h", xy=((meanTime+lastValley)/2, 0.04),
                                 xycoords=("data","axes fraction"), size=10, ha="center")
                    minimumPeriodList.append(str(meanTime-lastValley).replace(".", ","))

                top = minVoltage - (maxVoltage - minVoltage) * 0.15
                bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="black", linestyle="-")
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

                if(dayEnd == timePoints[-1]):
                    meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints[points:], daySample[points:],
                                                                    peak-points, threshold, "max")
                else:
                    meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints[points:-points],
                                                                    daySample[points:-points], peak-points,
                                                                    threshold, "max")
                if(lastPeak != None):
                    topLine = maxVoltage + (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastPeak], [topLine, topLine], color="black", linestyle="-")
                    plt.annotate(str(meanTime-lastPeak).replace(".", ",") + "h", xy=((meanTime+lastPeak)/2, 0.93),
                                 xycoords=("data","axes fraction"), size=10, ha="center")
                    maximumPeriodList.append(str(meanTime-lastPeak).replace(".", ","))

                top = maxVoltage + (maxVoltage - minVoltage) * 0.15
                bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="black", linestyle="-")
                maximumPhaseList.append(str(meanTime%24).replace(".", ",") + ";" + str(meanPeak).replace(".", ","))
                lastPeak = meanTime

    figure.savefig(outputDirectory + "tmp/" + sample + ".pdf", bbox_inches="tight")
    plt.close()
    with lock:
        progress.value += 1

    return {sample: [[timePoints, dataPoints], outputDirectory + "tmp/" + sample + ".pdf", minimumPhaseList,
            maximumPhaseList, minimumPeriodList, maximumPeriodList]}



def plotComparePlots(sampleList, progress, lock, plotList, datasheet, outputDirectory, informationOfTime,
                     pointSize, label):

    colorList = ("#000000", "#FF0000", "#FFD700", "#008000", "#0000FF", "#A52A2A", "#FF8C00", "#00FFFF", "#FF00FF",
                 "#E9967A", "#BDB76B", "#00FF00", "#6A5ACD", "#2F4F4F", "#BC8F8F")
    samples = sampleList.split(" - ")
    patches = list()
    colorIndex = 0
    firstPlot = True
    timePoints = informationOfTime[0]
    timePointLabels = informationOfTime[1]
    days = informationOfTime[2]
    figure = plt.figure()
    for sample in samples:
        plot = next(list(page.values()) for page in plotList if sample == list(page.keys())[0])[0][0]
        x = plot[0]
        y = plot[1]
        legendPatch, = plt.plot(x, y, label=sample, marker="o", markersize=pointSize, color=colorList[colorIndex],
                                linestyle="-")
        patches.append(legendPatch)
        if(firstPlot):
            plt.title(sampleList + "\n" + datasheet.split("/")[-1])
            plt.xticks(days, timePointLabels)
            plt.xlabel(label)
            plt.ylabel("mV")
            for day in days:
                if(day in timePoints):
                    plt.axvline(day, color="black", linestyle=":")

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
                if(y[i] > y[i-j] or y[i-j] < y[i-j-1] or y[i] > y[i+j] or y[i+j] < y[i+j-1]):
                    valleyFound = False
                    break

            if(valleyFound):
                valleys.append(i)

            peakFound = True
            for j in range(1, points+1, 1):
                if(y[i] < y[i-j] or y[i-j] > y[i-j-1] or y[i] < y[i+j] or y[i+j] > y[i+j-1]):
                    peakFound = False
                    break

            if(peakFound):
                peaks.append(i)

    return (valleys, peaks)



def calculatePeakAndValleyMean(x, y, point, threshold, mode):

    valueList = list()
    indexList = list()
    leftY = y[:point+1]
    for i in range(len(leftY)-2, -1, -1):
        if(mode == "min"):
            if(leftY[i] > y[point]+threshold or leftY[i] < leftY[i+1]):
                break
            elif(y[point] <= leftY[i] <= y[point]+threshold):
                valueList.append(leftY[i])
                indexList.append(i)
        elif(mode == "max"):
            if(leftY[i] < y[point]-threshold or leftY[i] > leftY[i+1]):
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
            if(rightY[i] > y[point]+threshold or leftY[i] < leftY[i-1]):
                break
            elif(y[point] <= rightY[i] <= y[point]+threshold):
                valueList.append(rightY[i])
                indexList.append(point+i)
        elif(mode == "max"):
            if(rightY[i] < y[point]-threshold or leftY[i] > leftY[i-1])):
                break
            elif(y[point] >= rightY[i] >= y[point]-threshold):
                valueList.append(rightY[i])
                indexList.append(point+i)

    meanX = int(np.mean(np.take(x, indexList)))
    meanY = np.mean(np.array(valueList))
    return (meanX, meanY)
