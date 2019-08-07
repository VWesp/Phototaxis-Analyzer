import tkinter as tk
from tkinter import filedialog
import tkinter.colorchooser as tkcc
import tkinter.ttk as ttk
import os

input_list =dict()

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
        file_options = ttk.OptionMenu(file_options_frame, file_options_var, *["Files", "All"])
        file_options.pack()
        file_options.configure(state="disabled")
        file_options_frame.pack(fill="both", expand=0)
        self.buildLabelEntry(files_frame, "Set header line of file", 1, 2)
        files_frame.pack(fill="both", expand=0)

        info_frame = tk.LabelFrame(self, borderwidth=3, relief="sunken")
        info_frame.pack(fill="both", expand=1)

        self.master.title("PisA - [P]hototax[is]-[A]nalyzer")
        self.pack(fill="both", expand=1)
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        file = tk.Menu(menu, tearoff=0)
        file.add_command(label="Open", command=lambda: self.openFile(menu, file_options, file_options_var))
        menu.add_cascade(label="Files", menu=file)
        pisa = tk.Menu(menu, tearoff=0)
        pisa.add_command(label="Start analysis")
        pisa.add_command(label="Cancel analysis")
        pisa.add_separator()
        pisa.add_command(label="Compare columns")
        pisa.add_command(label="Remove comparing columns")
        pisa.add_separator()
        pisa.add_command(label="Set period")
        pisa.add_separator()
        pisa.add_command(label="Settings", command=lambda: self.configureSettings(file_options_var))
        menu.add_cascade(label="PisA analysis", menu=pisa)
        exit = tk.Menu(menu, tearoff=0)
        exit.add_command(label="Exit PisA", command=self.closeApplication)
        menu.add_cascade(label="Exit", menu=exit)
        menu.entryconfig("PisA analysis", state="disabled")

    def openFile(self, menu, option_menu, option_menu_var):
        global input_list

        file = filedialog.askopenfilename(title = "Select phototaxis file",
                                          filetypes = (("text files","*.txt"),("all files","*.*")))
        if(len(file)):
            if(not len(input_list)):
                menu.entryconfig("PisA analysis", state="normal")
                option_menu.configure(state="normal")

            file_list = ["Files", "All"]
            for entry in input_list:
                file_list.append(entry)

            file_name = os.path.basename(file)
            if(not file_name in file_list):
                input_list[file_name] = {"path": file, "output": os.path.dirname(file) + "/", "pointsize": 3,
                                         "startingpoint": 12, "datanumber": 5, "minutepoint": -1,
                                         "color": "#000000", "minimum": {"exclude_firstday": False,
                                         "exclude_lastday": True}, "maximum": {"exclude_firstday": True,
                                         "exclude_lastday": False}, "xlabel": "Days", "sg_filter": {"On": False,
                                         "window": 11, "poly": 3, "color": "#800000"}, "pv_points": 1,
                                         "pk_amp_per": 3}
                file_list.append(file_name)
                option_menu.set_menu(*file_list)
                option_menu_var.set(file_name)

    def configureSettings(self, option_menu_var):
        global input_list

        settings_window = tk.Toplevel(self)
        settings_window.wm_title("Analysis settings")
        general_settings_frame = tk.LabelFrame(settings_window, text="General settings", borderwidth=2,
                                               relief="sunken")

        self.buildLabelScale(general_settings_frame, "Set point size of plot",
                             input_list[option_menu_var.get()]["pointsize"], 0, 20, 4)

        startingpoint_frame = tk.Frame(general_settings_frame)
        startingpoint_text = tk.StringVar()
        startingpoint_text.set("Set starting point of plot")
        tk.Label(startingpoint_frame, textvariable=startingpoint_text, height=3).pack(side="left")
        startingpoint_label = tk.IntVar()
        startingpoint_label.set(input_list[option_menu_var.get()]["startingpoint"])
        tk.Entry(startingpoint_frame, textvariable=startingpoint_label).pack(side="left")
        startingpoint_frame.pack()

        self.buildLabelScale(general_settings_frame, "Set number of used data points",
                             input_list[option_menu_var.get()]["datanumber"], 0, 40, 4)
        self.buildLabelScale(general_settings_frame, "Set data minute point",
                             input_list[option_menu_var.get()]["minutepoint"], -1, 19, 4)

        self.buildExcludeField(general_settings_frame, "Minimum", " Exclude first day",
                               input_list[option_menu_var.get()]["minimum"]["exclude_firstday"], " Exclude last day",
                               input_list[option_menu_var.get()]["minimum"]["exclude_lastday"])
        self.buildExcludeField(general_settings_frame, "Maximum", " Exclude first day",
                               input_list[option_menu_var.get()]["maximum"]["exclude_firstday"], " Exclude last day",
                               input_list[option_menu_var.get()]["maximum"]["exclude_lastday"])

        xlabel_frame = tk.LabelFrame(general_settings_frame, text="X-axis label", borderwidth=2, relief="sunken")
        xlabel = tk.StringVar()
        tk.Radiobutton(xlabel_frame, text="Days", variable=xlabel, value="Days").pack(side="left")
        tk.Radiobutton(xlabel_frame, text="Hours", variable=xlabel, value="Hours").pack(side="left")
        xlabel.set(input_list[option_menu_var.get()]["xlabel"])
        xlabel_frame.pack()

        general_settings_frame.pack()

    def closeApplication(self):
        exit()

    def buildLabelEntry(self, parent_frame, text, value, height):
        frame = tk.Frame(parent_frame)
        label_text = tk.StringVar()
        label_text.set(text)
        tk.Label(frame, textvariable=label_text, height=height).pack(side="left")
        label_entry = tk.IntVar()
        label_entry.set(value)
        tk.Entry(frame, textvariable=label_entry).pack(side="left")
        frame.pack()

    def buildLabelScale(self, parent_frame, text, value, min, max, height):
        frame = tk.Frame(parent_frame)
        label_text = tk.StringVar()
        label_text.set(text)
        tk.Label(frame, textvariable=label_text, height=height).pack(side="left")
        label_scale = tk.Scale(frame, from_=min, to=max, orient="horizontal", relief="groove")
        label_scale.set(value)
        label_scale.pack(side="left")
        frame.pack()

    def buildExcludeField(self, parent_frame, title, first_label, first_value, second_label, second_value):
        frame = tk.LabelFrame(parent_frame, text=title, borderwidth=2, relief="sunken")
        first_var = tk.BooleanVar()
        first_var.set(first_value)
        tk.Checkbutton(frame, text=first_label, var=first_var).pack(side="left")
        second_var = tk.BooleanVar()
        second_var.set(second_value)
        tk.Checkbutton(frame, text=second_label, var=second_var).pack(side="left")
        frame.pack()


root = tk.Tk()
root.geometry("380x400")
Application(root)
root.mainloop()
