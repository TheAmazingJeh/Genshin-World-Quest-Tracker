from lib.quest_data.quest_data import Quest, get_quest_rewards
from lib.quest_data.quest_step_processor import extract_steps_from_soup

class QuestSingle(Quest):
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "single"
        self.when_created()
        self.cleanup()
    
    def get_starting_location(self) -> dict[str,str]:
        soup = self.soup
        
        # Select the target div using the data-source attribute
        target_div = soup.select_one('div[data-source="startLocation"]')
        if not target_div: 
            return None
        
        # Select the div with start location data in it
        data_value_div = target_div.select_one('div[class*="pi-data-value"]') if target_div else None

        # Extract and clean the text content by removing links and generating markdown
        if data_value_div:
            # List to hold markdown text parts
            markdown_parts = []

            # Iterate over all child nodes of the data_value_div
            for element in data_value_div.children:
                # If the element is a string, add its text to the list
                if isinstance(element, str):
                    markdown_parts.append(element.strip())
                
                # If the element is a Tag and is an <a> tag, add its text to the list
                elif element.name == 'a':
                    link_text = element.get_text()
                    link_href = element['href']
                    markdown_parts.append(f'◀{link_text}▶◁{link_href}▷')
            
            # Join the text parts with spaces
            markdown_text = ' '.join(markdown_parts).strip()
        else:
            raise Exception("Start location not found in the page, but `startLocation` div was found.")
        
        return {
            "text": markdown_text
        }    
    
    def get_requirements(self) -> dict[str,str]:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        target_div = soup.select_one('div[data-source="requirement"]')
        if not target_div: 
            return None
        
        # Select the div with class "pi-data-value pi-font" inside the target div
        data_value_div = target_div.select_one('div[class*="pi-data-value"]') if target_div else None

        # Extract and clean the text content by removing links and generating markdown
        if data_value_div:
            # List to hold plain text parts
            text_parts = []
            # List to hold markdown text parts
            markdown_parts = []

            # Iterate over all child nodes of the data_value_div
            for element in data_value_div.children:
                # If the element is a NavigableString, add its text to the list
                if isinstance(element, str):
                    text_parts.append(element.strip())
                    markdown_parts.append(element.strip())
                # If the element is a Tag and is an <a> tag, add its text to the list
                elif element.name == 'a':
                    link_text = element.get_text()
                    link_href = element['href']
                    text_parts.append(link_text)
                    markdown_parts.append(f'◀{link_text}▶◁{link_href}▷')
            
            # Join the text parts with spaces
            markdown_text = ' '.join(markdown_parts).strip()
        else:
            raise Exception("Requirements not found in the page but `requirement` div was found.")
        
        return {
            "markdown": markdown_text
        }    

    def get_rewards(self) -> list:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        target_div = soup.select_one('div[data-source*="rewards"]')
        if not target_div: 
            return None

        rewards, quest_image_urls = get_quest_rewards(target_div)
        self.quest_img_urls.extend(quest_image_urls)

        return rewards

    def get_steps(self) -> list:
        return extract_steps_from_soup(
            self.soup, 
            self.quest_img_urls, 
            self.quest_data['name'], 
            "single"
        )
    
    def get_dialogue(self) -> bool:
        soup = self.soup
        dialogue_div = soup.select_one('div[class="dialogue"]')
        return True if dialogue_div else False

    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = self.get_starting_location()
        self.quest_data["requirements"] = self.get_requirements()
        self.quest_data["rewards"] = self.get_rewards()
        self.quest_data["steps"] = self.get_steps()
        self.quest_data["dialogue"] = self.get_dialogue()