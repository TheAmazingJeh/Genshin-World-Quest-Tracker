from utils.file_functions import get_image_path
from lib.quest_data.quest_data import Quest
from lib.quest_data.quest_step_processor import extract_steps_from_soup

class QuestSeries(Quest):
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "series"
        self.when_created()
        self.cleanup()

    def get_rewards(self) -> list:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        card_containers = soup.select('div[class="card-container"]')
        if not card_containers: 
            return None
        
        # List to hold the rewards
        rewards = []

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
            # Get the value of the card using the path span > span > span:nth-child(2) inner text
            current_reward['Value'] = card_container.select_one('span[class="card-text card-font"]').get_text().strip()
            
            # Get the Name of the item using the title parameter of the a tag
            current_reward['Name'] = inner_span.select_one('a')['title']
            # Get the class parameter of the spa
            current_reward['Rarity'] = outer_span["class"][1].replace('card-quality-', "")
            # Get the link of the item using the href parameter of the a tag
            current_reward['Link'] = inner_span.select_one('a')['href']
            # Check if there is an image tag in the span
            if inner_span.select_one('a > img'):
                # Get the image of the item using the data-src parameter of the img tag, or the src parameter if the data-src parameter is not found
                try: 
                    img = inner_span.select_one('a > img')['data-src']
                except KeyError: 
                    img = inner_span.select_one('a > img')['src']
            else:
                img = "https://static.wikia.nocookie.net/gensin-impact/images/f/f8/Icon_Emoji_Paimon%27s_Paintings_02_Qiqi_1.png"
            current_reward['Image'] = get_image_path(img)
            self.quest_img_urls.append(img)
            rewards.append(current_reward)

        return rewards

    def get_steps(self) -> list:
        return extract_steps_from_soup(
            self.soup, 
            self.quest_img_urls, 
            self.quest_data['name'], 
            "series"
        )

    
    def when_created(self) -> None:
        self.quest_data["rewards"] = self.get_rewards()
        self.quest_data["steps"] = self.get_steps()