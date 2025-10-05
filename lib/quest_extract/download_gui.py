import os
import sys
import shutil

from lib.quest_extract.extract_all import Download
from tkinter import Tk, Label
from tkinter.ttk import Progressbar
from tkinter.messagebox import askokcancel, showinfo

class DownloadPopup(Tk):
    def __init__(self, title=None):
        # Create all the necessary folders
        for key in ["dataPath", "baseQuestPath", "imgPath", "cachePath", "bkp", "worldQuestSeriesData"]:
            if not os.path.exists(os.environ[key]): os.makedirs(os.environ[key])
        d = Download()
        self.generator = d.allData()
        self.regionCount = next(self.generator)["regionCount"]
        self.currentRegion = 0
        self.currentQuest = 0
        self.currentQuestCount = 0

        self.complete = False
        
        super().__init__()
        self.title(title)
        self.geometry("200x150")

        self.warninglabel = Label(self, text="This may take a while. \nDO NOT CLOSE THE WINDOW")
        self.warninglabel.pack()

        self.regionText = Label(self, text="Current Region (0/0): None")
        self.regionText.pack()
        self.regionBar = Progressbar(self, orient="horizontal", length=190, mode="determinate")
        self.regionBar.pack()
        self.questText = Label(self, text="Current Quest (0/0): None")
        self.questText.pack()
        self.questBar = Progressbar(self, orient="horizontal", length=190, mode="determinate")
        self.questBar.pack()    

    def step(self):
        try:
            self.update()
            resp = next(self.generator)
            self.update()
            if resp["action"] == "update":
                if "regionChange" in resp:
                    self.currentRegion += 1
                if "questType" in resp:
                    self.currentQuest = -1
                    self.currentQuestCount = resp["questCount"]

            self.currentQuest += 1
            if resp["action"] in ["download", "skip"]:
                self.regionText.config(text=f"Current Region ({self.currentRegion}/{self.regionCount}): {resp['region']}")
                self.regionBar["value"] = (self.currentRegion / self.regionCount) * 100
                self.questText.config(text=f"Current Quest ({self.currentQuest}/{self.currentQuestCount}):\n{resp['questName']}")
                self.questBar["value"] = (self.currentQuest / self.currentQuestCount) * 100
        except StopIteration:
            self.complete = True
            # Destroy the window
            self.destroy()

    def buttonbox(self):
        return

def download():
    p = DownloadPopup("Downloading")
    while True:
        p.update()
        p.step()
        if p.complete: 
            break

def _cleanup_common_files():
    """Clean up common files that need to be removed during data refresh."""
    # Delete the world quest data dictionary
    try: 
        os.remove(os.environ["worldQuestDataDict"])
    except FileNotFoundError: 
        pass
    # Delete the conversion reference
    try: 
        os.remove(os.path.join(os.environ["dataPath"], "convertIDToNameDict.json"))
    except FileNotFoundError: 
        pass


def _download_and_exit():
    """Download data and exit with success message."""
    download()
    showinfo("Done", "Data has been downloaded. Please re-launch the program for the changes to take effect.")
    sys.exit()


def reFetchWorldQuestsAndDownload():
    """Re-fetch world quest data by clearing specific cache files."""
    if os.path.exists(os.environ["cachePath"]):
        # Delete the world quest list cache
        try: 
            os.remove(os.path.join(os.environ["cachePath"], "wiki_World_Quest_List.html"))
        except FileNotFoundError: 
            pass
        
        _cleanup_common_files()
        _download_and_exit()


def resetAndDownload():
    """Reset all data by clearing cache and data folders completely."""
    # Delete the cached data folder
    if os.path.exists(os.environ["cachePath"]): 
        shutil.rmtree(os.environ["cachePath"])
    
    # Delete the data folder (but not the completed quests file)
    if os.path.exists(os.environ["dataPath"]): 
        data_path = os.environ["dataPath"]
        for folder in ["quests", "img"]:
            folder_path = os.path.join(data_path, folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
    
    _cleanup_common_files()
    _download_and_exit()

def download_data_prompt(tk_window=None, show_prompt=True):
    downloadAutomatic = askokcancel("Error", "World Quest Data is missing. This is either available on the github page or can be generated now. Would you like to generate it now?")
    if downloadAutomatic:
        download()
        showinfo("Done", "Data has been downloaded. Please re-launch the program for the changes to take effect.")
    else:
        if tk_window is not None: 
            tk_window.quit()
    sys.exit() 