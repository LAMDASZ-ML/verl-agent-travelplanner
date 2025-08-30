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
    total_pattern = r"^.*<action>.*?</action>.*$"
    valids = [0] * len(text_actions)
    for i in range(len(text_actions)):
        if re.match(total_pattern, text_actions[i], re.DOTALL):
            valids[i] = 1
        else:
            valids[i] = 0

    thoughts = [None] * len(text_actions)
    plans = [None] * len(text_actions)
    actions = [None] * len(text_actions)
    ISs = [None] * len(text_actions)
    thought_pattern = r"<think>(.*?)</think>"
    action_pattern = r"<action>(.*?)</action>"
    plan_pattern = r"<plan>(.*?)</plan>"
    IS_pattern = r"<IS>(.*?)</IS>"
    for i in range(len(text_actions)):
        # Extract <think>...</think>
        think_match = re.search(thought_pattern, text_actions[i], re.DOTALL)
        thoughts[i] = think_match.group(1).strip() if think_match else ""

        # Extract <action>...</action>
        action_match = re.search(action_pattern, text_actions[i], re.DOTALL)
        actions[i] = action_match.group(1).strip() if action_match else ""

        # Extract <plan>...</plan>
        plan_match = re.search(plan_pattern, text_actions[i], re.DOTALL)
        plans[i] = plan_match.group(1).strip() if plan_match else ""
        
        # Extract <IS>...</IS>
        IS_match = re.search(IS_pattern, text_actions[i], re.DOTALL)
        ISs[i] = IS_match.group(1).strip() if IS_match else ""
    return valids, actions, thoughts, plans,ISs
