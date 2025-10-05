import os, sys, shutil, json


from tkinter import Tk, Frame, Menu, BooleanVar
from tkinter.messagebox import askokcancel, showinfo

from window.widgets import WorldQuestFrame, QuestDetailsFrame, FilterFrame
from utils.file_functions import load_json

from lib.quest_extract.download_gui import download, reFetchWorldQuestsAndDownload, download_data_prompt

class App(Tk):
    def __init__(self, basepath:str, *args, **kwargs):
        # Initialize the Tkinter window
        super().__init__(*args, **kwargs)
        # Hide the window
        self.withdraw()

        # Set environment variables
        os.environ["basePath"] = basepath
        os.environ["dataPath"] = os.path.join(basepath, "data")
        os.environ["baseQuestPath"] = os.path.join(os.environ["dataPath"], "quests")
        os.environ["currentSelectedQuestPath"] = os.environ["baseQuestPath"]

        os.environ["imgPath"] = os.path.join(os.environ["dataPath"], "img")
        os.environ["cachePath"] = os.path.join(basepath, "cache")
        os.environ["bkp"] = os.path.join(basepath, "bkp")
        os.environ["worldQuestSeriesData"] = os.path.join(os.environ["dataPath"], "quests")
        os.environ["questLoadingErrorFlag"] = "False"

        # Set icon
        if os.path.exists(os.path.join(os.environ["basePath"], "icon.ico")):
            self.iconbitmap(os.path.join(os.environ["basePath"], "icon.ico"))

        # File paths
        os.environ["worldQuestDataDict"] = os.path.join(os.environ["dataPath"], "worldQuestDataDict.json")

        # Check for the existence of the data folder
        if not os.path.exists(os.environ["worldQuestSeriesData"]): 
            download_data_prompt(tk_window=self)

        self.worldQuestDataDict = load_json(os.path.join(os.environ["dataPath"], "worldQuestDataDict.json"))
        self.completedQuestData = load_json(os.path.join(os.environ["dataPath"], "completedQuestData.json"))

        # Check if the worldQuestDataDict is empty
        if self.worldQuestDataDict == {}:
            download_data_prompt(tk_window=self)

        # Get the regions
        self.regions = list(self.worldQuestDataDict["regions"].keys())

        with open(os.path.join(os.environ["dataPath"], "completedQuestData.json"), "r", encoding="utf-8") as file:
            completedQuestData = json.load(file)
        for region in self.worldQuestDataDict["regions"]:
            if region not in completedQuestData: completedQuestData[region] = {"series": {}, "single": []}
        with open(os.path.join(os.environ["dataPath"], "completedQuestData.json"), "w", encoding="utf-8") as file:
            json.dump(completedQuestData, file, indent=4)

        # Initialize the window
        self.initialize()
        # Place the widgets
        self.place_widgets()
        # Load the quests
        self.filterFrame.update()
        self.filterFrame.set_expand_button(False)
        self.filterFrame.set_back_button(False)
        self.worldQuestFrame.reload()
        # Show the window
        self.deiconify()

    def initialize(self):
        # Initialize the window
        self.size = (1000, 500)
        self.MENUBAR_OFFSET = 18
        self.title("Genshin Impact World Quest Tool")
        self.geometry(f"{self.size[0]}x{self.size[1]+self.MENUBAR_OFFSET}")
        self.resizable(False, False)

    def place_widgets(self):
        self.place_menubar()
        self.place_frames()

    def place_menubar(self):
        self.menu = Menu(self)
        # Add a File Cascade
        self.fileMenu = Menu(self.menu, tearoff=0)
        self.convert_axp_to_mora = BooleanVar(value=False)

        self.fileMenu.add_checkbutton(
            label="Convert Xp to Mora",
            command=self.toggle_axp_mora_convert,
            variable=self.convert_axp_to_mora
        )
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Repair Resources", command=self.menu_download)
        self.fileMenu.add_command(label="Re-Download Resources", command=self.menu_reFetchWorldQuestsAndDownload)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Exit", command=self.quit)
        self.menu.add_cascade(label="File", menu=self.fileMenu)

        self.menu.add_command(label="Mark Complete", command=self.mark_complete)
        self.menu.add_separator()

        self.config(menu=self.menu)

    def toggle_axp_mora_convert(self):
        self.questDetailsFrame.set_axp_mora_convert(self.convert_axp_to_mora.get())
        # Reload the current quest to update the rewards display
        currentQuestID = self.questDetailsFrame.get_id()
        self.change_loaded_quest(currentQuestID)

    def menu_download(self):
        download()
        self.worldQuestFrame.reload()
        os.environ["questLoadingErrorFlag"] = "False"

    def menu_reFetchWorldQuestsAndDownload(self):
        reFetchWorldQuestsAndDownload()
        self.worldQuestFrame.reload()
        os.environ["questLoadingErrorFlag"] = "False"

    def place_frames(self):
        self.worldQuestFrame = WorldQuestFrame(self, self.worldQuestDataDict["regions"], bg="black",
                                    width=int(self.size[0]/4), 
                                    height=int(self.size[1]), 
                                    select_listbox=self.change_loaded_quest,
                                    double_click=self.expand_world_quest
                                    )
        
        # Filter options (Area, search ect...)
        self.filterFrame = FilterFrame(self, self.regions, width=int(self.size[0]/4*3), height=int(self.size[1]/8), 
                                    update_region_command=self.change_region,
                                    update_type_command=self.change_shown_types,
                                    open_world_quest_command=self.expand_world_quest,
                                    back_world_quest_command=self.collapse_world_quest
                                    )
        self.questDetailsFrame = QuestDetailsFrame(self, bg="white", width=int(self.size[0]/4*3), height=int(self.size[1]/8*7)) # Quest information


        self.worldQuestFrame.grid(row=0, column=0, rowspan=2, sticky="nw")
        self.filterFrame.grid(row=0, column=1, sticky="ne")
        self.questDetailsFrame.grid(row=1, column=1, sticky="se")

    def change_loaded_quest(self, questID:str):
        if questID in ["", "None", None]: return
        # Hide the current quest details
        self.questDetailsFrame.grid_forget()
        # Load the new quest details
        self.questDetailsFrame.set_data(os.path.join(os.environ["currentSelectedQuestPath"], f"{questID}.json"))
        # Disable the expand button if the quest is not a series
        if self.questDetailsFrame.get_type() not in ["series", "act"]: self.filterFrame.set_expand_button(False)
        else: self.filterFrame.set_expand_button(True)

        # Place the new quest details
        self.questDetailsFrame.grid(row=1, column=1, sticky="se")
    
    def change_region(self, region:str, reload:bool=True): 
        self.worldQuestFrame.set_region(region)
        if not reload: return
        self.worldQuestFrame.reload()
        self.questDetailsFrame.reset()

    def change_shown_types(self, types:str, reload:bool=True):
        self.worldQuestFrame.set_shown_types(types)
        if not reload: return
        self.worldQuestFrame.reload()
        self.questDetailsFrame.reset()

    def expand_world_quest(self):
        # Check if the quest is a series
        if self.questDetailsFrame.get_type() not in ["series", "act"]: return

        questID = self.questDetailsFrame.get_id()
        self.worldQuestFrame.expand_quest_series(questID)
        self.questDetailsFrame.reset()

        # Enable the back button
        self.filterFrame.set_back_button(True)
        self.filterFrame.set_expand_button(False)

    def collapse_world_quest(self):
        self.worldQuestFrame.collapse_quest_series()
        self.questDetailsFrame.reset()
        
        # Check if the current path is the base path + a region
        if os.environ["currentSelectedQuestPath"] in [os.path.join(os.environ["baseQuestPath"], region) for region in self.regions]: 
            self.filterFrame.set_back_button(False)
        self.filterFrame.set_expand_button(False)

    def mark_complete(self):
        self.worldQuestFrame.mark_complete()
        self.worldQuestFrame.reload()

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        loc = os.path.dirname(sys.executable)
        # Change the working directory to the executable directory
        os.chdir(loc)
    else:
        # Get the directory of the script
        loc = os.path.dirname(os.path.realpath(__file__))

    app = App(loc)
    app.mainloop()
    # Copy the completedQuestData.json to the backup folder
    if not os.path.exists(os.environ["bkp"]): os.makedirs(os.environ["bkp"])
    shutil.copy(os.path.join(os.environ["dataPath"], "completedQuestData.json"), os.path.join(os.environ["bkp"], "completedQuestData.json"))