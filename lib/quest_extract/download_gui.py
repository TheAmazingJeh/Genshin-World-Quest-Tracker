import os

from lib.quest_extract.extract_all import Download
from lib.page.get_wiki_url_from_name import get_wiki_url_from_name
from tkinter import Tk, Label
from tkinter.ttk import Progressbar

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
        if p.complete: break

def reFetchWorldQuestsAndDownload():
    if os.path.exists(os.environ["cachePath"]):
        # Delete the world quest list cache
        try: os.remove(os.path.join(os.environ["cachePath"], "wiki_World_Quest_List.html"))
        except FileNotFoundError: pass
        # Delete the world quest data dictionary
        try: os.remove(os.environ["worldQuestDataDict"])
        except FileNotFoundError: pass
        # Delete the conversion reference
        try: os.remove(os.path.join(os.environ["dataPath"], "convertIDToNameDict.json"))
        except FileNotFoundError: pass
        download()


def resetAndDownload():
    if not os.path.exists(os.environ["dataPath"]): os.makedirs(os.environ["dataPath"])
    p = DownloadPopup("Downloading")
    while True:
        p.update()
        p.step()
        if p.complete: break