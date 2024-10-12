from bs4 import BeautifulSoup
from copy import deepcopy

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
                            return {"plaintext": region}

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
        steps = soup.select("#mw-content-text > div > ol")
        # If the target list is not found, select the target list using the CSS selector <ul> (Thanks Aranyaka)
        step_list = []
        if not steps: steps = soup.select("#mw-content-text > div > ul")
        for step in steps:
            step_list.extend(loop_through_steps(step)) 
        return step_list

    
    def when_created(self) -> None:
        self.quest_data["starting_location"] = self.get_starting_location()
        self.quest_data["rewards"] = None
        self.quest_data["steps"] = self.get_steps()