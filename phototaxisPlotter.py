import os
import sys
import itertools
import numpy as np
import scipy.signal as signal
import matplotlib
matplotlib.use("PS")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages


def plotData(selected_group, input_list, progress, progress_per_step, lock):
    try:
        if(not os.path.exists(input_list[selected_group]["output"])):
            os.makedirs(input_list[selected_group]["output"])

        pdf_document = PdfPages(input_list[selected_group]["output"] + selected_group + ".pdf")
        with open(input_list[selected_group]["output"] + "period_log.csv", "w") as period_writer:
            period_writer.write("")

        with open(input_list[selected_group]["output"] + "phase_log.csv", "w") as phase_writer:
            phase_writer.write("")

        overall_minimum_period_list = list()
        overall_minimum_phase_list = list()
        overall_maximum_period_list = list()
        overall_maximum_phase_list = list()
        for file in input_list[selected_group]["file_names"]:
            columns = list(input_list[file]["data"])[2:]
            settings = file
            if(input_list[selected_group]["set_settings"]):
                settings = selected_group

            time_points = np.unique(input_list[file]["data"]["h"] // 1 + input_list[settings]["startingpoint"]).astype(float)
            time_point_labels = None
            hours = np.arange(0, time_points[-1], 24).astype(int)
            if(input_list[settings]["xlabel"] == "Days"):
                time_point_labels = np.unique((time_points // 24)).astype(int)
            elif(input_list[settings]["xlabel"] == "Hours"):
                time_point_labels = hours

            plot_minimum_period_list = list()
            plot_minimum_phase_list = list()
            plot_maximum_period_list = list()
            plot_maximum_phase_list = list()
            for column in columns:
                column_data = input_list[file]["data"][column]
                max_voltage = np.amax(column_data)
                min_voltage = np.amin(column_data)
                data_inverted_mean = None
                data_inverted = np.array((max_voltage + min_voltage) - column_data)
                if(input_list[settings]["minutepoint"] != -1):
                    minute_index = np.where(input_list[file]["data_minutepoints"] == input_list[settings]["minutepoint"])[0][0]
                    minute_indices = np.arange(minute_index, len(input_list[file]["data"]["h"]),
                                               input_list[file]["data_per_measurement"])
                    data_inverted_per_minutepoint = np.take(data_inverted, minute_indices)
                    data_inverted_mean = np.mean(data_inverted_per_minutepoint, axis=1)
                else:
                    data_inverted_per_timepoint = np.array(np.split(data_inverted, input_list[file]["timepoint_indices"]))
                    data_inverted_mean = np.mean(data_inverted_per_timepoint[:,-input_list[settings]["datanumber"]:],
                                                 axis=1)

                figure = plt.figure()
                plt.plot(time_points, data_inverted_mean, marker="o", markersize=input_list[settings]["pointsize"],
                         color=input_list[settings]["color"], linestyle="-", label="raw data")
                if(input_list[settings]["sg_filter"]["on"]):
                    data_inverted_mean_smoothed = signal.savgol_filter(data_inverted_mean,
                                                                       input_list[settings]["sg_filter"]["window"],
                                                                       input_list[settings]["sg_filter"]["poly"])
                    plt.plot(time_points, data_inverted_mean_smoothed, color=input_list[settings]["sg_filter"]["color"],
                             linestyle="-", label="smoothed data")
                    plt.legend(bbox_to_anchor=(1.05,0.40))

                plt.title(column + "\n" + file)
                plt.xticks(hours, time_point_labels)
                plt.xlabel(input_list[settings]["xlabel"])
                plt.ylabel("mV")
                threshold = (max_voltage - min_voltage) * (input_list[settings]["pv_amp_per"] / 100)
                last_valley = None
                last_peak = None
                mean_minimum_period = 0
                minimum_periods = 0
                mean_maximum_period = 0
                maximum_periods = 0
                points = input_list[settings]["pv_points"]
                minimum_period_list = list()
                minimum_phase_list = list()
                maximum_period_list = list()
                maximum_phase_list = list()
                for day in hours:
                    day_start = day - (2 * points)
                    day_end = day + (22 + (2 * points))
                    if(day == 0):
                        day_start = input_list[settings]["startingpoint"]
                    else:
                        if(input_list[settings]["period"] == "Minimum"):
                            plt.axvline(day, ymin=0.1, color="black", linestyle=":")
                        elif(input_list[settings]["period"] == "Maximum"):
                            plt.axvline(day, ymax=0.9, color="black", linestyle=":")
                        elif(input_list[settings]["period"] == "Both"):
                            plt.axvline(day, ymin=0.1, ymax=0.9, color="black", linestyle=":")

                    if(not day_end in time_points):
                        day_end = time_points[-1]

                    time_index_start = np.where(time_points == day_start)[0][0]
                    time_index_end = np.where(time_points == day_end)[0][0]
                    day_data = data_inverted_mean[time_index_start:time_index_end+1]
                    daytime_points = time_points[time_index_start:time_index_end+1]
                    valleys, peaks = findPeaksAndValleys(day_data, points)
                    if(len(valleys) and (input_list[settings]["period"] == "Minimum" or input_list[settings]["period"] == "Both")):
                        if(not ((input_list[settings]["minimum"]["exclude_firstday"] and day == 0)
                                 or (input_list[settings]["minimum"]["exclude_lastday"] and day_end == time_points[-1]))):
                            valley = None
                            smallest_valley = sys.float_info.max
                            valleys.reverse()
                            for i in valleys:
                                if(day_data[i] < smallest_valley):
                                    smallest_valley = day_data[i]
                                    valley = i

                            mean_time = None
                            mean_valley = None
                            if(day == 0):
                                mean_time, mean_valley = calculatePeakAndValleyMean(daytime_points[:-points], day_data[:-points],
                                                                                    valley, threshold, "min")
                            else:
                                mean_time, mean_valley = calculatePeakAndValleyMean(daytime_points[points:-points],
                                                                                    day_data[points:-points], valley-points,
                                                                                    threshold, "min")
                            if(last_valley != None):
                                bottom_line = min_voltage - (max_voltage - min_voltage) * 0.1
                                plt.plot([mean_time, last_valley], [bottom_line, bottom_line], color="black", linestyle="-")
                                plt.annotate(str(mean_time-last_valley).replace(".", ",") + "h", xy=((mean_time+last_valley)/2, 0.04),
                                             xycoords=("data","axes fraction"), size=10, ha="center")
                                minimum_period_list.append(str(mean_time-last_valley).replace(".", ","))
                                mean_minimum_period += mean_time - last_valley
                                minimum_periods += 1

                            top = min_voltage - (max_voltage - min_voltage) * 0.15
                            bottom = min_voltage - (max_voltage - min_voltage) * 0.05
                            plt.plot([mean_time, mean_time], [top, bottom], color="black", linestyle="-")
                            minimum_phase_list.append(str(mean_time%24).replace(".", ",") + ";" + str(mean_valley).replace(".", ","))
                            last_valley = mean_time
                    if(len(peaks) and (input_list[settings]["period"] == "Maximum" or input_list[settings]["period"] == "Both")):
                        if(not ((input_list[settings]["maximum"]["exclude_firstday"] and day == 0)
                                 or (input_list[settings]["maximum"]["exclude_lastday"] and day_end == time_points[-1]))):
                            peak = None
                            highest_peak = 0
                            for i in peaks:
                                if(day_data[i] > highest_peak):
                                    highest_peak = day_data[i]
                                    peak = i

                            if(day_end == time_points[-1]):
                                mean_time, meanPeak = calculatePeakAndValleyMean(daytime_points[points:], day_data[points:],
                                                                                 peak-points, threshold, "max")
                            else:
                                mean_time, meanPeak = calculatePeakAndValleyMean(daytime_points[points:-points],
                                                                                 day_data[points:-points], peak-points,
                                                                                 threshold, "max")
                            if(last_peak != None):
                                topLine = max_voltage + (max_voltage - min_voltage) * 0.1
                                plt.plot([mean_time, last_peak], [topLine, topLine], color="black", linestyle="-")
                                plt.annotate(str(mean_time-last_peak).replace(".", ",") + "h", xy=((mean_time+last_peak)/2, 0.93),
                                             xycoords=("data","axes fraction"), size=10, ha="center")
                                maximum_period_list.append(str(mean_time-last_peak).replace(".", ","))
                                mean_maximum_period += mean_time - last_peak
                                maximum_periods += 1

                            top = max_voltage + (max_voltage - min_voltage) * 0.15
                            bottom = max_voltage + (max_voltage - min_voltage) * 0.05
                            plt.plot([mean_time, mean_time], [top, bottom], color="black", linestyle="-")
                            maximum_phase_list.append(str(mean_time%24).replace(".", ",") + ";" + str(meanPeak).replace(".", ","))
                            last_peak = mean_time


                plot_minimum_period_list.append(column + ";" + ";".join(minimum_period_list))
                plot_minimum_phase_list.append(column + ";" + "\n;".join(minimum_phase_list))
                plot_maximum_period_list.append(column + ";" + ";".join(maximum_period_list))
                plot_maximum_phase_list.append(column + ";" + "\n;".join(maximum_phase_list))
                props = dict(boxstyle='round', facecolor='white', alpha=0.15)
                if(input_list[settings]["period"] == "Minimum"):
                    plt.gcf().text(0.955, 0.5, "mean min period: " + "{0:.2f}".format(mean_minimum_period / minimum_periods) + "h",
                                   bbox=props)
                elif(input_list[settings]["period"] == "Maximum"):
                    plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(mean_maximum_period / maximum_periods) + "h",
                                  bbox=props)
                else:
                    plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(mean_maximum_period / maximum_periods) +
                                   "h\n\n" + "mean min period: " + "{0:.2f}".format(mean_minimum_period / minimum_periods) + "h",
                                   bbox=props)

                pdf_document.savefig(figure)
                plt.close()
                with lock:
                    progress.value += progress_per_step

            overall_minimum_period_list.append(file + "\n" + "\n".join(plot_minimum_period_list))
            overall_minimum_phase_list.append(file + "\n" + "\n".join(plot_minimum_phase_list))
            overall_maximum_period_list.append(file + "\n" + "\n".join(plot_maximum_period_list))
            overall_maximum_phase_list.append(file + "\n" + "\n".join(plot_maximum_phase_list))

        if(input_list[selected_group]["period"] == "Minimum" or input_list[selected_group]["period"] == "Both"):
            with open(input_list[selected_group]["output"] + "period_log.csv", "a") as period_writer:
                period_writer.write("Minimum\nSample;Period per day\n" + "\n".join(overall_minimum_period_list) + "\n\n")

            with open(input_list[selected_group]["output"] + "phase_log.csv", "a") as phase_writer:
                phase_writer.write("Minimum\nSample;Phase;milliVolt\n" + "\n".join(overall_minimum_phase_list) + "\n\n")

        if(input_list[selected_group]["period"] == "Maximum" or input_list[selected_group]["period"] == "Both"):
            with open(input_list[selected_group]["output"] + "period_log.csv", "a") as period_writer:
                period_writer.write("Maximum\nSample;Period per day\n" + "\n".join(overall_maximum_period_list))

            with open(input_list[selected_group]["output"] + "phase_log.csv", "a") as phase_writer:
                phase_writer.write("Maximum\nSample;Phase;milliVolt\n" + "\n".join(overall_maximum_phase_list))

        pdf_document.close()
        return
    except Exception as ex:
        return ex



def plotComparePlots(sampleList, progress, lock, plotList, datasheet, outputDirectory, informationOfTime,
                     pointSize, label):

    colorList = ("#000000", "#FF0000", "#FFD700", "#008000", "#0000FF", "#A52A2A", "#FF8C00", "#00FFFF", "#FF00FF",
                 "#E9967A", "#BDB76B", "#00FF00", "#6A5ACD", "#2F4F4F", "#BC8F8F")
    samples = sampleList.split(" - ")
    patches = list()
    colorIndex = 0
    firstPlot = True
    time_points = informationOfTime[0]
    time_point_labels = informationOfTime[1]
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
            plt.xticks(days, time_point_labels)
            plt.xlabel(label)
            plt.ylabel("mV")
            for day in days:
                if(day in time_points):
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
