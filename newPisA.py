import tkinter as tk
from tkinter import filedialog
import tkinter.colorchooser as tkcc
import tkinter.ttk as ttk
import os
import sys
import pandas as pd
import numpy as np

input_list = dict()
input_list["All"] = {"path": [], "output": None, "pointsize": 3, "startingpoint": 12, "datanumber": 5,
                     "minutepoint": -1, "period": "Both", "color": "#000000",
                     "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                     "maximum": {"exclude_firstday": True, "exclude_lastday": False}, "xlabel": "Days",
                     "sg_filter": {"on": False, "window": 11, "poly": 3, "color": "#800000"},
                     "pv_points": 1, "pv_amp_per": 3, "data_per_measurement": sys.maxsize,
                     "timepoint_indices": [], "data_minutepoints": sys.maxsize, "file_names": []}

class Application(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.initWindow()

    def initWindow(self):
        files_frame = tk.LabelFrame(self, text="Files", borderwidth=2, relief="groove")
        file_options_frame = tk.Frame(files_frame)
        file_options_var = tk.StringVar()
        file_options_var.set("Files")
        file_options = ttk.OptionMenu(file_options_frame, file_options_var, *["Files"])
        file_options.pack()
        file_options.configure(state="disabled")
        file_options_frame.pack(fill="both", expand=0)
        header_line = self.buildLabelSpinbox(files_frame, "Set header line of file", 1, 1, 2)
        files_frame.pack(fill="both", expand=0)

        info_frame = tk.LabelFrame(self, borderwidth=3, relief="sunken")
        info_frame.pack(fill="both", expand=1)

        self.master.title("PisA - [P]hototax[is]-[A]nalyzer")
        self.pack(fill="both", expand=1)
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        file = tk.Menu(menu, tearoff=0)
        file.add_command(label="Open", command=lambda: self.openFile(menu, file_options, file_options_var,
                         header_line))
        menu.add_cascade(label="Files", menu=file)
        pisa = tk.Menu(menu, tearoff=0)
        pisa.add_command(label="Start analysis")
        pisa.add_command(label="Cancel analysis")
        pisa.add_separator()
        pisa.add_command(label="Compare columns", command=lambda: self.configureColumnWindow(file_options_var))
        pisa.add_command(label="Remove comparing columns")
        pisa.add_separator()
        pisa.add_command(label="Settings", command=lambda: self.configureSettings(file_options_var))
        menu.add_cascade(label="PisA analysis", menu=pisa)
        exit = tk.Menu(menu, tearoff=0)
        exit.add_command(label="Exit PisA", command=self.closeApplication)
        menu.add_cascade(label="Exit", menu=exit)
        menu.entryconfig("PisA analysis", state="disabled")

    def openFile(self, menu, option_menu, option_menu_var, header_line):
        global input_list

        file = filedialog.askopenfilename(title = "Select phototaxis file",
                                          filetypes = (("text files","*.txt"),("all files","*.*")))
        if(len(file)):
            if(not len(input_list["All"]["path"])):
                menu.entryconfig("PisA analysis", state="normal")
                option_menu.configure(state="normal")
                input_list["All"]["output"] = os.path.dirname(file) + "/"

            file_list = ["Files"]
            for entry in input_list:
                file_list.append(entry)

            file_name = os.path.basename(file)
            input_list["All"]["path"].append(file)
            input_list["All"]["file_names"].append(file_name)
            if(not file_name in file_list):
                input_list[file_name] = {"path": file, "output": os.path.dirname(file) + "/", "pointsize": 3,
                                         "startingpoint": 12, "datanumber": 5, "minutepoint": -1, "period": "Both",
                                         "color": "#000000", "minimum": {"exclude_firstday": False,
                                         "exclude_lastday": True}, "maximum": {"exclude_firstday": True,
                                         "exclude_lastday": False}, "xlabel": "Days", "sg_filter": {"on": False,
                                         "window": 11, "poly": 3, "color": "#800000"}, "pv_points": 1,
                                         "pv_amp_per": 3}
                file_list.append(file_name)
                option_menu.set_menu(*file_list)
                option_menu_var.set(file_name)
                data = pd.read_csv(file, sep="\t", header=int(header_line.get()), encoding="iso-8859-1")
                for column in data:
                    data[column] = data[column].str.replace(",", ".").astype(float)
                    data_int = data[column].astype(int)
                    if(column == "h"):
                        input_list[file_name]["data_per_measurement"] = np.argmax(np.array(data_int > 0))
                        input_list[file_name]["timepoint_indices"] = np.arange(
                                                    input_list[file_name]["data_per_measurement"], len(data[column]),
                                                    input_list[file_name]["data_per_measurement"])
                        input_list[file_name]["data_minutepoints"] = np.unique(
                                                    (60 * (data[column] % 1)).astype(int))[-1]
                        if(input_list[file_name]["data_per_measurement"] < input_list["All"]["data_per_measurement"]):
                            input_list["All"]["data_per_measurement"] = input_list[file_name]["data_per_measurement"]

                        if(len(input_list[file_name]["timepoint_indices"]) <
                                                    len(input_list["All"]["timepoint_indices"]) or
                                                    not len(input_list[file_name]["timepoint_indices"])):
                            input_list["All"]["timepoint_indices"] = input_list[file_name]["timepoint_indices"]

                        if(input_list[file_name]["data_minutepoints"] < input_list["All"]["data_minutepoints"]):
                            input_list["All"]["data_minutepoints"] = input_list[file_name]["data_minutepoints"]

                input_list[file_name]["data"] = data

    def configureColumnWindow(self, option_menu_var):
        column_window = tk.Toplevel(self)
        column_window.wm_title("Comparing columns")

        column_frame = tk.LabelFrame(column_window, text="Columns", borderwidth=2, relief="groove")
        data_columns = None
        if(option_menu_var.get() == "All"):
            data_columns = input_list[option_menu_var.get()]["file_names"]
        else:
            data_columns = [option_menu_var.get()]

        row_frame = None
        set_columns = {}
        for data_index in data_columns:
            column_names = list(input_list[data_index]["data"])[2:]
            for column_index in range(len(column_names)):
                if(column_index % 6 == 0):
                    row_frame = tk.Frame(column_frame)

                column_var = tk.BooleanVar()
                tk.Checkbutton(row_frame, text=" "+column_names[column_index], var=column_var).pack(side="left")
                set_columns[column_names[column_index]] = column_var
                if(column_index % 6 == 0):
                    row_frame.pack(fill="both", expand=1)

        column_frame.pack()

        button_frame = tk.Frame(column_window)
        tk.Button(button_frame, text="Set", command=lambda:
                  self.setColumns(option_menu_var, set_columns)).pack(side="left")
        tk.Button(button_frame, text="Close", command=lambda: self.closeWindow(column_window)).pack(side="left")
        button_frame.pack(fill="both", expand=1, pady=5)

    def configureSettings(self, option_menu_var):
        settings_window = tk.Toplevel(self)
        settings_window.wm_title("Analysis settings")

        general_settings_frame = tk.LabelFrame(settings_window, text="General settings", borderwidth=2,
                                               relief="groove")

        period_frame = tk.Frame(general_settings_frame)
        label_text = tk.StringVar()
        label_text.set("Set period")
        tk.Label(period_frame, textvariable=label_text, height=2).pack(side="left", padx=5)
        period = tk.StringVar()
        ttk.OptionMenu(period_frame, period, *["Period", "Minimum", "Maximum", "Both"]).pack(side="left", padx=30)
        period.set(input_list[option_menu_var.get()]["period"])
        period_frame.pack()

        point_size = self.buildLabelScale(general_settings_frame, "Set point size\nof plot",
                                         input_list[option_menu_var.get()]["pointsize"], 0, 20, 4)
        starting_point = self.buildLabelSpinbox(general_settings_frame, "Set starting point\nof plot",
                                                input_list[option_menu_var.get()]["startingpoint"], 0.1, 3)
        data_number = self.buildLabelScale(general_settings_frame, "Set number of\nused data points",
                                          input_list[option_menu_var.get()]["datanumber"], 0,
                                          input_list[option_menu_var.get()]["data_per_measurement"], 4)
        minute_point = self.buildLabelScale(general_settings_frame, "Set data minute point",
                                           input_list[option_menu_var.get()]["minutepoint"], -1,
                                           input_list[option_menu_var.get()]["data_minutepoints"], 4)

        plot_color = tk.Button(general_settings_frame, text="Set color of plot", command=lambda:
                               self.setPlotColor("Plot color", input_list[option_menu_var.get()]["color"])).pack()
        general_settings_frame.pack(fill="both", expand=1)

        minimum_exclude = self.buildExcludeField(settings_window, "Minimum", " Exclude first day",
                                                 input_list[option_menu_var.get()]["minimum"]["exclude_firstday"],
                                                 " Exclude last day",
                                                 input_list[option_menu_var.get()]["minimum"]["exclude_lastday"])
        maximum_exclude = self.buildExcludeField(settings_window, "Maximum", " Exclude first day",
                                                  input_list[option_menu_var.get()]["maximum"]["exclude_firstday"],
                                                  " Exclude last day",
                                                  input_list[option_menu_var.get()]["maximum"]["exclude_lastday"])

        x_label_frame = tk.LabelFrame(settings_window, text="X-axis label", borderwidth=2, relief="groove")
        x_label = tk.StringVar()
        tk.Radiobutton(x_label_frame, text="Days", variable=x_label, value="Days").pack(side="left", padx=50)
        tk.Radiobutton(x_label_frame, text="Hours", variable=x_label, value="Hours").pack(side="left", padx=50)
        x_label.set(input_list[option_menu_var.get()]["xlabel"])
        x_label_frame.pack(fill="both", expand=1, pady=5)

        sg_frame = tk.LabelFrame(settings_window, text="Sg-Filter", borderwidth=2, relief="groove")
        sg_filter = tk.BooleanVar()
        tk.Checkbutton(sg_frame, text=" Turn filter on", var=sg_filter).pack(side="left", padx=20)
        sg_plot_color = tk.Button(sg_frame, text="Set color of SG-Plot", command=lambda:
                                  self.setPlotColor("SG-Plot color",
                                  input_list[option_menu_var.get()]["sg_filter"]["color"])).pack(side="left")
        sg_frame.pack(fill="both", expand=1, pady=5)

        button_frame = tk.Frame(settings_window)
        tk.Button(button_frame, text="Ok", command=lambda:
                  self.setGeneralSettings(settings_window, option_menu_var, point_size, starting_point, data_number,
                                          minute_point, period, plot_color, minimum_exclude, maximum_exclude, x_label,
                                          sg_filter, sg_plot_color)).pack(side="left", padx=30)
        tk.Button(button_frame, text="Advanced", command=lambda:
                  self.configureAdvancedSettings(settings_window, option_menu_var)).pack(side="left", padx=30)
        tk.Button(button_frame, text="Cancel", command=lambda:
                  self.closeWindow(settings_window)).pack(side="left", padx=30)
        button_frame.pack(fill="both", expand=1, pady=5)

    def configureAdvancedSettings(self, parent_window, option_menu_var):
        advanced_settings_window = tk.Toplevel(parent_window)
        advanced_settings_window.wm_title("Advanced settings")

        peak_valley_frame = tk.LabelFrame(advanced_settings_window, text="Peak-Valley settings", borderwidth=2,
                                          relief="groove")
        peak_valley_points = self.buildLabelSpinbox(peak_valley_frame, "Peak-Valley\ndetection points",
                                                    input_list[option_menu_var.get()]["pv_points"], 1, 3)
        peak_valley_percentage = self.buildLabelSpinbox(peak_valley_frame, "Peak-Valley\namplitude percentage",
                                                        input_list[option_menu_var.get()]["pv_amp_per"], 0.1, 3)
        peak_valley_frame.pack(fill="both", expand=1)

        sg_filter_frame = tk.LabelFrame(advanced_settings_window, text="Savitzky-Golay-Filter settings",
                                        borderwidth=2, relief="groove")
        sg_window_size = self.buildLabelSpinbox(sg_filter_frame, "SG-Filter window size",
                                                input_list[option_menu_var.get()]["sg_filter"]["window"], 1, 2)
        sg_poly_order = self.buildLabelSpinbox(sg_filter_frame, "SG-Filter poly order",
                                               input_list[option_menu_var.get()]["sg_filter"]["poly"], 1, 2)
        sg_filter_frame.pack(fill="both", expand=1, pady=5)

        button_frame = tk.Frame(advanced_settings_window)
        tk.Button(button_frame, text="Ok", command=lambda:
                  self.setAdvancedSettings(advanced_settings_window, option_menu_var,
                  peak_valley_points, peak_valley_percentage,
                  sg_window_size, sg_poly_order)).pack(side="left", padx=70)
        tk.Button(button_frame, text="Cancel", command=lambda:
                  self.closeWindow(advanced_settings_window)).pack(side="left", padx=70)
        button_frame.pack(fill="both", expand=1, pady=5)

    def setColumns(self, option_menu_var, set_columns):
        global input_list

        true_columns = [col for col,val in set_columns.items() if val.get()]
        input_list[option_menu_var.get()]["set_columns"] = true_columns

    def setGeneralSettings(self, window, option_menu_var, point_size, starting_point, data_number, minute_point,
                           period, plot_color, minimum_exclude, maximum_exclude, x_label, sg_filter, sg_plot_color):
        global input_list

        input_list[option_menu_var.get()]["pointsize"] = point_size.get()
        input_list[option_menu_var.get()]["startingpoint"] = starting_point.get()
        input_list[option_menu_var.get()]["datanumber"] = data_number.get()
        input_list[option_menu_var.get()]["minutepoint"] = minute_point.get()
        input_list[option_menu_var.get()]["period"] = period.get()
        input_list[option_menu_var.get()]["color"] = plot_color
        input_list[option_menu_var.get()]["minimum"]["exclude_firstday"] = minimum_exclude[0].get()
        input_list[option_menu_var.get()]["minimum"]["exclude_lastday"] = minimum_exclude[1].get()
        input_list[option_menu_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[0].get()
        input_list[option_menu_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[1].get()
        input_list[option_menu_var.get()]["xlabel"] = x_label.get()
        input_list[option_menu_var.get()]["sg_filter"]["on"] = sg_filter.get()
        input_list[option_menu_var.get()]["sg_filter"]["color"] = sg_plot_color
        window.destroy()

    def setPlotColor(self, text, value):
        plot_color = tkcc.askcolor(initialcolor=value, title=text)[-1]
        return plot_color

    def setAdvancedSettings(self, window, option_menu_var, peak_valley_points, peak_valley_percentage,
                            sg_window_size, sg_poly_order):
        global input_list

        input_list[option_menu_var.get()]["pv_points"] = peak_valley_points.get()
        input_list[option_menu_var.get()]["pv_amp_per"] = peak_valley_percentage.get()
        input_list[option_menu_var.get()]["sg_filter"]["window"] = sg_window_size.get()
        input_list[option_menu_var.get()]["sg_filter"]["poly"] = sg_poly_order.get()
        window.destroy()


    def closeWindow(self, window):
        window.destroy()

    def closeApplication(self):
        exit()

    def buildLabelSpinbox(self, parent_frame, text, value, increment, height):
        frame = tk.Frame(parent_frame)
        label_text = tk.StringVar()
        label_text.set(text)
        tk.Label(frame, textvariable=label_text, height=height).pack(side="left")
        label_spinbox = tk.DoubleVar()
        label_spinbox.set(value)
        tk.Spinbox(frame, from_=0, to=10**9, textvariable=label_spinbox, increment=increment).pack(side="left")
        frame.pack()
        return label_spinbox

    def buildLabelScale(self, parent_frame, text, value, min, max, height):
        frame = tk.Frame(parent_frame)
        label_text = tk.StringVar()
        label_text.set(text)
        tk.Label(frame, textvariable=label_text, height=height).pack(side="left")
        label_scale = tk.Scale(frame, from_=min, to=max, orient="horizontal", relief="groove")
        label_scale.set(value)
        label_scale.pack(side="left")
        frame.pack()
        return label_scale

    def buildExcludeField(self, parent_frame, title, first_label, first_value, second_label, second_value):
        frame = tk.LabelFrame(parent_frame, text=title, borderwidth=2, relief="groove")
        first_var = tk.BooleanVar()
        first_var.set(first_value)
        tk.Checkbutton(frame, text=first_label, var=first_var).pack(side="left", padx=15)
        second_var = tk.BooleanVar()
        second_var.set(second_value)
        tk.Checkbutton(frame, text=second_label, var=second_var).pack(side="left")
        frame.pack(fill="both", expand=1, pady=5)
        return [first_var, second_var]


root = tk.Tk()
root.geometry("380x400")
Application(root)
root.mainloop()
