#!/usr/bin/env python3
#Icon made by Smashicons (https://www.flaticon.com/authors/smashicons) from www.flaticon.com

import argparse
import os
import sys
import shutil
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
import multiprocessing as mp
from functools import partial
from PyPDF2 import PdfFileMerger
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
    app.createMenu("PisA")
    app.addMenuList("PisA", pisaMenus, pisaPress)
    app.addMenuSeparator("PisA")
    app.addSubMenu("PisA", "Set period")
    app.addMenuRadioButton("Set period", "Period", "Minimum")
    app.addMenuRadioButton("Set period", "Period", "Maximum")
    app.addMenuRadioButton("Set period", "Period", "Both")
    app.setMenuRadioButton("Set period", "Period", "Minimum")
    app.addMenuSeparator("PisA")
    app.addMenuItem("PisA", "Settings ", pisaPress)
    app.disableMenuItem("PisA", "Start analysis")
    app.disableMenuItem("PisA", "Cancel analysis")
    app.disableMenuItem("PisA", "Compare columns")
    app.disableMenuItem("PisA", "Remove comparing columns")
    app.disableMenuItem("PisA", "Set period")
    app.disableMenuItem("PisA", "Settings ")

    app.createMenu("Settings")
    app.addMenuItem("Settings", "Header", fileSettingsPress)
    with app.subWindow("Header"):
        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.startFrame("HeaderTop", row=0, column=0)
        app.addHorizontalSeparator()
        app.addLabel("Header", "Header")
        app.addNumericEntry("Header")
        app.setEntry("Header", 1)
        app.addHorizontalSeparator()
        app.stopFrame()
        app.startFrame("HeaderBottom", row=1, column=0)
        app.addButtons([" Ok", " Cancel"], fileSettingsPress)
        app.stopFrame()

    app.addSubMenu("Settings", "Plot point size")
    for i in range(1, 21):
        app.addMenuRadioButton("Plot point size", "Sizes", i)

    app.setMenuRadioButton("Plot point size", "Sizes", 3)
    app.addMenuSeparator("Settings")
    app.addMenuItem("Settings", "Reset settings", fileSettingsPress)

    app.createMenu("Exit")
    app.addMenuItem("Exit", "Exit PisA", exitPress)

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



def buildAnalysisSettingsWindow(dataNumberOptions=[], dataMinuteOptions=[]):
    
    with app.subWindow("Analysis settings"):
        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.startFrame("SettingsTop", row=0, column=0)
        app.addHorizontalSeparator()
        app.addLabel("Data starting point", "Data starting point")
        app.addNumericEntry("Data starting point")
        app.setEntry("Data starting point", 8)
        app.addHorizontalSeparator()
        app.addLabel("Data number", "Data number")
        app.addOptionBox("Data number", dataNumberOptions)
        app.setOptionBox("Data number", 5, callFunction=False)
        app.addHorizontalSeparator()
        app.addLabel("Data minute point", "Data minute point")
        app.addOptionBox("Data minute point", dataMinuteOptions)
        app.setOptionBox("Data minute point", "None", callFunction=False)
        app.addHorizontalSeparator()
        app.stopFrame()
        app.startFrame("SettingsBottom", row=1, column=0)
        app.addButtons([" Ok ", " Reset "], analysisSettingsPress)
        app.stopFrame()
        
        

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
                header = int(app.getEntry("Header"))
                app.setLabel("Input", "\nInput: Loading file...\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
                if(datasheet != ""):
                    app.destroySubWindow("Compare columns")
                    app.destroySubWindow("Remove comparing columns")
                    app.destroySubWindow("Analysis settings")
                    app.disableMenuItem("PisA", "Remove comparing columns")

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
                buildAnalysisSettingsWindow(["All"]+list(range(1, dataPerMeasurement)), ["None"]+list(np.unique(dataMinutePoints)))
                with app.subWindow("Compare columns"):
                    app.setBg("silver", override=True)
                    app.setFont(size=12, underline=False, slant="roman")
                    app.startFrame("TOP", row=0, column=0)
                    app.addButtons(["Set", "Reset"], columnsPress)
                    app.stopFrame()
                    app.startFrame("CENTER", row=1, column=0)
                    columnNames = list(data.keys())[2:]
                    row = 1
                    for column in range(len(columnNames)):
                        if(column != 0 and column % 6 == 0):
                            row += 1

                        app.addCheckBox(columnNames[column], row, column % 6)

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

                app.enableMenuItem("PisA", "Start analysis")
                app.enableMenuItem("PisA", "Compare columns")
                app.enableMenuItem("PisA", "Set period")
                app.enableMenuItem("PisA", "Settings ")
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
        except:
            app.errorBox("Error!", traceback.format_exc())
            datasheet = ""
            outputDirectory = ""
            app.disableMenuItem("PisA", "Start analysis")
            app.disableMenuItem("PisA", "Compare columns")
            app.disableMenuItem("PisA", "Set period")
            app.disableMenuItem("PisA", "Settings ")
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
        app.disableMenuItem("PisA", "Start analysis")
        app.enableMenuItem("PisA", "Cancel analysis")
        app.disableMenuItem("PisA", "Compare columns")
        app.disableMenuItem("PisA", "Remove comparing columns")
        app.disableMenuItem("PisA", "Set period")
        app.disableMenuItem("PisA", "Settings ")
        app.disableMenuItem("Settings", "Header")
        app.disableMenuItem("Settings", "Plot point size")
        app.disableMenuItem("Settings", "Reset settings")

        dataNumber = app.getOptionBox("Data number")
        if(dataNumber == "All"):
            dataNumber = 0
        else:
            dataNumber = int(dataNumber)

        minutePoint = app.getOptionBox("Data minute point")
        if(minutePoint != "None"):
            minutePoint = int(minutePoint)

        period = app.getMenuRadioButton("Set period", "Period")
        startingPoint = app.getEntry("Data starting point")
        pointSize = int(app.getMenuRadioButton("Plot point size", "Sizes"))
        
        merger = PdfFileMerger()
        os.makedirs(outputDirectory + "tmp")
        progress.value = 0
        progressSize = len(columnNames) + len(comparePlots)
        pool = mp.Pool(processes=mp.cpu_count())
        poolMap =  partial(plotData, dataNumber=dataNumber, minutePoint=minutePoint, period=period, startingPoint=startingPoint, pointSize=pointSize)
        pages = pool.map_async(poolMap, columnNames)
        pool.close()
        while(progress.value != progressSize):
            if(cancelAnalysis or exitApp):
                pool.terminate()
                break
            
            app.setMeter("Progress", (progress.value/progressSize)*100)
            app.topLevel.update()
        
        pool.join()
        if(not (cancelAnalysis or exitApp)):
            app.setMeter("Progress", (progress.value/progressSize)*100)
            plotResults = pages.get()
            minimumPhaseList = list()
            maximumPhaseList = list()
            minimumPeriodList = list()
            maximumPeriodList = list()
            for sample in columnNames:
                sampleResults = next(list(page.values()) for page in plotResults if sample == list(page.keys())[0])[0]
                samplePage = sampleResults[0]
                minimumPhaseList.append(sample + ";" + "\n".join(sampleResults[1]))
                maximumPhaseList.append(sample + ";" + "\n".join(sampleResults[2]))
                minimumPeriodList.append(sample + ";" + ";".join(sampleResults[3]))
                maximumPeriodList.append(sample  + ";"+ ";".join(sampleResults[4]))
                merger.append(samplePage)
            
            merger.write(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf")
            if(period == "Minimum"):
                with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                    phaseWriter.write("\n".join(minimumPhaseList))
                
                with open(outputDirectory + "periodLog.csv", "w") as phaseWriter:
                    phaseWriter.write("\n".join(minimumPeriodList))
            elif(period == "Maximum"):
                with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                    phaseWriter.write("\n".join(maximumPhaseList))
                
                with open(outputDirectory + "periodLog.csv", "w") as phaseWriter:
                    phaseWriter.write("\n".join(maximumPeriodList))
            else:
                with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                    pass
                
                with open(outputDirectory + "periodLog.csv", "w") as phaseWriter:
                    pass
                
            if(os.name == "nt"):
                os.startfile(outputDirectory)
            else:
                subprocess.call(["xdg-open", outputDirectory])
            
        shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
        app.enableMenuItem("File", "Open")
        app.enableMenuItem("File", "Save")
        app.enableMenuItem("PisA", "Start analysis")
        app.disableMenuItem("PisA", "Cancel analysis")
        app.enableMenuItem("PisA", "Compare columns")
        app.enableMenuItem("PisA", "Set period")
        app.enableMenuItem("PisA", "Settings ")
        app.enableMenuItem("Settings", "Header")
        app.enableMenuItem("Settings", "Plot point size")
        app.enableMenuItem("Settings", "Reset settings")
        if(len(comparePlots)):
            app.enableMenuItem("PisA", "Remove comparing columns")
            
        cancelAnalysis = False
    if(button == "Cancel analysis"):
        cancelAnalysis = True

    if(button == "Compare columns"):
        app.showSubWindow("Compare columns")

    if(button == "Remove comparing columns"):
        app.showSubWindow("Remove comparing columns")
        
    if(button == "Settings "):
        app.showSubWindow("Analysis settings")



def columnsPress(button):

    global comparePlots

    if(button == "Set"):
        checkBoxes = app.getAllCheckBoxes()
        checklist = list()
        for check in checkBoxes:
            if(checkBoxes[check]):
                checklist.append(check)

        if(len(checklist)):
            app.enableMenuItem("PisA", "Remove comparing columns")
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
            app.disableMenuItem("PisA", "Remove comparing columns")

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
        
   
        
def analysisSettingsPress(button):
    
    if(button == " Ok "):
        app.hideSubWindow("Analysis settings")
        
    if(button == " Reset "):
        app.setEntry("Data starting point", 8)
        app.setOptionBox("Data number", 5, callFunction=False)
        app.setOptionBox("Data minute point", "None", callFunction=False)



def fileSettingsPress(button):

    global header
    global startingPoint

    if(button == "Header"):
        app.showSubWindow("Header")

    if(button == " Ok"):
        header = int(app.getEntry("Header"))
        app.hideSubWindow("Header")

    if(button == " Cancel"):
        app.hideSubWindow("Header")
        app.setEntry("Header", header)

    if(button == "Reset settings"):
        header = 1
        app.setEntry("Header", header)
        app.setMenuRadioButton("Plot point size", "Sizes", 3)



def exitPress(button):

    global exitApp

    if(button == "Exit PisA"):
        exitApp = True
        app.stop()



def plotData(sample, dataNumber, minutePoint, period, startingPoint, pointSize):
    
    timePoints = np.unique(data['h'] // 1 + startingPoint).astype(int)
    timePointLabels = np.unique((timePoints // 24).astype(int))
    days = np.arange(0, timePoints[-1], 24)
    minuteIndices = None
    if(minutePoint != "None"):
        minuteIndex = np.where(dataMinutePoints == minutePoint)[0][0]
        minuteIndices = np.arange(minuteIndex, len(data['h']), dataPerMeasurement)
        
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
        
    dataPoints = signal.savgol_filter(sampleData_invertMean, 11, 3)
    
    figure = plt.figure()
    plt.plot(timePoints, dataPoints, marker='o', markersize=pointSize, color='k', linestyle='-')
    plt.title(sample + "\n" + datasheet.split("/")[-1])
    plt.xticks(days, timePointLabels)
    plt.xlabel("Days")
    plt.ylabel("mV")
    threshold = (maxVoltage - minVoltage) * 0.05
    lastValley = None
    lastPeak = None
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
        daySample = dataPoints[timeIndexStart:timeIndexEnd]
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
                plt.annotate(str(meanTime-lastValley) + "h", xy=((meanTime+lastValley)/2, 0.04), xycoords=('data','axes fraction'), size=10, ha='center')
                minimumPeriodList.append(str(meanTime-lastValley))
                
            top = minVoltage - (maxVoltage - minVoltage) * 0.15
            bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
            plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
            minimumPhaseList.append(str(meanTime%24) + ";" + str(meanValley))
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
                plt.annotate(str(meanTime-lastPeak) + "h", xy=((meanTime+lastPeak)/2, 0.93), xycoords=('data','axes fraction'), size=10, ha='center')
                maximumPeriodList.append(str(meanTime-lastPeak))
                
            top = maxVoltage + (maxVoltage - minVoltage) * 0.15
            bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
            plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
            maximumPhaseList.append(str(meanTime%24) + ";" + str(meanPeak))
            lastPeak = meanTime
            
    figure.savefig(outputDirectory + "tmp/" + sample + ".pdf", bbox_inches='tight')
    plt.close()
    with progress.get_lock():
        progress.value += 1
        
    return ({sample: [outputDirectory + "tmp/" + sample + ".pdf", minimumPhaseList, maximumPhaseList, minimumPeriodList, maximumPeriodList]})

    

def plotData_t(dataNumber, minutePoint, period, startingPoint, pointSize):

    global finished

    progress = 0
    progressSize = len(columnNames) + len(comparePlots)
    dataPoints = dict()
    pdfOutput = PdfPages(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf")
    timePoints = np.unique(data['h'] // 1 + startingPoint).astype(int)
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
        threshold = (maxVoltage - minVoltage) * 0.05
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
                    plt.annotate(str(meanTime-lastValley) + "h", xy=((meanTime+lastValley)/2, 0.04), xycoords=('data','axes fraction'), size=10, ha='center')
                    minimumPeriodList.append(str(meanTime-lastValley))
                    #plt.annotate("{:.1f}".format(meanTime-lastValley) + "h", xy=((meanTime+lastValley)/2, 0.04), xycoords=('data','axes fraction'), size=10, ha='center')
                    #minimumPeriodList.append("{:.1f}".format(meanTime-lastValley))

                top = minVoltage - (maxVoltage - minVoltage) * 0.15
                bottom = minVoltage - (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
                minimumPhaseList.append(str(meanTime%24) + ";" + str(meanValley))
                #minimumPhaseList.append("{:.1f}".format(meanTime%24) + ";" + str(meanValley))
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
                    plt.annotate(str(meanTime-lastPeak) + "h", xy=((meanTime+lastPeak)/2, 0.93), xycoords=('data','axes fraction'), size=10, ha='center')
                    maximumPeriodList.append(str(meanTime-lastPeak))
                    #plt.annotate("{:.1f}".format(meanTime-lastPeak) + "h", xy=((meanTime+lastPeak)/2, 0.93), xycoords=('data','axes fraction'), size=10, ha='center')
                    #maximumPeriodList.append("{:.1f}".format(meanTime-lastPeak))

                top = maxVoltage + (maxVoltage - minVoltage) * 0.15
                bottom = maxVoltage + (maxVoltage - minVoltage) * 0.05
                plt.plot([meanTime, meanTime], [top, bottom], color='k', linestyle='-')
                maximumPhaseList.append(str(meanTime%24) + ";" + str(meanValley))
                #maximumPhaseList.append("{:.1f}".format(meanTime%24) + ";" + str(meanValley))
                lastPeak = meanTime

        if(period == "Minimum"):
            phaseList.append(sample + ";" + "\n;".join(minimumPhaseList))
            periodList.append(sample + ";" + ";".join(minimumPeriodList))
        elif(period == "Maximum"):
            phaseList.append(sample + ";" + "\n;".join(maximumPhaseList))
            periodList.append(sample + ";" + ";".join(maximumPeriodList))
        else:
            periodList.append(sample + ";" + ";".join(minimumPeriodList) + ";"*(maxPeriodNumber-len(minimumPeriodList)+2) + sample + ";" + ";".join(maximumPeriodList))
            samplePhaseList = itertools.zip_longest(minimumPhaseList, maximumPhaseList, fillvalue='--;--')
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



def findPeaksAndValleys(y, points=1):
    
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
    
    meanX = int(np.mean(np.take(x, indexList)))
    meanY = np.mean(np.array(pointsList))
    return (meanX, meanY)



if __name__ == '__main__':
    try:
        progress = mp.Value('i', 0) 
        app.winIcon = None
        buildAppJarGUI()
        app.go()
        while(not exitApp):
            mainloop() #tkinter
    except:
        app.errorBox("Critical error!", traceback.format_exc())
        with open(outputDirectory + "errorLog.txt", "w") as logWriter:
            logWriter.write(traceback.format_exc())
