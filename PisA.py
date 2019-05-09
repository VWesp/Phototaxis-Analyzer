#!/usr/bin/env python3
#Icon made by Smashicons (https://www.flaticon.com/authors/smashicons) from www.flaticon.com 

import argparse
import math
import os
import subprocess
import pandas as pd
import numpy as np
import scipy.signal as scsi
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
import itertools
from appJar import gui
#import time


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
windowBuild = False
cancelAnalysis = False
exitApp = False


app = gui("PISA", "380x330")


def buildAppJarGUI():

    app.addLabel("title", "Phototaxis-Analyzer")
    app.setLabelBg("title", "red")
    
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
    
    app.startScrollPane("Pane")
    app.addLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
    app.stopScrollPane()
    
    app.addStatusbar()
    #app.setStatusbar(u"\u2588"*38)
    app.setStatusbarFg("green")
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
                
                datasheet = inputFile
                del columnNames[:]
                del comparePlots[:]
                data = pd.read_csv(datasheet, sep="\t", header=header, encoding="iso-8859-1")
                data_int = dict()
                dataMinutePoints = None
                for key in data:
                    data[key] = data[key].str.replace(",", ".")
                    data[key] = data[key].astype(float)
                    data_int[key] = data[key].astype(int)
                    if(key == 'h'):
                        dataPerMeasurement = np.argmax(data_int[key] > 0)
                        timePointIndices = np.arange(dataPerMeasurement, len(data[key]), dataPerMeasurement)
                        dataMinutePoints = (60 * (data[key] % 1)).astype(int)
                
                data_int.clear()
                app.addMenuRadioButton("Data number", "Numbers", "All")
                for dataPoint in range(1, dataPerMeasurement):
                    app.addMenuRadioButton("Data number", "Numbers", dataPoint)
                    
                app.setMenuRadioButton("Data number", "Numbers", 5)
                app.addMenuRadioButton("Data minute point", "Minutes", "None")
                for minutePoint in np.unique(dataMinutePoints):
                    app.addMenuRadioButton("Data minute point", "Minutes", minutePoint)
                
                app.setMenuRadioButton("Data minute point", "Minutes", "None")
                with app.subWindow("Compare columns"):
                    app.startFrame("TOP", row=0, column=0)
                    app.addButtons(["Set", "Reset"], columnsPress)
                    app.stopFrame()
                    app.startFrame("CENTER", row=1, column=0)
                    columnNames = list(data.keys())[2:-1]
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
                    app.startFrame(" TOP ", row=0, column=0)
                    app.addButtons(["Remove", "Cancel"], columnsPress)
                    app.stopFrame()
                    app.startFrame(" BOTTOM ", row=1, column=0)
                    app.addProperties("Comparing columns", dict())
                    app.stopFrame()
                
                outputDirectory = "/".join(os.path.abspath(datasheet).split("/")[:-1]) + "/"
                app.enableMenuItem("PISA", "Start analysis")
                app.enableMenuItem("PISA", "Compare columns")
                app.enableMenuItem("Settings", "Data number")
                app.enableMenuItem("Settings", "Data minute point")
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
        except Exception as ex:
            print(ex)
            datasheet = ""
            outputDirectory = ""
            app.disableMenuItem("PISA", "Start analysis")
            app.disableMenuItem("PISA", "Compare columns")
            app.disableMenuItem("Settings", "Data number")
            app.disableMenuItem("Settings", "Data minute point")
            app.setLabel("Input", "\nInput: Error! Check input file!\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
    
    if(button == "Save"):
        output = app.directoryBox(title="Output directory")
        if(output != None and len(output)):
            outputDirectory = output + "/"
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")



def pisaPress(button):
    
    global comparePlots
    global cancelAnalysis

    if(button == "Start analysis"):
        #startTime = time.time()
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
        
        plotData(dataNumber, minutePoint, period, startingPoint, pointSize)
        if(len(comparePlots) and not cancelAnalysis):
            app.enableMenuItem("PISA", "Remove comparing columns")
        
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
        if(not exitApp and not cancelAnalysis):
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
        
        cancelAnalysis = False
        #print("--- %s seconds ---" % (time.time() - startTime))
        
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
        checked = False
        for check in checkBoxes:
            if(checkBoxes[check]):
                checklist.append(check)
                checked = True

        if(checked):
            app.enableMenuItem("PISA", "Remove comparing columns")
            comparePlots.append(" - ".join(checklist))
            app.setProperty("Comparing columns", " - ".join(checklist))
            app.clearAllCheckBoxes()
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> " + "\n -> ".join(comparePlots))
            
        del checklist[:]
    
    if(button == "Reset"):
        app.clearAllCheckBoxes()
        
    if(button == "Close"):
        app.hideSubWindow("Compare columns")
        
    if(button == "Remove"):
        properties = app.getProperties("Comparing columns")
        comparePlots[:] = [plots for plots in comparePlots if not properties[plots]]
        for plotProperty in properties:
            if(properties[plotProperty]):
                app.deleteProperty("Comparing columns", plotProperty)
        
        if(len(comparePlots) == 0):
            app.disableMenuItem("PISA", "Remove comparing columns")
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
        else:
            app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> " + "\n -> ".join(comparePlots))
        
        app.hideSubWindow("Remove comparing columns")
        
    if(button == "Cancel"):
        app.clearProperties("Comparing columns", callFunction=False)
        app.hideSubWindow("Remove comparing columns")
        
        
        
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
    
    
    progress = 0
    progressSize = len(columnNames) + len(comparePlots)
    dataPoints = dict()
    pdfOutput = PdfPages(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf")
    timePoints = np.unique(data['h'] // 1 + startingPoint).astype(int)
    timePointLabels = np.unique((timePoints // 24).astype(int))
    days = np.arange(0, timePoints[-1], 24)
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
        max_voltage = np.amax(data[sample])
        min_voltage = np.amin(data[sample])
        sampleData_invertMean = None
        if(minutePoint != "None"):
            sampleData_mean = np.take(np.array(data[sample]), minuteIndices)
            sampleData_invertMean = (max_voltage + min_voltage) - sampleData_mean
        else:
            sampleData_invert = np.array(np.split((max_voltage+min_voltage)-data[sample], timePointIndices))
            sampleData_invertMean = np.mean(sampleData_invert[:,-dataNumber:], axis=1)
            
        dataPoints[sample] = scsi.savgol_filter(sampleData_invertMean, 11, 3)
        
        plt.plot(timePoints, dataPoints[sample], marker='o', markersize=pointSize, color='k', linestyle='-')
        plt.title(sample + "\n" + datasheet.split("/")[-1])
        plt.xticks(days, timePointLabels)
        plt.xlabel("Days")
        plt.ylabel("mV")
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
            valleys = scsi.argrelextrema(daySample, np.less)[0]
            peaks = scsi.argrelextrema(daySample, np.greater)[0]
            if(len(valleys) and (period == "Minimum" or period == "Both")):
                valley = valleys[-1]
                timePoint = timePoints[timeIndexStart:timeIndexEnd][valley]
                if(lastValley != None):
                    bottomLine = min_voltage-(max_voltage-min_voltage)*0.1
                    plt.plot([timePoint, lastValley], [bottomLine, bottomLine], color='k', linestyle='-')
                    plt.annotate(str(timePoint-lastValley) + "h", xy=((timePoint+lastValley)/2, 0.04), xycoords=('data','axes fraction'), size=10, ha='center')
                    minimumPeriodList.append(str(timePoint-lastValley) + "h")
                
                top = min_voltage - (max_voltage - min_voltage) * 0.15
                bottom = min_voltage - (max_voltage - min_voltage) * 0.05
                plt.plot([timePoint, timePoint], [top, bottom], color='k', linestyle='-')
                minimumPhaseList.append(str(timePoint%24) + "h;" + str(daySample[valley]) + "mV")
                lastValley = timePoints[timeIndexStart:timeIndexEnd][valley]
            if(len(peaks) and (period == "Maximum" or period == "Both")):
                peak = peaks[0]
                timePoint = timePoints[timeIndexStart:timeIndexEnd][peak]
                if(lastPeak != None):
                    topLine = max_voltage+(max_voltage-min_voltage)*0.1
                    plt.plot([timePoint, lastPeak], [topLine, topLine], color='k', linestyle='-')
                    plt.annotate(str(timePoint-lastPeak) + "h", xy=((timePoint+lastPeak)/2, 0.93), xycoords=('data','axes fraction'), size=10, ha='center')
                    maximumPeriodList.append(str(timePoint-lastPeak) + "h")
                    
                top = max_voltage + (max_voltage - min_voltage) * 0.15
                bottom = max_voltage + (max_voltage - min_voltage) * 0.05
                plt.plot([timePoint, timePoint], [top, bottom], color='k', linestyle='-')
                maximumPhaseList.append(str(timePoint%24) + "h;" + str(daySample[peak]) + "mV")
                lastPeak = timePoints[timeIndexStart:timeIndexEnd][peak]
        
        if(period == "Minimum"):
            phaseList.append(sample + ";" + "\n;".join(minimumPhaseList))
            periodList.append(sample + ";" + "-".join(minimumPeriodList))
        elif(period == "Maximum"):
            phaseList.append(sample + ";" + "\n;".join(maximumPhaseList))
            periodList.append(sample + ";" + "-".join(maximumPeriodList))
        else:
            periodList.append(sample + ";" + "-".join(minimumPeriodList) + ";;" + sample + ";" + "-".join(maximumPeriodList))
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
        app.setStatusbar(u"\u2588"*math.ceil(progress*(38/progressSize)) + " "*(38-math.ceil(progress*(38/progressSize))))
        app.topLevel.update()
    
    pdfOutput.close()
    with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
        if(period == "Minimum"):
            phaseWriter.write("Minima\nSample;Phase;milliVolt\n" + "\n".join(phaseList))
        elif(period == "Maximum"):
            phaseWriter.write("Maxima\nSample;Phase;milliVolt\n" + "\n".join(phaseList))
        else:
            phaseWriter.write("Minima;;;;Maxima\nSample;Phase;milliVolt;;Sample;Phase;milliVolt\n" + "\n".join(phaseList))
            
        del phaseList[:]
        
    with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
        if(period == "Minimum"):
            periodWriter.write("Minima\nSample;Period\n" + "\n".join(periodList))
        elif(period == "Maximum"):
            periodWriter.write("Maxima\nSample;Period\n" + "\n".join(periodList))
        else:
            periodWriter.write("Minima;;;Maxima\nSample;Period;;Sample;Period\n" + "\n".join(periodList))
            
        del periodList[:]
    
    if(len(comparePlots)):
        pdfOutput = PdfPages(outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_comparePlots.pdf")
        colorList = ('k', 'b', 'g', 'r', 'c', 'm', 'y')
        for plotList in comparePlots:
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
            app.setStatusbar(u"\u2588"*math.ceil(progress*(38/progressSize)) + " "*(38-math.ceil(progress*(38/progressSize))))
            app.topLevel.update()
            
        pdfOutput.close()
        dataPoints.clear()

      

if __name__ == '__main__':
    try:
        buildAppJarGUI()
        app.setPollTime(1)
        app.registerEvent(app.topLevel.update)
        app.go()
    except:
        app.errorBox("Critical error!", traceback.format_exc())
        with open(outputDirectory + "plot_log.txt", "w") as logWriter:
            logWriter.write(traceback.format_exc())
