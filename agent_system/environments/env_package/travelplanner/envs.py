import ray
import numpy as np
import gymnasium as gym
from gymnasium import spaces

import re
import json
import traceback
from pandas import DataFrame
from typing import Literal, Tuple, Dict, Any


# -----------------------------------------------------------------------------
# Env for Ray -----------------------------------------------------------------
# -----------------------------------------------------------------------------
@ray.remote(num_cpus=0.2)
class TravelPlannerDataAndToolForRay:
    """
    A class to hold the dataset and tools for Ray remote workers.
    This class is used to pass the dataset and tools to the Ray remote workers.
    """

    def __init__(self, dataset_dict=None, tools=None):
        from .TravelPlanner.env import load_dataset_dict, load_tools
        from .TravelPlanner.evaluation.commonsense_constraint import (
            evaluation as commonsense_eval,
            global_init as commonsense_global_init,
        )
        from .TravelPlanner.evaluation.hard_constraint import (
            evaluation as hard_eval,
            global_init as hard_global_init,
        )
        from .TravelPlanner.tools import (
            Flights,
            Accommodations,
            Restaurants,
            Attractions,
            GoogleDistanceMatrix,
            Cities,
            Notebook,
        )

        self.dataset_dict = dataset_dict or load_dataset_dict()
        # 筛选days==3, visiting_city_number==1的数据
        self.dataset_dict = {
            split: self.dataset_dict[split].filter(
                lambda x: x["days"] == 3 and x["visiting_city_number"] == 1
            )
            for split in self.dataset_dict
        }
        self.tools = tools or load_tools()
        self.commonsense_eval = commonsense_eval
        self.hard_eval = hard_eval

    def get_data_with_split_idx(self, split: str, idx: int):
        idx = idx % len(self.dataset_dict[split])
        return self.dataset_dict[split][idx]

    def get_tools(self):
        return self.tools

    def _cal_plan_reward(self, split, query_idx, plan: str) -> float:
        """Calculate the reward for a given plan."""
        query_data = self.dataset_dict[split][query_idx]
        try:
            plan = json.loads(plan)
        except json.JSONDecodeError:
            return 0.0
        commonsense_info_box = self.commonsense_eval(query_data, plan)
        hard_logic_info_box = self.hard_eval(query_data, plan)
        # 每个box为key:(bool, info) bool表示是否满足，info为具体信息
        commonsense_bool_list = [v[0] for k, v in commonsense_info_box.items()]
        hard_logic_bool_list = [v[0] for k, v in hard_logic_info_box.items()]
        return (sum(commonsense_bool_list) + sum(hard_logic_bool_list)) / (
            len(commonsense_bool_list) + len(hard_logic_bool_list)
        )

    def call_tool(self, action_type: str, action_arg: str) -> Any:
        """Call the tool with the given action type and argument."""
        try:
            if action_type not in self.tools:
                return f"Invalid action type: {action_type}"
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
        except Exception as e:
            obs = f"Invalid action {action_type} with argument {action_arg}: {str(e)}\n{traceback.format_exc()}"
        return obs

    def get_data_len_with_split(self, split: str) -> int:
        """Get the length of the dataset for a given split."""
        return len(self.dataset_dict[split])


class TravelPlannerEnvForRay(gym.Env):

    def __init__(
        self,
        max_retries: int = 3,
        max_steps: int = 30,
        seed: int = 42,
        split: Literal["train", "validation"] = "train",
        ray_data_and_tools_actor=None,
        debug_worker_id: int = 0,
        use_cl: bool = False,
    ):
        super(TravelPlannerEnvForRay, self).__init__()
        self.debug_worker_id = debug_worker_id

        self.shared_data_and_tools_actor = ray_data_and_tools_actor
        self.max_retries = max_retries
        self.max_steps = max_steps
        self.step_count = 0
        self.valid_action_count = 0

        self.action_space = spaces.Text(max_length=131072)
        self.observation_space = spaces.Text(max_length=131072)

        self.tool_names = list(
            ray.get(self.shared_data_and_tools_actor.get_tools.remote()).keys()
        )
        if self.debug_worker_id == 0:
            print(f"Available tools: {self.tool_names}")
        self.retry_record = {name: 0 for name in self.tool_names}
        self.retry_record["InvalidAction"] = 0

        self.query_idx = seed
        self.split = split

        self.done = False

    def reset(self) -> str:
        self.retry_record = {name: 0 for name in self.retry_record}
        self.step_count = 0
        self.valid_action_count = 0
        self.done = False
        self.query_idx += 1
        query_data = ray.get(
            self.shared_data_and_tools_actor.get_data_with_split_idx.remote(
                self.split, self.query_idx
            )
        )
        return (
            query_data["query"],
            {
                "won": False,
                "state": "",
                "error": "",
                "plan_reward": 0.0,
                "valid_action_ratio": 0.0,
                "cur_action_is_valid": False,
                "info": query_data,
            },
        )

    def step(self, action: str) -> Tuple[str, float, bool, Dict]:
        """
        action: action_type[action_arg1, action_arg2, ...] # String format
        """
        if self.debug_worker_id == 0:
            print(f"Action received: {action}")
        info = {
            "state": "",
            "error": "",
            "plan_reward": 0.0,
            "won": False,
            "valid_action_ratio": 0.0,
            "cur_action_is_valid": False,
            "info": None,
        }
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
                # info["plan_reward"] = self._cal_plan_reward(plan)
                info["plan_reward"] = ray.get(
                    self.shared_data_and_tools_actor._cal_plan_reward.remote(
                        self.split, self.query_idx, plan
                    )
                )
                info["state"] = "Success"
                info["won"] = True if info["plan_reward"] == 1.0 else False
                self.valid_action_count += 1
                info["cur_action_is_valid"] = True
            except:
                info["plan_reward"] = 0.0
                info["error"] = "No valid plan found."
                info["won"] = False
            obs = "Task finished."

        try:
            if self.debug_worker_id == 0:
                print(f"Parsed action_type: {action_type}, action_arg: {action_arg}")
            result = self._call_tool(action_type, action_arg)
            obs = str(result)
            info["state"] = "Success"
            self.retry_record[action_type] = 0
            if not obs.startswith("Invalid action"):
                self.valid_action_count += 1
                info["cur_action_is_valid"] = True
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

        last_action = f"{action_type}[{action_arg}]"
        obs = f"Last Action: {last_action}. Don't repeat the same action again!\n" + obs
        if self.debug_worker_id == 0:
            print("Observation Output:", obs)
        return obs, reward, self.done, info

    def _call_tool(self, action_type: str, action_arg: str) -> Any:
        """
        Calls the tool with the given action type and argument.
        Uses the shared data and tools actor to get the result.
        """
        return ray.get(
            self.shared_data_and_tools_actor.call_tool.remote(action_type, action_arg)
        )

    def _parse_action(self, action: str) -> Tuple[str, str]:
        """
        Parses the action string into action type and argument.
        """

        # 首先提取<action> </action>之间的内容
        action_cmd = re.search(r"<action>(.*?)</action>", action, re.DOTALL)
        if self.debug_worker_id == 0:
            print(f"Extracted action command: {action_cmd}")
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
                if not action_type in self.tool_names:
                    return "InvalidAction", ""
                return action_type, action_arg
            else:
                return "InvalidAction", ""

        except:
            return "InvalidAction", ""


class TravelPlannerEnvForRay_CourseLearning_Wrapper(gym.Wrapper):
    """A wrapper for the TravelPlanner environment to handle course learning."""

    DAY_PLAN_TEMPLATE = {
        "days": None,
        "current_city": "-",
        "transportation": "-",
        "breakfast": "-",
        "attraction": "-",
        "lunch": "-",
        "dinner": "-",
        "accommodation": "-",
    }

    def __init__(self, env: TravelPlannerEnvForRay):
        """Initialize the wrapper with the environment and allowed days."""
        super().__init__(env)
        self.env = env

    def reset(self, allowed_days_list=None):
        """Reset the environment and return the initial observation."""

        obs, info = self.env.reset()
        return obs, info

    def _cal_plan_format_reward(self, str_plan: str) -> float:
        """Calculate the reward for a given plan based on allowed days."""
        try:
            plan = json.loads(str_plan)
            for day_idx, day_plan in enumerate(plan):
                if day_plan["days"] != day_idx + 1:
                    return 0.0
                ref_keys = self.DAY_PLAN_TEMPLATE.keys()
                plan_keys = day_plan.keys()
                if set(ref_keys) != set(plan_keys):
                    return 0.0
        except Exception as e:
            return 0.0
        return 1.0

    def _extract_plan_str(self, obs: str) -> str:
        """Extract the plan string from the observation."""
        match = re.search(r"<plan>(.*?)</plan>", obs, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def step(self, action: str):
        """Execute a step in the environment with the given action."""

        obs, reward, done, info = self.env.step(action)
        str_plan = self._extract_plan_str(action)
        if not str_plan:
            info["plan_format_reward"] = 0.0
        else:
            info["plan_format_reward"] = self._cal_plan_format_reward(str_plan)
        reward += info["plan_format_reward"]
        return obs, reward, done, info


# -----------------------------------------------------------------------------
# Ray remote worker actor -----------------------------------------------------
# -----------------------------------------------------------------------------


@ray.remote(num_cpus=0.2)
class TravelPlannerWorker:
    """Ray remote actor that replaces the worker function.
    Each actor hosts a *TravelPlannerEnv* instance.
    """

    def __init__(self, seed, env_kwargs):
        """Initialize the TravelPlannerWorker with a given seed and environment kwargs"""
        self.env_kwargs = env_kwargs or {}
        env_kwargs["seed"] = seed
        # self.env = gym.make("TravelPlanner-v0", **env_kwargs)
        # self.env = TravelPlannerEnv(**env_kwargs)
        if "use_cl" in env_kwargs and env_kwargs["use_cl"]:
            self.env = TravelPlannerEnvForRay_CourseLearning_Wrapper(
                TravelPlannerEnvForRay(**env_kwargs)
            )
        else:
            self.env = TravelPlannerEnvForRay(**env_kwargs)

    def step(self, action):
        """Execute a step in the environment"""
        obs, reward, done, info = self.env.step(action)
        info = dict(info or {})

        return obs, reward, done, info

    def reset(self):
        obs, info = self.env.reset()
        info = dict(info or {})
        return obs, info

    def close(self):
        """Close the environment"""
        self.env.close()


# -----------------------------------------------------------------------------
# Vectorised Ray environment --------------------------------------------------
# -----------------------------------------------------------------------------


class TravelPlannerMultiProcessEnv(gym.Env):
    """A vectorised, Ray-based wrapper around *TravelPlannerTextEnv*.

    ``info`` dictionaries returned by :py:meth:`step` **and** :py:meth:`reset`
    automatically contain the key ``'available_actions'`` so downstream RL code
    can obtain the *legal* action set without extra IPC overhead.
    """

    def __init__(
        self,
        seed: int = 0,
        env_num: int = 1,
        group_n: int = 1,
        is_train: bool = True,
        use_cl: bool = False,
        env_kwargs: dict = None,
    ) -> None:
        super().__init__()

        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init()

        self.group_n = group_n
        self.env_num = env_num
        self.num_processes = env_num * group_n
        self.is_train = is_train
        if not is_train:
            assert group_n == 1

        self._rng = np.random.RandomState(seed)

        self._env_kwargs = env_kwargs if env_kwargs is not None else {}

        # -------------------------- Ray actors setup --------------------------
        self._workers = []
        self.shared_data_and_tools_actor = TravelPlannerDataAndToolForRay.remote()
        self._env_kwargs["ray_data_and_tools_actor"] = self.shared_data_and_tools_actor
        self._env_kwargs["use_cl"] = use_cl
        for i in range(self.num_processes):
            self._env_kwargs["debug_worker_id"] = i
            worker = TravelPlannerWorker.remote(
                seed + (i // self.group_n),
                self._env_kwargs,
            )
            self._workers.append(worker)

    # ------------------------------------------------------------------
    # Base API ----------------------------------------------------------
    # ------------------------------------------------------------------

    def step(self, actions: list[str]):
        if len(actions) != self.num_processes:
            raise ValueError(
                f"Expected {self.num_processes} actions, got {len(actions)}",
            )

        # Send step commands to all workers
        futures = []
        for worker, action in zip(self._workers, actions):
            future = worker.step.remote(action)
            futures.append(future)

        # Collect results
        results = ray.get(futures)
        obs_list, reward_list, done_list, info_list = [], [], [], []
        for obs, reward, done, info in results:
            obs_list.append(obs)
            reward_list.append(reward)
            done_list.append(done)
            info_list.append(info)

        return obs_list, reward_list, done_list, info_list

    def reset(self):

        # Send reset commands to all workers
        futures = []
        for worker in self._workers:
            future = worker.reset.remote()
            futures.append(future)

        # Collect results
        results = ray.get(futures)
        obs_list, info_list = [], []
        for obs, info in results:
            obs_list.append(obs)
            info_list.append(info)

        return obs_list, info_list

    # ------------------------------------------------------------------
    # Clean‑up ----------------------------------------------------------
    # ------------------------------------------------------------------

    def close(self):
        if getattr(self, "_closed", False):
            return

        # Close all workers and kill Ray actors
        close_futures = []
        for worker in self._workers:
            future = worker.close.remote()
            close_futures.append(future)

        # Wait for all workers to close
        ray.get(close_futures)

        # Kill all Ray actors
        for worker in self._workers:
            ray.kill(worker)

        self._closed = True

    def __del__(self):  # noqa: D401
        self.close()


def build_travelplanner_envs(
    seed: int = 0,
    env_num: int = 1,
    group_n: int = 1,
    is_train: bool = True,
    use_cl: bool = False,
    env_kwargs: dict = None,
) -> TravelPlannerMultiProcessEnv:
    """Build a vectorised TravelPlanner environment."""
    return TravelPlannerMultiProcessEnv(
        seed=seed,
        env_num=env_num,
        group_n=group_n,
        is_train=is_train,
        use_cl=use_cl,
        env_kwargs=env_kwargs,
    )
