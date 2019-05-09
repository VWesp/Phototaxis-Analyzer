#!/usr/bin/env python3
#Icon made by Smashicons (https://www.flaticon.com/authors/smashicons) from www.flaticon.com

import argparse
import os
import sys
import subprocess
import pandas as pd
import numpy as np
import scipy.signal as signal
from scipy import interpolate
import traceback
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
import itertools
from appJar import gui
from tkinter import *


data = None
datasheet = ""
outputDirectory = ""
columnNames = list()
dataPerMeasurement = None
timePointIndices = None
dataMinutePoints = None
comparePlots = list()
header = 1
startingPoint = 8
finished = None
cancelAnalysis = None
exitApp = False
lbc = None
lbr = None


app = gui("PisA", "380x360")


def buildAppJarGUI():

    app.setBg("silver", override=True)
    app.setFont(size=12, underline=False, slant="roman")

    app.addLabel("Title", "PisA: [P]hototax[is]-[A]nalyzer")
    app.setLabelBg("Title", "orangered")

    inputMenus = ["Open", "Save"]
    app.createMenu("File")
    app.addMenuList("File", inputMenus, openPress)

    pisaMenus = ["Start analysis", "Cancel analysis", "-", "Compare columns", "Remove comparing columns"]
    app.createMenu("PISA")
    app.addMenuList("PISA", pisaMenus, pisaPress)
    app.addMenuSeparator("PISA")
    app.addSubMenu("PISA", "Set period")
    app.addMenuRadioButton("Set period", "Period", "Minimum")
    app.addMenuRadioButton("Set period", "Period", "Maximum")
    app.addMenuRadioButton("Set period", "Period", "Both")
    app.setMenuRadioButton("Set period", "Period", "Minimum")
    app.disableMenuItem("PISA", "Start analysis")
    app.disableMenuItem("PISA", "Cancel analysis")
    app.disableMenuItem("PISA", "Compare columns")
    app.disableMenuItem("PISA", "Remove comparing columns")

    app.createMenu("Settings")
    app.addMenuItem("Settings", "Header", settingsPress)
    with app.subWindow("Header"):
        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.startFrame("HeaderTop", row=0, column=0)
        app.addLabelEntry("Header")
        app.setEntry("Header", 1)
        app.stopFrame()
        app.startFrame("HeaderBottom", row=1, column=0)
        app.addButtons([" Ok", " Cancel"], settingsPress)
        app.stopFrame()

    app.addSubMenu("Settings", "Plot point size")
    for i in range(1, 21):
        app.addMenuRadioButton("Plot point size", "Sizes", i)

    app.setMenuRadioButton("Plot point size", "Sizes", 3)
    app.addMenuSeparator("Settings")
    app.addSubMenu("Settings", "Data number")
    app.addMenuItem("Settings", "Data starting point", settingsPress)
    with app.subWindow("Start"):
        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.startFrame("StartTop", row=0, column=0)
        app.addLabelEntry("Data starting point")
        app.setEntry("Data starting point", 8)
        app.stopFrame()
        app.startFrame("StartBottom", row=1, column=0)
        app.addButtons(["Ok ", "Cancel "], settingsPress)
        app.stopFrame()

    app.addSubMenu("Settings", "Data minute point")
    app.addMenuSeparator("Settings")
    app.addMenuItem("Settings", "Reset settings", settingsPress)
    app.disableMenuItem("Settings", "Data number")
    app.disableMenuItem("Settings", "Data minute point")

    app.createMenu("Exit")
    app.addMenuItem("Exit", "Exit PISA", exitPress)

    app.addMeter("Progress")
    app.setMeterFill("Progress", "forestgreen")

    app.addHorizontalSeparator()
    app.startScrollPane("Pane")
    app.addLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
    app.stopScrollPane()
    app.addHorizontalSeparator()

    app.setFastStop(True)
    app.setLocation("CENTER")
    app.setResizable(canResize=False)
    app.winIcon = None


def openPress(button):

    global data
    global datasheet
    global columnNames
    global outputDirectory
    global dataPerMeasurement
    global timePointIndices
    global dataMinutePoints
    global lbc
    global lbr

    if(button == "Open"):
        try:
            inputFile = app.openBox(title="Input datasheet file", fileTypes=[("datasheet files", "*.txt"), ("all files", "*.*")])
            if(inputFile != None and len(inputFile)):
                try:
                    header = int(app.getEntry("Header"))
                except ValueError as ve:
                    app.warningBox("Warning!", "The header must be an integer number!")
                    return

                app.setLabel("Input", "\nInput: Loading file...\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
                if(datasheet != ""):
                    app.destroySubWindow("Compare columns")
                    app.destroySubWindow("Remove comparing columns")
                    if(len(comparePlots)):
                        app.disableMenuItem("PISA", "Remove comparing columns")
                    
                    for dataPoint in range(0, dataPerMeasurement):
                        app.widgetManager.get(app.Widgets.Menu, "Data number").delete(0)

                    app.widgetManager.get(app.Widgets.Menu, "Data minute point").delete("None")
                    for minutePoint in range(len(np.unique(dataMinutePoints))):
                        app.widgetManager.get(app.Widgets.Menu, "Data minute point").delete(0)

                datasheet = inputFile
                del columnNames[:]
                del comparePlots[:]
                data = pd.read_csv(datasheet, sep="\t", header=header, encoding="iso-8859-1")
                dataInt = dict()
                dataMinutePoints = None
                for key in data:
                    data[key] = data[key].str.replace(",", ".")
                    data[key] = data[key].astype(float)
                    dataInt[key] = data[key].astype(int)
                    if(key == 'h'):
                        dataPerMeasurement = np.argmax(dataInt[key] > 0)
                        timePointIndices = np.arange(dataPerMeasurement, len(data[key]), dataPerMeasurement)
                        dataMinutePoints = (60 * (data[key] % 1)).astype(int)

                dataInt.clear()
                app.addMenuRadioButton("Data number", "Numbers", "All")
                for dataPoint in range(1, dataPerMeasurement):
                    app.addMenuRadioButton("Data number", "Numbers", dataPoint)

                app.setMenuRadioButton("Data number", "Numbers", 5)
                app.addMenuRadioButton("Data minute point", "Minutes", "None")
                for minutePoint in np.unique(dataMinutePoints):
                    app.addMenuRadioButton("Data minute point", "Minutes", minutePoint)

                app.setMenuRadioButton("Data minute point", "Minutes", "None")
                with app.subWindow("Compare columns"):
                    app.setBg("silver", override=True)
                    app.setFont(size=12, underline=False, slant="roman")
                    app.startFrame("TOP", row=0, column=0)
                    app.addButtons(["Set", "Reset"], columnsPress)
                    app.stopFrame()
                    app.startFrame("CENTER", row=1, column=0)
                    columnNames = list(data.keys())[2:]
                    column = 1
                    for row in range(len(columnNames)):
                        if(row != 0 and row % 6 == 0):
                            column += 1

                        app.addCheckBox(columnNames[row], column, row % 6)

                    app.stopFrame()
                    app.startFrame("BOTTOM", row=2, column=0)
                    app.addButton("Close", columnsPress)
                    app.stopFrame()

                with app.subWindow("Remove comparing columns"):
                    app.setBg("silver", override=True)
                    app.setFont(size=12, underline=False, slant="roman")
                    app.startFrame(" TOP ", row=0, column=0)
                    app.addButtons(["Remove", "Cancel"], columnsPress)
                    app.stopFrame()
                    app.startFrame(" BOTTOM ", row=1, column=0)
                    app.addLabel("Removable plots", "Comparing plots")
                    lbc = app.addListBox("Removable plots")
                    lbc.bind("<Double-1>", lambda *args: doubleClickAdd())
                    app.addHorizontalSeparator()
                    app.addLabel("Removing plots", "Removing plots")
                    lbr = app.addListBox("Removing plots")
                    lbr.bind("<Double-1>", lambda *args: doubleClickRemove())
                    app.stopFrame()

                if(os.name == "nt"):
                    outputDirectory = "/".join(os.path.abspath(datasheet).split("\\")[:-1]) + "/"
                else:
                    outputDirectory = "/".join(os.path.abspath(datasheet).split("/")[:-1]) + "/"

                app.enableMenuItem("PISA", "Start analysis")
                app.enableMenuItem("PISA", "Compare columns")
                app.enableMenuItem("Settings", "Data number")
                app.enableMenuItem("Settings", "Data minute point")
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
        except:
            datasheet = ""
            outputDirectory = ""
            app.disableMenuItem("PISA", "Start analysis")
            app.disableMenuItem("PISA", "Compare columns")
            app.disableMenuItem("Settings", "Data number")
            app.disableMenuItem("Settings", "Data minute point")
            app.setLabel("Input", "\nInput: Error loading! Check input file!\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")

    if(button == "Save"):
        output = app.directoryBox(title="Output directory")
        if(output != None and len(output)):
            outputDirectory = output + "/"
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")



def pisaPress(button):

    global comparePlots
    global finished
    global cancelAnalysis

    if(button == "Start analysis"):
        app.disableMenuItem("File", "Open")
        app.disableMenuItem("File", "Save")
        app.disableMenuItem("PISA", "Start analysis")
        app.enableMenuItem("PISA", "Cancel analysis")
        app.disableMenuItem("PISA", "Compare columns")
        app.disableMenuItem("PISA", "Remove comparing columns")
        app.disableMenuItem("PISA", "Set period")
        app.disableMenuItem("Settings", "Header")
        app.disableMenuItem("Settings", "Plot point size")
        app.disableMenuItem("Settings", "Data number")
        app.disableMenuItem("Settings", "Data starting point")
        app.disableMenuItem("Settings", "Data minute point")
        app.disableMenuItem("Settings", "Reset settings")

        dataNumber = app.getMenuRadioButton("Data number", "Numbers")
        if(dataNumber == "All"):
            dataNumber = 0
        else:
            dataNumber = int(dataNumber)

        minutePoint = app.getMenuRadioButton("Data minute point", "Minutes")
        if(minutePoint != "None"):
            minutePoint = int(minutePoint)

        period = app.getMenuRadioButton("Set period", "Period")
        startingPoint = float(app.getEntry("Data starting point"))
        pointSize = int(app.getMenuRadioButton("Plot point size", "Sizes"))

        finished = False
        cancelAnalysis = False
        app.thread(plotData, dataNumber, minutePoint, period, startingPoint, pointSize)
        while(not exitApp and not cancelAnalysis):
            if(finished):
                with open(outputDirectory + "plotLog.txt", "w") as logWriter:
                    space = len("[Data starting point]")
                    log = "[Datasheet file]" + " "*(space-len("[Datasheet file]")) + "\t" + datasheet + "\n"
                    log += "[Output directory]" + " "*(space-len("[Output directory]")) + "\t" + outputDirectory + "\n"
                    log += "[Period]" + " "*(space-len("[Period]")) + "\t" + period + "\n"
                    log += "[Header]" + " "*(space-len("[Header]")) + "\t" + str(header) + "\n"
                    log += "[Data number]" + " "*(space-len("[Data number]")) + "\t" + app.getMenuRadioButton("Data number", "Numbers") + "\n"
                    log += "[Data starting point]" + " "*(space-len("[Data starting point]")) + "\t" + str(startingPoint) + "\n"
                    log += "[Data minute point]" + " "*(space-len("[Data minute point]")) + "\t" + str(minutePoint) + "\n"
                    log += "[Plot point size]" + " "*(space-len("[Plot point size]")) + "\t" + str(pointSize) + "\n"
                    if(len(comparePlots)):
                        log += "[Compared plots]" + " "*(space-len("[Compared plots]")) + "\n" + "\n".join(comparePlots)

                    logWriter.write(log)

                if(os.name == "nt"):
                    os.startfile(outputDirectory)
                else:
                    subprocess.call(["xdg-open", outputDirectory])

                break

            app.topLevel.update()

        app.enableMenuItem("File", "Open")
        app.enableMenuItem("File", "Save")
        app.enableMenuItem("PISA", "Start analysis")
        app.disableMenuItem("PISA", "Cancel analysis")
        app.enableMenuItem("PISA", "Compare columns")
        app.enableMenuItem("PISA", "Set period")
        app.enableMenuItem("Settings", "Header")
        app.enableMenuItem("Settings", "Plot point size")
        app.enableMenuItem("Settings", "Data number")
        app.enableMenuItem("Settings", "Data starting point")
        app.enableMenuItem("Settings", "Data minute point")
        app.enableMenuItem("Settings", "Reset settings")
        if(len(comparePlots)):
            app.enableMenuItem("PISA", "Remove comparing columns")

    if(button == "Cancel analysis"):
        cancelAnalysis = True

    if(button == "Compare columns"):
        app.showSubWindow("Compare columns")

    if(button == "Remove comparing columns"):
        app.showSubWindow("Remove comparing columns")



def columnsPress(button):

    global comparePlots

    if(button == "Set"):
        checkBoxes = app.getAllCheckBoxes()
        checklist = list()
        for check in checkBoxes:
            if(checkBoxes[check]):
                checklist.append(check)

        if(len(checklist)):
            app.enableMenuItem("PISA", "Remove comparing columns")
            checkPlots = " - ".join(checklist)
            if(not checkPlots in comparePlots):
                comparePlots.append(checkPlots)
                app.addListItem("Removable plots", checkPlots)
                app.clearAllCheckBoxes()
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> " + "\n -> ".join(comparePlots))

        del checklist[:]

    if(button == "Reset"):
        app.clearAllCheckBoxes()

    if(button == "Close"):
        app.hideSubWindow("Compare columns")

    if(button == "Remove"):
        removePlots = app.getAllListItems("Removing plots")
        for plot in removePlots:
            comparePlots.remove(plot)
            app.removeListItem("Removing plots", plot)

        if(len(comparePlots)):
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> " + "\n -> ".join(comparePlots))
        else:
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
            app.disableMenuItem("PISA", "Remove comparing columns")

        app.hideSubWindow("Remove comparing columns")

    if(button == "Cancel"):
        removePlots = app.getAllListItems("Removing plots")
        for plot in removePlots:
            app.addListItem("Removable plots", plot)
            app.removeListItem("Removing plots", plot)

        app.hideSubWindow("Remove comparing columns")



def doubleClickAdd():

    lbcPlot = lbc.get(ACTIVE)
    if(len(lbcPlot)):
        app.addListItem("Removing plots", lbcPlot)
        app.removeListItem("Removable plots", lbcPlot)



def doubleClickRemove():

    lbrPlot = lbr.get(ACTIVE)
    if(len(lbrPlot)):
        app.addListItem("Removable plots", lbrPlot)
        app.removeListItem("Removing plots", lbrPlot)



def settingsPress(button):

    global header
    global startingPoint

    if(button == "Header"):
        app.showSubWindow("Header")

    if(button == " Ok"):
        app.hideSubWindow("Header")
        try:
            header = int(app.getEntry("Header"))
        except ValueError as ve:
            app.warningBox("Warning!", "The header must be an integer number!")
            app.setEntry("Header", header)

    if(button == " Cancel"):
        app.hideSubWindow("Header")
        app.setEntry("Header", header)

    if(button == "Data starting point"):
        app.showSubWindow("Start")

    if(button == "Ok "):
        app.hideSubWindow("Start")
        try:
            startingPoint = float(app.getEntry("Data starting point"))
        except ValueError as ve:
            app.warningBox("Warning!", "The data starting point must be an integer or floating point number!")
            app.setEntry("Data starting point", startingPoint)

    if(button == "Cancel "):
        app.hideSubWindow("Start")
        app.setEntry("Data starting point", startingPoint)

    if(button == "Reset settings"):
        app.setEntry("Header", 1)
        app.setMenuRadioButton("Plot point size", "Sizes", 3)
        app.setEntry("Data starting point", 8)
        if(datasheet != ""):
            app.setMenuRadioButton("Data number", "Numbers", 5)
            app.setMenuRadioButton("Data minute point", "Minutes", "None")



def exitPress(button):

    global exitApp

    if(button == "Exit PISA"):
        exitApp = True
        app.stop()



def plotData(dataNumber, minutePoint, period, startingPoint, pointSize):

    global finished

    progress = 0
    progressSize = len(columnNames) + len(comparePlots)
    dataPoints = dict()
    pdfOutput = PdfPages(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf")
    timePoints = np.unique(data['h'] // 1 + startingPoint).astype(float)
    timePointLabels = np.unique((timePoints // 24).astype(int))
    days = np.arange(0, timePoints[-1], 24)
    maxPeriodNumber = timePointLabels[-1]
    phaseList = list()
    periodList = list()
    minuteIndices = None
    if(minutePoint != "None"):
        minuteIndex = np.where(dataMinutePoints == minutePoint)[0][0]
        minuteIndices = np.arange(minuteIndex, len(data['h']), dataPerMeasurement)

    for sample in columnNames:
        if(exitApp or cancelAnalysis):
            return
            
        dataPoints[sample] = dict()
        maxVoltage = np.amax(data[sample])
        minVoltage = np.amin(data[sample])
        sampleData_invertMean = None
        if(minutePoint != "None"):
            sampleData_mean = np.take(np.array(data[sample]), minuteIndices)
            sampleData_invertMean = (maxVoltage + minVoltage) - sampleData_mean
        else:
            sampleData_invert = np.array(np.split((maxVoltage+minVoltage)-data[sample], timePointIndices))
            sampleData_invertMean = np.mean(sampleData_invert[:,-dataNumber:], axis=1)
            
        dataPoints[sample] = signal.savgol_filter(sampleData_invertMean, 11, 3)
        
        plt.plot(timePoints, dataPoints[sample], marker='o', markersize=pointSize, color='k', linestyle='-')
        plt.title(sample + "\n" + datasheet.split("/")[-1])
        plt.xticks(days, timePointLabels)
        plt.xlabel("Days")
        plt.ylabel("mV")
        threshold = (maxVoltage - minVoltage) * 0.1
        lastValley = None
        lastPeak = None
        minimumPhaseList = list()
        maximumPhaseList = list()
        minimumPeriodList = list()
        maximumPeriodList = list()
        for day in days:
            dayStart = day - 2
            dayEnd = day + 26
            if(day == 0):
                dayStart =int(startingPoint)
            else:
                if(period == "Minimum"):
                    plt.axvline(day, ymin=0.1, color='k', linestyle=':')
                elif(period == "Maximum"):
                    plt.axvline(day, ymax=0.9, color='k', linestyle=':')
                elif(period == "Both"):
                    plt.axvline(day, ymin=0.1, ymax=0.9, color='k', linestyle=':')

            if(not dayEnd in timePoints):
                dayEnd = timePoints[-1]

            timeIndexStart = np.where(timePoints == dayStart)[0][0]
            timeIndexEnd = np.where(timePoints == dayEnd)[0][0]
            daySample = dataPoints[sample][timeIndexStart:timeIndexEnd]
            dayTimePoints = timePoints[timeIndexStart:timeIndexEnd]
            valleys, peaks = findPeaksAndValleys(daySample)
            if(len(valleys) and (period == "Minimum" or period == "Both")):
                valley = None
                smallestValley = sys.float_info.max
                for i in valleys:
                    if(daySample[i] <= smallestValley):
                        smallestValley = daySample[i]
                        valley = i
                
                meanTime, meanValley = calculatePeakAndValleyMean(dayTimePoints, daySample, valley, threshold, "min")
                if(lastValley != None):
                    bottomLine = minVoltage - (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastValley], [bottomLine, bottomLine], color='k', linestyle='-')
                    plt.annotate("{:.1f}".format(meanTime-lastValley) + "h", xy=((meanTime+lastValley)/2, 0.04), xycoords=('data','axes fraction'), size=10, ha='center')
                    minimumPeriodList.append("{:.1f}".format(meanTime-lastValley))

                top = minVoltage - (maxVoltage - minVoltage) * 0.15
                bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
                minimumPhaseList.append("{:.1f}".format(meanTime%24) + ";" + str(meanValley))
                lastValley = meanTime
            if(len(peaks) and (period == "Maximum" or period == "Both")):
                peak = None
                highestPeak = 0
                for i in peaks:
                    if(daySample[i] > highestPeak):
                        highestPeak = daySample[i]
                        peak = i
                
                meanTime, meanPeak = calculatePeakAndValleyMean(dayTimePoints, daySample, peak, threshold, "max")
                if(lastPeak != None):
                    topLine = maxVoltage + (maxVoltage - minVoltage) * 0.1
                    plt.plot([meanTime, lastPeak], [topLine, topLine], color='k', linestyle='-')
                    plt.annotate("{:.1f}".format(meanTime-lastPeak) + "h", xy=((meanTime+lastPeak)/2, 0.93), xycoords=('data','axes fraction'), size=10, ha='center')
                    maximumPeriodList.append("{:.1f}".format(meanTime-lastPeak))

                top = maxVoltage + (maxVoltage - minVoltage) * 0.15
                bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
                maximumPhaseList.append("{:.1f}".format(meanTime%24) + ";" + str(meanValley))
                lastPeak = meanTime

        if(period == "Minimum"):
            phaseList.append(sample + ";" + "\n;".join(minimumPhaseList))
            periodList.append(sample + ";" + ";".join(minimumPeriodList))
        elif(period == "Maximum"):
            phaseList.append(sample + ";" + "\n;".join(maximumPhaseList))
            periodList.append(sample + ";" + ";".join(maximumPeriodList))
        else:
            periodList.append(sample + ";" + ";".join(minimumPeriodList) + ";"*(maxPeriodNumber-len(minimumPeriodList)+2) + sample + ";" + ";".join(maximumPeriodList))
            samplePhaseList = itertools.zip_longest(minimumPhaseList, maximumPhaseList, fillvalue='--')
            for samplePhase in samplePhaseList:
                phaseList.append(sample + ";" + (";;" + sample + ";").join(samplePhase))
                sample = ""

        del minimumPhaseList[:]
        del maximumPhaseList[:]
        del minimumPeriodList[:]
        del maximumPeriodList[:]
        pdfOutput.savefig(bbox_inches='tight')
        plt.close()
        
        progress += 1
        app.queueFunction(app.setMeter, "Progress", (progress/progressSize)*100)

    pdfOutput.close()
    with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
        if(period == "Minimum"):
            phaseWriter.write("Minima\nSample;Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))
        elif(period == "Maximum"):
            phaseWriter.write("Maxima\nSample;Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))
        else:
            phaseWriter.write("Minima;;;;Maxima\nSample;Phase [h];milliVolt [mV];;Sample;Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))

        del phaseList[:]

    with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
        if(period == "Minimum"):
            periodWriter.write("Minima\nSample;Period [h]\n" + "\n".join(periodList))
        elif(period == "Maximum"):
            periodWriter.write("Maxima\nSample;Period [h]\n" + "\n".join(periodList))
        else:
            periodWriter.write("Minima" + ";"*(maxPeriodNumber+2) + "Maxima\nSample;Period [h]" + ";"*(maxPeriodNumber+1) + "Sample;Period [h]\n" + "\n".join(periodList))

        del periodList[:]

    if(len(comparePlots)):
        pdfOutput = PdfPages(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_comparePlots.pdf")
        colorList = ('k', 'b', 'g', 'r', 'c', 'm', 'y')
        for plotList in comparePlots:
            if(exitApp or cancelAnalysis):
                return

            plots = plotList.split(" - ")
            patches = list()
            colorIndex = 0
            firstPlot = True
            for plot in plots:
                legendPatch, = plt.plot(timePoints, dataPoints[plot], label=plot, marker='o', markersize=pointSize, color=colorList[colorIndex], linestyle='-')
                patches.append(legendPatch)
                if(firstPlot):
                    plt.title(plotList + "\n" + datasheet.split("/")[-1])
                    plt.xticks(days, timePointLabels)
                    plt.xlabel("Days")
                    plt.ylabel("mV")
                    for day in days:
                        if(day in timePoints):
                            timeIndex = np.where(timePoints == day)[0][0]
                            plt.axvline(day, color='k', linestyle=':')

                    firstPlot = False

                if(colorIndex == len(colorList)-1):
                    colorIndex = 0
                else:
                    colorIndex += 1

            plt.legend(handles=patches, bbox_to_anchor=(1.05,0.5))
            pdfOutput.savefig(bbox_inches='tight')
            plt.close()
            del patches[:]

            progress += 1
            app.queueFunction(app.setMeter, "Progress", (progress/progressSize)*100)

        pdfOutput.close()
        dataPoints.clear()

    finished = True



def findPeaksAndValleys(array, points=1):
    
    valleys = list()
    peaks = list()
    if(len(array) > points*2):
        for i in range(points, len(array)-points, 1):
            valleyFound = True
            for j in range(1, points+1, 1):
                if(array[i] > array[i-j] or array[i] > array[i+j]):
                    valleyFound = False
                    break
            
            if(valleyFound):
                valleys.append(i)
                
            peakFound = True
            for j in range(1, points+1, 1):
                if(array[i] < array[i-j] or array[i] < array[i+j]):
                    peakFound = False
                    break
                
            if(peakFound):
                peaks.append(i)

    return (valleys, peaks)



def calculatePeakAndValleyMean(x, y, point, threshold, mode):

    pointsList = list()
    indexList = list()
    leftY = y[:point]
    for i in range(len(leftY)-1, -1, -1):
        if(mode == "min"):
            if(leftY[i] > y[point]+threshold):
                break
            elif(y[point] <= leftY[i] <= y[point]+threshold):
                pointsList.append(leftY[i])
                indexList.append(i)
        elif(mode == "max"):
            if(leftY[i] < y[point]-threshold):
                break
            elif(y[point] >= leftY[i] >= y[point]-threshold):
                pointsList.append(leftY[i])
                indexList.append(i)
    
    indexList = list(reversed(indexList))
    pointsList.append(y[point])
    indexList.append(point)
    rightY = y[point:]
    for i in range(1, len(rightY), 1):
        if(mode == "min"):
            if(rightY[i] > y[point]+threshold):
                break
            elif(y[point] <= rightY[i] <= y[point]+threshold):
                pointsList.append(rightY[i])
                indexList.append(point+i)
        elif(mode == "max"):
            if(rightY[i] < y[point]-threshold):
                break
            elif(y[point] >= rightY[i] >= y[point]-threshold):
                pointsList.append(rightY[i])
                indexList.append(point+i)
    
    meanX = np.mean(np.take(x, indexList))
    meanY = np.mean(np.array(pointsList))
    return (meanX, meanY)



if __name__ == '__main__':
    try:
        app.winIcon = None
        buildAppJarGUI()
        app.go()
        while(not exitApp):
            mainloop() #tkinter
    except:
        app.errorBox("Critical error!", traceback.format_exc())
        with open(outputDirectory + "errorLog.txt", "w") as logWriter:
            logWriter.write(traceback.format_exc())
