from bs4 import BeautifulSoup
from copy import deepcopy
from utils.file_functions import get_image_path, name_to_id

from lib.quest_data.quest_data import Quest

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
        def process_text(tagType, tag):
            # Initialize the step dictionary
            step_dict = {
                "tag": tagType,
                "text": None,
                "img": {}
            }
            
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
                        a_tag.replace_with(f"◀{a_tag.get_text()}▶◁{a_tag['href']}▷")
                
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
                sub_step = step.select_one('ol') or step.select_one('ul')
                # Remove the sub-step from the current step
                # This avoids duplication of data

                if sub_step: sub_step.extract()

                internal_step_dict["steps"].append(process_text("li", step))
                # Process substeps
                if sub_step:
                    internal_step_dict["steps"].append(process_list(sub_step.name, sub_step))

            return internal_step_dict

        # Parse the HTML content with Beautiful Soup
        soup = self.soup
        read = False
        step_list = []

        # Loop through h2, p, ol and ul tags to find the steps
        for tag in soup.select("h2, h3, p, ol, ul"):
            if tag.name == "h2" and tag.get_text() == "Quests":
                read = True
                continue
            if tag.name == "h2" and tag.get_text() == "Summary":
                read = False
            
            # If the current section is in bounds, process the tag
            if read:
                if tag.name in ["h2", "h3"]:
                    step_list.append({"tag": "h", "text": tag.get_text()})
                if tag.name == "p":
                    step_list.append(process_text("p", tag))
                if tag.name in ["ol", "ul"]:
                    # Check if tag has a parent
                    if tag.parent != None:
                        step_list.append(process_list(tag.name, tag))
        
        if step_list == []:
            print(f"WARN: {self.quest_data['name']} has no steps (act)")
        
        return step_list

    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = self.get_starting_location()
        self.quest_data["rewards"] = None
        self.quest_data["steps"] = self.get_steps()