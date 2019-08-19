if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    import tkinter.colorchooser as tkcc
    import os
    import sys
    import pandas as pd
    import numpy as np
    import phototaxisPlotter
    from functools import partial

    class Application(tk.Frame):

        def __init__(self, master=None):
            self.input_list = dict()
            self.input_list["All"] = {"path": list(), "output": None, "pointsize": 3, "startingpoint": 12,
                                      "datanumber": 5, "minutepoint": -1, "period": "Both", "color": "#000000",
                                      "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                                      "maximum": {"exclude_firstday": True, "exclude_lastday": False},
                                      "xlabel": "Days","sg_filter": {"on": False, "window": 11, "poly": 3,
                                      "color": "#800000"},"pv_points": 1, "pv_amp_per": 3,
                                      "data_per_measurement": sys.maxsize,"timepoint_indices": list(),
                                      "data_minutepoints": sys.maxsize, "file_names": [],"set_columns": dict()}
            tk.Frame.__init__(self, master)
            self.master = master
            self.initWindow()

        def initWindow(self):
            self.progress_frame = tk.LabelFrame(self, text="Analysis progress", borderwidth=2, relief="groove")
            self.progress = tk.DoubleVar()
            ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate", variable=self.progress,
                            length=380).pack()
            self.progress_frame.pack()

            self.master.title("PisA - [P]hototax[is]-[A]nalyzer")
            self.pack(fill="both", expand=1)
            self.files_frame = tk.LabelFrame(self, text="Files", borderwidth=2, relief="groove")
            self.file_options_frame = tk.Frame(self.files_frame)
            self.file_options_var = tk.StringVar()
            self.file_options_var.set("Files")
            self.file_options = ttk.OptionMenu(self.file_options_frame, self.file_options_var, *["Files"],
                           command=lambda _: self.showComparisons())
            self.file_options.pack()
            self.file_options.configure(state="disabled")
            self.file_options_frame.pack()
            self.header_line = self.buildLabelSpinbox(self.files_frame, "Set header line of file", 1, 1, 2)
            self.files_frame.pack(fill="both", expand=0)

            self.canvas = tk.Canvas(self, borderwidth=3, relief="sunken")
            self.info_frame = tk.LabelFrame(self.canvas, borderwidth=0)
            self.info_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self.info_scrollbar.set, scrollregion=self.canvas.bbox("all"))
            self.info_scrollbar.pack(side="right", fill="y")
            self.info_frame.pack(fill="both", expand=1)
            self.canvas.pack(fill="both", expand=1)
            self.canvas.create_window((0,0), window=self.info_frame)
            self.info_frame.bind("<Configure>", self.configureScrollbar)

            self.menu = tk.Menu(self.master)
            self.master.config(menu=self.menu)
            self.file = tk.Menu(self.menu, tearoff=0)
            self.file.add_command(label="Open", command=self.openFile)
            self.file.add_separator()
            self.file.add_command(label="Compare files", command=self.configureFilesWindow)
            self.file.add_command(label="Remove compared files", command=self.configureRemoveFilesWindow)
            self.file.entryconfig("Compare files", state="disabled")
            self.file.entryconfig("Remove compared files", state="disabled")
            self.menu.add_cascade(label="Files", menu=self.file)
            self.pisa = tk.Menu(self.menu, tearoff=0)
            self.pisa.add_command(label="Start analysis", command=lambda:
                             self.startPhotoaxisAnalysis(self.file_options_var, self.menu, self.pisa, self.progress))
            self.pisa.add_command(label="Cancel analysis")
            self.pisa.add_separator()
            self.pisa.add_command(label="Compare columns", command=self.configureColumnWindow)
            self.pisa.add_command(label="Remove compared columns", command=self.configureRemoveColumnsWindow)
            self.pisa.add_separator()
            self.pisa.add_command(label="Settings", command=self.configureSettings)
            self.pisa.entryconfig("Cancel analysis", state="disabled")
            self.menu.add_cascade(label="PisA analysis", menu=self.pisa)
            self.menu.entryconfig("PisA analysis", state="disabled")
            self.exit = tk.Menu(self.menu, tearoff=0)
            self.exit.add_command(label="Exit PisA", command=self.closeApplication)
            self.menu.add_cascade(label="Exit", menu=self.exit)

        def openFile(self):
            file = filedialog.askopenfilename(title = "Select phototaxis file",
                                              filetypes = (("text files","*.txt"),("all files","*.*")))
            if(len(file)):
                if(not len(self.input_list["All"]["file_names"])):
                    self.file.entryconfig("Compare files", state="normal")
                    self.menu.entryconfig("PisA analysis", state="normal")
                    self.pisa.entryconfig("Remove compared columns", state="disabled")
                    self.file_options.configure(state="normal")
                    self.input_list["All"]["output"] = "/".join(os.path.dirname(file).split("/")[:-1]) + "/all/"

                file_options_list = ["Files"] + list(self.input_list.keys())
                file_name = os.path.basename(file)
                if(not file_name in file_options_list):
                    self.file.entryconfig("Remove compared files", state="normal")
                    self.input_list["All"]["file_names"].append(file_name)
                    self.input_list[file_name] = {"path": file, "output": os.path.dirname(file) + "/", "pointsize": 3,
                                             "startingpoint": 12, "datanumber": 5, "minutepoint": -1, "period": "Both",
                                             "color": "#000000", "minimum": {"exclude_firstday": False,
                                             "exclude_lastday": True}, "maximum": {"exclude_firstday": True,
                                             "exclude_lastday": False}, "xlabel": "Days", "sg_filter": {"on": False,
                                             "window": 11, "poly": 3, "color": "#800000"}, "pv_points": 1,
                                             "pv_amp_per": 3, "set_columns": dict(), "file_names": [file_name]}
                    file_options_list.append(file_name)
                    self.file_options.set_menu(*file_options_list)
                    self.file_options_var.set(file_name)
                    data = pd.read_csv(file, sep="\t", header=int(self.header_line.get()), encoding="iso-8859-1")
                    for column in data:
                        data[column] = data[column].str.replace(",", ".").astype(float)
                        data_int = data[column].astype(int)
                        if(column == "h"):
                            self.input_list[file_name]["data_per_measurement"] = np.argmax(np.array(data_int > 0))
                            self.input_list[file_name]["timepoint_indices"] = np.arange(
                                                        self.input_list[file_name]["data_per_measurement"],
                                                        len(data[column]),
                                                        self.input_list[file_name]["data_per_measurement"])
                            self.input_list[file_name]["data_minutepoints"] = np.unique(
                                                        (60 * (data[column] % 1)).astype(int))[-1]
                            if(self.input_list[file_name]["data_per_measurement"] < self.input_list["All"]["data_per_measurement"]):
                                self.input_list["All"]["data_per_measurement"] = self.input_list[file_name]["data_per_measurement"]

                            if(len(self.input_list[file_name]["timepoint_indices"]) <
                                                        len(self.input_list["All"]["timepoint_indices"]) or
                                                        not len(self.input_list[file_name]["timepoint_indices"])):
                                self.input_list["All"]["timepoint_indices"] = self.input_list[file_name]["timepoint_indices"]

                            if(self.input_list[file_name]["data_minutepoints"] < self.input_list["All"]["data_minutepoints"]):
                                self.input_list["All"]["data_minutepoints"] = self.input_list[file_name]["data_minutepoints"]

                    self.input_list[file_name]["data"] = data

                self.showComparisons()

        def startPhotoaxisAnalysis(self):
            self.disableMenus(self.menu, self.pisa)
            files = self.input_list[self.file_options_var.get()]["file_names"]
            for file in files:
                columns = list(self.input_list[file]["data"])[2:]
                pool = mp.Pool(processes=mp.cpu_count())
                pool_map = partial(func, input_list)
                pdf_single_pages = pool.map_async(pool_map, columns)
                pool.close()

                pool.join()

            self.enableMenus(menu, self.pisa)

        def configureFilesWindow(self):
            self.files_window = tk.Toplevel(self)
            self.files_window.wm_title("Comparing files")

            label_frame = tk.Frame(self.files_window)
            label_text = tk.StringVar()
            label_text.set("Set name of group")
            tk.Label(label_frame, textvariable=label_text, height=2).pack(side="left")
            name = tk.StringVar()
            name.set("file group")
            tk.Entry(label_frame, textvariable=name).pack(side="left")
            label_frame.pack(fill="both", expand=1, pady=5)

            file_frame = tk.LabelFrame(self.files_window, text="Files", borderwidth=2, relief="groove")
            set_files = dict()
            for file in list(self.input_list.keys())[1:]:
                row_frame = tk.Frame(file_frame)
                file_var = tk.BooleanVar()
                tk.Checkbutton(row_frame, text=" "+file, var=file_var).pack(side="left")
                set_files[file] = file_var
                row_frame.pack(fill="both", expand=1)

            file_frame.pack()

            button_frame = tk.Frame(self.files_window)
            tk.Button(button_frame, text="Set", command=lambda:
                      self.setFiles(set_files, name)).pack(side="left", padx=30)
            tk.Button(button_frame, text="Close", command=lambda:
                      self.closeWindow(self.files_window)).pack(side="left", padx=30)
            button_frame.pack(fill="both", expand=1, pady=5)

        def configureColumnWindow(self):
            self.column_window = tk.Toplevel(self)
            self.column_window.wm_title("Comparing columns")

            column_frame = tk.LabelFrame(self.column_window, text="Columns", borderwidth=2, relief="groove")
            set_column_data = dict()
            for data_index in self.input_list[self.file_options_var.get()]["file_names"]:
                data_frame = tk.LabelFrame(column_frame, text=data_index, borderwidth=2, relief="groove")
                columns = list(self.input_list[data_index]["data"])[2:]
                set_columns = dict()
                row_frame = None
                for column_index in range(len(columns)):
                    if(column_index % 10 == 0):
                        row_frame = tk.Frame(data_frame)

                    column_var = tk.BooleanVar()
                    tk.Checkbutton(row_frame, text=" "+columns[column_index], var=column_var).pack(side="left")
                    set_columns[columns[column_index]] = column_var
                    if(column_index % 10 == 0):
                        row_frame.pack(fill="both", expand=1)

                set_column_data[data_index] = set_columns
                data_frame.pack(pady=5)

            column_frame.pack()

            button_frame = tk.Frame(self.column_window)
            tk.Button(button_frame, text="Set", command=lambda:
                      self.setColumns(set_column_data)).pack(side="left", padx=30)
            tk.Button(button_frame, text="Close", command=lambda:
                      self.closeWindow(self.column_window)).pack(side="left", padx=30)
            button_frame.pack(fill="both", expand=1, pady=5)

        def configureRemoveFilesWindow(self):
            self.remove_files_window = tk.Toplevel(self)
            self.remove_files_window.wm_title("Remove set files")

            remove_frame = tk.LabelFrame(self.remove_files_window, text="Compared files",
                                         borderwidth=2, relief="groove")
            files = self.input_list[self.file_options_var.get()]["file_names"]
            set_files = dict()
            for file in files:
                file_frame = tk.Frame(remove_frame)
                file_var = tk.BooleanVar()
                tk.Checkbutton(file_frame, text=" "+file, var=file_var).pack(side="left")
                set_files[file] = file_var
                file_frame.pack(fill="both", expand=1)

            remove_frame.pack()

            button_frame = tk.Frame(self.remove_files_window)
            tk.Button(button_frame, text="Set", command=lambda:
                      self.removeFiles(set_files)).pack(side="left", padx=30)
            tk.Button(button_frame, text="Close", command=lambda:
                      self.closeWindow(self.remove_files_window)).pack(side="left", padx=30)
            button_frame.pack(fill="both", expand=1, pady=5)

        def configureRemoveColumnsWindow(self):
            self.remove_columns_window = tk.Toplevel(self)
            self.remove_columns_window.wm_title("Remove set columns")

            remove_frame = tk.LabelFrame(self.remove_columns_window, text="Compared columns",
                                         borderwidth=2, relief="groove")
            files = self.input_list[self.file_options_var.get()]["file_names"]
            set_file_columns = dict()
            for file in files:
                columns = self.input_list[self.file_options_var.get()]["set_columns"][file]
                file_frame = tk.LabelFrame(remove_frame, text=file, borderwidth=2, relief="groove")
                set_columns = dict()
                for column in columns:
                    column_frame = tk.Frame(file_frame)
                    column_var = tk.BooleanVar()
                    tk.Checkbutton(remove_frame, text=" "+column, var=column_var).pack(side="left")
                    set_columns[column] = column_var
                    column_frame.pack()

                set_file_columns[file] = set_columns
                file_frame.pack(pady=5)

            button_frame = tk.Frame(self.remove_columns_window)
            tk.Button(button_frame, text="Set", command=lambda:
                      self.removeColumns(set_columns)).pack(side="left", padx=30)
            tk.Button(button_frame, text="Close", command=lambda:
                      self.closeWindow(self.remove_columns_window)).pack(side="left", padx=30)
            button_frame.pack(fill="both", expand=1, pady=5)

        def configureSettings(self):
            self.settings_window = tk.Toplevel(self)
            self.settings_window.wm_title("Analysis settings")

            self.general_settings_frame = tk.LabelFrame(self.settings_window, text="General settings", borderwidth=2,
                                                   relief="groove")

            period_frame = tk.Frame(self.general_settings_frame)
            label_text = tk.StringVar()
            label_text.set("Amplitude period")
            tk.Label(period_frame, textvariable=label_text, height=2).pack(side="left", padx=5)
            period = tk.StringVar()
            ttk.OptionMenu(period_frame, period, *["Period", "Minimum", "Maximum", "Both"]).pack(side="left", padx=30)
            period.set(self.input_list[self.file_options_var.get()]["period"])
            period_frame.pack()

            point_size = self.buildLabelScale(self.general_settings_frame, "Point size\nof plot",
                                              self.input_list[self.file_options_var.get()]["pointsize"], 0, 20)
            starting_point = self.buildLabelSpinbox(self.general_settings_frame, "Starting point\nof plot",
                                                    self.input_list[self.file_options_var.get()]["startingpoint"],
                                                    0.1, 3)
            data_number = self.buildLabelScale(self.general_settings_frame, "Number of\nused data points",
                                               self.input_list[self.file_options_var.get()]["datanumber"], 0,
                                               self.input_list[self.file_options_var.get()]["data_per_measurement"])
            minute_point = self.buildLabelScale(self.general_settings_frame, "Data minute point",
                                                self.input_list[self.file_options_var.get()]["minutepoint"], -1,
                                                self.input_list[self.file_options_var.get()]["data_minutepoints"])

            plot_color = tk.Button(self.general_settings_frame, text="Color of plot", command=lambda:
                                   self.setPlotColor("Plot color",
                                   self.input_list[self.file_options_var.get()]["color"])).pack()
            self.general_settings_frame.pack(fill="both", expand=1)

            minimum_exclude = self.buildExcludeField(self.settings_window, "Minimum", " Exclude first day",
                                                     self.input_list[self.file_options_var.get()]["minimum"]["exclude_firstday"],
                                                     " Exclude last day",
                                                     self.input_list[self.file_options_var.get()]["minimum"]["exclude_lastday"])
            maximum_exclude = self.buildExcludeField(self.settings_window, "Maximum", " Exclude first day",
                                                     self.input_list[self.file_options_var.get()]["maximum"]["exclude_firstday"],
                                                     " Exclude last day",
                                                     self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"])

            x_label_frame = tk.LabelFrame(self.settings_window, text="X-axis label", borderwidth=2, relief="groove")
            x_label = tk.StringVar()
            tk.Radiobutton(x_label_frame, text="Days", variable=x_label, value="Days").pack(side="left", padx=50)
            tk.Radiobutton(x_label_frame, text="Hours", variable=x_label, value="Hours").pack(side="left", padx=50)
            x_label.set(self.input_list[self.file_options_var.get()]["xlabel"])
            x_label_frame.pack(fill="both", expand=1, pady=5)

            sg_frame = tk.LabelFrame(self.settings_window, text="Sg-Filter", borderwidth=2, relief="groove")
            sg_filter = tk.BooleanVar()
            sg_filter.set(self.input_list[self.file_options_var.get()]["sg_filter"]["on"])
            tk.Checkbutton(sg_frame, text=" Turn filter on", var=sg_filter).pack(side="left", padx=20)
            sg_plot_color = tk.Button(sg_frame, text="Set color of SG-Plot", command=lambda:
                                      self.setPlotColor("SG-Plot color",
                                      self.input_list[self.file_options_var.get()]["sg_filter"]["color"])).pack(side="left")
            sg_frame.pack(fill="both", expand=1, pady=5)

            button_frame = tk.Frame(self.settings_window)
            tk.Button(button_frame, text="Ok", command=lambda:
                      self.setGeneralSettings(point_size, starting_point, data_number,
                                              minute_point, period, plot_color, minimum_exclude, maximum_exclude,
                                              x_label, sg_filter, sg_plot_color)).pack(side="left", padx=30)
            tk.Button(button_frame, text="Advanced",
                      command=self.configureAdvancedSettings).pack(side="left", padx=30)
            tk.Button(button_frame, text="Cancel",
                      command=lambda: self.closeWindow(self.settings_window)).pack(side="left", padx=30)
            button_frame.pack(fill="both", expand=1, pady=5)

        def configureAdvancedSettings(self):
            self.advanced_settings_window = tk.Toplevel(self.settings_window)
            self.advanced_settings_window.wm_title("Advanced settings")

            self.peak_valley_frame = tk.LabelFrame(self.advanced_settings_window, text="Peak-Valley settings",
                                              borderwidth=2, relief="groove")
            peak_valley_points = self.buildLabelSpinbox(self.peak_valley_frame, "Peak-Valley\ndetection points",
                                                        self.input_list[self.file_options_var.get()]["pv_points"],
                                                        1, 3)
            peak_valley_percentage = self.buildLabelSpinbox(self.peak_valley_frame, "Peak-Valley\namplitude percentage",
                                                            self.input_list[self.file_options_var.get()]["pv_amp_per"],
                                                            0.1, 3)
            self.peak_valley_frame.pack(fill="both", expand=1)

            self.sg_filter_frame = tk.LabelFrame(self.advanced_settings_window, text="Savitzky-Golay-Filter settings",
                                            borderwidth=2, relief="groove")
            sg_window_size = self.buildLabelSpinbox(self.sg_filter_frame, "SG-Filter window size",
                                                    self.input_list[self.file_options_var.get()]["sg_filter"]["window"],
                                                    1, 2)
            sg_poly_order = self.buildLabelSpinbox(self.sg_filter_frame, "SG-Filter poly order",
                                                   self.input_list[self.file_options_var.get()]["sg_filter"]["poly"],
                                                   1, 2)
            self.sg_filter_frame.pack(fill="both", expand=1, pady=5)

            button_frame = tk.Frame(self.advanced_settings_window)
            tk.Button(button_frame, text="Ok", command=lambda:
                      self.setAdvancedSettings(peak_valley_points, peak_valley_percentage,
                                               sg_window_size, sg_poly_order)).pack(side="left", padx=70)
            tk.Button(button_frame, text="Cancel", command=lambda:
                      self.closeWindow(self.advanced_settings_window)).pack(side="left", padx=70)
            button_frame.pack(fill="both", expand=1, pady=5)

        def setFiles(self, set_files, name):
            if(name.get() and not name.get() in self.input_list):
                file_list = ["Files"] + list(self.input_list.keys()) + [name.get()]
                data_per_measurement = sys.maxsize
                timepoint_indices = list()
                data_minutepoints = sys.maxsize
                for entry in self.input_list:
                    if(data_per_measurement < self.input_list[entry]["data_per_measurement"]):
                        data_per_measurement = self.input_list[entry]["data_per_measurement"]

                    if(len(timepoint_indices) < len(self.input_list[entry]["timepoint_indices"])):
                        timepoint_indices = self.input_list[entry]["timepoint_indices"]

                    if(data_minutepoints < self.input_list[entry]["data_minutepoints"]):
                        data_minutepoints = self.input_list[entry]["data_minutepoints"]

                true_files = list()
                none_chosen = True
                for file,val in set_files.items():
                    if(val.get()):
                        true_files.append(file)
                        val.set(False)
                        none_chosen = False

                if(not none_chosen):
                    self.input_list[name.get()] = {"path": list(), "output": None, "pointsize": 3,
                                                   "startingpoint": 12,"datanumber": 5, "minutepoint": -1,
                                                   "period": "Both", "color": "#000000",
                                                   "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                                                   "maximum": {"exclude_firstday": True, "exclude_lastday": False},
                                                   "xlabel": "Days", "sg_filter": {"on": False, "window": 11,
                                                   "poly": 3,"color": "#800000"}, "pv_points": 1, "pv_amp_per": 3,
                                                   "data_per_measurement": data_per_measurement,
                                                   "timepoint_indices": timepoint_indices,
                                                   "data_minutepoints": data_minutepoints,
                                                   "file_names": true_files,"set_columns": dict()}
                    self.file_options.set_menu(*file_list)
                    self.file_options_var.set(name.get())
                    self.file.entryconfig("Remove compared files", state="normal")
                    self.showComparisons()

        def setColumns(self, set_column_data):
            chosen_list = list()
            for file,data in set_column_data.items():
                true_columns = list()
                none_chosen = True
                for col,val in data.items():
                    if(val.get()):
                        true_columns.append(col)
                        val.set(False)
                        none_chosen = False

                chosen_list.append(none_chosen)
                if(not none_chosen):
                    if(not file in self.input_list[self.file_options_var.get()]["set_columns"]):
                        self.input_list[self.file_options_var.get()]["set_columns"][file] = list()

                    self.input_list[self.file_options_var.get()]["set_columns"][file].append(" - ".join(true_columns))

            if(len(chosen_list) and not all(chosen_list)):
                self.showComparisons()

        def removeFiles(self, files):
            if(len(list(files.keys()))):
                for file,val in files.items():
                    if(val.get()):
                        self.input_list[self.file_options_var.get()]["file_names"].remove(file)
                        if(self.file_options_var.get() in self.input_list["All"]["file_names"]):
                            self.input_list["All"]["file_names"].remove(file)
                        elif(self.file_options_var.get() == "All"):
                            self.input_list.pop(file, None)

                all_deleted = False
                if(not len(self.input_list[self.file_options_var.get()]["file_names"])):
                    if(self.file_options_var.get() != "All"):
                        self.input_list.pop(self.file_options_var.get(), None)
                        file_list = ["Files"] + list(self.input_list.keys())
                        self.file_options.set_menu(*file_list)
                        self.file_options_var.set("All")
                    else:
                        self.file_options.set_menu(*["Files"])
                        self.file_options.configure(state="disabled")
                        self.file.entryconfig("Compare files", state="disabled")
                        self.file.entryconfig("Remove compared files", state="disabled")
                        self.menu.entryconfig("PisA analysis", state="disabled")
                        all_deleted = True
                        for child in self.info_frame.winfo_children():
                            child.pack_forget()

                elif(self.file_options_var.get() == "All"):
                    file_list = ["Files", "All"] + self.input_list["All"]["file_names"]
                    self.file_options.set_menu(*file_list)
                    self.file_options_var.set("All")

                if(not all_deleted):
                    self.showComparisons()

                self.closeWindow(self.remove_files_window)

        def removeColumns(self, columns):
            if(len(list(columns.keys()))):
                for file,data in columns.items():
                    empty = False
                    column_list = self.input_list[self.file_options_var.get()]["set_columns"]
                    for col,var in data.items():
                        if(val.get()):
                            column_list[file].remove(col)
                            if(not len(column_list[file])):
                                column_list.pop(file, None)
                                empty =True

                if(not empty):
                    self.showComparisons()
                else:
                    for child in self.info_frame.winfo_children():
                        child.destroy()

                self.closeWindow(self.remove_columns_window)


        def showComparisons(self):
            for child in self.info_frame.winfo_children():
                child.pack_forget()

            frame = tk.Frame(self.info_frame)
            label_frame = tk.Frame(frame)
            label_text = tk.StringVar()
            label_text.set("Compared files:")
            tk.Label(label_frame, textvariable=label_text, height=2).pack(side="left")
            label_frame.pack(fill="both", expand=1)
            list_frame = tk.Frame(frame)
            files = self.input_list[self.file_options_var.get()]["file_names"]
            for file in files:
                file_frame = tk.Frame(list_frame)
                file_text = tk.StringVar()
                file_text.set("  " + file)
                tk.Label(file_frame, textvariable=file_text).pack(side="left")
                file_frame.pack(fill="both", expand=1)
                columns = self.input_list[self.file_options_var.get()]["set_columns"]
                if(file in columns):
                    column_label_frame = tk.Frame(list_frame)
                    label_column_text = tk.StringVar()
                    label_column_text.set("   Compared columns:")
                    tk.Label(column_label_frame, textvariable=label_column_text).pack(side="left")
                    column_label_frame.pack(fill="both", expand=1)
                    for column in columns[file]:
                        col_frame = tk.Frame(list_frame)
                        col_text = tk.StringVar()
                        col_text.set("    -> " + column)
                        tk.Label(col_frame, textvariable=col_text).pack(side="left")
                        col_frame.pack(fill="both", expand=1)

            list_frame.pack()
            frame.pack(side="left")


        def setGeneralSettings(self, point_size, starting_point, data_number, minute_point,
                               period, plot_color, minimum_exclude, maximum_exclude, x_label, sg_filter,
                               sg_plot_color):
            global input_list

            self.input_list[self.file_options_var.get()]["pointsize"] = point_size.get()
            self.input_list[self.file_options_var.get()]["startingpoint"] = starting_point.get()
            self.input_list[self.file_options_var.get()]["datanumber"] = data_number.get()
            self.input_list[self.file_options_var.get()]["minutepoint"] = minute_point.get()
            self.input_list[self.file_options_var.get()]["period"] = period.get()
            self.input_list[self.file_options_var.get()]["color"] = plot_color
            self.input_list[self.file_options_var.get()]["minimum"]["exclude_firstday"] = minimum_exclude[0].get()
            self.input_list[self.file_options_var.get()]["minimum"]["exclude_lastday"] = minimum_exclude[1].get()
            self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[0].get()
            self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[1].get()
            self.input_list[self.file_options_var.get()]["xlabel"] = x_label.get()
            self.input_list[self.file_options_var.get()]["sg_filter"]["on"] = sg_filter.get()
            self.input_list[self.file_options_var.get()]["sg_filter"]["color"] = sg_plot_color
            self.settings_window.destroy()

        def setPlotColor(self, text, value):
            plot_color = tkcc.askcolor(initialcolor=value, title=text)[-1]
            return plot_color

        def setAdvancedSettings(self, peak_valley_points, peak_valley_percentage, sg_window_size, sg_poly_order):
            self.input_list[self.file_options_var.get()]["pv_points"] = peak_valley_points.get()
            self.input_list[self.file_options_var.get()]["pv_amp_per"] = peak_valley_percentage.get()
            self.input_list[self.file_options_var.get()]["sg_filter"]["window"] = sg_window_size.get()
            self.input_list[self.file_options_var.get()]["sg_filter"]["poly"] = sg_poly_order.get()
            self.advanced_settings_window.destroy()

        def checkComparedColumns(self):
            if(len(self.input_list[self.file_options_var.get()]["set_columns"])):
                self.pisa.entryconfig("Remove compared columns", state="normal")
            else:
                self.pisa.entryconfig("Remove compared columns", state="disabled")

        def closeWindow(self, window):
            window.destroy()

        def closeApplication(self):
            exit()

        def enableMenus(self):
            self.menu.entryconfig("Files", state="normal")
            self.pisa.entryconfig("Start analysis", state="normal")
            self.pisa.entryconfig("Cancel analysis", state="disabled")
            self.pisa.entryconfig("Compare columns", state="normal")
            self.pisa.entryconfig("Remove compared columns", state="normal")
            self.pisa.entryconfig("Settings", state="normal")
            self.menu.entryconfig("Exit", state="normal")

        def disableMenus(self, menu):
            menu.entryconfig("Files", state="disabled")
            self.pisa.entryconfig("Start analysis", state="disabled")
            self.pisa.entryconfig("Cancel analysis", state="normal")
            self.pisa.entryconfig("Compare columns", state="disabled")
            self.pisa.entryconfig("Remove compared columns", state="disabled")
            self.pisa.entryconfig("Settings", state="disabled")
            menu.entryconfig("Exit", state="disabled")

        def buildLabelSpinbox(self, parent_frame, text, value, increment, height):
            frame = tk.Frame(parent_frame)
            label_text = tk.StringVar()
            label_text.set(text)
            tk.Label(frame, textvariable=label_text, height=height).pack(side="left")
            label_spinbox = tk.DoubleVar()
            label_spinbox.set(value)
            tk.Spinbox(frame, from_=0, to=10**6, textvariable=label_spinbox, increment=increment).pack(side="left")
            frame.pack()
            return label_spinbox

        def buildLabelScale(self, parent_frame, text, value, min, max):
            frame = tk.Frame(parent_frame)
            label_text = tk.StringVar()
            label_text.set(text)
            tk.Label(frame, textvariable=label_text, height=4).pack(side="left")
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

        def configureScrollbar(self, event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    root = tk.Tk()
    root.geometry("380x400")
    Application(root)
    root.mainloop()
