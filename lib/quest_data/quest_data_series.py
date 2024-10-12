from bs4 import BeautifulSoup
from copy import deepcopy
from utils.file_functions import get_image_path


from lib.quest_data.quest_data import Quest

class QuestSeries(Quest):
    def __init__(self, name:str, basepath:str, conversionRef:dict) -> None:
        super().__init__(name, basepath, conversionRef)
        self.quest_data["type"] = "series"
        self.when_created()
        self.cleanup()
    
    def get_starting_location(self) -> dict[str,str]:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup

        # Select the target div using the data-source attribute
        region = soup.select_one('div[data-source="region"]')
        if not region: return None

        # Select the div with class "pi-data-value pi-font" inside the target div
        data_value_div = region.select_one('div[class="pi-data-value pi-font"]') if region else None

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
            raise Exception("Start location not found in the page, but `startLocation` div was found.")
        
        return {
            "plaintext": plain_text,
            "markdown": markdown_text
        }    

    def get_rewards(self) -> list:
        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        
        # Select the target div using the data-source attribute
        card_containers = soup.select('div[class="card-container"]')
        if not card_containers: return None
        
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
            # Get the image of the item using the data-src parameter of the img tag, or the src parameter if the data-src parameter is not found
            try: img = inner_span.select_one('a > img')['data-src']
            except KeyError: img = inner_span.select_one('a > img')['src']
            current_reward['Image'] = get_image_path(img)
            self.quest_img_urls.append(img)
            rewards.append(current_reward)

        return rewards

    def get_steps(self) -> list:
        def loop_through_steps(steps:BeautifulSoup) -> list:
            step_list = []
            for step in steps:
                if step.name == 'li':

                    # Check if the step has a child <ol> or <ul> tag
                    # This indicates that the step has sub-steps
                    sub_step = step.select_one('ol') or step.select_one('ul')
                    # Remove the sub-step from the current step
                    # This avoids duplication of data
                    if sub_step: sub_step.extract()
                    
                    # replace × with x in the entire step
                    step = BeautifulSoup(str(step).replace('×', 'x'), 'lxml')


                    # Remove any span with the class "mobile-only"
                    for span in step.select('span.mobile-only'):
                        span.decompose()

                    # Clone current step to format it using markdown
                    step_md = deepcopy(step)

                    # Initialize the step dictionary
                    step_dict = {
                        "plaintext": "",
                        "markdown": "",
                    }
                    
                    # Format all a tags in the step using markdown
                    for a_tag in step_md.select('a'):   
                        a_tag.replace_with(f"◀{a_tag.get_text()}▶◁{a_tag['href']}▷")

                    # If the step has a sub-step, call the function recursively
                    if sub_step:
                        step_dict["substeps"] = loop_through_steps(sub_step)

                    # If the step does not have a sub-step, add the step to the list
                    step_dict["plaintext"] = step.get_text().strip().split('\n')[0].strip()
                    step_dict["markdown"] = step_md.get_text().split('\n')[0].strip()
                    step_list.append(step_dict)

            return step_list

        # Parse the HTML content with Beautiful Soup
        soup = self.soup

        # Select the target list using the CSS selector <ol>
        steps = soup.select_one("#mw-content-text > div > ol")
        # If the target list is not found, select the target list using the CSS selector <ul> (Thanks Aranyaka)
        if not steps: steps = soup.select_one("#mw-content-text > div > ul")
        step_list = loop_through_steps(steps)
        return step_list

    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = self.get_starting_location()
        self.quest_data["rewards"] = self.get_rewards()
        self.quest_data["steps"] = self.get_steps()