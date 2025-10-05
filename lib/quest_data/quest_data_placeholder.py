from lib.quest_data.quest_data import Quest

class QuestPlaceholder(Quest):
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "series"
        self.when_created()
        self.cleanup()
    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = None
        self.quest_data["rewards"] = None
        self.quest_data["steps"] = None