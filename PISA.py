if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    import tkinter.colorchooser as tkcc
    import os
    import sys
    import pandas as pd
    import numpy as np
    import phototaxisPlotter
    from functools import partial
    import subprocess
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from PIL import ImageTk, Image
    import traceback

    class LoadingScreen(tk.Toplevel):

        def __init__(self, parent):
            tk.Toplevel.__init__(self, parent)
            self.title("Loading screen")
            try:
                loading_image = None
                try:
                    loading_image = ImageTk.PhotoImage(Image.open("../../icon/loading_sun.png"))
                except:
                    loading_image = root.iconbitmap("icon/loading_sun.png")

                tk.Label(self, image=loading_image).pack(side="bottom", fill="both", expand="yes")
            except:
                self.geometry("210x210")
                loading_text = tk.StringVar()
                loading_text.set("<Unable\n\nto display\n\nloading image!>\n\nLoading\napplication...")
                label = tk.Label(self, textvariable=loading_text)
                label.config(font=("Courier", 18))
                label.pack(side="bottom", fill="both", expand="yes")

            self.update()

    class Application(tk.Frame):

        def __init__(self, master=None):
            self.input_list = {}
            self.input_list["All"] = {"file_names": [], "path": [], "output": None, "pointsize": 3, "startingpoint": 12,
                                      "datanumber": 5, "minutepoint": -1, "period": "Both", "color": "#000000",
                                      "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                                      "maximum": {"exclude_firstday": True, "exclude_lastday": False},
                                      "xlabel": "Days","sg_filter": {"on": False, "window": 11, "poly": 3,
                                      "color": "#800000"},"pv_points": 1, "pv_amp_per": 3,
                                      "data_per_measurement": sys.maxsize, "timepoint_indices": [],
                                      "data_minutepoints": sys.maxsize, "set_columns": {}, "dn_cycle": {"on": True,
                                      "background": "#929591", "visibility": 50}, "set_settings": False,
                                      "merge_plots": {"on": True, "threshold": 3.5, "color": "#000000"}}
            tk.Frame.__init__(self, master)
            self.master = master
            self.manager = mp.Manager()
            self.progress = self.manager.Value("i", 0.0)
            self.lock = self.manager.Lock()
            self.log_list = []
            self.columns_index_list = {"All": 1}
            self.cancel_analysis = False
            self.initWindow()

        def initWindow(self):
            self.progress_frame = tk.LabelFrame(self, text="Analysis progress", borderwidth=2, relief="groove")
            self.progressbar = tk.DoubleVar()
            ttk.Progressbar(self.progress_frame, orient="horizontal", mode="determinate", variable=self.progressbar,
                            length=380, style="green.Horizontal.TProgressbar").pack()
            self.progress_frame.pack()

            self.master.title("PISA - [P]hototax[IS]-[A]nalyzer")
            self.pack(fill="both", expand=1)
            self.files_frame = tk.LabelFrame(self, text="Files", borderwidth=2, relief="groove")
            self.file_options_frame = tk.Frame(self.files_frame)
            self.file_options_var = tk.StringVar()
            self.file_options_var.set("Files")
            self.file_options = ttk.OptionMenu(self.file_options_frame, self.file_options_var, *["Files"],
                                               command=self.checkComparedColumns)
            self.file_options.pack()
            self.file_options.configure(state="disabled")
            self.file_options_frame.pack()
            self.header_line = self.buildLabelSpinbox(self.files_frame, "Set header line of file", 1, 1, 2)
            self.files_frame.pack(fill="both", expand=0)

            self.status_frame = tk.Frame(self, borderwidth=2, relief="groove")
            self.status_var = tk.StringVar()
            self.status_var.set("Status:")
            tk.Label(self.status_frame, textvariable=self.status_var).pack(side="left")
            self.status_frame.pack(fill="both", expand=0)

            self.canvas = tk.Canvas(self, borderwidth=3, relief="sunken")
            self.info_frame = tk.LabelFrame(self.canvas, borderwidth=0)
            self.x_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self.x_scrollbar.set, scrollregion=self.canvas.bbox("all"))
            self.x_scrollbar.pack(side="bottom", fill="x")
            self.y_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self.y_scrollbar.set, scrollregion=self.canvas.bbox("all"))
            self.y_scrollbar.pack(side="right", fill="y")
            self.info_frame.pack(fill="both", expand=1)
            self.canvas.pack(fill="both", expand=1)
            self.canvas.create_window((0,0), window=self.info_frame)
            self.info_frame.bind("<Configure>", self.configureMainScrollbar)

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
            self.pisa.add_command(label="Start analysis", command=self.startPhotoaxisAnalysis)
            self.pisa.add_command(label="Cancel analysis", command=self.cancelAnalysis)
            self.pisa.add_separator()
            self.pisa.add_command(label="Compare columns", command=self.configureColumnWindow)
            self.pisa.add_command(label="Remove compared columns", command=self.configureRemoveColumnsWindow)
            self.pisa.add_separator()
            self.pisa.add_command(label="Settings", command=self.configureSettings)
            self.pisa.entryconfig("Cancel analysis", state="disabled")
            self.menu.add_cascade(label="PISA analysis", menu=self.pisa)
            self.menu.entryconfig("PISA analysis", state="disabled")
            self.exit = tk.Menu(self.menu, tearoff=0)
            self.exit.add_command(label="Exit PISA", command=self.closeApplication)
            self.menu.add_cascade(label="Exit", menu=self.exit)


        def openFile(self):
            file_name = None
            try:
                file = filedialog.askopenfilename(title = "Select phototaxis file",
                                                  filetypes = (("text files","*.txt"),("all files","*.*")))
                if(len(file)):
                    if(not len(self.input_list["All"]["file_names"])):
                        self.file.entryconfig("Compare files", state="normal")
                        self.menu.entryconfig("PISA analysis", state="normal")
                        self.pisa.entryconfig("Remove compared columns", state="disabled")
                        self.file_options.configure(state="normal")
                        self.input_list["All"]["output"] = "/".join(os.path.dirname(file).split("/")[:-1]) + "/all/"

                    file_options_list = ["Files"] + list(self.input_list.keys())
                    file_name = ".".join(os.path.basename(file).split(".")[:-1])
                    if(not file_name in file_options_list):
                        self.file.entryconfig("Remove compared files", state="normal")
                        self.input_list["All"]["file_names"].append(file_name)
                        self.input_list["All"]["path"].append(file)
                        self.columns_index_list[file_name] = 1
                        self.input_list[file_name] = {"file_names": [file_name], "path": [file], "output": os.path.dirname(file) + "/",
                                                      "pointsize": 3, "startingpoint": 12, "datanumber": 5,
                                                      "minutepoint": -1, "period": "Both", "color": "#000000",
                                                      "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                                                      "maximum": {"exclude_firstday": True, "exclude_lastday": False},
                                                      "xlabel": "Days", "sg_filter": {"on": False, "window": 11, "poly": 3,
                                                      "color": "#800000"}, "pv_points": 1, "pv_amp_per": 3, "dn_cycle": {"on": True,
                                                      "background": "#929591", "visibility": 50}, "set_columns": {}, "set_settings": False,
                                                      "merge_plots": {"on": True, "threshold": 3.5, "color": "#000000"}}
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
                                                            len(self.input_list["All"]["timepoint_indices"])):
                                    self.input_list["All"]["timepoint_indices"] = self.input_list[file_name]["timepoint_indices"]

                                if(self.input_list[file_name]["data_minutepoints"] < self.input_list["All"]["data_minutepoints"]):
                                    self.input_list["All"]["data_minutepoints"] = self.input_list[file_name]["data_minutepoints"]

                        self.input_list[file_name]["data"] = data
                    else:
                        messagebox.showerror("File loading error", "A file with the same name is already loaded.")

                    self.showComparisons()
            except Exception:
                file_name_var = tk.BooleanVar()
                file_name_var.set(True)
                self.remove_files_window = tk.Toplevel(self)
                error_output = self.input_list[file_name]["output"]
                self.removeFiles({file_name: file_name_var})
                self.showErrorWindow("File error", "An error occurred while opening a file. The file is most likely just in a wrong/unknown format."
                                     " Check the file and try again or open a new file.", traceback.format_exc(), error_output)

        def startPhotoaxisAnalysis(self):
            self.disableMenus()
            self.progress.value = 0.0
            files = self.input_list[self.file_options_var.get()]["file_names"]
            progress_end = 0
            for file in files:
                progress_end += len(list(self.input_list[file]["data"])[2:])

            for file,column_set in self.input_list[self.file_options_var.get()]["set_columns"].items():
                progress_end += len(column_set)

            if(len(list(self.input_list[self.file_options_var.get()]["set_columns"].keys())) and self.input_list[self.file_options_var.get()]["merge_plots"]["on"]):
                num_data_points = len(self.input_list[files[0]]["data"][list(self.input_list[files[0]]["data"])[2:][0]])
                for file in files:
                    current_num_data_points = len(self.input_list[file]["data"][list(self.input_list[file]["data"])[2:][0]])
                    if(num_data_points != current_num_data_points):
                        error_output = self.input_list[self.file_options_var.get()]["output"]
                        self.showErrorWindow("Analysis error", "An error occurred while initializing the analysis.\n"
                                             "To fix the problem, change files or turn off the 'Merge set plots/columns' option.",
                                             "The file '" + file + "' has a different number of data points than the rest of the files.\n"
                                             "Previous number of data points: " + str(num_data_points) + "\n"
                                             "'" + file + "' number of data points: " + str(current_num_data_points),
                                             error_output)
                        self.cancel_analysis = True
                        break

                progress_end += len(self.input_list[files[0]]["data"][list(self.input_list[files[0]]["data"])[2:][0]]) / self.input_list[files[0]]["data_per_measurement"]


            pool = mp.Pool(processes=1)
            pool_map = partial(phototaxisPlotter.plotData, input_list=self.input_list, progress=self.progress,
                               highest_columns_index=self.columns_index_list[self.file_options_var.get()], lock=self.lock)
            single_plots_pdf = pool.map_async(pool_map, [self.file_options_var.get()])
            pool.close()
            error = False
            while(self.progress.value != progress_end):
                if(self.cancel_analysis or single_plots_pdf.ready()):
                    pool.terminate()
                    error = True
                    break

                if(self.progress.value == 0):
                    self.status_var.set("Status: Starting threads...")
                else:
                    self.status_var.set("Status: Analyzing...")

                self.progressbar.set(self.progress.value * (100/progress_end))
                self.update()

            self.progressbar.set(self.progress.value * (100/progress_end))
            pool.join()
            self.status_var.set("Status: Analysis finished/stopped.")
            self.enableMenus()
            if(not self.cancel_analysis and (not error or single_plots_pdf.get()[0] == None)):
                self.status_var.set("Status: Analysis finished.")
                if(os.name == "nt"):
                    os.startfile(self.input_list[self.file_options_var.get()]["output"])
                else:
                    subprocess.call(["xdg-open", self.input_list[self.file_options_var.get()]["output"]])

                del self.log_list[:]
                if(self.input_list[self.file_options_var.get()]["set_settings"]):
                    self.getLogStats(self.file_options_var.get())
                else:
                    for file in self.input_list[self.file_options_var.get()]["file_names"]:
                        self.getLogStats(file)

                with open(self.input_list[self.file_options_var.get()]["output"] + "log.txt", "w") as log_writer:
                    log_writer.write("#Log file of group: " + self.file_options_var.get() + "\n" + "\n".join(self.log_list))
            elif(not self.cancel_analysis and error and single_plots_pdf.get()[0] != None):
                self.status_var.set("Status: Error during analysis.")
                self.showErrorWindow("Analysis error", "An error occurred while running the analysis.",
                                     single_plots_pdf.get()[0], self.input_list[self.file_options_var.get()]["output"])
                error = False
            elif(self.cancel_analysis):
                self.status_var.set("Status: Analysis canceled.")
                self.cancel_analysis = False

        def configureFilesWindow(self):
            self.files_window = tk.Toplevel(self)
            self.files_window.wm_title("Comparing files")
            self.files_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.files_window, text="",
                                    borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Set", command=lambda:
                      self.setFiles(set_files, name)).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Close", command=self.files_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

            label_frame = tk.Frame(self.files_window)
            label_text = tk.StringVar()
            label_text.set("Set name of group")
            tk.Label(label_frame, textvariable=label_text, height=2).pack(side="left")
            name = tk.StringVar()
            name.set("file group")
            tk.Entry(label_frame, textvariable=name).pack(side="left")
            label_frame.pack(fill="both", expand=1, pady=5)

            file_frame = tk.LabelFrame(self.files_window, text="Files", borderwidth=2, relief="groove")
            set_files = {}
            for file in list(self.input_list.keys())[1:]:
                row_frame = tk.Frame(file_frame)
                file_var = tk.BooleanVar()
                tk.Checkbutton(row_frame, text=" "+file, var=file_var).pack(side="left")
                set_files[file] = file_var
                row_frame.pack(fill="both", expand=1)

            file_frame.pack()

        def configureColumnWindow(self):
            self.column_window = tk.Toplevel(self)
            self.column_window.wm_title("Comparing columns")
            self.column_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.column_window, text="",
                                    borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Set", command=lambda:
                      self.setColumns(set_column_data)).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Close", command=self.column_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

            self.column_canvas = tk.Canvas(self.column_window)
            column_frame = tk.LabelFrame(self.column_canvas, text="Columns", borderwidth=2, relief="groove")
            set_column_data = {}
            for data_index in self.input_list[self.file_options_var.get()]["file_names"]:
                data_frame = tk.LabelFrame(column_frame, text=data_index, borderwidth=2, relief="groove")
                columns = list(self.input_list[data_index]["data"])[2:]
                set_columns = {}
                row_frame = None
                for column_index in range(len(columns)):
                    if(column_index % 8 == 0):
                        row_frame = tk.Frame(data_frame)

                    column_var = tk.BooleanVar()
                    tk.Checkbutton(row_frame, text=" "+columns[column_index], var=column_var).pack(side="left")
                    set_columns[columns[column_index]] = column_var
                    if(column_index % 10 == 0):
                        row_frame.pack(fill="both", expand=1)

                set_column_data[data_index] = set_columns
                data_frame.pack(anchor="w", pady=5)

            column_scrollbar = tk.Scrollbar(self.column_window, orient="vertical", command=self.column_canvas.yview)
            self.column_canvas.configure(yscrollcommand=column_scrollbar.set, scrollregion=self.column_canvas.bbox("all"))
            column_scrollbar.pack(side="right", fill="y")
            column_frame.pack(fill="both", expand=1)
            self.column_canvas.pack(fill="both", expand=1)
            self.column_canvas.create_window((0,0), window=column_frame)
            column_frame.bind("<Configure>", self.configureComparingColumnsScrollbar)
            self.column_canvas.update()
            self.column_canvas.yview_moveto(0)
            width = 400 if column_frame.winfo_width()+20 > 400 else column_frame.winfo_width()+20
            height = 210 if column_frame.winfo_height()+50 > 210 else column_frame.winfo_height()+50
            self.column_window.geometry(str(width) + "x" + str(height))

        def configureRemoveFilesWindow(self):
            self.remove_files_window = tk.Toplevel(self)
            self.remove_files_window.wm_title("Remove set files")
            self.remove_files_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.remove_files_window, text="",
                                    borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Set", command=lambda:
                      self.removeFiles(set_files)).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Close", command=self.remove_files_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

            remove_frame = tk.LabelFrame(self.remove_files_window, text="Compared files",
                                         borderwidth=2, relief="groove")
            files = self.input_list[self.file_options_var.get()]["file_names"]
            set_files = {}
            for file in files:
                file_frame = tk.Frame(remove_frame)
                file_var = tk.BooleanVar()
                tk.Checkbutton(file_frame, text=" "+file, var=file_var).pack(side="left")
                set_files[file] = file_var
                file_frame.pack(fill="both", expand=1)

            remove_frame.pack()

        def configureRemoveColumnsWindow(self):
            self.remove_columns_window = tk.Toplevel(self)
            self.remove_columns_window.wm_title("Remove set columns")
            self.remove_columns_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.remove_columns_window, text="",
                                    borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Set", command=lambda:
                      self.removeColumns(set_file_columns)).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Close", command=self.remove_columns_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

            self.remove_canvas = tk.Canvas(self.remove_columns_window)
            remove_frame = tk.LabelFrame(self.remove_canvas, text="Compared columns",
                                         borderwidth=2, relief="groove")
            files = list(self.input_list[self.file_options_var.get()]["set_columns"].keys())
            set_file_columns = {}
            for file in files:
                columns = self.input_list[self.file_options_var.get()]["set_columns"][file]
                file_frame = tk.LabelFrame(remove_frame, text=file, borderwidth=2, relief="groove")
                set_columns = {}
                for column in columns:
                    column_frame = tk.Frame(file_frame)
                    column_var = tk.BooleanVar()
                    tk.Checkbutton(column_frame, text=" "+column, var=column_var).pack(side="left")
                    set_columns[column] = column_var
                    column_frame.pack(fill="both", expand=1)

                set_file_columns[file] = set_columns
                file_frame.pack(anchor="w", pady=5)

            remove_x_scrollbar = tk.Scrollbar(self.remove_columns_window, orient="horizontal", command=self.remove_canvas.xview)
            self.remove_canvas.configure(yscrollcommand=remove_x_scrollbar.set, scrollregion=self.remove_canvas.bbox("all"))
            remove_x_scrollbar.pack(side="bottom", fill="x")
            remove_y_scrollbar = tk.Scrollbar(self.remove_columns_window, orient="vertical", command=self.remove_canvas.yview)
            self.remove_canvas.configure(yscrollcommand=remove_y_scrollbar.set, scrollregion=self.remove_canvas.bbox("all"))
            remove_y_scrollbar.pack(side="right", fill="y")
            remove_frame.pack(fill="both", expand=1)
            self.remove_canvas.pack(fill="both", expand=1)
            self.remove_canvas.create_window((0,0), window=remove_frame)
            remove_frame.bind("<Configure>", self.configureRemoveColumnsScrollbar)
            self.remove_canvas.update()
            self.remove_canvas.xview_moveto(0)
            self.remove_canvas.yview_moveto(0)
            width = 370 if remove_frame.winfo_width()+20 > 370 else remove_frame.winfo_width()+20
            height = 210 if remove_frame.winfo_height()+50 > 210 else remove_frame.winfo_height()+50
            self.remove_columns_window.geometry(str(width) + "x" + str(height))

        def configureSettings(self):
            self.settings_window = tk.Toplevel(self)
            self.settings_window.wm_title("Analysis settings")
            self.settings_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.settings_window, text="",
                                         borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Ok", command=lambda:
                      self.setGeneralSettings(point_size, starting_point, data_number, minute_point,
                                              period, minimum_exclude, maximum_exclude, x_label, sg_filter,
                                              dn_cycle, visibility, merge_setting, merge_threshold, set_settings)
                                              ).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Advanced",
                      command=self.configureAdvancedSettings).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Cancel",
                      command=self.settings_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

            self.settings_canvas = tk.Canvas(self.settings_window)
            self.settings_frame = tk.Frame(self.settings_canvas)
            self.general_settings_frame = tk.LabelFrame(self.settings_frame, text="General settings",
                                                        borderwidth=2, relief="groove")

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

            tk.Button(self.general_settings_frame, text="Color of plot", command=lambda:
                      self.setPlotColor(1)).pack()
            self.general_settings_frame.pack(fill="both", expand=1)

            minimum_exclude = self.buildExcludeField(self.settings_frame, "Minimum", " Exclude first day",
                                                     self.input_list[self.file_options_var.get()]["minimum"]["exclude_firstday"],
                                                     " Exclude last day",
                                                     self.input_list[self.file_options_var.get()]["minimum"]["exclude_lastday"])
            maximum_exclude = self.buildExcludeField(self.settings_frame, "Maximum", " Exclude first day",
                                                     self.input_list[self.file_options_var.get()]["maximum"]["exclude_firstday"],
                                                     " Exclude last day",
                                                     self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"])

            x_label_frame = tk.LabelFrame(self.settings_frame, text="X-axis label", borderwidth=2, relief="groove")
            x_label = tk.StringVar()
            tk.Radiobutton(x_label_frame, text="Days", variable=x_label, value="Days").pack(side="left", padx=50)
            tk.Radiobutton(x_label_frame, text="Hours", variable=x_label, value="Hours").pack(side="left", padx=50)
            x_label.set(self.input_list[self.file_options_var.get()]["xlabel"])
            x_label_frame.pack(fill="both", expand=1, pady=5)

            cycle_frame = tk.LabelFrame(self.settings_frame, text="Color day-night cycle", borderwidth=2, relief="groove")
            background_frame = tk.Frame(cycle_frame)
            dn_cycle = tk.BooleanVar()
            dn_cycle.set(self.input_list[self.file_options_var.get()]["dn_cycle"]["on"])
            tk.Checkbutton(background_frame, text=" Turn background color on", var=dn_cycle).pack(side="left", padx=35)
            background_frame.pack(fill="both", expand=1, pady=5)
            background_color_frame = tk.Frame(cycle_frame)
            tk.Button(background_color_frame, text="Set color of background", command=lambda:
                      self.setPlotColor(2)).pack(side="left", padx=35)
            background_color_frame.pack(fill="both", expand=1, pady=5)
            visibility_frame = tk.Frame(cycle_frame)
            visibility = self.buildLabelScale(visibility_frame, "Opacity of background",
                                              self.input_list[self.file_options_var.get()]["dn_cycle"]["visibility"],
                                              0, 100)
            visibility_frame.pack(fill="both", expand=1, pady=5)
            cycle_frame.pack(fill="both", expand=1, pady=5)

            merge_frame = tk.LabelFrame(self.settings_frame, text="Merge compared plots", borderwidth=2, relief="groove")
            merge_settings = tk.Frame(merge_frame)
            merge_setting = tk.BooleanVar()
            merge_setting.set(self.input_list[self.file_options_var.get()]["merge_plots"]["on"])
            tk.Checkbutton(merge_settings, text=" Merge set plots/columns", var=merge_setting).pack(side="left", padx=20)
            tk.Button(merge_settings, text="Color of merged plot", command=lambda:
                      self.setPlotColor(3)).pack(side="left")
            merge_settings.pack(fill="both", expand=1, pady=5)
            merge_threshold_frame = tk.Frame(merge_frame)
            merge_threshold = self.buildLabelSpinbox(merge_threshold_frame, "Threshold for outliers",
                                                     self.input_list[self.file_options_var.get()]["merge_plots"]["threshold"],
                                                     0.1, 3)
            merge_threshold_frame.pack(fill="both", expand=1, pady=5)
            merge_frame.pack(fill="both", expand=1, pady=5)

            sg_frame = tk.LabelFrame(self.settings_frame, text="Sg-Filter", borderwidth=2, relief="groove")
            sg_filter = tk.BooleanVar()
            sg_filter.set(self.input_list[self.file_options_var.get()]["sg_filter"]["on"])
            tk.Checkbutton(sg_frame, text=" Turn filter on", var=sg_filter).pack(side="left", padx=20)
            tk.Button(sg_frame, text="Color of SG-Plot", command=lambda:
                      self.setPlotColor(0)).pack(side="left")
            sg_frame.pack(fill="both", expand=1, pady=5)

            set_settings = tk.BooleanVar()
            set_settings.set(self.input_list[self.file_options_var.get()]["set_settings"])
            if(not self.file_options_var.get() in self.input_list["All"]["file_names"]):
                set_settings_frame = tk.LabelFrame(self.settings_frame, text="Group settings", borderwidth=2,
                                                   relief="groove")
                tk.Checkbutton(set_settings_frame, text=" Set settings for all files in the group",
                               var=set_settings).pack(side="left", padx=20)
                set_settings_frame.pack(fill="both", expand=1, pady=5)

            settings_scrollbar = tk.Scrollbar(self.settings_window, orient="vertical", command=self.settings_canvas.yview)
            self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set, scrollregion=self.settings_canvas.bbox("all"))
            settings_scrollbar.pack(side="right", fill="y")
            self.settings_frame.pack(fill="both", expand=1)
            self.settings_canvas.pack(fill="both", expand=1)
            self.settings_canvas.create_window((0,0), window=self.settings_frame)
            self.settings_frame.bind("<Configure>", self.configureSettingsScrollbar)
            self.settings_canvas.update()
            self.settings_canvas.yview_moveto(0)
            self.settings_window.geometry(str(self.settings_frame.winfo_width()+20) + "x" + str(self.settings_frame.winfo_height()-580))

        def configureAdvancedSettings(self):
            self.advanced_settings_window = tk.Toplevel(self.settings_window)
            self.advanced_settings_window.wm_title("Advanced settings")
            self.advanced_settings_window.attributes('-topmost', 'true')

            button_frame = tk.LabelFrame(self.advanced_settings_window, text="",
                                         borderwidth=2, relief="groove")
            tk.Button(button_frame, text="Ok", command=lambda:
                      self.setAdvancedSettings(peak_valley_points, peak_valley_percentage,
                                               sg_window_size, sg_poly_order)).pack(side="left", expand=1, pady=3)
            tk.Button(button_frame, text="Cancel", command=self.advanced_settings_window.destroy).pack(side="left", expand=1, pady=3)
            button_frame.pack(fill="both", expand=1, pady=5)

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

        def setFiles(self, set_files, name):
            group_name = name.get().strip()
            if(group_name and not group_name in self.input_list):
                file_list = ["Files"] + list(self.input_list.keys()) + [group_name]
                data_per_measurement = sys.maxsize
                timepoint_indices = []
                data_minutepoints = sys.maxsize
                for entry in self.input_list:
                    if(data_per_measurement < self.input_list[entry]["data_per_measurement"]):
                        data_per_measurement = self.input_list[entry]["data_per_measurement"]

                    if(len(timepoint_indices) < len(self.input_list[entry]["timepoint_indices"])):
                        timepoint_indices = self.input_list[entry]["timepoint_indices"]

                    if(data_minutepoints < self.input_list[entry]["data_minutepoints"]):
                        data_minutepoints = self.input_list[entry]["data_minutepoints"]

                true_files = []
                file_paths = []
                none_chosen = True
                output = None
                for file,val in set_files.items():
                    if(val.get()):
                        true_files.append(file)
                        file_paths.append(self.input_list[file]["path"][0])
                        if(output == None):
                            output = "/".join(self.input_list[file]["output"].split("/")[:-2]) + "/" + group_name + "/"

                        val.set(False)
                        none_chosen = False

                if(not none_chosen):
                    self.columns_index_list[group_name] = 1
                    self.input_list[group_name] = {"file_names": true_files, "path": file_paths, "output": output, "pointsize": 3,
                                                   "startingpoint": 12,"datanumber": 5, "minutepoint": -1,
                                                   "period": "Both", "color": "#000000",
                                                   "minimum": {"exclude_firstday": False, "exclude_lastday": True},
                                                   "maximum": {"exclude_firstday": True, "exclude_lastday": False},
                                                   "xlabel": "Days", "sg_filter": {"on": False, "window": 11,
                                                   "poly": 3,"color": "#800000"}, "pv_points": 1, "pv_amp_per": 3,
                                                   "data_per_measurement": data_per_measurement,
                                                   "timepoint_indices": timepoint_indices, "set_columns": {},
                                                   "data_minutepoints": data_minutepoints, "dn_cycle": {"on": True,
                                                   "background": "#929591", "visibility": 50}, "set_settings": False,
                                                   "merge_plots": {"on": True, "threshold": 3.5, "color": "#000000"}}
                    self.file_options.set_menu(*file_list)
                    self.file_options_var.set(group_name)
                    self.file.entryconfig("Remove compared files", state="normal")
                    self.showComparisons()
                else:
                    messagebox.showerror("File comparison error", "At least one file has to be chosen")
            else:
                if(not group_name):
                    messagebox.showerror("Naming error", "The group name is empty.")
                elif(group_name in self.input_list):
                    messagebox.showerror("Naming error", "The group name already exists.")

        def setColumns(self, set_column_data):
            chosen_list = []
            for file,data in set_column_data.items():
                true_columns = []
                none_chosen = True
                for col,val in data.items():
                    if(val.get()):
                        true_columns.append(col)
                        val.set(False)
                        none_chosen = False

                chosen_list.append(none_chosen)
                if(not none_chosen):
                    if(not file in self.input_list[self.file_options_var.get()]["set_columns"]):
                        self.input_list[self.file_options_var.get()]["set_columns"][file] = []

                    self.input_list[self.file_options_var.get()]["set_columns"][file].append(str(self.columns_index_list[self.file_options_var.get()])
                                    + " :=: " + " - ".join(true_columns))

            if(len(chosen_list) and not all(chosen_list)):
                self.canvas.update()
                self.canvas.xview_moveto(0)
                self.canvas.yview_moveto(1)
                self.columns_index_list[self.file_options_var.get()] += 1
                self.pisa.entryconfig("Remove compared columns", state="normal")
                self.showComparisons()
            else:
                messagebox.showerror("Column comparison error", "At least one column has to be chosen")

        def removeFiles(self, files):
            any_chosen = False
            for file,val in files.items():
                if(val.get()):
                    if(not any_chosen):
                        any_chosen = True

                    self.input_list[self.file_options_var.get()]["file_names"].remove(file)
                    if(not self.file_options_var.get() in self.input_list["All"]["file_names"]
                       and self.file_options_var.get() != "All"):
                        self.input_list[self.file_options_var.get()]["set_columns"].pop(file, None)
                    else:
                        if(self.file_options_var.get() == "All"):
                            self.input_list.pop(file, None)
                        else:
                            self.input_list["All"]["file_names"].remove(file)
                            self.input_list["All"]["set_columns"].pop(file, None)

                        for entry in reversed(list(self.input_list.keys())):
                            if(not entry in self.input_list["All"]["file_names"]
                               and file in self.input_list[entry]["file_names"]):
                                self.input_list[entry]["file_names"].remove(file)
                                self.input_list[entry]["set_columns"].pop(file, None)
                                if(not len(self.input_list[entry]["file_names"])):
                                    self.input_list.pop(entry, None)

            if(any_chosen):
                all_deleted = False
                if(not len(self.input_list[self.file_options_var.get()]["file_names"])):
                    if(self.file_options_var.get() != "All"):
                        self.input_list.pop(self.file_options_var.get(), None)
                        file_list = ["Files"] + list(self.input_list.keys())
                        self.file_options.set_menu(*file_list)
                        self.file_options_var.set("All")

                if(not len(self.input_list["All"]["file_names"])):
                        self.file_options.set_menu(*["Files"])
                        self.file_options.configure(state="disabled")
                        self.file.entryconfig("Compare files", state="disabled")
                        self.file.entryconfig("Remove compared files", state="disabled")
                        self.menu.entryconfig("PISA analysis", state="disabled")
                        all_deleted = True
                        for child in self.info_frame.winfo_children():
                            child.pack_forget()
                else:
                    file_list = ["Files"] + list(self.input_list.keys())
                    self.file_options.set_menu(*file_list)
                    self.file_options_var.set("All")

                if(not all_deleted):
                    self.checkComparedColumns(None)

                self.remove_files_window.destroy()
            else:
                messagebox.showerror("File removing error", "At least one file has to be chosen.")

        def removeColumns(self, columns):
            any_chosen = False
            deleted_list = []
            for file,data in columns.items():
                deleted = False
                column_list = self.input_list[self.file_options_var.get()]["set_columns"]
                for col,val in data.items():
                    if(val.get()):
                        if(not any_chosen):
                            any_chosen = True

                        column_list[file].remove(col)
                        if(not len(column_list[file])):
                            column_list.pop(file, None)
                            deleted =True

                deleted_list.append(deleted)


            if(any_chosen):
                self.showComparisons()
                self.remove_columns_window.destroy()
                if(all(deleted_list)):
                    self.pisa.entryconfig("Remove compared columns", state="disabled")
            else:
                messagebox.showerror("Column removing error", "At least one column has to be chosen.")

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
                               period, minimum_exclude, maximum_exclude, x_label, sg_filter,
                               dn_cycle, visibility, merge_setting, merge_threshold, set_settings):
            global input_list
            self.input_list[self.file_options_var.get()]["pointsize"] = point_size.get()
            self.input_list[self.file_options_var.get()]["startingpoint"] = starting_point.get()
            self.input_list[self.file_options_var.get()]["datanumber"] = data_number.get()
            self.input_list[self.file_options_var.get()]["minutepoint"] = minute_point.get()
            self.input_list[self.file_options_var.get()]["period"] = period.get()
            self.input_list[self.file_options_var.get()]["minimum"]["exclude_firstday"] = minimum_exclude[0].get()
            self.input_list[self.file_options_var.get()]["minimum"]["exclude_lastday"] = minimum_exclude[1].get()
            self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[0].get()
            self.input_list[self.file_options_var.get()]["maximum"]["exclude_lastday"] = maximum_exclude[1].get()
            self.input_list[self.file_options_var.get()]["xlabel"] = x_label.get()
            self.input_list[self.file_options_var.get()]["dn_cycle"]["on"] = dn_cycle.get()
            self.input_list[self.file_options_var.get()]["dn_cycle"]["visibility"] = visibility.get()
            self.input_list[self.file_options_var.get()]["sg_filter"]["on"] = sg_filter.get()
            self.input_list[self.file_options_var.get()]["merge_plots"]["on"] = merge_setting.get()
            self.input_list[self.file_options_var.get()]["merge_plots"]["threshold"] = merge_threshold.get()
            self.input_list[self.file_options_var.get()]["set_settings"] = set_settings.get()
            self.settings_window.destroy()

        def setPlotColor(self, sg):
            if(sg == 0):
                plot_color = tkcc.askcolor(initialcolor=self.input_list[self.file_options_var.get()]["sg_filter"]["color"],
                                           title="SG-Plot color")[-1]
                if(plot_color == None):
                    plot_color = "#800000"

                self.input_list[self.file_options_var.get()]["sg_filter"]["color"] = plot_color
            elif(sg == 1):
                plot_color = tkcc.askcolor(initialcolor=self.input_list[self.file_options_var.get()]["color"],
                                           title="Plot color")[-1]
                if(plot_color == None):
                    plot_color = "#000000"

                self.input_list[self.file_options_var.get()]["color"] = plot_color
            elif(sg == 2):
                background_color = tkcc.askcolor(initialcolor=self.input_list[self.file_options_var.get()]["dn_cycle"]["background"],
                                                 title="Background color")[-1]
                if(background_color == None):
                    plotbackground_color_color = "#929591"

                self.input_list[self.file_options_var.get()]["dn_cycle"]["background"] = background_color
            elif(sg == 3):
                plot_color = tkcc.askcolor(initialcolor=self.input_list[self.file_options_var.get()]["merge_plots"]["color"],
                                           title="Merged plot color")[-1]
                if(plot_color == None):
                    plot_color = "#000000"

                self.input_list[self.file_options_var.get()]["merge_plots"]["color"] = plot_color

        def setAdvancedSettings(self, peak_valley_points, peak_valley_percentage, sg_window_size, sg_poly_order):
            if(int(sg_poly_order.get()) < int(sg_window_size.get())):
                self.input_list[self.file_options_var.get()]["pv_points"] = int(peak_valley_points.get())
                self.input_list[self.file_options_var.get()]["pv_amp_per"] = peak_valley_percentage.get()
                self.input_list[self.file_options_var.get()]["sg_filter"]["window"] = int(sg_window_size.get())
                self.input_list[self.file_options_var.get()]["sg_filter"]["poly"] = int(sg_poly_order.get())
                self.advanced_settings_window.destroy()
            else:
                messagebox.showerror("Parameter error", "The poly order has to be smaller than the window size.")

        def checkComparedColumns(self, dummy):
            if(len(self.input_list[self.file_options_var.get()]["set_columns"])):
                self.pisa.entryconfig("Remove compared columns", state="normal")
            else:
                self.pisa.entryconfig("Remove compared columns", state="disabled")

            self.showComparisons()

        def getLogStats(self, group_name):
            self.log_list.append("#<---------- file/group " + group_name + " ---------->")
            for attribute,value in self.input_list[group_name].items():
                if(not attribute in ["data", "timepoint_indices"]):
                    if(isinstance(value, list)):
                        self.log_list.append("[" + attribute + "]\t" + ";".join(value))
                    elif(attribute == "set_columns" and len(self.input_list[self.file_options_var.get()][attribute])):
                        column_list = []
                        for file,columns in self.input_list[self.file_options_var.get()][attribute].items():
                            column_list.append(file + "=" + "-".join(columns))

                        self.log_list.append("[" + attribute + "]\t" +";".join(column_list))
                    else:
                        self.log_list.append("[" + attribute + "]\t" + str(value))

        def cancelAnalysis(self):
            self.cancel_analysis = True

        def closeApplication(self):
            self.quit()

        def enableMenus(self):
            self.menu.entryconfig("Files", state="normal")
            self.pisa.entryconfig("Start analysis", state="normal")
            self.pisa.entryconfig("Cancel analysis", state="disabled")
            self.pisa.entryconfig("Compare columns", state="normal")
            if(len(self.input_list[self.file_options_var.get()]["set_columns"])):
                self.pisa.entryconfig("Remove compared columns", state="normal")

            self.pisa.entryconfig("Settings", state="normal")
            self.menu.entryconfig("Exit", state="normal")

        def disableMenus(self):
            self.menu.entryconfig("Files", state="disabled")
            self.pisa.entryconfig("Start analysis", state="disabled")
            self.pisa.entryconfig("Cancel analysis", state="normal")
            self.pisa.entryconfig("Compare columns", state="disabled")
            self.pisa.entryconfig("Remove compared columns", state="disabled")
            self.pisa.entryconfig("Settings", state="disabled")
            self.menu.entryconfig("Exit", state="disabled")

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

        def configureMainScrollbar(self, event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def configureComparingColumnsScrollbar(self, event):
            self.column_canvas.configure(scrollregion=self.column_canvas.bbox("all"))

        def configureRemoveColumnsScrollbar(self, event):
            self.remove_canvas.configure(scrollregion=self.remove_canvas.bbox("all"))

        def configureSettingsScrollbar(self, event):
            self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"))

        def showErrorWindow(self, title, simple_message, detailed_message, error_output):
            self.error_window = tk.Toplevel(self)
            self.error_window.wm_title(title)
            self.error_window.attributes('-topmost', 'true')

            simple_error_frame = tk.Frame(self.error_window)
            simple_error_scrollbar = tk.Scrollbar(simple_error_frame)
            simple_error_area = tk.Text(simple_error_frame, width=50, height=4)
            simple_error_area.insert("1.0", simple_message)
            simple_error_scrollbar.pack(side="right", fill="both")
            simple_error_area.pack(pady=5)
            simple_error_area.config(state="disabled")
            simple_error_frame.pack(fill="both", expand=1)
            simple_error_scrollbar.config(command=simple_error_area.yview)
            simple_error_area.config(yscrollcommand=simple_error_scrollbar.set)

            self.detailed_error_frame = tk.Frame(self.error_window)
            button_frame = tk.Frame(self.error_window)
            tk.Button(button_frame, text="Ok", command=self.error_window.destroy).pack(side="left", expand=1)
            self.button_var = tk.StringVar()
            self.button_var.set("Show details")
            tk.Button(button_frame, textvariable=self.button_var, command=self.showHideDetails).pack(side="left", expand=1)
            tk.Button(button_frame, text="Save error log", command=lambda:
                      self.saveTraceback(detailed_message, error_output)).pack(side="left", expand=1)
            button_frame.pack(fill="both", expand=1, pady=5)

            detailed_error_scrollbar = tk.Scrollbar(self.detailed_error_frame)
            detailed_error_area = tk.Text(self.detailed_error_frame, width=50, height=10)
            detailed_error_area.insert("1.0", detailed_message)
            detailed_error_scrollbar.pack(side="right", fill="both")
            detailed_error_area.pack(pady=5)
            detailed_error_area.config(state="disabled")
            self.detailed_error_frame.pack(fill="both", expand=1)
            detailed_error_scrollbar.config(command=detailed_error_area.yview)
            detailed_error_area.config(yscrollcommand=detailed_error_scrollbar.set)
            self.detailed_error_frame.pack_forget()

        def showHideDetails(self):
            if(self.button_var.get() == "Show details"):
                self.detailed_error_frame.pack()
                self.button_var.set("Hide details")
            else:
                self.detailed_error_frame.pack_forget()
                self.button_var.set("Show details")

        def saveTraceback(self, traceback, error_output):
             with open(error_output + "error.txt", "w") as error_writer:
                 error_writer.write(traceback)

    try:
        root = tk.Tk()
        #loading_screen = LoadingScreen(root)
        #root.geometry("380x400")
        try:
            root.iconbitmap("../../icon/leaning-tower-of-pisa.ico")
        except:
            try:
                root.iconbitmap("icon/leaning-tower-of-pisa.ico")
            except:
                try:
                    root.iconbitmap("leaning-tower-of-pisa.ico")
                except:
                    pass

        root.style = ttk.Style()
        root.style.theme_use("clam")
        root.style.configure("green.Horizontal.TProgressbar", foreground="green", background="green")
        Application(root)
        #loading_screen.destroy()
        root.mainloop()
    except Exception:
        messagebox.showerror("Critical error", "A critical error occurred while executing the program. See the message below for more details:\n\n"
                             + traceback.format_exc())
