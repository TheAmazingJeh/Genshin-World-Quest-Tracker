import json, os, webbrowser, sys

from PIL import Image, ImageTk
from copy import deepcopy

from tkinter import Tk, Toplevel, Frame, Canvas, Listbox, Scrollbar, Label, Text, Button, OptionMenu, StringVar
from tkinter.messagebox import askyesno, showwarning, showerror
from tkinter.font import Font
from tkinter.scrolledtext import ScrolledText

from utils.file_functions import name_to_id, load_json

from lib.quest_extract.download_gui import resetAndDownload

CURRENT_QUEST_FORMAT_VERSION = "1.1"

def olderQuestFormatWarning(version):
    if version != CURRENT_QUEST_FORMAT_VERSION:
        do_update = askyesno("Old Quest Format", f"The quest formatting version of the downloaded quests ({version}), is incorrect and will not work with the current quest version. {CURRENT_QUEST_FORMAT_VERSION}. Do you want to update? (Choosing NO will close the program)", icon="error")
        if do_update:
            resetAndDownload()
        else:
            sys.exit()

class ScrollableFrame(Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = Canvas(self)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollable_frame = Frame(self.canvas, bg=self.cget("background"))

        self.canvas_frame = self.canvas.create_window((0, 0), 
            window=self.scrollable_frame, anchor="nw")
        # self.canvas_frame.pack(side="left", fill="both", expand=True)

        self.scrollbar = Scrollbar(self, orient="vertical", 
            command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)

class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify="left",
                    background="#ffffe0", relief="solid", borderwidth=1,
                    font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        "Hide the tooltip"
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    """Create a tooltip for a widget.
    
    Attached to `widget` with the text `text`."""
    toolTip = ToolTip(widget)
    
    def enter(event):
        toolTip.id = widget.after(500, toolTip.showtip, text)
    
    def leave(event):
        toolTip.hidetip()
    
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class WorldQuestFrameItem:
    def __init__(self, path:str) -> None:

        self.MAX_CHARS = 40

        with open(path, "r", encoding="utf-8") as f:
            res = json.load(f)

        # Check if the quest format is correct
        olderQuestFormatWarning(res["version"] if "version" in res else "-1.0")

        self.questName = res["name"]
        self.questType = res["type"]
        self.filePath = path

    def getDisplayName(self):
        if len(self.questName) >= self.MAX_CHARS:
            return self.questName[:self.MAX_CHARS-3] + "..."
        return self.questName
    
    def getQuestType(self):
        return self.questType

    def getQuestID(self):
        # Remove special characters and spaces
        return name_to_id(self.questName)

class ErrorQuestItem:
    def __init__(self, questID) -> None:

        self.MAX_CHARS = 40

        self.questName = questID
        self.questType = "single"
        self.filePath = None

    def getDisplayName(self):
        if len(self.questName) >= self.MAX_CHARS:
            return self.questName[:self.MAX_CHARS-3] + "..."
        return self.questName
    
    def getQuestType(self):
        return self.questType

    def getQuestID(self):
        # Remove special characters and spaces
        return name_to_id(self.questName)

class WorldQuestFrame(Frame):
    def __init__(self, master, worldQuestData, *args, double_click:callable = None, select_listbox:callable = lambda _: None, **kwargs):#
        self.data = []
        self.worldQuestData = worldQuestData
        self.completedQuestData = load_json(os.path.join(os.environ["dataPath"], "completedQuestData.json"))
        self.current_region = None
        self.shown_quests = "None"    # Options: none, single, series, both
        
        super().__init__(master, **kwargs)
        self.pack_propagate(False)
        self.listbox = Listbox(self, fg="white", **kwargs)
        self.listbox.configure(width=0, height=10, borderwidth=0, highlightthickness=0, background=self.cget("background"))
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.listbox.pack(padx=5, pady=2, fill="both", expand=True)

        # Bind the on_item_select function to the Listbox double click event
        self.listbox.bind("<Double-Button-1>", lambda _: double_click())
        # Bind the on_item_select function to the Listbox select event
        self.listbox.bind("<<ListboxSelect>>", lambda _: select_listbox(self.get_selected()))

    def append_quest(self, questID:str, completedQuestData:dict):
        """Uses a `questID` to create a WorldQuestFrameItem object and add it to the listbox and data list."""
        path = os.path.join(os.environ["currentSelectedQuestPath"], f"{questID}.json")
        # Check if the quest file exists
        errorFlag = False
        if os.path.exists(path):
            item = WorldQuestFrameItem(path)
        else:
            item = ErrorQuestItem(questID)
            errorFlag = True
            os.environ["questLoadingErrorFlag"] = "True"
        name = item.getDisplayName()
            
        self.listbox.insert("end", name)
        # Change the colour of the text based on the quest type
        background_colour = {"completed": "#002902", "uncompleted": "black", "in_progress": "#0e2133", "error": "red"}
        text_colour = {"single": "white", "series": "cyan", "act": "cyan"}

        state = "uncompleted"

        # Check what quest type the quest is
        if item.questType in ["series", "act"]:
            steps = os.environ["currentSelectedQuestPath"].replace(os.environ["baseQuestPath"], "").split(os.sep)[1:]
            
            if len(steps) == 1:
                if questID not in self.completedQuestData[steps[0]]["series"]:
                    state = "uncompleted"
                else:
                    state = "in_progress"
                    # If the quest is a simple series, which only contain strings not dictionaries
                    if type(completedQuestData[steps[0]]["series"][questID]) == list and \
                        all([type(quest) != dict for quest in completedQuestData[steps[0]]["series"][questID]]):
                        
                        if set(completedQuestData[steps[0]]["series"][questID]) == set(self.worldQuestData[steps[0]]["series"][questID]):
                            state = "completed"
                        else:
                            state = "in_progress"
                    # If the quest is a complex series, which contain dictionaries, which contain subquests that are lists
                    else:
                        # Loop through the acts of the quest series
                        for act in self.worldQuestData[steps[0]]["series"][questID]:
                            # Check if the act is in the completed quests
                            if act["name"] not in [act["name"] for act in completedQuestData[steps[0]]["series"][questID]]:
                                state = "in_progress"
                                break
                            else:
                                # Sort the subquests of the act, and compare them to the completed quest's subquests
                                if set(act["subquests"]) in [set(subquest["subquests"]) for subquest in completedQuestData[steps[0]]["series"][questID]]:
                                    state = "completed"
                                else:
                                    state = "in_progress"
                                    break
            elif len(steps) == 2:
                # Processing acts
                
                # No clue what this does, probably The Gourmet Supremos or something
                if questID not in [quest["name"] for quest in self.worldQuestData[steps[0]]["series"][steps[1]]]:
                    state = "uncompleted"
                else:
                    state = "in_progress"
                    # Get all the subquests of the current act
                    for quest in self.worldQuestData[steps[0]]["series"][steps[1]]:
                        if quest["name"] == questID:
                            quests = set(quest["subquests"])

                    completed_quests = None
                    # Check if the act is in the completed quests
                    if steps[1] in completedQuestData[steps[0]]["series"]:
                        # Get all the completed quests of the current act
                        for quest in completedQuestData[steps[0]]["series"][steps[1]]:
                            if quest["name"] == questID:
                                completed_quests = set(quest["subquests"])
                    
                    if completed_quests == None:
                        state = "uncompleted"
                    elif quests == completed_quests:
                        state = "completed"
                    else:
                        state = "in_progress"
                        
        if item.questType == "single":
            steps = os.environ["currentSelectedQuestPath"].replace(os.environ["baseQuestPath"], "").split(os.sep)[1:]
            if len(steps) == 1:
                if questID in self.completedQuestData[steps[0]]["single"]:
                    state = "completed"
                else: state = "uncompleted"

            elif len(steps) == 2:
                # If the parent quest is not in the completed quests, set the state to uncompleted
                if steps[1] not in self.completedQuestData[steps[0]]["series"]:
                    state = "uncompleted"
                elif questID in self.completedQuestData[steps[0]]["series"][steps[1]]:
                    state = "completed"
            
            elif len(steps) == 3:
                # If the parent parent quest is not in the completed quests, set the state to uncompleted
                if steps[1] not in self.completedQuestData[steps[0]]["series"]:
                    state = "uncompleted"
                else:
                    current_quest = None
                    # If the parent quest is not in the completed quests, set the state to uncompleted
                    for quest in self.completedQuestData[steps[0]]["series"][steps[1]]:
                        if quest["name"] == steps[2]:
                            current_quest = quest
                    if current_quest == None:
                        state = "uncompleted"
                    else:
                        if questID in current_quest["subquests"]:
                            state = "completed"

            else:
                showerror("Error", f"Cannot determine the state of the quest {steps[-1]}")
                state = "error"

        if errorFlag: state = "error"
        # Set the text colour of the item, according to the quest type
        self.listbox.itemconfig("end", fg=text_colour[item.questType], bg=background_colour[state])
        self.data.append(item)

    def load_quests(self, quests):
        """Loads the quests from a dictionary or list into the listbox."""
        with open(os.path.join(os.environ["dataPath"], "completedQuestData.json"), "r", encoding="utf-8") as f:
            completedQuestData = json.load(f)
        # Check if the dictionary contains "series" or "single" keys
        # Process the single and series quest types
        if type(quests) == dict and {"series", "single"}.issubset(quests):
            for quest in quests["series"]:
                self.append_quest(quest, completedQuestData)
            for quest in quests["single"]:
                self.append_quest(quest, completedQuestData)
            return

        # Check if the type of the quests is a list, and does not contain dictionaries
        # Process simple quest series
        if type(quests) == list and all([type(quest) != dict for quest in quests]):
            for quest in quests:
                self.append_quest(quest, completedQuestData)
            return
        
        # Check if the type of the quests is a list, and contains dictionaries
        # Process complex quest series
        if type(quests) == list and all([type(quest) == dict for quest in quests]):
            for quest in quests:
                self.append_quest(quest["name"], completedQuestData)
            return
    
        raise ValueError("Invalid type for `quests`", type(quests))

    def clear_all(self):
        """Clears all the items in the listbox and the data list."""
        self.listbox.delete(0, "end")
        self.data.clear()

    def get_selected(self):
        """Returns the quest ID of the selected quest in the listbox."""
        try:
            return self.data[self.listbox.curselection()[0]].getQuestID()
        except IndexError:
            return None

    def set_shown_types(self, shown_quests:str):
        '''Sets the type of quests to be shown in the listbox.

        Options:
        - `None`: No quests will be shown
        - `Single`: Only single quests will be shown
        - `Series`: Only series quests will be shown
        - `Both`: Both single and series quests will be shown
        '''
        if shown_quests not in ["None", "Single", "Series", "Both"]:
            raise ValueError("Invalid value for `shown_quests`")
        self.shown_quests = shown_quests
        self.reload()

    def set_region(self, regionName:str):
        """Sets the current region, and reloads the listbox with the quests from the region."""
        self.current_region = regionName
        os.environ["currentSelectedQuestPath"] = os.path.join(os.environ["baseQuestPath"], self.current_region)
        self.reload()
    
    def get_region(self):
        """Returns the current region."""
        return self.current_region
    
    def reload(self):
        """Reloads the listbox with the quests from the current path."""
        self.clear_all()
        if self.current_region is None: return
        if self.shown_quests == "None": return

        # Reopen the completed quest data file
        self.completedQuestData = load_json(os.path.join(os.environ["dataPath"], "completedQuestData.json"))

        steps = os.environ["currentSelectedQuestPath"].replace(os.environ["baseQuestPath"], "").split(os.sep)[1:]
        current = self.worldQuestData
        for step in steps:
            # Check if the current step is valid
            if step in current: 
                current = current[step]
            # Check if there is a "series" key in "current"
            elif "series" in current: 
                current = current["series"][step]
            elif type(current) == list:
                for quest in current:
                    if quest["name"] == step:
                        current = quest["subquests"]
            else:
                raise ValueError("Invalid step in path")
            
                
        self.load_quests(current)
        if os.environ["questLoadingErrorFlag"] == "True":
            showwarning("Error", "There was an error one or more quests, please repair the quests and try again.")

    def mark_complete(self):
        """Marks a quest as complete in the `completedQuestData.json` file."""
        # Check if a quest is selected
        if len(self.listbox.curselection()) == 0: return
        # Load the completed quest data file
        completedQuestData = load_json(os.path.join(os.environ["dataPath"], "completedQuestData.json"))
        # Add keys for all of the regions if they do not exist
        for region in self.worldQuestData:
            if region not in completedQuestData: completedQuestData[region] = {"series": {}, "single": []}
        # Get the current path
        steps = os.environ["currentSelectedQuestPath"].replace(os.environ["baseQuestPath"], "").split(os.sep)[1:]
        questID = self.get_selected()

        if len(steps) == 1:
            # Check if step is in the single quests
            if questID in self.worldQuestData[steps[0]]["single"]:
                # Check if the quest is already in the completed quests
                if questID not in completedQuestData[steps[0]]["single"]:
                    completedQuestData[steps[0]]["single"].append(questID)
            
            # Check if step is in the series quests
            elif questID in self.worldQuestData[steps[0]]["series"]:
                # As this is just setting the quest as complete, 
                # we do not need to check if the quest is already in the completed quests
                completedQuestData[steps[0]]["series"][questID] = self.worldQuestData[steps[0]]["series"][questID]

        elif len(steps) == 2:
            # Check if the step is in the non-complex series quests
            if questID in self.worldQuestData[steps[0]]["series"][steps[1]]:
                # Check if the world quest series is already in the completed quests
                if steps[1] not in completedQuestData[steps[0]]["series"]:
                    completedQuestData[steps[0]]["series"][steps[1]] = []
                # Check if the quest is already in the completed quests
                if questID not in completedQuestData[steps[0]]["series"][steps[1]]:
                    completedQuestData[steps[0]]["series"][steps[1]].append(questID)
            else:
                showwarning("Error", "It is not possible to mark an act as complete, please mark the individual quests as complete.")

        else:
            if steps[1] not in completedQuestData[steps[0]]["series"]:
                completedQuestData[steps[0]]["series"][steps[1]] = []
            
            current = completedQuestData[steps[0]]["series"][steps[1]]
            for step in steps[2:]:
                # Check if the step is in the current list, if not, add it
                if step not in [quest["name"] for quest in current]:
                    current.append({"name": step, "subquests": []})
                # Locate the current step in the list
                current = [quest for quest in current if quest["name"] == step][0]
            # Check if the quest is already in the completed quests
            if questID not in current["subquests"]:
                current["subquests"].append(questID)
                        

        # Save the completed quest data
        with open(os.path.join(os.environ["dataPath"], "completedQuestData.json"), "w", encoding="utf-8") as f:
            json.dump(completedQuestData, f, indent=4)
        
    def expand_quest_series(self, questID:str):
        """Expands the quest series of the selected quest."""
        os.environ["currentSelectedQuestPath"] = os.path.join(os.environ["currentSelectedQuestPath"], questID)
        self.reload()

    def collapse_quest_series(self):
        """Collapses the quest series of the selected quest."""
        os.environ["currentSelectedQuestPath"] = os.path.dirname(os.environ["currentSelectedQuestPath"])
        self.reload()

class QuestDetailsFrame(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pack_propagate(False)

        self.questData = {
            "name": "No Quest Selected",
            "url": None,
            "type": None,
            "starting_location": None,
            "rewards": None,
            "steps": None
        }


        self.place_widgets()
        self.format_widgets()

    def place_widgets(self):
        self.questName = Label(self, text=self.questData["name"], bg=self.cget("background"), cursor="hand2", font=Font(size=20), wraplength=self.winfo_reqwidth())
        self.questType = Label(self, text=self.questData["type"], bg=self.cget("background"), wraplength=self.winfo_reqwidth())
        self.questLocation = StartingLocationFrame(self, bg=self.cget("background"))
        self.questRewards = QuestRewardFrame(self, bg=self.cget("background"))
        self.questHorizontalBar = Frame(self, height=1, bg="black")
        self.questSteps = QuestStepsFrame(self, bg=self.cget("background"))

        self.questName.bind("<Button-1>", lambda _: webbrowser.open(self.questData["url"]))

        self.questName.pack(padx=5, pady=5)
        self.questType.pack(padx=5, pady=5)
        self.questLocation.pack(padx=5, pady=5, fill="x", anchor="n")
        self.questRewards.pack(padx=5, pady=5)
        self.questHorizontalBar.pack(fill="x")
        self.questSteps.pack(padx=10, pady=5, fill="x")

    def reset(self):
        self.questData = {
            "name": "No Quest Selected",
            "url": None,
            "type": None,
            "starting_location": None,
            "rewards": None,
            "steps": None
        }
        self.questName.config(text=self.questData["name"])
        self.questType.config(text=self.questData["type"])
        self.questLocation.pack_forget()
        self.questRewards.clear_rewards()
        self.questHorizontalBar.pack_forget()
        self.questSteps.clear_steps()

        self.format_widgets()

    def hide_all_widgets(self):
        self.questLocation.pack_forget()
        self.questRewards.pack_forget()
        self.questHorizontalBar.pack_forget()
        self.questSteps.pack_forget()

    def format_widgets(self):
        self.hide_all_widgets()
        if self.questData["starting_location"] is not None: self.questLocation.pack(padx=5, pady=5, fill="x", anchor="n")
        if self.questData["rewards"] is not None: self.questRewards.pack(padx=5, pady=5)
        self.questHorizontalBar.pack(fill="x")
        if self.questData["steps"] is not None: self.questSteps.pack(padx=10, pady=5, fill="x")

    def set_data(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.questData = json.load(f)
        
        self.questName.config(text=self.questData["name"])

        questTypeText = f"Quest Type: {self.questData['type'].capitalize()}"
        self.questType.config(text=questTypeText)

        # If the starting location is not N/A, set the starting location
        if self.questData["starting_location"] is not None:
            self.questLocation.set_start(self.questData["starting_location"])

        # If the rewards are not N/A, set the rewards
        if self.questData["rewards"] is not None:
            self.questRewards.set_rewards(self.questData["rewards"])

        # If the steps are not N/A, set the steps
        if self.questData["steps"] is not None:
            self.questSteps.set_steps(self.questData["steps"])

        self.format_widgets()

    def get_id(self):
        return name_to_id(self.questData["name"])
    
    def get_type(self):
        return self.questData["type"]

class QuestReward(Frame):
    questInfoDictTemplate = {
        "Name": "",
        "Value": "100",
        "Link": "https://example.com",
        "Image": "74.png",
        "Rarity": "5"
    }
    def __init__(self, parent, imgPath:str, *args, questInfoDict:dict = questInfoDictTemplate, click_event:callable=None, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = Canvas(self, width=75, height=91, borderwidth=0, highlightthickness=0, bg=self.cget("background"))
        self.canvas.pack()
        self.imageDirPath = imgPath

        self.questInfoDict = questInfoDict
        self.rarity_colours = ["#a0a0a0", "#a0a0a0", "#67a287", "#6da6c9", "#9271bc", "#de9053"]

        # Check if image exists
        if os.path.exists(os.path.join(self.imageDirPath, self.questInfoDict["Image"])):
            imgPath = os.path.join(self.imageDirPath, self.questInfoDict["Image"])
        else: 
            imgPath = os.path.join(self.imageDirPath, "74.png")

        # Load the image and resize it
        self.image = Image.open(imgPath)
        self.image = self.image.resize((74, 74), Image.LANCZOS)  # Use LANCZOS for high-quality resampling
        self.photo_image = ImageTk.PhotoImage(self.image)

        self.canvas.create_rectangle(1, 1, 74, 89, fill=self.rarity_colours[int(self.questInfoDict["Rarity"])])        # Draw the main rectangle FIXME: Use proper colour
        imgObj = self.canvas.create_image(1, 1, anchor="nw", image=self.photo_image)                                   # Place the image at the top left corner
        self.canvas.create_rectangle(1, 1, 74, 89, outline="black")                                                    # Add a border around the image
        self.canvas.create_rectangle(1, 75, 74, 90, outline="black", fill="white")                                     # Add a rectangle around the text
        self.canvas.create_text(37, 83   , text=f"{self.questInfoDict['Value']}", anchor="center", font=("Arial", 10)) # Add text below the image    

        CreateToolTip(self, text=self.questInfoDict["Name"])

        if click_event is not None: self.canvas.bind("<Button-1>", click_event)
        else: self.canvas.bind("<Button-1>", self.open_link)



    def open_link(self, *args, **kwargs):
        resp = askyesno(self.questInfoDict["Name"], f"Would you like to open the Fandom Wiki page for \n\"{self.questInfoDict['Name']}\"?")
        if resp: webbrowser.open(self.questInfoDict["Link"])

class QuestRewardFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        # Create frame that is the same width as the parent
        super().__init__(parent, *args, **kwargs)
        self.max_x = 9
        self.imgPath = os.environ["imgPath"]

    def rewards_popup(self, rewardsList:list):
        rewardsList = deepcopy(rewardsList)
        popup = Toplevel(self)
        popup.title("Rewards")
        popup.resizable(False, False)
        frame = Frame(popup)
        frame.pack(padx=5, pady=5)
        current_pos = [0,0]
        max_width = 6
        rewardsList.append({"Name": "Close", "Value": len(rewardsList), "Link": None, "Image": "!Img_close.png", "Rarity": "1"})
        for reward in rewardsList:
            r = QuestReward(frame, self.imgPath, questInfoDict=reward, click_event=(lambda _: popup.destroy()) if reward["Link"] == None else None)
            r.grid(row=current_pos[0], column=current_pos[1], padx=1, pady=1)
            current_pos[1] += 1
            if current_pos[1] >= max_width:
                current_pos[0] += 1
                current_pos[1] = 0

    def set_rewards(self, rewardsList:list):
        self.clear_rewards()
        flag = False
        if len(rewardsList) > self.max_x:
            temp = rewardsList
            rewardsList = rewardsList[:self.max_x-1]
            flag = True
        for reward in rewardsList:
            r = QuestReward(self, self.imgPath, questInfoDict=reward)
            r.pack(side="left", padx=1)
        if flag:
            r = QuestReward(self, self.imgPath, questInfoDict={"Name": "More", "Value": f"{str(len(temp)-self.max_x+1)}", "Link": None, "Image": "!Img_more.png", "Rarity": "1"}, click_event=lambda _: self.rewards_popup(temp))
            r.pack(side="left", padx=1)
        
    def clear_rewards(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.nextPos = [0,0]

class MarkdownTextGenerator:
    def __init__(self, parent, data_string:str, 
                imgPath:str, imageHost:list, imgDict:dict={}, 
                startText:str=""
                ):
        self.markdown_string = data_string
        self.border_width = 0

        self.parent = parent
        self.imageHost = imageHost

        self.imgpath = imgPath
        self.imageDict = imgDict
        self.widgetList = []
        self.image_reference = [] # List of image references, to prevent images disappearing

        self.linkMode = False
        self.imageMode = False
        self.startText = startText
        self.textBuffer = ""
        self.linkText = ""

    def append_text(self, text, url:str=None):
        # Strip the text buffer of any ending or starting spaces
        if text == "": return

        if url:
            self.widgetList.append(Label(self.parent, text=text, fg="blue", bg=self.parent.cget("background"), cursor="hand2", borderwidth=self.border_width, relief="solid"))
            self.widgetList[-1].bind("<Button-1>", lambda event, url=url: webbrowser.open_new(url))
            CreateToolTip(self.widgetList[-1], text=url)
        else:
            self.widgetList.append(Label(self.parent, text=text, bg=self.parent.cget("background"), borderwidth=self.border_width, relief="solid"))
        
        # Make scrolling on the text effect the text widget
        self.widgetList[-1].bind("<MouseWheel>", lambda event: self.parent.yview_scroll(-1*(event.delta//120), "units"))

    def append_image(self, image):
        # Remove the img:from the image string
        image = image.replace("img:", "")
        # Get the image path
        image_path = os.path.join(self.imgpath, self.imageDict[image])
        # Load the image with pillow
        img = Image.open(image_path)
        # Resize the image
        img = img.resize((20, 20))
        # Convert the image to a Tkinter PhotoImage
        img = ImageTk.PhotoImage(img)
        # Prevent the image from being garbage collected
        self.imageHost.append(img)
        # Add the image to the widget list
        self.widgetList.append(Label(self.parent, image=img, bg=self.parent.cget("background"), borderwidth=self.border_width, relief="solid"))
        # Make scrolling on the image effect the text widget
        self.widgetList[-1].bind("<MouseWheel>", lambda event: self.parent.yview_scroll(-1*(event.delta//120), "units"))

    def insert_markdown(self):
        self.markdown_string = f"{self.startText}{self.markdown_string}"
        for char in self.markdown_string:

            # Check for the start of a link
            if char == "◀":
                # Strip the text buffer of any ending or starting spaces
                self.textBuffer = self.textBuffer.strip()
                # Add the text to the widget list 
                self.append_text(self.textBuffer)
                # Reset the text buffer
                self.textBuffer = ""
                # Set the link mode to True, so we know we are in a link
                self.linkMode = True
                continue

            # Check for the end of the seeable text content of a link
            elif char == "▶" and self.linkMode:
                # Set the text of the link, and reset the text buffer
                self.linkText = self.textBuffer
                self.textBuffer = ""
                continue

            # Check for the start of a link
            elif char == "◁" and self.linkMode:
                # Ignore the opening bracket
                continue

            # Check for the end of a link
            elif char == "▷" and self.linkMode:
                # Add the link to the widget list
                self.append_text(self.linkText, url=self.textBuffer)

                self.textBuffer = ""
                self.linkMode = False
                continue

            elif char == "<":
                self.append_text(self.textBuffer)
                self.textBuffer = ""
                self.imageMode = True
                continue

            elif char == ">" and self.imageMode:
                # Add the image to the widget list
                self.append_image(self.textBuffer)
                self.textBuffer = ""
                self.imageMode = False
                continue
            
            elif char == "🡂":
                self.textBuffer = f"{self.textBuffer}  "
                continue

            elif char == " " and (not self.linkMode and not self.imageMode):
                self.append_text(self.textBuffer+"")
                self.textBuffer = ""
                continue
                

            # Increment the text buffer with the current character
            self.textBuffer = f"{self.textBuffer}{char}"
        
        self.append_text(self.textBuffer)


        self.widgetList.append("\n")
        return self.widgetList

class QuestStepsFrame(Frame):
    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        
        self.imgPath = os.environ["imgPath"]
        self.image_host = []
        self.steps = []
        self.text_widget = ScrolledText(self, borderwidth=0, relief=None, background=None)
        self.text_widget.pack(fill="both", expand=True, ipadx=0, ipady=0)

    def set_steps(self, stepsDict:dict):
        # Tags to process:
        # - h: headings (h2 or h3)
        # - p: paragraphs
        # - ul: unordered lists
        # - ol: ordered lists
        # - li: list items

        def _process_list(step:dict, indent_level:int):
            list_type = step["tag"]
            
            steps = []

            i = 0
            for substep in step["steps"]:
                if list_type == "ol":
                    prefix = f"{i+1}. "
                else:
                    prefix = "• "
                
                if substep["tag"] == "li":
                    i += 1

                steps.extend(_process_list_item(substep, indent_level, prefix))
                
            
            return steps

        def _process_list_item(step:dict, indent_level:int, prefix:str):
            if step["tag"] in ["ul", "ol"]:
                return _process_list(step, indent_level+1)
            if step["tag"] == "li":
                return [_process_li(step, prefix, indent_level)]
            else:
                raise ValueError(f"Invalid tag {step['tag']}")

        def _process_li(step:str, prefix:str, indent_level:int):
            newPrefix = "🡂"*indent_level + prefix
            return MarkdownTextGenerator(self.text_widget, step["text"], self.imgPath, self.image_host, startText=newPrefix, imgDict=step["img"] if "img" in step else {}).insert_markdown()

        def _process_p(step:str):
            return MarkdownTextGenerator(self.text_widget, step["text"], self.imgPath, self.image_host, imgDict=step["img"] if "img" in step else {}).insert_markdown()

        self.clear_steps()
        self.text_widget.configure(state="normal")


        try:
            for step in stepsDict:
                if step["tag"] == "p":
                    self.steps.append(_process_p(step))
                elif step["tag"] == "h": #FIXME: Add headings
                    self.steps.append(_process_p(step))
                elif step["tag"] in ["ul", "ol"]:
                    self.steps.extend(_process_list(step, indent_level=1))
                else:
                    print("WARNING: Unhandled tag", step["tag"])
        except Exception as e:
            showerror("Error", f"An error occurred while processing the steps, press OK to show the error message in the console.")
            raise e

        # Place all the widgets contained in the steps list
        for step in self.steps:
            # Insert the step into the text widget
            for widget in step:
                if isinstance(widget, str):
                    self.text_widget.insert("end", widget)
                else:
                    self.text_widget.window_create("end", window=widget)

        self.text_widget.configure(state="disabled")

        self.scroll_to_top()

    def clear_steps(self):
        # Set the text widget to be editable
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.configure(state="disabled")
        self.steps = []
        self.image_host = []

    def scroll_to_top(self):
        # Scroll to the end of the text widget
        self.text_widget.see("end")
        # Scroll to the top of the text widget
        self.text_widget.see("1.0")

class StartingLocationFrame(Frame):
    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.internal_frame = Frame(self, bg=self.cget("background"))
        self.internal_frame.pack(anchor="n", side="top")
        self.imgPath = os.environ["imgPath"]

    def set_start(self, infodict):
        self.clear_start()
        widgets = MarkdownTextGenerator(self.internal_frame, infodict["text"], self.imgPath, [], startText="Location: ").insert_markdown()
        for widget in widgets:
            if isinstance(widget, str): continue
            widget.pack(side="left", anchor="w")

    def clear_start(self):
        # Delete all children in frame
        for widget in self.internal_frame.winfo_children():
            widget.destroy()

class FilterFrame(Frame):
    def __init__(self, root, regions:list, *args, 
                update_region_command:callable = None, 
                update_type_command:callable = None, 
                open_world_quest_command:callable = None, 
                back_world_quest_command:callable = None,
                
                **kwargs):
        super().__init__(root, *args, bg=root.cget("background"), **kwargs)
        self.pack_propagate(False)
        self.questTypes = ["Both", "Series", "Single"]
        self.regions = regions
        self.update_type_command = update_type_command
        self.update_region_command = update_region_command
        self.open_world_quest_command = open_world_quest_command
        self.back_world_quest_command = back_world_quest_command
        self.place_widgets()

    def place_widgets(self):
        self.leftSide = Frame(self, bg=self.cget("background"))

        self.regionFrame = Frame(self.leftSide, bg=self.cget("background"))
        self.regionLabel = Label(self.regionFrame, text="Region: ", bg=self.cget("background"))
        self.regionLabel.pack(side="left")
        self.regionDropdown = OptionMenu(self.regionFrame, StringVar(self, self.regions[0]), *self.regions, command=lambda _: self.update_region())
        self.regionDropdown.pack(side="left")
        self.regionFrame.pack(side="top", anchor="w")

        self.questTypeFrame = Frame(self.leftSide, bg=self.cget("background"))
        self.questTypeLabel = Label(self.questTypeFrame, text="Quest Type: ", bg=self.cget("background"))
        self.questTypeLabel.pack(side="left")
        self.questTypeDropdown = OptionMenu(self.questTypeFrame, StringVar(self, self.questTypes[0]), *self.questTypes, command=lambda _: self.update_type())
        self.questTypeDropdown.pack(side="left")
        self.questTypeFrame.pack(side="top", anchor="w")

        self.leftSide.pack(side="left")

        self.rightSide = Frame(self, bg=self.cget("background"))
        self.questSeriesOpenButton = Button(self.rightSide, text="Expand", bg=self.cget("background"), command=self.open_world_quest_command)
        self.questSeriesOpenButton.pack(side="top", anchor="e", padx=5, pady=(0, 2))

        self.questSeriesbackButton = Button(self.rightSide, text="Back", bg=self.cget("background"), command=self.back_world_quest_command)
        self.questSeriesbackButton.pack(side="top", anchor="e", padx=5, pady=(2,0))

        self.rightSide.pack(side="right")

    def update_type(self):
        self.update_type_command(self.questTypeDropdown.cget("text"))

    def update_region(self):
        self.update_region_command(self.regionDropdown.cget("text"))

    def update(self):
        self.update_region()
        self.update_type()
    
    def set_expand_button(self, state:bool):
        self.questSeriesOpenButton.config(state="normal" if state else "disabled")

    def set_back_button(self, state:bool):
        self.questSeriesbackButton.config(state="normal" if state else "disabled")

    def fill_widgets(self):
        pass