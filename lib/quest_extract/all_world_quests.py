from bs4 import BeautifulSoup
from copy import deepcopy
import json

from datetime import datetime

from lib.page.get_page import get_local_page
from utils.file_functions import name_to_id


class WorldQuestSeriesData:
    def __init__(self, paths:dict, conversionRef:dict) -> None:
        self.paths = paths
        self.conversionRefFilePath = conversionRef
        self.conversionRef = {}
        self.all_quests = {}

    def get_subquests(self, subquest:str, soup:BeautifulSoup) -> list:
        result = []
        # Check if the subquests parent has a <ul> tag as a child
        for quest_series in subquest.children:
            # If the child is a <ul> tag (This will be the subquest series)
            if quest_series.name == 'ul':
                # Loop through all children of the <ul> tag (These will be <li> tags)
                for quest_item in quest_series.children:
                    # If the quest item is a quest series
                    if quest_item.find('ul'):
                        subquests = self.get_subquests(quest_item, soup)
                        child_quest_series_name = name_to_id(quest_item.select_one('a')["title"])
                        # Append the subquests to the result list
                        result.append({"name": child_quest_series_name, "subquests": subquests})
                        self.conversionRef[child_quest_series_name] = quest_item.select_one('a')["title"]
                    # If the quest item is a single quest
                    else:
                        result.append(name_to_id(quest_item.select_one('a')["title"]))
                        self.conversionRef[result[-1]] = quest_item.select_one('a')["title"]
        
        return result

    def _internal_getAll(self) -> dict:
        """Requires `_getAllSeries` to be run first to get the quest series."""
        url = "https://genshin-impact.fandom.com/wiki/World_Quest/List"
        html = get_local_page(url, self.paths["cachePath"])

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # Create an empty dictionary to store the data
        data = {}

        # Create a variable to store the current region
        current_region = None
        # Flags to determine if the main section is active and if the current tag should be read
        main_section = False
        read = True
        # Loop through all <h2> tags
        for tag in soup.find_all(['h2', 'h3', 'h4', 'h5', 'ul']):
            # This is the start of the main section
            if tag.name =="h2" and "Mondstadt" in tag.text:
                main_section = True
            # This is the end of the main section
            if tag.name =="h2" and "Adventure Rank Ascension" in tag.text:
                main_section = False

            # If the main section is currently being read
            if main_section:
                # If the tag is a <h2> tag, set read to True
                # This is to re-allow the <ul> tags to be read, if they have been disabled by a previous <h3> tag
                if tag.name == 'h2':
                    read = True
                    #if (span := tag.select_one('span[class="mw-editsection"]')): span.decompose()
                    if (span := tag.select_one('span[class="mw-headline"]')): 
                        span.unwrap()
                    current_region = tag.text
                    data[current_region] = {}
                    data[current_region]["series"] = {}
                    data[current_region]["single"] = []
                
                # If the tag is a <h3> tag, set read to False
                # This is to prevent Random Quests / Events from being added to the list
                if tag.name == 'h3':
                    read = False

                # If the tag is a <h5> tag, set read to False
                # This is to prevent Items like the Crimson Wish Events from being added to the list
                if tag.name == 'h5':
                    read = False

                # If the tag is a <ul> tag and read is True
                if tag.name == 'ul' and read:
                    # Check if the <ul>'s parent is a div
                    if tag.parent.name == 'div':  
                        # Loop through all <li> tags that are a direct child of the <ul> tag
                        for li in tag.find_all('li', recursive=False):
                            # Case for Chapter I to add Bough Keeper: Dainsleif instead of the quest series
                            # This is because "Chapter I" is an archon quest not a world quest
                            if "Chapter I" in li.text:
                                self.conversionRef[name_to_id("Bough Keeper: Dainsleif")] = "Bough Keeper: Dainsleif"
                                data[current_region]["single"].append(name_to_id("Bough Keeper: Dainsleif"))
                                continue
                            # Copy the <li> tag
                            li_copy = deepcopy(li)
                            # Get the title attribute from the <a> tag
                            quest_name = li_copy.select_one('a')['title']
                            # Check if the <li> tag contains any children <ol> or <ul> tags
                            if li_copy.find(['li', 'ul']):
                                self.conversionRef[name_to_id(quest_name)] = quest_name
                                data[current_region]["series"][name_to_id(quest_name)] = self.get_subquests(li_copy, soup)
        
                            else:
                                self.conversionRef[name_to_id(quest_name)] = quest_name
                                data[current_region]["single"].append(name_to_id(quest_name))
                            
        for region in data:
            data[region]["single"].sort()
    
        return data

    def getAll(self):
        """Generator. Returns the progress of the function.
        `string`: The current progress (string)
        `dict`: The resulting dictionary
        """
        yield "Getting all world quests"
        self.all_quests = self._internal_getAll()

        with open(self.conversionRefFilePath, 'w', encoding="utf-8") as file:
            json.dump(self.conversionRef, file, indent=4)

        yield {
            "timeUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "regions": self.all_quests
        }

        