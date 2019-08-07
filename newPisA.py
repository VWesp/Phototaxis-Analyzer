import tkinter as tk
from tkinter import filedialog, StringVar
import tkinter.ttk as ttk
import os

input_list = list()
selection = None

class Application(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.initWindow()

    def initWindow(self):
        file_options_var = StringVar()
        file_options_var.set("Files")
        file_options = ttk.OptionMenu(self, file_options_var, *["Files", "All"])

        self.master.title("GUI")
        self.pack(fill="both", expand=1)
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        file = tk.Menu(menu, tearoff=0)
        file.add_command(label="Open", command=lambda: self.openFile(file_options, file_options_var))
        menu.add_cascade(label="File", menu=file)
        edit = tk.Menu(menu, tearoff=0)
        edit.add_command(label="Start analysis")
        edit.add_command(label="Cancel analysis")
        edit.add_separator()
        edit.add_command(label="Compare columns")
        edit.add_command(label="Remove comparing columns")
        edit.add_separator()
        edit.add_command(label="Set period")
        edit.add_separator()
        edit.add_command(label="Settings")
        menu.add_cascade(label="PisA analysis", menu=edit)
        exit = tk.Menu(menu, tearoff=0)
        exit.add_command(label="Exit PisA", command=self.closeApplication)
        menu.add_cascade(label="Exit", menu=exit)

        file_options.pack(fill="both", expand=0)
        file_options.configure(state="disabled")

    def openFile(self, option_menu, option_menu_var):
        global input_list
        global selection

        file = filedialog.askopenfilename(title = "Select phototaxis file",filetypes = (("text files","*.txt"),("all files","*.*")))
        if(len(file)):
            if(not len(input_list)):
                option_menu.configure(state="normal")

            file_list = ["Files", "All"]
            for entry in input_list:
                file_list.append(list(entry.keys())[0])

            file_name = os.path.basename(file)
            if(not file_name in file_list):
                file_settings = {file_name: {"path": file, "output": os.path.dirname(file) + "/"}}
                input_list.append(file_settings)
                file_list.append(file_name)
                option_menu.set_menu(*file_list)
                option_menu_var.set(file_name)

    def closeApplication(self):
        exit()


root = tk.Tk()
root.geometry("380x400")
app = Application(root)
root.mainloop()
