import re
from typing import List


def travelplanner_projection(text_actions: List[str]):
    """
    A function to process the actions.
    actions: the list of actions to be processed, it is a list of strings.
    Expected format:
        <think>some reasoning...</think>
        <action>...</action>
    """
    valids = [0] * len(text_actions)

    thoughts = [""] * len(text_actions)
    plans = [""] * len(text_actions)
    actions = [""] * len(text_actions)
    ISs = [""] * len(text_actions)
    thought_pattern = r"<think>(.*?)</think>"
    action_pattern = r"<action>(.*?)</action>"
    plan_pattern = r"<plan>(.*?)</plan>"
    IS_pattern = r"<IS>(.*?)</IS>"
    
    for i in range(len(text_actions)):
        text = text_actions[i]
        
        # Check if </think> exists in the text
        # Find the last occurrence of </think> instead of just the first one
        think_end_pos = text.rfind('</think>')
        if think_end_pos != -1:
            # If </think> exists, only search after the LAST one for action, plan, IS
            search_text = text[think_end_pos + len('</think>'):]
        else:
            # If </think> doesn't exist, search the entire text
            search_text = text
        
        # Extract <think>...</think> from the entire text (not affected by the rule)
        think_matches = re.findall(thought_pattern, text, re.DOTALL)
        thoughts[i] = think_matches[-1].strip() if think_matches else ""

        # Extract other tags from search_text (after </think> if it exists)
        action_matches = re.findall(action_pattern, search_text, re.DOTALL)
        plan_matches = re.findall(plan_pattern, search_text, re.DOTALL)
        IS_matches = re.findall(IS_pattern, search_text, re.DOTALL)
        
        # Ensure only one match for each tag (except think)
        if len(action_matches)==0:
            actions[i] = ""  # Invalid if multiple matches
            valids[i] = 0
        else:
            actions[i] = action_matches[-1].strip()
            valids[i] = 1

        plans[i] = plan_matches[-1].strip() if plan_matches else ""
        ISs[i] = IS_matches[-1].strip() if IS_matches else ""
            
    return valids, actions, thoughts, plans, ISs
