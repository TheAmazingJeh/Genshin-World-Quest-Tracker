from lib.page.get_page import get_local_page
from lib.page.get_wiki_url_from_name import get_wiki_url_from_name
from utils.file_functions import get_image_path

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

def get_quest_rewards(soup:BeautifulSoup):
    # Get all cards
    card_containers = soup.select('div[class*="card-container"]') if soup else None

    # List to hold the rewards
    rewards = []
    quest_image_urls = []

    # Iterate over all card containers
    for card_container in card_containers:
        current_reward = {
            "Name": "",
            "Value": "",
            "Link": "",
            "Image": ""
        }
        outer_span = card_container.select_one('span > span > span:nth-child(1)')
        inner_span = outer_span.select_one('span')
        # Get the amount of the item using the card-text class
        try: current_reward['Value'] = card_container.select_one('span[class*="card-text"]').get_text().strip()
        except Exception: current_reward['Value'] = "1"
        # Get the Name of the item using the title parameter of the a tag
        current_reward['Name'] = card_container.select_one('a')['title']
        # Get the rarity of the item from the class of the card-image-container span
        # Search for the class that contains "rarity-"
        rarity_temp = card_container.select_one('span[class*="card-image-container"]')['class']
        current_reward['Rarity'] = [cls for cls in rarity_temp if cls.startswith('card-quality-')][0].replace('card-quality-', '')
        # Get the link of the item using the href parameter of the a tag
        current_reward['Link'] = inner_span.select_one('a')['href']
        # Check if there is an image tag in the span
        if inner_span.select_one('a > img'):
            # Get the image of the item using the data-src parameter of the img tag, or the src parameter if the data-src parameter is not found
            try: img = inner_span.select_one('a > img')['data-src']
            except KeyError: img = inner_span.select_one('a > img')['src']
        else:
            img = "https://static.wikia.nocookie.net/gensin-impact/images/f/f8/Icon_Emoji_Paimon%27s_Paintings_02_Qiqi_1.png"
        current_reward['Image'] = get_image_path(img)
        quest_image_urls.append(img)
        rewards.append(current_reward)
    
    return rewards, list(set(quest_image_urls))