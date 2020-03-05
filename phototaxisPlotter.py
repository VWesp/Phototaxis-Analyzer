import os
import sys
import itertools
import numpy as np
import scipy.signal as signal
import matplotlib
matplotlib.use("PS")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.pyplot import cm
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import traceback
import datetime

def plotData(selected_group, input_list, highest_columns_index, progress, lock):
    try:
        if(not os.path.exists(input_list[selected_group]["output"])):
            os.makedirs(input_list[selected_group]["output"])

        with open(input_list[selected_group]["output"] + selected_group + "_period_log.csv", "w") as period_writer:
            period_writer.write("")

        with open(input_list[selected_group]["output"]+ selected_group + "_phase_log.csv", "w") as phase_writer:
            phase_writer.write("")

        overall_minimum_period_list = []
        overall_minimum_phase_list = []
        overall_maximum_period_list = []
        overall_maximum_phase_list = []
        plot_minimum_period_list = []
        plot_minimum_phase_list = []
        plot_maximum_period_list = []
        plot_maximum_phase_list = []
        minimum_period_list = []
        minimum_phase_list = []
        maximum_period_list = []
        maximum_phase_list = []
        x_y_values = {}
        valleys = []
        peaks = []
        pdf_document = PdfPages(input_list[selected_group]["output"] + selected_group + ".pdf")
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

            x_y_values[file] = {}
            x_y_values[file]["time_points"] = time_points
            x_y_values[file]["day_hours"] = hours
            x_y_values[file]["time_point_labels"] = time_point_labels
            x_y_values[file]["mean_values"]= {}
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
                data_inverted_mean_smoothed = signal.savgol_filter(data_inverted_mean,
                                                                   input_list[settings]["sg_filter"]["window"],
                                                                   input_list[settings]["sg_filter"]["poly"])
                x_y_values[file]["mean_values"][column] = data_inverted_mean
                figure = plt.figure()
                plt.plot(time_points, data_inverted_mean, marker="o", markersize=input_list[settings]["pointsize"],
                         color=input_list[settings]["color"], linestyle="-", label="raw data")
                if(input_list[settings]["sg_filter"]["on"]):
                    plt.plot(time_points, data_inverted_mean_smoothed, color=input_list[settings]["sg_filter"]["color"],
                             linestyle="-", label="smoothed data")
                    plt.legend(bbox_to_anchor=(1.05,0.40))

                plt.title(column + "\n" + file)
                plt.xticks(hours, time_point_labels)
                plt.xlabel(input_list[settings]["xlabel"])
                plt.ylabel("mV")
                mean_minimum_period = 0
                minimum_periods = 0
                mean_maximum_period = 0
                maximum_periods = 0
                points = input_list[settings]["pv_points"]
                if(input_list[settings]["sg_filter"]["period"]):
                    for day in hours:
                        day_start = (day + (input_list[settings]["startingpoint"] % 2)) - (2 * points)
                        day_end = (day + (input_list[settings]["startingpoint"] % 2)) + (22 + (2 * points))
                        if(input_list[settings]["dn_cycle"]["on"]):
                            plt.axvspan(day_end-12, day_end, facecolor=input_list[settings]["dn_cycle"]["background"],
                                        alpha=float(input_list[settings]["dn_cycle"]["visibility"])/100)
                        if(day != 0):
                            if(input_list[settings]["period"] == "Minimum"):
                                plt.axvline(day, ymin=0.1, color="black", linestyle=":")
                            elif(input_list[settings]["period"] == "Maximum"):
                                plt.axvline(day, ymax=0.9, color="black", linestyle=":")
                            elif(input_list[settings]["period"] == "Both"):
                                plt.axvline(day, ymin=0.1, ymax=0.9, color="black", linestyle=":")

                    if(input_list[settings]["period"] == "Maximum" or input_list[settings]["period"] == "Both"):
                        peaks = time_points[signal.find_peaks(data_inverted_mean_smoothed)[0]]
                        if(len(peaks)):
                            top = max_voltage + (max_voltage - min_voltage) * 0.15
                            bottom = max_voltage + (max_voltage - min_voltage) * 0.05
                            top_line = max_voltage + (max_voltage - min_voltage) * 0.1
                            plt.plot([peaks[0], peaks[-1]], [top_line, top_line], color="black", linestyle="-")
                            for i in range(len(peaks)):
                                plt.plot([peaks[i], peaks[i]], [top, bottom], color="black", linestyle="-")
                                maximum_phase_list.append(str(peaks[i]%24).replace(".", ",") + ";" + str(data_inverted_mean_smoothed[i]).replace(".", ","))
                                if(i != 0):
                                    plt.annotate(str(peaks[i]-peaks[i-1]).replace(".", ",") + "h",
                                                 xy=((peaks[i]+peaks[i-1])/2, 0.93),
                                                 xycoords=("data","axes fraction"), size=10, ha="center")
                                    maximum_period_list.append(str(peaks[i]-peaks[i-1]).replace(".", ","))
                                    mean_maximum_period += peaks[i] - peaks[i-1]
                                    maximum_periods += 1

                        if(input_list[settings]["period"] == "Minimum" or input_list[settings]["period"] == "Both"):
                            valleys = time_points[signal.find_peaks(data_inverted_mean_smoothed*-1)[0]]
                            if(len(valleys)):
                                top = min_voltage - (max_voltage - min_voltage) * 0.15
                                bottom = min_voltage - (max_voltage - min_voltage) * 0.05
                                bottom_line = min_voltage - (max_voltage - min_voltage) * 0.1
                                plt.plot([valleys[0], valleys[-1]], [bottom_line, bottom_line], color="black", linestyle="-")
                                for i in range(len(valleys)):
                                    plt.plot([valleys[i], valleys[i]], [top, bottom], color="black", linestyle="-")
                                    minimum_phase_list.append(str(valleys[i]%24).replace(".", ",") + ";" + str(data_inverted_mean_smoothed[i]).replace(".", ","))
                                    if(i != 0):
                                        plt.annotate(str(valleys[i]-valleys[i-1]).replace(".", ",") + "h",
                                                     xy=((valleys[i]+valleys[i-1])/2, 0.04),
                                                     xycoords=("data","axes fraction"), size=10, ha="center")
                                        minimum_period_list.append(str(valleys[i]-valleys[i-1]).replace(".", ","))
                                        mean_minimum_period += valleys[i] - valleys[i-1]
                                        minimum_periods += 1
                else:
                    threshold = (max_voltage - min_voltage) * (input_list[settings]["pv_amp_per"] / 100)
                    last_valley = None
                    last_peak = None
                    for day in hours:
                        valleys = []
                        peaks = []
                        day_start = (day + (input_list[settings]["startingpoint"] % 2)) - (2 * points)
                        day_end = (day + (input_list[settings]["startingpoint"] % 2)) + (22 + (2 * points))
                        if(input_list[settings]["dn_cycle"]["on"]):
                            plt.axvspan(day_end-12, day_end, facecolor=input_list[settings]["dn_cycle"]["background"],
                                        alpha=float(input_list[settings]["dn_cycle"]["visibility"])/100)

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
                        if(len(day_data) > points*2):
                            for i in range(points, len(day_data)-points, 1):
                                valley_found = True
                                for j in range(1, points+1, 1):
                                    if(day_data[i] > day_data[i-j] or day_data[i] > day_data[i+j]):
                                        valley_found = False
                                        break

                                if(valley_found):
                                    valleys.append(i)

                                peak_found = True
                                for j in range(1, points+1, 1):
                                    if(day_data[i] < day_data[i-j] or day_data[i] < day_data[i+j]):
                                        peak_found = False
                                        break

                                if(peak_found):
                                    peaks.append(i)

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
                                    top_line = max_voltage + (max_voltage - min_voltage) * 0.1
                                    plt.plot([mean_time, last_peak], [top_line, top_line], color="black", linestyle="-")
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
                        if(len(valleys) and (input_list[settings]["period"] == "Minimum" or input_list[settings]["period"] == "Both")):
                            if(not ((input_list[settings]["minimum"]["exclude_firstday"] and day == 0)
                                     or (input_list[settings]["minimum"]["exclude_lastday"] and day_end == time_points[-1]))):
                                valley = None
                                smallest_valley = sys.float_info.max
                                for i in valleys:
                                    if(day_data[i] <= smallest_valley):
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

                    del valleys[:]
                    del peaks[:]

                plot_minimum_period_list.append(column + ";" + ";".join(minimum_period_list))
                plot_minimum_phase_list.append(column + ";" + "\n;".join(minimum_phase_list))
                plot_maximum_period_list.append(column + ";" + ";".join(maximum_period_list))
                plot_maximum_phase_list.append(column + ";" + "\n;".join(maximum_phase_list))
                del minimum_period_list[:]
                del minimum_phase_list[:]
                del maximum_period_list[:]
                del maximum_phase_list[:]

                props = dict(boxstyle='round', facecolor='white', alpha=0.15)
                if(input_list[settings]["period"] == "Minimum" and minimum_periods != 0):
                    plt.gcf().text(0.955, 0.5, "mean min period: " + "{0:.2f}".format(mean_minimum_period / minimum_periods) + "h",
                                   bbox=props)
                elif(input_list[settings]["period"] == "Maximum" and maximum_periods != 0):
                    plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(mean_maximum_period / maximum_periods) + "h",
                                  bbox=props)
                else:
                    if(minimum_periods == 0 and maximum_periods != 0):
                        plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(mean_maximum_period / maximum_periods) + "h",
                                      bbox=props)
                    elif(maximum_periods == 0 and minimum_periods != 0):
                        plt.gcf().text(0.955, 0.5, "mean min period: " + "{0:.2f}".format(mean_minimum_period / minimum_periods) + "h",
                                       bbox=props)
                    elif(minimum_periods != 0 and maximum_periods != 0):
                        plt.gcf().text(0.955, 0.5, "mean max period: " + "{0:.2f}".format(mean_maximum_period / maximum_periods) +
                                       "h\n\n" + "mean min period: " + "{0:.2f}".format(mean_minimum_period / minimum_periods) + "h",
                                       bbox=props)

                pdf_document.savefig(figure, bbox_inches="tight")
                plt.close()
                with lock:
                    progress.value += 1

            overall_minimum_period_list.append(file + "\n" + "\n".join(plot_minimum_period_list))
            overall_minimum_phase_list.append(file + "\n" + "\n".join(plot_minimum_phase_list))
            overall_maximum_period_list.append(file + "\n" + "\n".join(plot_maximum_period_list))
            overall_maximum_phase_list.append(file + "\n" + "\n".join(plot_maximum_phase_list))
            del plot_minimum_period_list[:]
            del plot_minimum_phase_list[:]
            del plot_maximum_period_list[:]
            del plot_maximum_phase_list[:]

        if(input_list[selected_group]["period"] == "Minimum" or input_list[selected_group]["period"] == "Both"):
            with open(input_list[selected_group]["output"] + selected_group + "_period_log.csv", "a") as period_writer:
                period_writer.write("Minimum\nSample;Period per day\n" + "\n".join(overall_minimum_period_list) + "\n\n")

            with open(input_list[selected_group]["output"] + selected_group + "_phase_log.csv", "a") as phase_writer:
                phase_writer.write("Minimum\nSample;Phase;milliVolt\n" + "\n".join(overall_minimum_phase_list) + "\n\n")

        if(input_list[selected_group]["period"] == "Maximum" or input_list[selected_group]["period"] == "Both"):
            with open(input_list[selected_group]["output"]+ selected_group + "_period_log.csv", "a") as period_writer:
                period_writer.write("Maximum\nSample;Period per day\n" + "\n".join(overall_maximum_period_list))

            with open(input_list[selected_group]["output"]+ selected_group + "_phase_log.csv", "a") as phase_writer:
                phase_writer.write("Maximum\nSample;Phase;milliVolt\n" + "\n".join(overall_maximum_phase_list))

        del overall_minimum_period_list[:]
        del overall_minimum_phase_list[:]
        del overall_maximum_period_list[:]
        del overall_maximum_phase_list[:]
        pdf_document.close()
        if(len(input_list[selected_group]["set_columns"])):
            pdf_compared_document = PdfPages(input_list[selected_group]["output"] + selected_group + "_compared.pdf")
            current_file_columns_map = {}
            merged_columns = []
            np_merged_columns = []
            modified_y = []
            legend_patches = []
            new_plots_df = pd.DataFrame()
            for i in range(highest_columns_index+1):
                number_of_columns = 0
                for file,column_set in input_list[selected_group]["set_columns"].items():
                    for columns in column_set:
                        column_index = int(columns.split(" :=: ")[0])
                        if(column_index == i):
                            current_file_columns_map[file] = columns
                            number_of_columns += len(columns.split(" :=: ")[1].split(" - "))
                            break

                if(number_of_columns != 0):
                    first_plot = True
                    colors = iter(cm.rainbow(np.linspace(0, 1, number_of_columns)))
                    figure = plt.figure()
                    for file,column_set in current_file_columns_map.items():
                        columns = column_set.split(" :=: ")[1].split(" - ")
                        x = x_y_values[file]["time_points"]
                        for column in columns:
                            y = x_y_values[file]["mean_values"][column]
                            color = next(colors)
                            legend_patch, = plt.plot(x, y, label=file+"|"+column, marker="o", markersize=input_list[selected_group]["pointsize"],
                                                     linestyle="-", color=color)
                            legend_patches.append(legend_patch)
                            merged_columns.append(y)
                            if(first_plot):
                                time_points = x_y_values[file]["time_points"]
                                new_plots_df["h"] = [str(s).replace(".", ",") for s in (time_points - 12)]
                                new_plots_df["°C"] = ["-1000000,000000"] * len(time_points)
                                plt.title(str(i) + "\n" + selected_group)
                                plt.xticks(x_y_values[file]["day_hours"], x_y_values[file]["time_point_labels"])
                                plt.xlabel(input_list[file]["xlabel"])
                                plt.ylabel("mV")
                                points = input_list[file]["pv_points"]
                                for day in x_y_values[file]["day_hours"]:
                                    if(day in x_y_values[file]["time_points"]):
                                        plt.axvline(day, color="black", linestyle=":")

                                    if(input_list[file]["dn_cycle"]["on"]):
                                        day_end = (day + (input_list[file]["startingpoint"] % 2)) + (22 + (2 * points))
                                        plt.axvspan(day_end-12, day_end, facecolor=input_list[file]["dn_cycle"]["background"],
                                                    alpha=float(input_list[settings]["dn_cycle"]["visibility"])/100)

                                first_plot = False

                            with lock:
                                progress.value += 1

                    if(input_list[selected_group]["merge_plots"]["on"]):
                        longest_column = max(merged_columns, key=len)
                        np_merged_columns = np.asarray(merged_columns)
                        for index in range(len(longest_column)):
                            column_data = np.asarray(np_merged_columns[:,index])
                            column_data_median = column_data - np.median(column_data)
                            mad = np.median(np.abs(column_data_median))
                            modified_z = (0.6745 * column_data_median) / mad
                            mod_column_data = column_data[np.abs(modified_z)<=input_list[selected_group]["merge_plots"]["threshold"]]
                            avg_mod_column_data = np.mean(mod_column_data)
                            modified_y.append(avg_mod_column_data)
                            with lock:
                                progress.value += 1

                        max_modified_y = np.amax(modified_y)
                        min_modified_y = np.amin(modified_y)
                        modified_y_inverted = np.array((max_modified_y + min_modified_y) - modified_y)
                        new_plots_df[i] = [str(s).replace(".", ",") for s in modified_y_inverted]
                        legend_patch, = plt.plot(time_points, modified_y, color=input_list[selected_group]["merge_plots"]["color"], marker="o", linestyle="-",
                                        	     markersize=input_list[selected_group]["pointsize"], label="merged plot")
                        legend_patches.append(legend_patch)
                        del merged_columns[:]
                        del modified_y[:]

                    plt.legend(handles=legend_patches, bbox_to_anchor=(1.05,0.5))
                    pdf_compared_document.savefig(figure, bbox_inches="tight")
                    plt.close()
                    del legend_patches[:]

                current_file_columns_map.clear()

            pdf_compared_document.close()
            if(input_list[selected_group]["merge_plots"]["on"]):
                new_plots_df.to_csv(input_list[selected_group]["output"] + selected_group + "_merged.txt",
                                    index=None, sep="\t")
                with open(input_list[selected_group]["output"] + selected_group + "_merged.txt", "r+") as merge_reader:
                    content = merge_reader.read()
                    merge_reader.seek(0, 0)
                    merge_reader.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n" + content)

            del new_plots_df

        x_y_values.clear()
        return
    except:
        return traceback.format_exc()

def calculatePeakAndValleyMean(x, y, point, threshold, mode):
    value_list = []
    index_list = []
    left_y = y[:point+1]
    for i in range(len(left_y)-2, -1, -1):
        if(mode == "min"):
            if(left_y[i] > y[point]+threshold):
                break
            elif(y[point] <= left_y[i] <= y[point]+threshold):
                value_list.append(left_y[i])
                index_list.append(i)
        elif(mode == "max"):
            if(left_y[i] < y[point]-threshold):
                break
            elif(y[point] >= left_y[i] >= y[point]-threshold):
                value_list.append(left_y[i])
                index_list.append(i)

    index_list = list(reversed(index_list))
    value_list.append(y[point])
    index_list.append(point)
    right_y = y[point:]
    for i in range(1, len(right_y), 1):
        if(mode == "min"):
            if(right_y[i] > y[point]+threshold):
                break
            elif(y[point] <= right_y[i] <= y[point]+threshold):
                value_list.append(right_y[i])
                index_list.append(point+i)
        elif(mode == "max"):
            if(right_y[i] < y[point]-threshold):
                break
            elif(y[point] >= right_y[i] >= y[point]-threshold):
                value_list.append(right_y[i])
                index_list.append(point+i)

    mean_x = int(np.mean(np.take(x, index_list)))
    mean_y = np.mean(np.array(value_list))
    return (mean_x, mean_y)
