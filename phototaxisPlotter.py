import sys
import numpy as np
import scipy.signal as signal
import matplotlib
matplotlib.use("PS")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages


def plotData(file, input_list, progress, progress_per_step, lock):
    columns = list(input_list[file]["data"])[2:]
    time_points = np.unique(input_list[file]["data"]["h"] // 1 + input_list[file]["startingpoint"]).astype(float)
    time_point_labels = None
    hours = np.arange(0, time_points[-1], 24).astype(int)
    if(input_list[file]["xlabel"] == "Days"):
        timePointLabels = np.unique((time_points // 24)).astype(int)
    elif(input_list[file]["xlabel"] == "Hours"):
        timePointLabels = hours

    pdf_document = PdfPages(input_list[file]["output"] + ".".join(file.split(".")[:-1]) + ".pdf")
    for column in columns:
        column_data = input_list[file]["data"][column]
        max_voltage = np.amax(column_data)
        min_voltage = np.amin(column_data)
        data_mean_inverted = None
        data_inverted = np.array((max_voltage+min_voltage) - column_data)
        if(input_list[file]["minutepoint"] != -1):
            minute_index = np.where(input_list[file]["data_minutepoints"] == input_list[file]["minutepoint"])[0][0]
            minute_indices = np.arange(minute_index, len(input_list[file]["data"]["h"]),
                                       input_list[file]["data_per_measurement"])
            data_inverted_per_minutepoint = np.take(data_inverted, minute_indices)
            data_mean_inverted = np.mean(data_inverted_per_minutepoint, axis=1)
        else:
            data_inverted_per_timepoint = np.array(np.split(data_inverted, input_list[file]["timepoint_indices"]))
            data_mean_inverted = np.mean(data_inverted_per_timepoint[:,-input_list[file]["datanumber"]:],
                                         axis=1)

        figure = plt.figure()
        plt.plot(time_points, data_mean_inverted, marker="o", markersize=input_list[file]["pointsize"],
                 color=input_list[file]["color"], linestyle="-", label="raw data")
        if(input_list[file]["sg_filter"]["on"]):
            data_mean_inverted_smoothed = signal.savgol_filter(data_mean_inverted,
                                                               input_list[file]["sg_filter"]["window"],
                                                               input_list[file]["sg_filter"]["poly"])
            plt.plot(time_points, data_mean_inverted_smoothed, color=input_list[file]["sg_filter"]["color"],
                     linestyle="-", label="smoothed data")
            plt.legend(bbox_to_anchor=(1.05,0.40))

        for day in hours:
            if(day != 0):
                plt.axvline(day, ymin=0.1, ymax=0.9, color="black", linestyle=":")

        plt.title(column + "\n" + file)
        plt.xticks(hours, time_point_labels)
        plt.xlabel(input_list[file]["xlabel"])
        plt.ylabel("mV")
        pdf_document.savefig(figure)
        plt.close()
        with lock:
            progress.value += progress_per_step

    pdf_document.close()
    return pdf_document



def plotData_outdated(sample, progress, lock, data, datasheet, outputDirectory, dataNumber, informationOfTime,
             timePointIndices, plotColor, minFirstDay, minLastDay, maxFirstDay, maxLastDay, points,
             amplitudePercentage, sgFilter, sgPlotColor, windowSize, polyOrder, period, startingPoint,\
             pointSize, label):

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
    figure = plt.figure()
    plt.plot(timePoints, dataPoints, marker="o", markersize=pointSize, color=plotColor, linestyle="-",
             label="raw data")
    if(sgFilter):
        dataPoints_smoothed = signal.savgol_filter(sampleData_invertMean, windowSize, polyOrder)
        plt.plot(timePoints, dataPoints_smoothed, color=sgPlotColor, linestyle="-", label="smoothed data")
        plt.legend(bbox_to_anchor=(1.05,0.40))

    plt.title(sample + "\n" + datasheet.split("/")[-1])
    plt.xticks(days, timePointLabels)
    plt.xlabel(label)
    plt.ylabel("mV")
    threshold = (maxVoltage - minVoltage) * (amplitudePercentage / 100)
    lastValley = None
    lastPeak = None
    meanMinimumPeriod = 0
    minimumPeriods = 0
    meanMaximunPeriod = 0
    maximumPeriods = 0
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
            if(not ((minFirstDay and day == 0) or (minLastDay and dayEnd == timePoints[-1]))):
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
                    meanMinimumPeriod += meanTime - lastValley
                    minimumPeriods += 1

                top = minVoltage - (maxVoltage - minVoltage) * 0.15
                bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="black", linestyle="-")
                minimumPhaseList.append(str(meanTime%24).replace(".", ",") + ";" + str(meanValley).replace(".", ","))
                lastValley = meanTime
        if(len(peaks) and (period == "Maximum" or period == "Both")):
            if(not ((maxFirstDay and day == 0) or (maxLastDay and dayEnd == timePoints[-1]))):
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
                    meanMaximunPeriod += meanTime - lastPeak
                    maximumPeriods += 1

                top = maxVoltage + (maxVoltage - minVoltage) * 0.15
                bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color="black", linestyle="-")
                maximumPhaseList.append(str(meanTime%24).replace(".", ",") + ";" + str(meanPeak).replace(".", ","))
                lastPeak = meanTime

    props = dict(boxstyle='round', facecolor='white', alpha=0.15)
    if(period == "Minimum"):
        plt.gcf().text(0.955, 0.5, "mean min period: " + "{0:.2f}".format(meanMinimumPeriod / minimumPeriods) + "h",
                       bbox=props)
    elif(period == "Maximum"):
        plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(meanMaximunPeriod / maximumPeriods) + "h",
                      bbox=props)
    else:
        plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(meanMaximunPeriod / maximumPeriods) +
                       "h\n\n" + "mean min period: " + "{0:.2f}".format(meanMinimumPeriod / minimumPeriods) + "h",
                       bbox=props)

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
    leftY = y[:point+1]
    for i in range(len(leftY)-2, -1, -1):
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
