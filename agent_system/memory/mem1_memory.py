"""
MEM1 Memory Management System

Simplified version focused on core functionality:
1. Extract agent-generated internal states from responses
2. Track states for environment integration
3. Efficient memory usage for long-running training
"""

import re
import logging
from typing import List, Dict, Any, Optional
from agent_system.memory.base import BaseMemory

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class MEM1Memory(BaseMemory):
    """
    Simplified MEM1 Memory system for agent-generated internal state tracking.
    Focuses on core functionality with efficient memory usage.
    """
    
    def __init__(self, clip_IS:bool=False,max_internal_state_length: int = 1024):
        """
        Initialize MEM1 Memory.
        
        Args:
            clip_IS(bool): Whether to clip internal state length to max_internal_state_length.
            max_internal_state_length (int): Maximum length of internal state to store.Only enable when clip_IS is true.
        """
        self.clip_IS=clip_IS
        self.max_internal_state_length = max_internal_state_length
        self.batch_size = 1
        
        # Only track essential data - agent's latest internal state per environment
        self.agent_internal_states: List[str|None] = []
        self.current_step: List[int] = []
        self.agent_last_actions: List[str|None] = []
        

    def __len__(self):
        """Return the number of memory slots (batch size)."""
        return self.batch_size

    def __getitem__(self, idx: int):
        """Access memory of specific environment index."""
        if idx >= len(self.agent_internal_states):
            return {'internal_state': ''}
        
        return {'internal_state': self.agent_internal_states[idx]}

    def reset(self, batch_size: int):
        """Reset memory tracking for new episode."""
        self.batch_size = batch_size
        self.agent_internal_states = [None for _ in range(batch_size)]
        self.current_step = [0 for _ in range(batch_size)]
        self.agent_last_actions = [None for _ in range(batch_size)]

        logger.debug(f"Reset MEM1 memory tracking for batch_size={batch_size}")

    def store(self, record: Dict[str, List[Any]]):
        """Store agent internal states extracted from responses.
        record: A dictionary containing 'IS' and 'action' keys.
        """
        # for env_idx, response in enumerate(record['responses']):
        #     if env_idx < len(self.agent_internal_states):
        #         internal_state = self.extract_internal_state_from_response(response)
        #         if internal_state:
        #             self.agent_internal_states[env_idx] = internal_state
        #             # # Truncate if too long to prevent memory bloat
        #             if self.clip_IS and len(internal_state) > self.max_internal_state_length:
        #                 internal_state = internal_state[:self.max_internal_state_length]
        #                 logger.warning(f"Truncated internal state to {self.max_internal_state_length} chars")
        #         else:
        #             logger.warning(f"No internal state found in response for env {env_idx}")
        #         self.current_step[env_idx] += 1  # Increment step count
        for env_idx, internal_state in enumerate(record['IS']):
            if env_idx < len(self.agent_internal_states):
                if internal_state != "":
                    self.agent_internal_states[env_idx] = internal_state
                    # # Truncate if too long to prevent memory bloat
                    if self.clip_IS and len(internal_state) > self.max_internal_state_length:
                        internal_state = internal_state[:self.max_internal_state_length]
                        logger.warning(f"Truncated internal state to {self.max_internal_state_length} chars")
                else:
                    logger.warning(f"No internal state found in response for env {env_idx},remaining the last one")
                self.current_step[env_idx] += 1  # Increment step count
        for env_idx, action in enumerate(record['action']):
            if env_idx < len(self.agent_last_actions):
                self.agent_last_actions[env_idx] = action
                

    def extract_internal_state_from_response(self, response: str) -> Optional[str]:
        """
        Extract agent-generated internal state from response.
        
        Args:
            response (str): Agent's response containing <IS>...</IS>
            
        Returns:
            Optional[str]: Extracted internal state, or None if not found
        """
        match = re.search(r'<IS>(.*?)</IS>', response, re.DOTALL | re.IGNORECASE)
        
        if match:
            internal_state = match.group(1).strip()
            return internal_state
        else:
            return None

    # def get_latest_internal_state(self, env_idx: int = 0) -> tuple[Optional[str],int]:
    #     """Get the agent's latest internal state for specific environment."""
    #     if env_idx < len(self.agent_internal_states):
    #         state = self.agent_internal_states[env_idx]
    #         return state, self.current_step[env_idx]
    #     return None,0

    def fetch(self, step: int=-1)->tuple[List[str],list[int],list[str]]:
        """Fetch internal state, current_step and last_action, step parameter is unuse."""
        return self.agent_internal_states, self.current_step, self.agent_last_actions
