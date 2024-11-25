from lib.page.get_page import get_local_page
from lib.page.get_wiki_url_from_name import get_wiki_url_from_name

from bs4 import BeautifulSoup

class Quest:
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        self.quest_url = get_wiki_url_from_name(name, conversionRef)
        self.quest_img_urls = []
        self.html = get_local_page(self.quest_url, basepath)
        self.soup = BeautifulSoup(self.html, 'lxml')

        self.quest_data = {
            "version": "1.1", # Version of the quest data (For error checking)
            "type": "",       # Single or Series
            "name": conversionRef[name], # Name of the quest
            "url": self.quest_url, # URL for the quest
        }
    
    def get_starting_location(self, html:str) -> str:
        raise NotImplementedError("Method `get_starting_location` not implemented")
    
    def get_requirements(self, html:str) -> dict[str,str]:
        raise NotImplementedError("Method `get_requirements` not implemented")
    
    def get_rewards(self, html:str) -> list[str]:
        raise NotImplementedError("Method `get_rewards` not implemented")
    
    def get_steps(self, html:str) -> list[str]:
        raise NotImplementedError("Method `get_steps` not implemented")
    
    def get_dialogue(self, html:str) -> bool:
        raise NotImplementedError("Method `get_dialogue` not implemented")
    
    def when_created(self) -> None:
        raise NotImplementedError("Method `when_created` not implemented")
    
    def cleanup(self) -> None:
        del self.html
        self.html = None

    def get_data(self) -> dict:
        return self.quest_data

