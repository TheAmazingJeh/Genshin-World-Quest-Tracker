from lib.quest_data.quest_data import Quest
from lib.quest_data.quest_step_processor import extract_steps_from_soup

class QuestAct(Quest):
    def __init__(self, name:str, basepath:str, questDict:dict, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "act"
        self.tempQuestDict = questDict
        self.when_created()
        self.cleanup()
    
    def get_starting_location(self) -> dict[str,str]:
        for region in self.tempQuestDict["regions"]:
            for questSeries in self.tempQuestDict["regions"][region]["series"]:
                if isinstance(self.tempQuestDict["regions"][region]["series"][questSeries][0], dict):
                    for quest in self.tempQuestDict["regions"][region]["series"][questSeries]:
                        if quest["name"] == self.quest_data["name"]:
                            return {"text": region}

    def get_steps(self) -> list:
        return extract_steps_from_soup(
            self.soup, 
            self.quest_img_urls, 
            self.quest_data['name'], 
            "act"
        )

    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = self.get_starting_location()
        self.quest_data["rewards"] = None
        self.quest_data["steps"] = self.get_steps()