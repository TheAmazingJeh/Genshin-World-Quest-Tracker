from bs4 import BeautifulSoup
from copy import deepcopy

from utils.file_functions import get_image_path, name_to_id

from lib.quest_data.quest_data import Quest

class QuestSingle(Quest):
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "single"
        self.when_created()
        self.cleanup()
    
    def get_starting_location(self) -> dict[str,str]:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        target_div = soup.select_one('div[data-source="startLocation"]')
        if not target_div: return None
        
        # Select the div with class "pi-data-value pi-font" inside the target div
        data_value_div = target_div.select_one('div[class="pi-data-value pi-font"]') if target_div else None

        # Extract and clean the text content by removing links and generating markdown
        if data_value_div:
            # List to hold markdown text parts
            markdown_parts = []

            # Iterate over all child nodes of the data_value_div
            for element in data_value_div.children:
                # If the element is a NavigableString, add its text to the list
                if isinstance(element, str):
                    markdown_parts.append(element.strip())
                # If the element is a Tag and is an <a> tag, add its text to the list
                elif element.name == 'a':
                    link_text = element.get_text()
                    link_href = element['href']
                    markdown_parts.append(f'◀{link_text}▶◁{link_href}▷')
            
            # Join the text parts with spaces
            markdown_text = ' '.join(filter(None, markdown_parts)).strip()
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
        if not target_div: return None
        
        # Select the div with class "pi-data-value pi-font" inside the target div
        data_value_div = target_div.select_one('div[class="pi-data-value pi-font"]') if target_div else None

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
            plain_text = ' '.join(filter(None, text_parts)).strip()
            markdown_text = ' '.join(filter(None, markdown_parts)).strip()
        else:
            raise Exception("Requirements not found in the page but `requirement` div was found.")
        
        return {
            "plaintext": plain_text,
            "markdown": markdown_text
        }    

    def get_rewards(self) -> list:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        target_div = soup.select_one('div[data-source="rewards"]')
        if not target_div: return None

        # Get all elements with class "card-container"
        card_containers = target_div.select('div.card-container') if target_div else None

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
            # Get the rarity of the item using the class parameter of the span tag
            current_reward['Rarity'] = outer_span["class"][1].replace('card-quality-', "")
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
            self.quest_img_urls.append(img)
            rewards.append(current_reward)

        return rewards

    def get_steps(self) -> list:
        def process_text(tagType, tag):
            # Initialize the step dictionary
            step_dict = {
                "tag": tagType,
                "text": None,
                "img": {}
            }

            # # Check if the step has a child <ol> or <ul> tag
            # # This indicates that the step has sub-steps
            # sub_step = tag.select_one('ol') or tag.select_one('ul')

            # # Remove the sub-step from the current step
            # # This avoids duplication of data
            # if sub_step: sub_step.extract()
            
            # # replace × with x in the entire step
            # step = BeautifulSoup(str(step).replace('×', 'x'), 'lxml')

            # Remove any span with the class "mobile-only"
            for span in tag.select('span.mobile-only'): span.decompose()

            # Check if the step has a span tag with class "item"
            # This indicates that the step has a either a combat section or an item section
            stepItems = tag.select('span.item')

            # Format all a tags in the step using markdown
            for a_tag in tag.select('a'):
                ignore = False
                if stepItems:
                    for item in stepItems:              
                        img_tag = item.select_one('img')
                        if img_tag:
                            # Get the image src (data-src if available, else src)
                            img_src = (img_tag['data-src'] if 'data-src' in img_tag.attrs else img_tag['src']).rsplit('.png')[0] + ".png"
                            self.quest_img_urls.append(img_src)
                            # resize the image to 20x20
                            # img_src = resize(img_src, 20, 20)
                            img_tag.replace_with(f"<img:{name_to_id(img_tag['alt'])}>")
                            step_dict["img"][f"{name_to_id(img_tag['alt'])}"] = get_image_path(img_src)
                            ignore = True
                
                # If the a tag does not have an img tag as a child, format it using markdown
                if not ignore:
                    # Check if <img: in the a tag text (If it is an image tag, ignore it)
                    if not "<img:" in a_tag.get_text():
                        # Check if a_tag has a href attribute
                        if 'href' in a_tag.attrs:
                            a_tag.replace_with(f"◀{a_tag.get_text()}▶◁{a_tag['href']}▷")
                        else:
                            print(f"Warning: {a_tag} does not have a href attribute")

            # If the step does not have a sub-step, add the step to the list
            step_dict["text"] = tag.get_text().split('\n')[0].strip()
            if step_dict['img'] == {}: del step_dict['img']
            return step_dict

        def process_list(tagType, tag):
            internal_step_dict = {
                "tag": tagType,
                "steps": []
            }

            for step in tag.select('li'):
                # Check if the step is a child of an <ol> or <ul> tag
                # This indicates that the step is a sub-step
                if step.parent != tag:
                    continue

                # Check if a step has a child <ol> or <ul> tag
                # This indicates that the step has sub-steps
                sub_steps = step.select('ol ul')
                # Remove the sub-step from the current step
                # This avoids duplication of data

                if sub_steps: 
                    for sub_step in sub_steps:
                        sub_step.extract()

                internal_step_dict["steps"].append(process_text("li", step))
                # Process substeps
                if sub_steps:
                    for sub_step in sub_steps:
                        internal_step_dict["steps"].append(process_list(sub_step.name, sub_step))

            return internal_step_dict

        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        read = False
        step_list = []

        # Loop through h2, p, ol and ul tags to find the steps
        for tag in soup.select("h2, h3, p, ol, ul"):
            if tag.name == "h2" and tag.get_text() == "Steps":
                read = True
                continue
            if tag.name == "h2":# and tag.get_text() == "Dialogue":
                read = False
            
            # If the current section is in bounds, process the tag
            if read:
                if tag.name in ["h2", "h3"]:
                    step_list.append({"tag": "h", "text": tag.get_text()})
                if tag.name == "p":
                    step_list.append(process_text("p", tag))
                if tag.name in ["ol", "ul"]:
                    # Check if tag has a pzarent
                    if tag.parent != None:
                        step_list.append(process_list(tag.name, tag))
        
        if step_list == []:
            print(f"WARN: {self.quest_data['name']} has no steps (single)")

        return step_list
    
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