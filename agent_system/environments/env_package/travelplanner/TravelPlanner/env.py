import os
import sys
import json
import inspect
import importlib
from typing import Literal

import re
import gymnasium as gym
from gymnasium import spaces
from typing import Any, Dict, List, Tuple
from datasets import load_dataset
from pandas import DataFrame

from .evaluation.commonsense_constraint import (
    evaluation as commonsense_eval,
)
from .evaluation.hard_constraint import evaluation as hard_eval
from .tools import *

_file_path = os.path.dirname(os.path.abspath(__file__))
if _file_path not in sys.path:
    sys.path.append(_file_path)

actionMapping = {
    "FlightSearch": "flights",
    "AttractionSearch": "attractions",
    "GoogleDistanceMatrix": "googleDistanceMatrix",
    "AccommodationSearch": "accommodations",
    "RestaurantSearch": "restaurants",
    "Planner": "planner",
    "NotebookWrite": "notebook",
    "CitySearch": "cities",
}
actionMappingReverse = {
    v: k for k, v in actionMapping.items()
}  # e.g. flights -> FlightSearch, attractions -> AttractionSearch


def load_dataset_dict():
    """
    Load the dataset dictionary for the Travel Planner environment.
    This function is used to load the dataset from the Hugging Face hub.
    """
    train_data = load_dataset(
        "osunlp/TravelPlanner", "train", download_mode="reuse_dataset_if_exists"
    )["train"]
    validation_data = load_dataset(
        "osunlp/TravelPlanner", "validation", download_mode="reuse_dataset_if_exists"
    )["validation"]
    return {
        "train": train_data,
        "validation": validation_data,
    }


def load_tools() -> Dict[str, Any]:
    tools_map = {}
    tools = [
        "notebook",
        "flights",
        "attractions",
        "accommodations",
        "restaurants",
        "googleDistanceMatrix",
        "cities",
    ]
    for tool_name in tools:
        tool_cls = globals()[tool_name[0].upper() + tool_name[1:]]
        sig = inspect.signature(tool_cls.__init__)
        if "path" in sig.parameters:
            new_path_str = str(sig.parameters["path"].default).replace("..", _file_path)
            instance = tool_cls(path=new_path_str)
        else:
            instance = tool_cls()
        tools_map[tool_name] = instance
    tools_map = {actionMappingReverse.get(k, k): v for k, v in tools_map.items()}
    for k in list(tools_map.keys()):
        if k not in actionMappingReverse.values():
            del tools_map[k]
    return tools_map


class TravelPlannerEnv(gym.Env):

    DATA_DICT = {
        "train": None,
        "validation": None,
    }

    tools = load_tools()

    def __init__(
        self,
        max_retries: int = 3,
        max_steps: int = 30,
        seed: int = 42,
        split: Literal["train", "validation"] = "train",
    ):
        super(TravelPlannerEnv, self).__init__()

        self.max_retries = max_retries
        self.max_steps = max_steps
        self.step_count = 0
        self.valid_action_count = 0

        self.action_space = spaces.Text(max_length=131072)
        self.observation_space = spaces.Text(max_length=131072)

        self.tool_names = list(self.tools.keys())
        self.retry_record = {name: 0 for name in self.tool_names}
        self.retry_record["InvalidAction"] = 0

        # self.query_data_list = self.DATA_DICT[split]
        if self.DATA_DICT[split] is None:
            self.DATA_DICT[split] = load_dataset(
                "osunlp/TravelPlanner",
                split,
                download_mode="reuse_dataset_if_exists",
            )[split]
        self.query_data_list = self.DATA_DICT[split]
        self.query_idx = -1

        self.done = False

    def reset(self, idx=None) -> str:
        self.retry_record = {name: 0 for name in self.retry_record}

        self.step_count = 0
        self.valid_action_count = 0
        self.done = False
        self.query_idx += 1
        self.query_idx %= len(self.query_data_list)

        return (
            self.query_data_list[self.query_idx]["query"],
            {
                "won": False,
                "state": "",
                "error": "",
                "plan_reward": 0.0,
                "valid_action_ratio": 0.0,
                "cur_action_is_valid": False,
                "info": self.query_data_list[self.query_idx],
            },
        )


    def _cal_plan_reward(self, plan: str) -> float:
        """Calculate the reward for a given plan."""
        query_data = self.query_data_list[self.query_idx]
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError:
            return 0.0
        commonsense_info_box = commonsense_eval(query_data, plan)
        hard_logic_info_box = hard_eval(query_data, plan)
        # 每个box为key:(bool, info) bool表示是否满足，info为具体信息
        commonsense_bool_list = [v[0] for k, v in commonsense_info_box.items()]
        hard_logic_bool_list = [v[0] for k, v in hard_logic_info_box.items()]
        return (sum(commonsense_bool_list) + sum(hard_logic_bool_list)) / (
            len(commonsense_bool_list) + len(hard_logic_bool_list)
        )

    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """
        action: action_type[action_arg1, action_arg2, ...] # String format
        """
        info = {}
        info["state"] = ""
        info["error"] = ""
        info["plan_reward"] = 0.0
        info["won"] = False
        info["valid_action_ratio"] = 0.0
        obs = ""
        reward = 0.0
        if self.done:
            info["error"] = "Environment is done, please reset."

        action_type, action_arg = self._parse_action(action)
        self.step_count += 1

        if action_type == "Finish":
            self.done = True
            try:
                plan = (
                    re.search(r"<plan>(.*?)</plan>", action, re.DOTALL).group(1).strip()
                )
                info["plan_reward"] = self._cal_plan_reward(plan)
                info["state"] = "Success"
                info["won"] = True if info["plan_reward"] == 1.0 else False
                self.valid_action_count += 1
            except:
                info["plan_reward"] = 0.0
                info["error"] = "No valid plan found."
                info["won"] = False
            obs = "Task finished."
        if action_type not in self.tools:
            self.retry_record["InvalidAction"] += 1
            info["error"] = "InvalidAction"
            obs = f"Invalid action: {action_type}."
        else:
            try:
                result = self._call_tool(action_type, action_arg)
                obs = str(result)
                info["state"] = "Success"
                self.retry_record[action_type] = 0

            except Exception as e:
                self.retry_record[action_type] += 1
                obs = str(e)
                info["error"] = type(e).__name__

        # 判断终止条件
        if (
            self.retry_record[action_type] >= self.max_retries
            or self.step_count >= self.max_steps
        ):
            self.done = True
        info["won"] = False
        reward = info["plan_reward"]
        info["valid_action_ratio"] = (
            self.valid_action_count / self.step_count if self.step_count > 0 else 0.0
        )
        return obs, reward, self.done, info

    def _call_tool(self, action_type: str, action_arg: str) -> Any:
        if action_type == "FlightSearch":
            depart, dest, date = [x.strip() for x in action_arg.split(",")]
            obs = self.tools[action_type].run(depart, dest, date)
        elif action_type == "GoogleDistanceMatrix":
            depart, dest, mode = [x.strip() for x in action_arg.split(",")]
            obs = self.tools[action_type].run(depart, dest, mode)
        else:
            obs = self.tools[action_type].run(action_arg)
        if isinstance(obs, DataFrame):
            obs = obs.to_string(
                index=False,
                max_cols=None,
                max_rows=None,
                max_colwidth=None,
                justify="left",
            )
        return obs

    def _parse_action(self, action: str) -> Tuple[str, str]:
        """
        Parses the action string into action type and argument.
        """

        # 首先提取<action> </action>之间的内容
        action_cmd = re.search(r"<action>(.*?)</action>", action, re.DOTALL)
        if action_cmd:
            action_cmd = action_cmd.group(1).strip()
        else:
            return "InvalidAction", ""

        pattern = r"^(\w+)\[(.+)\]$"
        match = re.match(pattern, action_cmd)

        try:
            if match:
                action_type = match.group(1).strip()
                action_arg = match.group(2).strip()
                if not action_type in self.tools:
                    return "InvalidAction", ""
                return action_type, action_arg
            else:
                return "InvalidAction", ""

        except:
            return "InvalidAction", ""

    @property
    def query(self) -> str:
        """
        Returns the current query from the dataset.
        """
        if self.query_idx < 0 or self.query_idx >= len(self.query_data_list):
            return ""
        return self.query_data_list[self.query_idx]["query"]


# Register the environment with Gym
gym.register(
    id="TravelPlanner-v0",
    entry_point=TravelPlannerEnv,
)
print("[TravelPlannerEnv] Environment registered.")


if __name__ == "__main__":
    # env = TravelPlannerEnv()
    env = gym.make("TravelPlanner-v0", split="train")
    print(env.reset())
    print(env.step("FlightSearch[New York, Los Angeles, 2023-10-01]"))
    print(env.step("AttractionSearch[Los Angeles]"))
    print(env.step("InvalidAction[Some argument]"))
    print(env.step("FlightSearch[New York, San Francisco, 2023-10-02]"))
    print(env.step("Plan[Plan a trip from New York to Los Angeles]"))