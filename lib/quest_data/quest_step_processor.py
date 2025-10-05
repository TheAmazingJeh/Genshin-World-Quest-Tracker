"""
Shared utilities for processing quest steps across different quest types.

This module contains common functionality for processing HTML content 
into structured step data, avoiding code duplication across QuestSingle, 
QuestSeries, and QuestAct classes.
"""

from utils.file_functions import get_image_path, name_to_id


def process_step_images(tag, quest_img_urls):
    """
    Process images within step items and update quest_img_urls list.
    
    Args:
        tag: BeautifulSoup tag containing the step
        quest_img_urls: List to append image URLs to
    
    Returns:
        dict: Dictionary mapping image IDs to paths
    """
    step_images = {}
    stepItems = tag.select('span.item')
    
    if stepItems:
        for item in stepItems:              
            img_tag = item.select_one('img')
            if img_tag:
                # Get the image src (data-src if available, else src)
                img_src = (img_tag['data-src'] if 'data-src' in img_tag.attrs else img_tag['src']).rsplit('.png')[0] + ".png"
                quest_img_urls.append(img_src)
                # Replace img tag with placeholder
                img_id = name_to_id(img_tag['alt'])
                img_tag.replace_with(f"<img:{img_id}>")
                step_images[img_id] = get_image_path(img_src)
    
    return step_images


def process_step_links(tag, stepItems):
    """
    Process anchor tags within a step, formatting them as markdown.
    
    Args:
        tag: BeautifulSoup tag containing the step
        stepItems: List of step items that may contain images
    """
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


def process_text_step(tag_type, tag, quest_img_urls):
    """
    Process a text-based step (p, li, etc.) and extract structured data.
    
    Args:
        tag_type: String representing the HTML tag type
        tag: BeautifulSoup tag to process
        quest_img_urls: List to append image URLs to
    
    Returns:
        dict: Structured step data
    """
    # Initialize the step dictionary
    step_dict = {
        "tag": tag_type,
        "text": None,
        "img": {}
    }
    
    # Remove any span with the class "mobile-only"
    for span in tag.select('span.mobile-only'): 
        span.decompose()

    # Check if the step has a span tag with class "item"
    stepItems = tag.select('span.item')

    # Process images in stepItems
    step_images = process_step_images(tag, quest_img_urls)
    step_dict["img"].update(step_images)

    # Format all anchor tags in the step using markdown
    process_step_links(tag, stepItems)
                
    # Extract text content
    step_dict["text"] = tag.get_text().split('\n')[0].strip()
    
    # Remove empty img dict
    if step_dict['img'] == {}: 
        del step_dict['img']
        
    return step_dict


def process_list_step(tag_type, tag, quest_img_urls, use_scope_selector=True):
    """
    Process a list step (ol, ul) and extract structured data including substeps.
    
    Args:
        tag_type: String representing the HTML tag type (ol or ul)
        tag: BeautifulSoup tag to process
        quest_img_urls: List to append image URLs to
        use_scope_selector: Whether to use :scope selector for direct children
    
    Returns:
        dict: Structured step data with nested substeps
    """
    internal_step_dict = {
        "tag": tag_type,
        "steps": []
    }

    # Select list items - use different selectors based on quest type
    if use_scope_selector:
        list_items = tag.select(':scope > li')  # Only find direct child list items
    else:
        list_items = tag.select('li')

    for step in list_items:
        # For non-scope selector, check if step is direct child
        if not use_scope_selector and step.parent != tag:
            continue

        # Check if a step has a child <ol> or <ul> tag
        if use_scope_selector:
            sub_steps = step.select(':scope > ol, :scope > ul')  # Only find direct child lists
        else:
            sub_steps = step.select('ol, ul')
        
        # Remove the sub-step from the current step to avoid duplication
        if sub_steps: 
            for sub_step in sub_steps:
                sub_step.extract()

        # Add the current step first
        internal_step_dict["steps"].append(process_text_step("li", step, quest_img_urls))
        
        # Process substeps immediately after the parent step to maintain order
        if sub_steps:
            for sub_step in sub_steps:
                internal_step_dict["steps"].append(
                    process_list_step(sub_step.name, sub_step, quest_img_urls, use_scope_selector)
                )

    return internal_step_dict


def extract_steps_from_soup(soup, quest_img_urls, quest_name, quest_type="single"):
    """
    Extract steps from BeautifulSoup object based on quest type.
    
    Args:
        soup: BeautifulSoup object of the quest page
        quest_img_urls: List to append image URLs to
        quest_name: Name of the quest for warning messages
        quest_type: Type of quest ("single", "series", "act")
    
    Returns:
        list: List of structured step data
    """
    step_list = []
    correct_area = False

    # Loop through h2, h3, p, ol and ul tags to find the steps
    for tag in soup.select("h2, h3, p, ol, ul"):
        # Determine if we're in the correct section based on quest type
        if quest_type == "single":
            if tag.name == "h2" and tag.get_text() == "Steps":
                correct_area = True
                continue  # Skip the "Steps" header itself
            if tag.name == "h2":
                correct_area = False
        elif quest_type == "series":
            if tag.name == "h2" and tag.get_text().startswith("List of "):
                correct_area = True
                continue
            if tag.name == "h2" and tag.get_text() == "Summary":
                correct_area = False
        elif quest_type == "act":
            if tag.name == "h2" and tag.get_text() == "Quests":
                correct_area = True
                continue
            if tag.name == "h2" and tag.get_text() == "Summary":
                correct_area = False
        
        # If we're in the correct section, process the tag
        if correct_area:
            if tag.name in ["h2", "h3"]:
                step_list.append({"tag": "h", "text": tag.get_text()})
            elif tag.name == "p":
                step_list.append(process_text_step("p", tag, quest_img_urls))
            elif tag.name in ["ol", "ul"]:
                # Check if tag has a parent
                if tag.parent is not None:
                    # Use scope selector for single quests, regular selector for others
                    use_scope = quest_type == "single"
                    step_list.append(process_list_step(tag.name, tag, quest_img_urls, use_scope))

    if step_list == []:
        print(f"WARN: {quest_name} has no steps ({quest_type})")

    return step_list