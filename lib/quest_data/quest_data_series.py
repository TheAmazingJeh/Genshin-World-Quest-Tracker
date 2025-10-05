from utils.file_functions import get_image_path, name_to_id

from lib.quest_data.quest_data import Quest

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
            for span in tag.select('span.mobile-only'): 
                span.decompose()

            # Check if the step has a span tag with class "item"
            # This indicates that the step has a either a combat section or an item section
            stepItems = tag.select('span.item')

            # First process images in stepItems
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

            # Format all a tags in the step using markdown
            for a_tag in tag.select('a'):
                # Check if this a_tag is inside a stepItem (which would contain an image)
                ignore = False
                if stepItems:
                    for item in stepItems:
                        if item.find(a_tag):  # Check if a_tag is a descendant of this item
                            ignore = True
                            break
                
                # If the a tag is not part of an image item, format it using markdown
                if not ignore:
                    # Check if <img: in the a tag text (If it is an image tag, ignore it)
                    if "<img:" not in a_tag.get_text():
                        # Check if a_tag has a href attribute
                        if 'href' in a_tag.attrs:
                            a_tag.replace_with(f"◀{a_tag.get_text()}▶◁{a_tag['href']}▷")
                        else:
                            print(f"Warning: {a_tag} does not have a href attribute")
                
            # If the step does not have a sub-step, add the step to the list
            step_dict["text"] = tag.get_text().split('\n')[0].strip()
            if step_dict['img'] == {}: 
                del step_dict['img']
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
            if tag.name == "h2" and tag.get_text().startswith("List of "):
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
                    if tag.parent is not None:
                        step_list.append(process_list(tag.name, tag))
        
        if step_list == []:
            print(f"WARN: {self.quest_data['name']} has no steps (series)")
        return step_list

    
    def when_created(self) -> None:
        self.quest_data["rewards"] = self.get_rewards()
        self.quest_data["steps"] = self.get_steps()