#!/usr/bin/env python3
#Icon made by Smashicons (https://www.flaticon.com/authors/smashicons) from www.flaticon.com

if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()

    import appJar
    app = appJar.gui("PisA", "380x400")
    app.winIcon = None
    with app.subWindow("Loading PisA..."):
        app.addImage("LoadingSun", "icon/loading_sun.gif")

    app.showSubWindow("Loading PisA...")

    import phototaxisPlotter
    import os
    import shutil
    import subprocess
    import pandas as pd
    import numpy as np
    import traceback
    import itertools
    from functools import partial
    from PyPDF2 import PdfFileMerger, PdfFileReader
    from tkinter import *

    data = None
    header = 1
    datasheet = ""
    outputDirectory = ""
    columnNames = list()
    dataPerMeasurement = None
    timePointIndices = None
    dataMinutePoints = None
    plotColor = None
    sgPlotColor = None
    comparePlots = list()
    cancelAnalysis = None
    exitApp = False
    lbc = None
    lbr = None
    progress = None
    lock = None
    pages = None
    compareResults = None

    #app = appJar.gui("PisA", "380x400")

    def buildAppJarGUI():

        global lbc
        global lbr

        app.setTitle("PisA")
        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.setLocation(300, 250)
        app.setFastStop(True)
        app.setResizable(canResize=False)

        app.startFrame("TitleFrame")
        app.addLabel("Title", "PisA: [P]hototax[is]-[A]nalyzer")
        app.setLabelBg("Title", "orangered")
        app.stopFrame()

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
        app.setMenuRadioButton("Set period", "Period", "Both")
        app.addMenuSeparator("PisA")
        app.addMenuItem("PisA", "PisA Settings", pisaPress)
        app.disableMenuItem("PisA", "Start analysis")
        app.disableMenuItem("PisA", "Cancel analysis")
        app.disableMenuItem("PisA", "Compare columns")
        app.disableMenuItem("PisA", "Remove comparing columns")
        app.disableMenuItem("PisA", "Set period")
        app.disableMenuItem("PisA", "PisA Settings")

        app.createMenu("Settings")
        app.addMenuItem("Settings", "Header", fileSettingsPress)
        with app.subWindow("Header settings", modal=True):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("HeaderLabelFrame", row=0, column=0)
            with app.labelFrame("Header"):
                app.addEmptyLabel("HeaderFiller1")
                app.addLabelEntry(" Header line ")
                app.setEntry(" Header line ", 1)
                app.addEmptyLabel("HeaderFiller2")

            app.stopFrame()
            app.startFrame("HeaderButtonsFrame", row=1, column=0)
            app.addNamedButton("Ok", "HeaderOk", fileSettingsPress, row=0, column=0)
            app.addNamedButton("Cancel", "HeaderCancel", fileSettingsPress, row=0, column=1)
            app.stopFrame()

        app.addSubMenu("Settings", "Plot point size")
        for i in range(1, 21):
            app.addMenuRadioButton("Plot point size", "Sizes", i)

        app.setMenuRadioButton("Plot point size", "Sizes", 3)
        app.addMenuItem("Settings", "Plot color", fileSettingsPress)
        app.addMenuSeparator("Settings")
        app.addMenuItem("Settings", "Reset settings", fileSettingsPress)
        app.disableMenuItem("Settings", "Plot point size")
        app.disableMenuItem("Settings", "Plot color")

        app.createMenu("Exit")
        app.addMenuItem("Exit", "Exit PisA", exitPress)

        with app.subWindow("Remove comparing columns", modal=True):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("ComparingPlotsFrame", row=0, column=0)
            app.addLabel("Removable plots", "Comparing plots")
            lbc = app.addListBox("Removable plots")
            lbc.bind("<Double-1>", lambda *args: doubleClickAdd())
            app.stopFrame()
            app.startFrame("RemovingPlotsFrame", row=0, column=1)
            app.addLabel("Removing plots", "Removing plots")
            lbr = app.addListBox("Removing plots")
            lbr.bind("<Double-1>", lambda *args: doubleClickRemove())
            app.stopFrame()
            app.startFrame("RemoveFrame", row=1, column=0)
            app.addNamedButton("Remove", "RemoveOk", columnsPress)
            app.stopFrame()
            app.startFrame("CancelFrame", row=1, column=1)
            app.addNamedButton("Cancel", "RemoveCancel", columnsPress)
            app.stopFrame()

        with app.subWindow("Analysis settings", modal=True):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("AnalysisOptionsFrame", row=0, column=0)
            with app.labelFrame("General settings"):
                app.addEmptyLabel("AnalysisFiller1")
                app.addLabelEntry(" Starting point ")
                app.setEntry(" Starting point ", 12)
                app.addEmptyLabel("AnalysisFiller2")
                app.addLabelScale(" Data number ")
                app.showScaleValue(" Data number ", show=True)
                app.addEmptyLabel("AnalysisFiller3")
                app.addLabelScale(" Data minute point ")
                app.showScaleValue(" Data minute point ", show=True)
                app.addEmptyLabel("AnalysisFiller4")
                with app.labelFrame("Minimum"):
                    app.addEmptyLabel("AnalysisFiller5")
                    app.addCheckBox(" Exclude first Day [min]", row=0, column=0)
                    app.addCheckBox(" Exclude last Day [min]", row=0, column=1)
                    app.setCheckBox(" Exclude last Day [min]", ticked=True, callFunction=False)
                    app.addEmptyLabel("AnalysisFiller6")

                with app.labelFrame("Maximum"):
                    app.addEmptyLabel("AnalysisFiller7")
                    app.addCheckBox(" Exclude first Day [max]", row=0, column=0)
                    app.addCheckBox(" Exclude last Day [max]", row=0, column=1)
                    app.setCheckBox(" Exclude first Day [max]", ticked=True, callFunction=False)
                    app.addEmptyLabel("AnalysisFiller8")

            with app.labelFrame("X-axis label"):
                app.addEmptyLabel("AnalysisFiller9", row=0, column=0)
                app.addRadioButton("Label", "Days", row=1, column=0)
                app.addRadioButton("Label", "Hours", row=1, column=1)
                app.addEmptyLabel("AnalysisFiller10")

            with app.labelFrame("SG-Filter"):
                app.addEmptyLabel("AnalysisFiller11", row=0, column=0)
                app.addCheckBox(" SG-Filter On", row=1, column=0)
                app.addNamedButton("Set color", "SGPlotColor", analysisSettingsPress, row=1, column=1)
                app.addEmptyLabel("AnalysisFiller12")

            app.stopFrame()
            app.startFrame("AnalysisButtonsFrame", row=3, column=0)
            app.addNamedButton("Ok", "AnalysisOk", analysisSettingsPress, row=0, column=0)
            app.addNamedButton("Advanced", "AnalysisAdvanced", analysisSettingsPress, row=0, column=1)
            app.addNamedButton("Reset", "AnalysisReset", analysisSettingsPress, row=0, column=2)
            app.stopFrame()

        with app.subWindow("Advanced settings", modal=True):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("AdvancedOptionsFrame", row=0, column=0)
            with app.labelFrame("Peak-Valley-Detection"):
                app.addEmptyLabel("AdvancedFiller1")
                app.addLabelSpinBox(" Points ", list(np.arange(1, 1000, 1)))
                app.setSpinBox(" Points ", 1)
                app.addEmptyLabel("AdvancedFiller2")

            with app.labelFrame("Peak-Valley-Mean-Calculation"):
                app.addEmptyLabel("AdvancedFiller3")
                app.addLabelEntry(" Amplitude percentage %")
                app.setEntry(" Amplitude percentage %", 3)
                app.addEmptyLabel("AdvancedFiller4")

            with app.labelFrame("Savitzky-Golay-Filter"):
                app.addEmptyLabel("AdvancedFiller5")
                app.addLabelEntry(" Window size ")
                app.setEntry(" Window size ", 11)
                app.addEmptyLabel("AdvancedFiller6")
                app.addLabelEntry(" Poly order ")
                app.setEntry(" Poly order ", 3)
                app.addEmptyLabel("AdvancedFiller7")

            with app.labelFrame("Threads"):
                app.addEmptyLabel("AdvancedFiller8")
                app.addLabelSpinBox(" Thread number ", list(np.arange(1, mp.cpu_count()+1, 1)))
                if(os.name == "nt"):
                    app.setSpinBox(" Thread number ", 1, callFunction=False)
                else:
                    app.setSpinBox(" Thread number ", mp.cpu_count(), callFunction=False)
                app.addEmptyLabel("AdvancedFiller9")

            app.stopFrame()
            app.startFrame("AdvancecButtonsFrame", row=1, column=0)
            app.addNamedButton("Ok", "AdvancedOk", advancedSettingsPress, row=0, column=0)
            app.addNamedButton("Reset", "AdvancedReset", advancedSettingsPress, row=0, column=1)
            app.stopFrame()

        app.startFrame("MeterFrame")
        app.addSplitMeter("Progress")
        app.setMeterFill("Progress", ["forestgreen", "lavender"])
        app.stopFrame()

        app.startFrame("PaneFrame")
        with app.labelFrame("Data"):
            app.startScrollPane("Pane")
            app.addEmptyLabel("MainFiller1")
            app.addLabel("Input", " Input: ")
            app.setLabelAlign("Input", "left")
            app.addEmptyLabel("MainFiller2")
            app.addLabel("Output", " Output: ")
            app.setLabelAlign("Output", "left")
            app.addEmptyLabel("MainFiller3")
            app.addLabel("Plots", " Comparing plots:\n  None")
            app.setLabelAlign("Plots", "left")
            app.stopScrollPane()

        app.stopFrame()
        app.addStatusbar("Status")



    def openPress(button):

        global data
        global header
        global datasheet
        global columnNames
        global outputDirectory
        global dataPerMeasurement
        global dataMinutePoints
        global timePointIndices
        global plotColor
        global sgPlotColor

        if(button == "Open"):
            try:
                inputFile = app.openBox(title="Input datasheet file", fileTypes=[("datasheet files", "*.txt"),
                                       ("all files", "*.*")])
                if(inputFile != None and len(inputFile)):
                    header = app.getEntry(" Header line ")
                    if(not len(header)):
                        header = 0
                    else:
                        try:
                            header = int(header)
                            if(header < 0):
                                raise ValueError()
                        except ValueError:
                            app.warningBox("Value warning", "The header has to be a positive integer number!")
                            return

                    app.setLabel("Input", " Input: ")
                    app.setLabel("Output", " Output: ")
                    app.setLabel("Plots", " Comparing plots:\n  None")
                    app.setStatusbar("Loading input file")
                    if(datasheet != ""):
                        try:
                            app.destroySubWindow("Compare columns")
                        except appJar.appjar.ItemLookupError:
                            pass

                        app.clearListBox("Removable plots", callFunction=False)
                        app.clearListBox("Removing plots", callFunction=False)
                        app.disableMenuItem("PisA", "Remove comparing columns")

                    datasheet = inputFile
                    del columnNames[:]
                    del comparePlots[:]
                    data = pd.read_csv(datasheet, sep="\t", header=int(header), encoding="iso-8859-1")
                    dataInt = dict()
                    dataMinutePoints = None
                    for key in data:
                        data[key] = data[key].str.replace(",", ".")
                        data[key] = data[key].astype(float)
                        dataInt[key] = data[key].astype(int)
                        if(key == "h"):
                            dataPerMeasurement = np.argmax(np.array(dataInt[key] > 0))
                            timePointIndices = np.arange(dataPerMeasurement, len(data[key]), dataPerMeasurement)
                            dataMinutePoints = (60 * (data[key] % 1)).astype(int)

                    dataInt.clear()
                    plotColor = "#000000"
                    sgPlotColor = "#800000"
                    with app.subWindow("Compare columns"):
                        app.setLocation(700, 300)
                        app.setResizable(canResize=False)
                        app.setBg("silver", override=True)
                        app.setFont(size=12, underline=False, slant="roman")
                        app.startFrame("ComparePlotsFrame", row=0, column=0)
                        with app.labelFrame("Columns"):
                            app.addEmptyLabel("ColumnFiller1")
                            columnNames = list(data.keys())[2:]
                            row = 1
                            for column in range(len(columnNames)):
                                if(column != 0 and column % 6 == 0):
                                    row += 1

                                app.addCheckBox(columnNames[column], row, column % 6)

                            app.addEmptyLabel("ColumnFiller2")

                        app.stopFrame()
                        app.startFrame("CompareButtonsFrame", row=1, column=0)
                        app.addNamedButton("Set", "CompareSet", columnsPress, row=0, column=0)
                        app.addNamedButton("Close", "CompareClose", columnsPress, row=0, column=1)
                        app.stopFrame()

                    app.setScaleRange(" Data number ", 0, dataPerMeasurement, curr=5)
                    app.setScaleIncrement(" Data number ", 1/dataPerMeasurement)
                    app.showScaleIntervals(" Data number ", dataPerMeasurement)
                    app.setScaleRange(" Data minute point ", -1, np.unique(dataMinutePoints)[-1], curr=-1)
                    app.setScaleIncrement(" Data minute point ", 1/np.unique(dataMinutePoints)[-1])
                    app.showScaleIntervals(" Data minute point ", np.unique(dataMinutePoints)[-1]+1)
                    if(os.name == "nt"):
                        outputDirectory = "/".join(os.path.abspath(datasheet).split("\\")[:-1]) + "/"
                    else:
                        outputDirectory = "/".join(os.path.abspath(datasheet).split("/")[:-1]) + "/"

                    app.enableMenuItem("PisA", "Start analysis")
                    app.enableMenuItem("PisA", "Compare columns")
                    app.enableMenuItem("PisA", "Set period")
                    app.enableMenuItem("PisA", "PisA Settings")
                    app.enableMenuItem("Settings", "Plot point size")
                    app.enableMenuItem("Settings", "Plot color")
                    app.setLabel("Input", " Input: " + datasheet)
                    app.setLabel("Output", " Output: " + outputDirectory)
                    app.setLabel("Plots", " Comparing plots:\n  None")
                    app.setMeter("Progress", 0)
                    app.setStatusbar("Input file loaded")
            except Exception:
                outputDirectory = ""
                app.disableMenuItem("PisA", "Start analysis")
                app.disableMenuItem("PisA", "Compare columns")
                app.disableMenuItem("PisA", "Set period")
                app.disableMenuItem("PisA", "PisA Settings")
                app.disableMenuItem("Settings", "Plot point size")
                app.disableMenuItem("Settings", "Plot color")
                app.setStatusbar("Error file loading!")
                app.warningBox("File loading error!", "An unexpected error occurred! Please check the error message" +
                           " in the second window and retry!")
                app.errorBox("File loading error!", traceback.format_exc())

        if(button == "Save"):
            output = app.directoryBox(title="Output directory")
            if(output != None and len(output)):
                outputDirectory = output + "/"
                app.setLabel("Input", " Input: " + datasheet)
                app.setLabel("Output", " Output: " + outputDirectory)



    def pisaPress(button):

        global pages
        global compareResults
        global cancelAnalysis

        if(button == "Start analysis"):
            app.disableMenuItem("File", "Open")
            app.disableMenuItem("File", "Save")
            app.disableMenuItem("PisA", "Start analysis")
            app.enableMenuItem("PisA", "Cancel analysis")
            app.disableMenuItem("PisA", "Compare columns")
            app.disableMenuItem("PisA", "Remove comparing columns")
            app.disableMenuItem("PisA", "Set period")
            app.disableMenuItem("PisA", "PisA Settings")
            app.disableMenuItem("Settings", "Header")
            app.disableMenuItem("Settings", "Plot point size")
            app.disableMenuItem("Settings", "Reset settings")
            app.disableMenuItem("Settings", "Plot point size")
            app.disableMenuItem("Settings", "Plot color")
            app.disableMenuItem("Exit", "Exit PisA")
            app.hideSubWindow("Compare columns")
            app.hideSubWindow("Remove comparing columns")
            app.hideSubWindow("Analysis settings")
            app.hideSubWindow("Advanced settings")
            app.hideSubWindow("Header settings")

            dataNumber = int(app.getScale(" Data number "))
            minutePoint = int(app.getScale(" Data minute point "))
            period = app.getMenuRadioButton("Set period", "Period")
            startingPoint = app.getEntry(" Starting point ")
            if(not len(startingPoint)):
                startingPoint = 0
            else:
                try:
                    startingPoint = float(startingPoint.replace(",", "."))
                except ValueError:
                    app.warningBox("Value error", "The starting point has to be a positive integer or floating point number!")
                    enableMenus()
                    return

            pointSize = int(app.getMenuRadioButton("Plot point size", "Sizes"))
            minFirstDay = app.getCheckBox(" Exclude first Day [min]")
            minLastDay = app.getCheckBox(" Exclude last Day [min]")
            maxFirstDay = app.getCheckBox(" Exclude first Day [max]")
            maxLastDay = app.getCheckBox(" Exclude last Day [max]")
            label = app.getRadioButton("Label")
            points = int(app.getSpinBox(" Points "))
            amplitudePercentage = app.getEntry(" Amplitude percentage %")
            if(not len(amplitudePercentage)):
                amplitudePercentage = 3
            else:
                try:
                    amplitudePercentage = float(amplitudePercentage)
                    if(amplitudePercentage < 0):
                        raise ValueError()
                except ValueError:
                    app.warningBox("Value warning", "The amplitude percentage has to be a positive integer number!")
                    enableMenus()
                    return

            sgFilter = app.getCheckBox(" SG-Filter On")
            windowSize = app.getEntry(" Window size ")
            if(not len(windowSize)):
                windowSize = 11
            else:
                try:
                    windowSize = int(windowSize)
                    if(windowSize < 0):
                        raise ValueError()
                except ValueError:
                    app.warningBox("Value warning", "The window size has to be a positive integer number!")
                    enableMenus()
                    return

            polyOrder = app.getEntry(" Poly order ")
            if(not len(polyOrder)):
                polyOrder = 3
            else:
                try:
                    polyOrder = int(polyOrder)
                    if(polyOrder < 0):
                        raise ValueError()
                except ValueError:
                    app.warningBox("Value warning", "The poly order has to be a positive integer number!")
                    enableMenus()
                    return

            checkFailed = False
            if(int(windowSize) % 2 == 0 or int(windowSize) <= int(polyOrder)):
                app.warningBox("Filter warning!", "Window size of the SG-Filter must be a positive odd integer" +
                               " and larger than the order of the poly order!")
                checkFailed = True

            if(not checkFailed and not os.access(outputDirectory, os.W_OK | os.R_OK | os.X_OK)):
                app.warningBox("Output folder warning!", "The output folder is not accessible! Please make sure" +
                               " that it exist and is accessible!")
                checkFailed = True

            if(not checkFailed):
                outputList = ["".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf",
                              "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_compared.pdf", "phaseLog.csv",
                              "periodLog.csv", "plotLog.csv"]
                for outputFile in outputList:
                    if(os.path.exists(outputDirectory + outputFile)):
                        try:
                            with open(outputDirectory + outputFile, "w") as fileReader:
                                pass
                        except PermissionError:
                            app.warningBox("Output file warning!", "The output file '" + outputFile +
                                           "' is not accessible! Please make sure that it is closed!")
                            checkFailed = True
                            break

            if(checkFailed):
                enableMenus()
                return

            threads = int(app.getSpinBox(" Thread number "))
            if(os.path.exists(outputDirectory + "tmp")):
                shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)

            os.makedirs(outputDirectory + "tmp")
            progress.value = 0
            progressSize = len(columnNames) + len(comparePlots)
            try:
                app.setStatusbar("Plotting datapoints - " +
                                 "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                timePoints = np.unique(data["h"] // 1 + startingPoint).astype(float)
                timePointLabels = None
                days = np.arange(0, timePoints[-1], 24).astype(int)
                if(label == "Days"):
                    timePointLabels = np.unique((timePoints // 24)).astype(int)
                elif(label == "Hours"):
                    timePointLabels = days

                minuteIndices = None
                if(minutePoint != -1):
                    minuteIndex = np.where(dataMinutePoints == minutePoint)[0][0]
                    minuteIndices = np.arange(minuteIndex, len(data["h"]), dataPerMeasurement)

                informationOfTime = [timePoints, timePointLabels, days, minuteIndices]
                pages = None
                pool = None
                if(threads == 1):
                    app.thread(startSingleThreaded_PlotData, columnNames=columnNames, progress=progress, lock=lock, data=data,
                               datasheet=datasheet, outputDirectory=outputDirectory, dataNumber=dataNumber,
                               informationOfTime=informationOfTime, timePointIndices=timePointIndices,
                               plotColor=plotColor, minFirstDay=minFirstDay, minLastDay=minLastDay, maxFirstDay=maxFirstDay,
                               maxLastDay=maxLastDay, points=points, amplitudePercentage=amplitudePercentage,
                               sgFilter=sgFilter, sgPlotColor=sgPlotColor, windowSize=windowSize, polyOrder=polyOrder,
                               period=period, startingPoint=startingPoint, pointSize=pointSize, label=label)
                else:
                    pool = mp.Pool(processes=threads)
                    poolMap = partial(phototaxisPlotter.plotData, progress=progress, lock=lock, data=data,
                                      datasheet=datasheet, outputDirectory=outputDirectory, dataNumber=dataNumber,
                                      informationOfTime=informationOfTime, timePointIndices=timePointIndices,
                                      plotColor=plotColor, minFirstDay=minFirstDay, minLastDay=minLastDay, maxFirstDay=maxFirstDay,
                                      maxLastDay=maxLastDay, points=points, amplitudePercentage=amplitudePercentage,
                                      sgFilter=sgFilter, sgPlotColor=sgPlotColor, windowSize=windowSize, polyOrder=polyOrder,
                                      period=period, startingPoint=startingPoint, pointSize=pointSize, label=label)
                    pages = pool.map_async(poolMap, columnNames)
                    pool.close()

                while(progress.value != len(columnNames)):
                    if(cancelAnalysis):
                        if(threads > 1):
                            pool.terminate()

                        break

                    app.setMeter("Progress", (progress.value/progressSize)*100)
                    app.setStatusbar("Plotting datapoints - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                    app.topLevel.update()

                app.setMeter("Progress", (progress.value/progressSize)*100)
                app.setStatusbar("Plotting datapoints - " +
                                 "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                if(threads > 1):
                    pool.join()
                    pages = pages.get()

                compareResults = None
                if(os.path.exists(outputDirectory + "tmpCompare")):
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)

                os.makedirs(outputDirectory + "tmpCompare")
                if(len(comparePlots) and not cancelAnalysis):
                    app.setStatusbar("Comparing plots - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                    pool = None
                    if(threads == 1):
                        app.thread(startSingleThreaded_PlotComparePlots, comparePlots=comparePlots, progress=progress,
                                   lock=lock, plotList=pages, datasheet=datasheet, outputDirectory=outputDirectory,
                                   informationOfTime=informationOfTime, pointSize=pointSize, label=label)
                    else:
                        pool = mp.Pool(processes=threads)
                        poolMap =  partial(phototaxisPlotter.plotComparePlots, progress=progress, lock=lock,
                                           plotList=pages, datasheet=datasheet, outputDirectory=outputDirectory,
                                           informationOfTime=informationOfTime, pointSize=pointSize, label=label)
                        compareResults = pool.map_async(poolMap, comparePlots)
                        pool.close()

                    while(progress.value != len(columnNames) + len(comparePlots)):
                        if(cancelAnalysis):
                            if(threads > 1):
                                pool.terminate()

                            break

                        app.setMeter("Progress", (progress.value/progressSize)*100)
                        app.setStatusbar("Comparing plots - " +
                                         "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                        app.topLevel.update()

                    app.setMeter("Progress", (progress.value/progressSize)*100)
                    app.setStatusbar("Plotting datapoints - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                    if(threads > 1):
                        pool.join()
                        compareResults = compareResults.get()

                if(not cancelAnalysis):
                    minimumPhaseList = list()
                    maximumPhaseList = list()
                    minimumPeriodList = list()
                    maximumPeriodList = list()
                    merger = PdfFileMerger()
                    maxMinimumPeriodLength = 0
                    for sample in columnNames:
                        sampleResults = next(list(page.values()) for page in pages
                                                  if sample == list(page.keys())[0])[0]
                        samplePage = sampleResults[1]
                        minimumPhaseList.append(sample + ";" + "\n;".join(sampleResults[2]))
                        maximumPhaseList.append(sample + ";" + "\n;".join(sampleResults[3]))
                        minimumPeriodList.append(sample + ";" + ";".join(sampleResults[4]))
                        maximumPeriodList.append(sample  + ";"+ ";".join(sampleResults[5]))
                        if(len(sampleResults[4]) >= maxMinimumPeriodLength):
                            maxMinimumPeriodLength = len(sampleResults[4]) + 1

                        merger.append(samplePage)

                    outputFile = outputDirectory + "".join(datasheet.split("/")[-1].split(".")[:-1])
                    if(os.path.exists(outputFile + ".pdf")):
                        try:
                            with open(outputFile + ".pdf", "w") as fileReader:
                                pass
                        except PermissionError:
                            app.warningBox("Output file warning!", "The output file '" +
                                           "".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf" +
                                           "' is not accessible! Please make sure that it is closed and" +
                                           " restart the analysis!")
                            shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                            shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                            enableMenus()
                            return

                    merger.write(outputFile + ".pdf")
                    merger.close()
                    if(len(comparePlots)):
                        compareMerger = PdfFileMerger()
                        for samples in comparePlots:
                            samplesPage = next(list(page.values()) for page in compareResults
                                                    if samples == list(page.keys())[0])[0]
                            compareMerger.append(samplesPage)

                        if(os.path.exists(outputFile + "_compared.pdf")):
                            try:
                                with open(outputFile + "_compared.pdf", "w") as fileReader:
                                    pass
                            except PermissionError:
                                app.warningBox("Output file warning!", "The output file '" +
                                               "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_compared.pdf"
                                               +"' is not accessible! Please make sure that it is closed and" +
                                               " restart the analysis!")
                                shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                                shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                                enableMenus()
                                return

                        compareMerger.write(outputFile + "_compared.pdf")
                        compareMerger.close()
                    try:
                        if(period == "Minimum"):
                            with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                                phaseWriter.write("Minima\nSample;Phase [h];milliVolt [mV]\n" +
                                                  "\n".join(minimumPhaseList))
                            with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
                                periodWriter.write("Minima\nSample;Period [h]\n" + "\n".join(minimumPeriodList))
                        elif(period == "Maximum"):
                            with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                                phaseWriter.write("Maxima\nSample;Phase [h];milliVolt [mV]\n" +
                                                  "\n".join(maximumPhaseList))
                            with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
                                periodWriter.write("Maxima\nSample;Period [h]\n" + "\n".join(maximumPeriodList))
                        else:
                            with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
                                phaseList = list()
                                for listIndex in range(len(minimumPhaseList)):
                                    insideMinimumPhaseList = minimumPhaseList[listIndex].split("\n")
                                    insideMaximumPhaseList = maximumPhaseList[listIndex].split("\n")
                                    mergedLists = list(itertools.zip_longest(insideMinimumPhaseList,
                                                                             insideMaximumPhaseList,
                                                                             fillvalue=";--;--"))
                                    for mergedList in mergedLists:
                                        phaseList.append(";;".join(mergedList))

                                phaseWriter.write("Minima;;;;Maxima\nSample;Phase [h];milliVolt [mV];;Sample;" +
                                "Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))
                                del phaseList[:]

                            with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
                                periodList = list()
                                for listIndex in range(len(minimumPeriodList)):
                                    insideMinimumPeriodList = minimumPeriodList[listIndex].split(";")
                                    insideMaximumPeriodList = maximumPeriodList[listIndex].split(";")
                                    periodList.append(";".join(insideMinimumPeriodList) + ";;" +
                                                      ";"*(maxMinimumPeriodLength-len(insideMinimumPeriodList)) +
                                                      ";".join(insideMaximumPeriodList))

                                periodWriter.write("Minima;;" + ";"*(maxMinimumPeriodLength-1) +
                                                   "Maxima\nSample;Period [h];" + ";"*(maxMinimumPeriodLength-1) +
                                                   "Sample;Period [h]\n" + "\n".join(periodList))
                                del periodList[:]
                    except PermissionError:
                        app.warningBox("Output file warning!", "The output file 'phaseLog.csv' or 'periodLog.csv'" +
                                       " is not accessible! Please make sure that they are closed and restart" +
                                       " the analysis!")
                        shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                        shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                        enableMenus()
                        return

                    with open(outputDirectory + "plotLog.txt", "w") as logWriter:
                        if(dataNumber == 0):
                            dataNumber = "All"
                        if(minutePoint == -1):
                            minutePoint = "None"

                        space = len("[Amplitude percentage %]")
                        logList = list()
                        logList.append("[Datasheet file]" + " "*(space-len("[Datasheet file]")) + "\t" + datasheet)
                        logList.append("[Output directory]" + " "*(space-len("[Output directory]")) + "\t" +
                                       outputDirectory)
                        logList.append("[Header]" + " "*(space-len("[Header]")) + "\t" + str(header))
                        logList.append("[Plot point size]" + " "*(space-len("[Plot point size]")) + "\t" +
                                       str(pointSize))
                        logList.append("[X-axis label]" + " "*(space-len("[X-axis label]")) + "\t" + label)
                        logList.append("[Period]" + " "*(space-len("[Period]")) + "\t" + period)
                        logList.append("[Starting point]" + " "*(space-len("[Starting point]")) +
                                       "\t" + str(startingPoint))
                        logList.append("[Data number]" + " "*(space-len("[Data number]")) + "\t" +
                                       str(dataNumber))
                        logList.append("[Minute point]" + " "*(space-len("[Minute point]")) +
                                       "\t" + str(minutePoint))
                        logList.append("[Minimum]")
                        logList.append("  [Exclude first day]" + " "*(space-len("  [Exclude first day]")) + "\t" +
                                       str(minFirstDay))
                        logList.append("  [Exclude last day]" + " "*(space-len("  [Exclude last day]")) + "\t" +
                                       str(minLastDay))
                        logList.append("[Maximum]")
                        logList.append("  [Exclude first day]" + " "*(space-len("  [Exclude first day]")) + "\t" +
                                       str(maxFirstDay))
                        logList.append("  [Exclude last day]" + " "*(space-len("  [Exclude last day]")) + "\t" +
                                       str(maxLastDay))
                        logList.append("[Peak-Valley-Points]" + " "*(space-len("[Peak-Valley-Points]")) + "\t" +
                                       str(points))
                        logList.append("[Amplitude percentage %]" + " "*(space-len("[Amplitude percentage %]")) + "\t" +
                                       str(amplitudePercentage))
                        logList.append("[SG-Filter On]" + " "*(space-len("[SG-Filter]")) + "\t" + str(sgFilter))
                        logList.append("  [Window size]" + " "*(space-len("[Window size]")) + "\t" + str(windowSize))
                        logList.append("  [Polynomial order]" + " "*(space-len("[Polynomial order]")) + "\t" +
                                       str(polyOrder))
                        logList.append("[Threads]" + " "*(space-len("[Threads]")) + "\t" + str(threads))
                        if(len(comparePlots)):
                             logList.append("[Compared plots]" + " "*(space-len("[Compared plots]")) + "\n  " +
                                            "\n  ".join(comparePlots))

                        logWriter.write("\n".join(logList))

                    del minimumPhaseList[:]
                    del maximumPhaseList[:]
                    del minimumPeriodList[:]
                    del maximumPeriodList[:]
                    app.setStatusbar("Analysis finished")
                    shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                    if(os.name == "nt"):
                        os.startfile(outputDirectory)
                    else:
                        subprocess.call(["xdg-open", outputDirectory])

                enableMenus()
                if(cancelAnalysis):
                    app.setStatusbar("Analysis canceled")
                    shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)

                cancelAnalysis = False
            except Exception:
                app.setStatusbar("Analysis error")
                app.warningBox("Unexpected error!", "An unexpected error occurred! Please check the error" +
                               " message in the second window and retry!")
                app.errorBox("Unexpected error!", traceback.format_exc())
                enableMenus()
                if(os.path.exists(outputDirectory + "tmp")):
                    shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)

                if(os.path.exists(outputDirectory + "tmpCompare")):
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)

                cancelAnalysis = False

        if(button == "Cancel analysis"):
            cancelAnalysis = True

        if(button == "Compare columns"):
            app.showSubWindow("Compare columns")

        if(button == "Remove comparing columns"):
            app.showSubWindow("Remove comparing columns")

        if(button == "PisA Settings"):
            app.showSubWindow("Analysis settings")



    def columnsPress(button):

        global comparePlots

        if(button == "CompareSet"):
            checkBoxes = app.getAllCheckBoxes()
            checklist = list()
            for check in columnNames:
                if(checkBoxes[check]):
                    checklist.append(check)
                    app.setCheckBox(check, ticked=False, callFunction=False)

            if(len(checklist)):
                app.enableMenuItem("PisA", "Remove comparing columns")
                checkPlots = " - ".join(checklist)
                if(not checkPlots in comparePlots):
                    comparePlots.append(checkPlots)
                    app.addListItem("Removable plots", checkPlots)
                    app.setLabel("Plots", " Comparing plots:\n  " + "\n  ".join(comparePlots))

            del checklist[:]

        if(button == "CompareClose"):
            checkBoxes = app.getAllCheckBoxes()
            for check in columnNames:
                if(checkBoxes[check]):
                    app.setCheckBox(check, ticked=False, callFunction=False)

            app.hideSubWindow("Compare columns")

        if(button == "RemoveOk"):
            removePlots = app.getAllListItems("Removing plots")
            for plot in removePlots:
                comparePlots.remove(plot)
                app.removeListItem("Removing plots", plot)

            if(len(comparePlots)):
                app.setLabel("Plots", " Comparing plots:\n  " + "\n  ".join(comparePlots))
            else:
                app.setLabel("Plots", " Comparing plots:\n  None")
                app.disableMenuItem("PisA", "Remove comparing columns")

            app.hideSubWindow("Remove comparing columns")

        if(button == "RemoveCancel"):
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

        global sgPlotColor

        if(button == "AnalysisOk"):
            app.confirmHideSubWindow("Analysis settings")

        if(button == "AnalysisAdvanced"):
            app.showSubWindow("Advanced settings")

        if(button == "SGPlotColor"):
            sgPlotColor = app.colourBox(colour=sgPlotColor)

        if(button == "AnalysisReset"):
            app.setEntry(" Starting point ", 12)
            app.setScale(" Data number ", 5, callFunction=False)
            app.setScale(" Data minute point ", -1, callFunction=False)
            app.setCheckBox(" Exclude first Day [min]", ticked=False, callFunction=False)
            app.setCheckBox(" Exclude last Day [min]", ticked=True, callFunction=False)
            app.setCheckBox(" Exclude first Day [max]", ticked=True, callFunction=False)
            app.setCheckBox(" Exclude last Day [max]", ticked=False, callFunction=False)
            app.setRadioButton("Label", "Days", callFunction=False)
            app.setCheckBox(" SG-Filter On", ticked=False, callFunction=False)
            sgPlotColor = "#800000"


    def advancedSettingsPress(button):

        if(button == "AdvancedOk"):
            app.hideSubWindow("Advanced settings")

        if(button == "AdvancedReset"):
            app.setSpinBox(" Points ", 1)
            app.setEntry(" Amplitude percentage %", 3)
            app.setEntry(" Window size ", 11)
            app.setEntry(" Poly order ", 3)
            if(os.name == "nt"):
                app.setSpinBox(" Thread number ", 1, callFunction=False)
            else:
                app.setSpinBox(" Thread number ", mp.cpu_count(), callFunction=False)



    def fileSettingsPress(button):

        global header
        global plotColor

        if(button == "Header"):
            app.showSubWindow("Header settings")

        if(button == "HeaderOk"):
            app.hideSubWindow("Header settings")

        if(button == "HeaderCancel"):
            app.hideSubWindow("Header settings")
            app.setEntry(" Header line ", header)

        if(button == "Plot color"):
            plotColor = app.colourBox(colour=plotColor)

        if(button == "Reset settings"):
            header = 1
            app.setEntry(" Header line ", header)
            app.setMenuRadioButton("Plot point size", "Sizes", 3)
            plotColor = "#000000"



    def exitPress(button):

        global exitApp

        if(button == "Exit PisA"):
            exitApp = True
            app.stop()



    def enableMenus():

        app.enableMenuItem("File", "Open")
        app.enableMenuItem("File", "Save")
        app.enableMenuItem("PisA", "Start analysis")
        app.disableMenuItem("PisA", "Cancel analysis")
        app.enableMenuItem("PisA", "Compare columns")
        app.enableMenuItem("PisA", "Set period")
        app.enableMenuItem("PisA", "PisA Settings")
        app.enableMenuItem("Settings", "Header")
        app.enableMenuItem("Settings", "Plot point size")
        app.enableMenuItem("Settings", "Reset settings")
        app.enableMenuItem("Settings", "Plot point size")
        app.enableMenuItem("Settings", "Plot color")
        app.enableMenuItem("Exit", "Exit PisA")
        if(len(comparePlots)):
            app.enableMenuItem("PisA", "Remove comparing columns")



    def startSingleThreaded_PlotData(columnNames, progress, lock, data, datasheet, outputDirectory, dataNumber, informationOfTime,
                                  timePointIndices, plotColor, minFirstDay, minLastDay, maxFirstDay, maxLastDay, points, amplitudePercentage,
                                  sgFilter, sgPlotColor, windowSize, polyOrder, period, startingPoint, pointSize, label):

        global pages

        pages = list()
        for sample in columnNames:
            pageResult = phototaxisPlotter.plotData(sample=sample, progress=progress, lock=lock, data=data,
                                                    datasheet=datasheet, outputDirectory=outputDirectory, dataNumber=dataNumber,
                                                    informationOfTime=informationOfTime, timePointIndices=timePointIndices,
                                                    plotColor=plotColor, minFirstDay=minFirstDay, minLastDay=minLastDay, maxFirstDay=maxFirstDay,
                                                    maxLastDay=maxLastDay, points=points, amplitudePercentage=amplitudePercentage,
                                                    sgFilter=sgFilter, sgPlotColor=sgPlotColor, windowSize=windowSize, polyOrder=polyOrder,
                                                    period=period, startingPoint=startingPoint, pointSize=pointSize, label=label)

            pages.append(pageResult)



    def startSingleThreaded_PlotComparePlots(comparePlots, progress, lock, plotList, datasheet, outputDirectory,
                                          informationOfTime, pointSize, label):

        global compareResults

        compareResults = list()
        for sampleList in comparePlots:
            pageCompareResult = phototaxisPlotter.plotComparePlots(sampleList=sampleList, progress=progress, lock=lock, plotList=pages,
                                                                   datasheet=datasheet, outputDirectory=outputDirectory,
                                                                   informationOfTime=informationOfTime, pointSize=pointSize, label=label)

            compareResults.append(pageCompareResult)




    try:
        manager = mp.Manager()
        progress = manager.Value("i", 0)
        lock = manager.Lock()
        buildAppJarGUI()
        app.destroySubWindow("Loading PisA...")
        app.go()
        while(not exitApp):
            mainloop() #tkinter
    except Exception:
        app.errorBox("Critical error!", traceback.format_exc())
        with open(outputDirectory + "errorLog.txt", "w") as logWriter:
            logWriter.write(traceback.format_exc())
