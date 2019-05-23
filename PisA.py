#!/usr/bin/env python3
#Icon made by Smashicons (https://www.flaticon.com/authors/smashicons) from www.flaticon.com

if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
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
    progress = None
    lock = None
<<<<<<< HEAD
=======

>>>>>>> parent of 7ef7c77... added new options

    app = gui("PisA", "380x360")

    def buildAppJarGUI():
        
        global lbc
        global lbr

        app.setBg("silver", override=True)
        app.setFont(size=12, underline=False, slant="roman")
        app.setLocation(300, 250)

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
            app.setResizable(canResize=False)
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
        
        with app.subWindow("Remove comparing columns"):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame(" TOPLEFT ", row=0, column=0)
            app.addLabel("Removable plots", "Comparing plots")
            lbc = app.addListBox("Removable plots")
            lbc.bind("<Double-1>", lambda *args: doubleClickAdd())
            app.stopFrame()
            app.startFrame(" TOPRIGHT ", row=0, column=1)
            app.addLabel("Removing plots", "Removing plots")
            lbr = app.addListBox("Removing plots")
            lbr.bind("<Double-1>", lambda *args: doubleClickRemove())
            app.stopFrame()
            app.startFrame(" BOTTOMLEFT ", row=1, column=0)
            app.addButton("Remove", columnsPress)
            app.stopFrame()
            app.startFrame(" BOTTOMRIGHT ", row=1, column=1)
            app.addButton("Cancel", columnsPress)
            app.stopFrame()
<<<<<<< HEAD

        with app.subWindow("Analysis settings", modal=True):
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("SettingsTop", row=0, column=0)
            app.addHorizontalSeparator()
            app.addLabel("Data starting point", "Data starting point [h]")
            app.addNumericEntry("Data starting point")
            app.setEntry("Data starting point", 12)
            app.addEmptyLabel("AnalysisFiller1")
            app.addLabel("Data number", "Data number")
            app.addOptionBox("Data number", [])
            app.addEmptyLabel("AnalysisFiller2")
            app.addLabel("Data minute point", "Data minute point [m]")
            app.addOptionBox("Data minute point", [])
            app.addEmptyLabel("AnalysisFiller3")
            app.addLabelSpinBox(" Label ", ["Days", "Hours"])
            app.addEmptyLabel("AnalysisFiller4")
            app.stopFrame()
            app.startToggleFrame("Addtional settings", row=1, column=0)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.addCheckBox(" SG-Filter", row=0, column=0)
            app.addEmptyLabel("AnalysisFiller5", row=1, column=0)
            app.addCheckBox(" Include last day\nfor minima", row=2, column=0)
            app.addEmptyLabel("AnalysisFiller6", row=3, column=0)
            app.addCheckBox(" Include first day\nfor maxima", row=4, column=0)
            app.addEmptyLabel("AnalysisFiller7", row=5, column=0)
            app.addCheckBox(" Don't use suboptimal\npeak/valley threshold", row=6, column=0)
            app.addEmptyLabel("AnalysisFiller8", row=7, column=0)
            app.addCheckBox(" Don't use mean\n calculation threshold", row=8, column=0)
            app.stopToggleFrame()
            app.startFrame("SettingsBottom", row=2, column=0)
            app.addHorizontalSeparator()
            app.addButtons([" Ok ", "Advanced", " Reset "], analysisSettingsPress)
            app.stopFrame()

        with app.subWindow("Advanced settings", modal=True):
=======
        
        with app.subWindow("Advanced settings"):
>>>>>>> parent of 7ef7c77... added new options
            app.setResizable(canResize=False)
            app.setBg("silver", override=True)
            app.setFont(size=12, underline=False, slant="roman")
            app.startFrame("AdvancedTop", row=0, column=0)
            app.addHorizontalSeparator()
            app.addLabel("Filter", "Savitzky-Golay-Filter")
            app.addHorizontalSeparator()
            app.addLabel("WindowSize", "Window size")
            app.addNumericEntry("WindowSize")
            app.setEntry("WindowSize", 11)
            app.addLabel("PolyOrder", "Polynomial order")
            app.addNumericEntry("PolyOrder")
            app.setEntry("PolyOrder", 3)
            app.addHorizontalSeparator()
            app.addHorizontalSeparator()
            app.addLabelSpinBox(" Threads ", list(np.arange(1, mp.cpu_count()+1, 1)))
            app.setSpinBox(" Threads ", mp.cpu_count(), callFunction=False)
            app.addHorizontalSeparator()
            app.stopFrame()
            app.startFrame("AdvancedBottom", row=1, column=0)
            app.addButtons(["  Ok  ", "  Reset  "], advancedSettingsPress)
            app.stopFrame()
<<<<<<< HEAD

        app.addSplitMeter("Progress")
        app.setMeterFill("Progress", ["forestgreen", "lavender"])
        app.addHorizontalSeparator()
        app.stopFrame()

        app.startFrame("MainCenter")
        app.startScrollPane("Pane")
        app.addLabel("Input", "\nInput:\n\nOutput:\n\nComparing plots:\n  None")
=======
        
        app.addMeter("Progress")
        app.setMeterFill("Progress", "forestgreen")
        
        app.startScrollPane("Pane")
        app.addLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
>>>>>>> parent of 7ef7c77... added new options
        app.stopScrollPane()
        
        app.setFastStop(True)
        app.setResizable(canResize=False)
        app.winIcon = None
            


    def openPress(button):

        global data
        global datasheet
        global columnNames
        global outputDirectory
        global dataPerMeasurement
        global dataMinutePoints
        global timePointIndices

        if(button == "Open"):
            try:
                inputFile = app.openBox(title="Input datasheet file", fileTypes=[("datasheet files", "*.txt"),
                                       ("all files", "*.*")])
                if(inputFile != None and len(inputFile)):
                    header = app.getEntry("Header")
                    if(header == None):
                        header = 0
<<<<<<< HEAD

                    app.setLabel("Input", "\nInput:\n\nOutput:\n\nComparing plots:\n  None")
=======
                    
                    app.setLabel("Input", "\nInput: Loading file...\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
>>>>>>> parent of 7ef7c77... added new options
                    built = False
                    if(datasheet != ""):
                        try:
                            app.destroySubWindow("Compare columns")
                        except:
                            pass

                        app.clearListBox("Removable plots", callFunction=False)
                        app.clearListBox("Removing plots", callFunction=False)
                        app.disableMenuItem("PisA", "Remove comparing columns")
                        built = True

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
                            dataPerMeasurement = np.argmax(dataInt[key] > 0)
                            timePointIndices = np.arange(dataPerMeasurement, len(data[key]), dataPerMeasurement)
                            dataMinutePoints = (60 * (data[key] % 1)).astype(int)

                    dataInt.clear()
                    with app.subWindow("Compare columns"):
                        app.setLocation(700, 300)
                        app.setResizable(canResize=False)
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
<<<<<<< HEAD

                    app.changeOptionBox("Data number", ["All"]+list(range(1, dataPerMeasurement)), 5)
                    app.changeOptionBox("Data minute point", ["None"]+list(np.unique(dataMinutePoints)), "None")
=======
                    
                    if(not built):
                        with app.subWindow("Analysis settings"):
                            app.setResizable(canResize=False)
                            app.setBg("silver", override=True)
                            app.setFont(size=12, underline=False, slant="roman")
                            app.startFrame("SettingsTop", row=0, column=0)
                            app.addHorizontalSeparator()
                            app.addLabel("Data starting point", "Data starting point [h]")
                            app.addNumericEntry("Data starting point")
                            app.setEntry("Data starting point", 12)
                            app.addHorizontalSeparator()
                            app.addLabel("Data number", "Data number")
                            app.addOptionBox("Data number", ["All"]+list(range(1, dataPerMeasurement)))
                            app.setOptionBox("Data number", 5, callFunction=False)
                            app.addHorizontalSeparator()
                            app.addLabel("Data minute point", "Data minute point [m]")
                            app.addOptionBox("Data minute point", ["None"]+list(np.unique(dataMinutePoints)))
                            app.setOptionBox("Data minute point", "None", callFunction=False)
                            app.addHorizontalSeparator()
                            app.addLabelSpinBox(" Label ", ["Days", "Hours"])
                            app.addHorizontalSeparator()
                            app.addLabelSpinBox(" SG-Filter ", ["Off", "On"])
                            app.addHorizontalSeparator()
                            app.stopFrame()
                            app.startFrame("SettingsBottom", row=1, column=0)
                            app.addButtons([" Ok ", "Advanced", " Reset "], analysisSettingsPress)
                            app.stopFrame()
                    else:
                        app.changeOptionBox("Data number", ["All"]+list(range(1, dataPerMeasurement)), 5)
                        app.changeOptionBox("Data minute point", ["None"]+list(np.unique(dataMinutePoints)), "None")
                    
>>>>>>> parent of 7ef7c77... added new options
                    if(os.name == "nt"):
                        outputDirectory = "/".join(os.path.abspath(datasheet).split("\\")[:-1]) + "/"
                    else:
                        outputDirectory = "/".join(os.path.abspath(datasheet).split("/")[:-1]) + "/"

                    app.enableMenuItem("PisA", "Start analysis")
                    app.enableMenuItem("PisA", "Compare columns")
                    app.enableMenuItem("PisA", "Set period")
                    app.enableMenuItem("PisA", "Settings ")
<<<<<<< HEAD
                    app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory +
                                 "\n\nComparing plots:\n  None")
                    app.setStatusbar("Status: Input file loaded")
=======
                    app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory + "\n\nComparing plots:\n -> None")
>>>>>>> parent of 7ef7c77... added new options
            except:
                print(traceback.format_exc())
                app.warningBox("Unexpected error!", "An unexpected error occurred! Please check the error message" +
                               " in the second window and restart the analysis!")
                outputDirectory = ""
                app.disableMenuItem("PisA", "Start analysis")
                app.disableMenuItem("PisA", "Compare columns")
                app.disableMenuItem("PisA", "Set period")
                app.disableMenuItem("PisA", "Settings ")
                app.setLabel("Input", "\nInput: Error loading! Check input file!\n\nOutput: " + outputDirectory +
                             "\n\nComparing plots:\n  None")

        if(button == "Save"):
            output = app.directoryBox(title="Output directory")
            if(output != None and len(output)):
                outputDirectory = output + "/"
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " + outputDirectory +
                             "\n\nComparing plots:\n  None")



    def pisaPress(button):
        
        global comparePlots
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
            app.disableMenuItem("Exit", "Exit PisA")

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
            if(startingPoint == None):
                startingPoint = 0
            
            pointSize = int(app.getMenuRadioButton("Plot point size", "Sizes"))
            label = app.getSpinBox(" Label ")
<<<<<<< HEAD
            sgFilter = app.getCheckBox(" SG-Filter")
            inc_min = app.getCheckBox(" Include last day\nfor minima")
            inc_max = app.getCheckBox(" Include first day\nfor maxima")
            usePeakValleyThreshold = not app.getCheckBox(" Don't use suboptimal\npeak/valley threshold")
            useMeanThreshold = not app.getCheckBox(" Don't use mean\n calculation threshold")
=======
            sgFilter = app.getSpinBox(" SG-Filter ")
>>>>>>> parent of 7ef7c77... added new options
            windowSize = app.getEntry("WindowSize")
            if(windowSize == None):
                windowSize = 11
            else:
                windowSize = int(windowSize)
            
            polyOrder = app.getEntry("PolyOrder")
            if(polyOrder == None):
                polyOrder = 3
            else:
                polyOrder = int(polyOrder)
            
            checkFailed = False
            if(int(windowSize) % 2 == 0 or int(windowSize) <= int(polyOrder)):
<<<<<<< HEAD
                app.warningBox("Filter warning!", "Window size of the SG-Filter must be a positive odd integer" +
                               " and larger than the order of the polynomial!")
                checkFailed = True

            if(not checkFailed and not os.access(outputDirectory, os.W_OK | os.R_OK | os.X_OK)):
                app.warningBox("Output folder warning!", "The output folder is not accessible! Please make sure" +
                               " that it exist and is accessible!")
                checkFailed = True

            if(not checkFailed):
                outputList = ["".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf",
                              "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_compared.pdf", "phaseLog.csv",
                              "periodLog.csv", "plotLog.csv"]
=======
                app.warningBox("Filter warning!", "Window size of the SG-Filter must be a positive odd integer and larger than the order of the polynomial!")
                checkFailed = True
            
            elif(not os.access(outputDirectory, os.W_OK | os.R_OK | os.X_OK)):
                app.warningBox("Output folder warning!", "The output folder is not accessible! Please make sure that it exist and is accessible!")
                checkFailed = True
            else:
                outputList = ["".join(datasheet.split("/")[-1].split(".")[:-1]) + ".pdf", "".join(datasheet.split("/")[-1].split(".")[:-1]) + "_compared.pdf", "phaseLog.csv", "periodLog.csv", "plotLog.csv"]
>>>>>>> parent of 7ef7c77... added new options
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
            
            threads = int(app.getSpinBox(" Threads "))
            if(os.path.exists(outputDirectory + "tmp")):
                shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                
            os.makedirs(outputDirectory + "tmp")
            progress.value = 0
            progressSize = len(columnNames) + len(comparePlots)
            try:
<<<<<<< HEAD
                app.setStatusbar("Status: Plotting datapoints - " +
                                 "{0:.2f}".format((progress.value/progressSize)*100) + " %")
                timePoints = np.unique(data["h"] // 1 + startingPoint).astype(float)
                timePointLabels = None
                days = np.arange(0, timePoints[-1], 24).astype(int)
                if(label == "Days"):
                    timePointLabels = np.unique((timePoints // 24)).astype(int)
                elif(label == "Hours"):
                    timePointLabels = days

                minuteIndices = None
                if(minutePoint != "None"):
                    minuteIndex = np.where(dataMinutePoints == minutePoint)[0][0]
                    minuteIndices = np.arange(minuteIndex, len(data["h"]), dataPerMeasurement)

                informationOfTime = [timePoints, timePointLabels, days, minuteIndices]
=======
>>>>>>> parent of 7ef7c77... added new options
                pool = mp.Pool(processes=threads)
                poolMap = partial(phototaxisPlotter.plotData, progress=progress, lock=lock, data=data,
                                  datasheet=datasheet, outputDirectory=outputDirectory, dataNumber=dataNumber,
                                  informationOfTime=informationOfTime, minutePoint=minutePoint,
                                  timePointIndices=timePointIndices, sgFilter=sgFilter, windowSize=windowSize,
                                  polyOrder=polyOrder, period=period, startingPoint=startingPoint, inc_min=inc_min,
                                  inc_max=inc_max, usePeakValleyThreshold=usePeakValleyThreshold,
                                  useMeanThreshold=useMeanThreshold, pointSize=pointSize, label=label)
                pages = pool.map_async(poolMap, columnNames)
                pool.close()
                while(progress.value != len(columnNames)):
                    if(cancelAnalysis):
                        pool.terminate()
                        break
                    
                    app.setMeter("Progress", (progress.value/progressSize)*100)
<<<<<<< HEAD
                    app.setStatusbar("Status: Plotting datapoints - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
=======
>>>>>>> parent of 7ef7c77... added new options
                    app.topLevel.update()
                
                app.setMeter("Progress", (progress.value/progressSize)*100)
<<<<<<< HEAD
                app.setStatusbar("Status: Datapoints plotted - " +
                                 "{0:.2f}".format((progress.value/progressSize)*100) + " %")
=======
>>>>>>> parent of 7ef7c77... added new options
                pool.join()
                compareResults = None
                if(os.path.exists(outputDirectory + "tmpCompare")):
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                    
                os.makedirs(outputDirectory + "tmpCompare")
                if(len(comparePlots) and not cancelAnalysis):
<<<<<<< HEAD
                    app.setStatusbar("Status: Comparing plots - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
=======
>>>>>>> parent of 7ef7c77... added new options
                    pool = mp.Pool(processes=threads)
                    poolMap =  partial(phototaxisPlotter.plotComparePlots, progress=progress, lock=lock,
                                       plotList=pages.get(), datasheet=datasheet, outputDirectory=outputDirectory,
                                       informationOfTime=informationOfTime, pointSize=pointSize, label=label)
                    compareResults = pool.map_async(poolMap, comparePlots)
                    pool.close()
                    while(progress.value != len(columnNames) + len(comparePlots)):
                        if(cancelAnalysis):
                            pool.terminate()
                            break
                        
                        app.setMeter("Progress", (progress.value/progressSize)*100)
<<<<<<< HEAD
                        app.setStatusbar("Status: Comparing plots - " +
                                         "{0:.2f}".format((progress.value/progressSize)*100) + " %")
=======
>>>>>>> parent of 7ef7c77... added new options
                        app.topLevel.update()
                    
                    app.setMeter("Progress", (progress.value/progressSize)*100)
<<<<<<< HEAD
                    app.setStatusbar("Status: Plots compared - " +
                                     "{0:.2f}".format((progress.value/progressSize)*100) + " %")
=======
>>>>>>> parent of 7ef7c77... added new options
                    pool.join()
                
                if(not cancelAnalysis):
                    minimumPhaseList = list()
                    maximumPhaseList = list()
                    minimumPeriodList = list()
                    maximumPeriodList = list()
                    merger = PdfFileMerger()
                    maxMinimumPeriodLength = 0
                    for sample in columnNames:
                        sampleResults = next(list(page.values()) for page in pages.get()
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
                            samplesPage = next(list(page.values()) for page in compareResults.get()
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
<<<<<<< HEAD
                                phaseWriter.write("Minima\nSample;Phase [h];milliVolt [mV]\n" +
                                                  "\n".join(minimumPhaseList))

=======
                                phaseWriter.write("Minima\nSample;Phase [h];milliVolt [mV]\n" + "\n".join(minimumPhaseList))
                            
>>>>>>> parent of 7ef7c77... added new options
                            with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
                                periodWriter.write("Minima\nSample;Period [h]\n" + "\n".join(minimumPeriodList))
                        elif(period == "Maximum"):
                            with open(outputDirectory + "phaseLog.csv", "w") as phaseWriter:
<<<<<<< HEAD
                                phaseWriter.write("Maxima\nSample;Phase [h];milliVolt [mV]\n" +
                                                  "\n".join(maximumPhaseList))

=======
                                phaseWriter.write("Maxima\nSample;Phase [h];milliVolt [mV]\n" + "\n".join(maximumPhaseList))
                            
>>>>>>> parent of 7ef7c77... added new options
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
<<<<<<< HEAD

                                phaseWriter.write("Minima;;;;Maxima\nSample;Phase [h];milliVolt [mV];;Sample;" +
                                "Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))
=======
                                        
                                phaseWriter.write("Minima;;;;Maxima\nSample;Phase [h];milliVolt [mV];;Sample;Phase [h];milliVolt [mV]\n" + "\n".join(phaseList))
>>>>>>> parent of 7ef7c77... added new options
                                del phaseList[:]
                                
                            with open(outputDirectory + "periodLog.csv", "w") as periodWriter:
                                periodList = list()
                                for listIndex in range(len(minimumPeriodList)):
                                    insideMinimumPeriodList = minimumPeriodList[listIndex].split(";")
                                    insideMaximumPeriodList = maximumPeriodList[listIndex].split(";")
<<<<<<< HEAD
                                    periodList.append(";".join(insideMinimumPeriodList) + ";;" +
                                                      ";"*(maxMinimumPeriodLength-len(insideMinimumPeriodList)) +
                                                      ";".join(insideMaximumPeriodList))

                                periodWriter.write("Minima;;" + ";"*(maxMinimumPeriodLength-1) +
                                                   "Maxima\nSample;Period [h];" + ";"*(maxMinimumPeriodLength-1) +
                                                   "Sample;Period [h]\n" + "\n".join(periodList))
=======
                                    periodList.append(";".join(insideMinimumPeriodList) + ";;" + ";"*(maxMinimumPeriodLength-len(insideMinimumPeriodList)) + ";".join(insideMaximumPeriodList))
                                
                                periodWriter.write("Minima;;" + ";"*(maxMinimumPeriodLength-1) + "Maxima\nSample;Period [h];" + ";"*(maxMinimumPeriodLength-1) + "Sample;Period [h]\n" + "\n".join(periodList))
>>>>>>> parent of 7ef7c77... added new options
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
                        space = len("[Don't use suboptimal peak/valley threshold]")
                        logList = list()
                        logList.append("[Datasheet file]" + " "*(space-len("[Datasheet file]")) + "\t" + datasheet)
                        logList.append("[Output directory]" + " "*(space-len("[Output directory]")) + "\t" +
                                       outputDirectory)
                        logList.append("[Header]" + " "*(space-len("[Header]")) + "\t" + str(header))
                        logList.append("[Plot point size]" + " "*(space-len("[Plot point size]")) + "\t" +
                                       str(pointSize))
                        logList.append("[X-axis label]" + " "*(space-len("[X-axis label]")) + "\t" + label)
                        logList.append("[Period]" + " "*(space-len("[Period]")) + "\t" + period)
                        logList.append("[Data number]" + " "*(space-len("[Data number]")) + "\t" +
                                       app.getOptionBox("Data number"))
                        logList.append("[Data starting point [h]]" + " "*(space-len("[Data starting point [h]]")) +
                                       "\t" + str(startingPoint))
                        logList.append("[Data minute point [m]]" + " "*(space-len("[Data minute point [m]]")) +
                                       "\t" + str(minutePoint))
                        logList.append("[SG-Filter On]" + " "*(space-len("[SG-Filter]")) + "\t" + str(sgFilter))
                        logList.append("  [Window size]" + " "*(space-len("[Window size]")) + "\t" + str(windowSize))
                        logList.append("  [Polynomial order]" + " "*(space-len("[Polynomial order]")) + "\t" +
                                       str(polyOrder))
                        logList.append("[Included last day for minima]" +
                                       " "*(space-len("[Included last day for minima]")) + "\t" + str(inc_min))
                        logList.append("[Included first day for maxima]" +
                                       " "*(space-len("[Included first day for maxima]")) + "\t" + str(inc_max))
                        logList.append("[Don't use suboptimal peak/valley threshold]" +
                                       " "*(space-len("[Don't use suboptimal peak/valley threshold]")) +
                                       "\t" + str(app.getCheckBox(" Don't use suboptimal\npeak/valley threshold")))
                        logList.append("[Don't use mean calculation threshold]" +
                                      " "*(space-len("[Don't use mean calculation threshold]")) +
                                      "\t" + str(app.getCheckBox(" Don't use mean\n calculation threshold")))
                        logList.append("[Threads]" + " "*(space-len("[Threads]")) + "\t" + str(threads))
                        if(len(comparePlots)):
<<<<<<< HEAD
                             logList.append("[Compared plots]" + " "*(space-len("[Compared plots]")) + "\n  " +
                                            "\n  ".join(comparePlots))

                        logWriter.write("\n".join(logList))
=======
                            log += "[Compared plots]" + " "*(space-len("[Compared plots]")) + "\n  " + "\n  ".join(comparePlots)
                            
                        logWriter.write(log)
>>>>>>> parent of 7ef7c77... added new options

                    del minimumPhaseList[:]
                    del maximumPhaseList[:]
                    del minimumPeriodList[:]
                    del maximumPeriodList[:]
                    shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                    if(os.name == "nt"):
                        os.startfile(outputDirectory)
                    else:
                        subprocess.call(["xdg-open", outputDirectory])
                        
                enableMenus()
                if(cancelAnalysis):
                    shutil.rmtree(outputDirectory + "tmp", ignore_errors=True)
                    shutil.rmtree(outputDirectory + "tmpCompare", ignore_errors=True)
                    
                cancelAnalysis = False
            except:
                print(traceback.format_exc())
                app.warningBox("Unexpected error!", "An unexpected error occurred! Please check the error" +
                               " message in the second window and restart the analysis!")
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
                    app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " +
                                 outputDirectory + "\n\nComparing plots:\n  " + "\n  ".join(comparePlots))

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
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " +
                             outputDirectory + "\n\nComparing plots:\n  " + "\n  ".join(comparePlots))
            else:
                app.setLabel("Input", "\nInput: " + datasheet + "\n\nOutput: " +
                             outputDirectory + "\n\nComparing plots:\n  None")
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
            
        if(button == "Advanced"):
            app.showSubWindow("Advanced settings")
            
        if(button == " Reset "):
            app.setEntry("Data starting point", 12)
            app.setOptionBox("Data number", 5, callFunction=False)
            app.setOptionBox("Data minute point", "None", callFunction=False)
            app.setSpinBox(" Label ", "Days", callFunction=False)
<<<<<<< HEAD
            app.setCheckBox(" SG-Filter", ticked=False, callFunction=False)
            app.setCheckBox(" Include last day\nfor minima", ticked=False, callFunction=False)
            app.setCheckBox(" Include first day\nfor maxima", ticked=False, callFunction=False)
            app.setCheckBox(" Don't use suboptimal\npeak/valley threshold", ticked=False, callFunction=False)
            app.setCheckBox(" Don't use mean\n calculation threshold", ticked=False, callFunction=False)
=======
            app.setSpinBox(" SG-Filter ", "Off", callFunction=False)
>>>>>>> parent of 7ef7c77... added new options



    def advancedSettingsPress(button):
        
        if(button == "  Ok  "):
            app.hideSubWindow("Advanced settings")
        
        if(button == "  Reset  "):
            app.setEntry("WindowSize", 11)
            app.setEntry("PolyOrder", 3)
            app.setSpinBox(" Threads ", mp.cpu_count(), callFunction=False)



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



    def enableMenus():
        
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
        app.enableMenuItem("Exit", "Exit PisA")
        if(len(comparePlots)):
            app.enableMenuItem("PisA", "Remove comparing columns")



    try:
        manager = mp.Manager()
        progress = manager.Value("i", 0)
        lock = manager.Lock()
        app.winIcon = None
        buildAppJarGUI()
        app.go()
        while(not exitApp):
            mainloop() #tkinter
    except:
        app.errorBox("Critical error!", traceback.format_exc())
        with open(outputDirectory + "errorLog.txt", "w") as logWriter:
            logWriter.write(traceback.format_exc())
