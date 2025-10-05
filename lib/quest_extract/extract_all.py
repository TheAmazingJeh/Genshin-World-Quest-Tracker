import os
import json
import requests
from datetime import datetime
from lib.quest_extract.all_world_quests import WorldQuestSeriesData
from utils.quest_utils import getQuest
from utils.file_functions import name_to_id, get_image_path

class Download:
    def __init__(self, forceUpdate:bool=False):
        print("Initializing download object")

        self.forceUpdate = forceUpdate

        #TODO: When implementing into the app, replace os.environ with os.environ

        self.convertIDToNameDict = os.path.join(os.environ["dataPath"], "convertIDToNameDict.json")

        # Create the files
        if not os.path.exists(self.convertIDToNameDict):
            with open(self.convertIDToNameDict, 'w+', encoding="utf-8") as file:
                json.dump({}, file)

    def _allWorldQuests(self):
        """`filepath` is the path to the file where the data should be stored
        """
        # Check if the file exists, or if the user wants to force an update
        if os.path.exists(os.environ["worldQuestDataDict"]) and not self.forceUpdate:
            with open(os.environ["worldQuestDataDict"], 'r', encoding="utf-8") as file:
                if json.load(file) != {}:
                    print("Data already exists. Use `forceUpdate=True` to force update the data")
                    return
    
        questSeriesDataObject = WorldQuestSeriesData(os.environ, self.convertIDToNameDict)
        questSeriesData = questSeriesDataObject.getAll()
        
        while True:
            try:
                res = next(questSeriesData)
                # Check if the result is a string
                if isinstance(res, str):
                    print(res)
                # Check if the result is a dictionary
                elif isinstance(res, dict):
                    with open(os.path.join(os.environ["worldQuestDataDict"]), 'w', encoding="utf-8") as file:
                        json.dump(res, file, indent=4)
            except StopIteration:
                break

    def _allWorldQuestsData(self):
        """It is assumed that `allWorldQuests` has been called before this method
        """
        with open(self.convertIDToNameDict, 'r', encoding="utf-8") as file:
            self.convertIDToNameDictOpen = json.load(file)
        def saveQuestData(name:str, path:str):
            # Get the quest data
            quest = getQuest(name, worldQuestDataDict, os.environ["cachePath"], self.convertIDToNameDictOpen)
            # Save the quest data
            with open(os.path.join(path, name_to_id(name) + ".json"), 'w', encoding="utf-8") as file:
                json.dump(quest.quest_data, file, indent=4)


            if quest.quest_img_urls != []:
                for url in quest.quest_img_urls:
                    path = os.path.join(os.environ["imgPath"], get_image_path(url))
                    if not os.path.exists(path):
                        self.download_image(url, get_image_path(url))
        
        def loopThroughSeries(seriesData:dict, path:str):
            # Loop through the quests
            i = 0
            for quest in seriesData:
                i += 1
                # Check if the quest is a single quest
                if isinstance(quest, str):
                    # Save the quest data
                    saveQuestData(quest, path)
                else:
                    # Get the series name
                    seriesName = f"{quest['name']}"
                    # Check if the folder exists
                    if not os.path.exists(os.path.join(path, name_to_id(seriesName))):
                        os.makedirs(os.path.join(path, name_to_id(seriesName)))
                    # Replace any spaces with underscores in the immediate path
                    saveQuestData(seriesName, path)

                    

                    # Check if the series has subquests
                    for subquest in quest["subquests"]:
                        # Check if the subquest is a single quest
                        if isinstance(subquest, str):
                            # Save the quest data
                            saveQuestData(subquest, os.path.join(path, name_to_id(seriesName)))
                        else:
                            loopThroughSeries(subquest, os.path.join(path, name_to_id(seriesName)))
        
        # Load worldQuestDataDict
        with open(os.environ["worldQuestDataDict"], 'r', encoding="utf-8") as file:
            worldQuestDataDict = json.load(file)

        if "timeUpdated" not in worldQuestDataDict: 
            lastUpdated = datetime.now()
        else: 
            lastUpdated = datetime.strptime(worldQuestDataDict["timeUpdated"], "%Y-%m-%d %H:%M:%S")
        # Print how long ago the data was last updated
        print(f"Data was last updated {lastUpdated.strftime('%Y-%m-%d %H:%M:%S')}")
        self.worldQuestDataDict = worldQuestDataDict["regions"]

        # Yield the number of regions, to be used in the progress bar
        yield {"action": "update", "regionCount": len(self.worldQuestDataDict)}

        # Loop through the regions
        for region in self.worldQuestDataDict:
            # Yield the region name, to be used in the progress bar
            yield {"action": "update", "regionChange": region}
            # Check if the folder exists
            if not os.path.exists(os.path.join(os.environ["worldQuestSeriesData"], region)):
                # Create the folder for the current region
                os.makedirs(os.path.join(os.environ["worldQuestSeriesData"], region))
            # Loop through the quest types
            for questType in self.worldQuestDataDict[region]:
                # Yield the number of quests in the current quest type, to be used in the progress bar
                yield {"action": "update", "questType": questType, "questCount": len(self.worldQuestDataDict[region][questType])}
                # Loop through the quests
                for questName in self.worldQuestDataDict[region][questType]:
                    # Check if the json file exists
                    if os.path.exists(os.path.join(os.environ["worldQuestSeriesData"], region, name_to_id(questName) + ".json")) and not self.forceUpdate:

                        yield {
                            "action": "skip",
                            "region": region,
                            "questType": questType,
                            "questName": questName
                        }

                        continue
                    
                    yield {
                            "action": "download",
                            "region": region,
                            "questType": questType,
                            "questName": questName
                        }

                    currentPath = os.path.join(os.environ["worldQuestSeriesData"], region)
                    quest = getQuest(questName, worldQuestDataDict, os.environ["cachePath"], self.convertIDToNameDictOpen)

                    
                    saveQuestData(questName, currentPath)

                    if quest.quest_data["type"] in ["series", "act"]:
                        if not os.path.exists(os.path.join(currentPath, name_to_id(questName))):
                            os.makedirs(os.path.join(currentPath, name_to_id(questName)))
                        try:
                            loopThroughSeries(self.worldQuestDataDict[region]["series"][questName], os.path.join(currentPath, name_to_id(questName)))
                        except KeyError:
                            print(f"Warn > Series '{questName}' not found in '{region}'.", end="\t\t\t\t\t\t\t\t\n")
                        
    def download_image(self, url:str, name:str):
        path = os.path.join(os.environ["imgPath"], name)
        if not os.path.exists(path):
            resp = requests.get(url)
            with open(path, "wb") as img:
                img.write(resp.content)
    
    def allData(self):
        # Download placeholder images
        placeholders = [74, 256]
        for placeholder in placeholders:
            self.download_image(f"https://placehold.co/{placeholder}/gray/white.png?text=Placeholder%5Cn{placeholder}x{placeholder}", f"{placeholder}.png")
        self.download_image("https://placehold.co/74/gray/white.png?text=More", "!Img_more.png")
        self.download_image("https://placehold.co/74/gray/white.png?text=Close", "!Img_close.png")
        
        self._allWorldQuests()
        generator = self._allWorldQuestsData()
        while True:
            try:
                yield next(generator)
            except StopIteration:
                break
