TRAVELPLANNER_ZEROSHOT_REACT_INSTRUCTION = """Collect information for a query plan using interleaving <think> <action> and <plan> steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. Note that the nested use of tools is prohibited. 

The following functions are available for you to call:

(1) FlightSearch[Departure City, Destination City, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City: The city you'll be flying out from.
Destination City: The city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[New York, London, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
Example: GoogleDistanceMatrix[Paris, Lyon, self-driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City]:
Description: Discover accommodations in your desired city.
Parameter: City - The name of the city where you're seeking accommodation.
Example: AccommodationSearch[Rome] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City]:
Description: Explore dining options in a city of your choice.
Parameter: City – The name of the city where you're seeking restaurants.
Example: RestaurantSearch[Tokyo] would show a curated list of restaurants in Tokyo.

(5) AttractionSearch[City]:
Description: Find attractions in a city of your choice.
Parameter: City – The name of the city where you're seeking attractions.
Example: AttractionSearch[London] would return attractions in London.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) Finish[]
Description: Tell the system that you have completed the task and no further actions are needed.
Parameters: None
Example: Finish[] would indicate that you have finished the task.


Each action only calls one function once. Do not add any description in the action.
surround the action with <action> and </action> tags. For example, <action>FlightSearch[New York, London, 2022-10-01]</action>. After each action, the environment will return an observation.

The plan should be a json list with each element containing the following keys:
- days: The day number of the trip.
- current_city: The city you are currently in or from A to B.
- transportation: The transportation information for the day, such as flight or driving details. "-" if no transportation is needed.
- breakfast: Breakfast information for the day. "-" if no breakfast is needed.
- attraction: The attractions you plan to visit that day, separated by semicolons. "-" if no attractions are planned.
- lunch: Lunch information for the day. "-" if no lunch is needed.
- dinner: Dinner information for the day. "-" if no dinner is needed.  
- accommodation: Accommodation information for the day. "-" if no accommodation is needed(e.g., the last day of the trip).
Here is an example of the plan:
-----EXAMPLE-----
 [{{
        "days": 1,
        "current_city": "from Dallas to Peoria",
        "transportation": "Flight Number: 4044830, from Dallas to Peoria, Departure Time: 13:10, Arrival Time: 15:01",
        "breakfast": "-",
        "attraction": "Peoria Historical Society, Peoria;Peoria Holocaust Memorial, Peoria;",
        "lunch": "-",
        "dinner": "Tandoor Ka Zaika, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 2,
        "current_city": "Peoria",
        "transportation": "-",
        "breakfast": "Tandoor Ka Zaika, Peoria",
        "attraction": "Peoria Riverfront Park, Peoria;The Peoria PlayHouse, Peoria;Glen Oak Park, Peoria;",
        "lunch": "Cafe Hashtag LoL, Peoria",
        "dinner": "The Curzon Room - Maidens Hotel, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 3,
        "current_city": "from Peoria to Dallas",
        "transportation": "Flight Number: 4045904, from Peoria to Dallas, Departure Time: 07:09, Arrival Time: 09:20",
        "breakfast": "-",
        "attraction": "-",
        "lunch": "-",
        "dinner": "-",
        "accommodation": "-"
    }}]
-----EXAMPLE END-----

Put your reasoning between <think> and </think> tags. Put the action to be taken between <action> and </action> tags. The action should be a single function call with the format: FunctionName[Parameter1, Parameter2, ...].  Put the generated plan between <plan> and </plan> tags. You can output an incomplete plan <plan></plan> which should be in the correct format in which "-" is used for unfilled values. The plan you output will be used to replace the incomplete plan in the input prompt. Don't output empty <plan></plan> tags!

Please use <think></think>, <action></action>, <plan></plan> to format your response. Do not use any other tags or markdown syntax. Do not output any text outside of these tags.
Use all the tools provided above to gather information for the query. Don't repeat the same action multiple times!!!
One legal response example is:

<think>...</think>
<action>...</action>
<plan>...</plan>

Here is your task:
Query: 
{query}
Incomplete Plan:
{plan}
History of Actions:
{history}
Current Observation:
{observation}
"""

TRAVELPLANNER_ZEROSHOT_REACT_INSTRUCTION_NO_HIS = """
You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

Collect information for a query plan using interleaving <think> <action> <IS> and <plan> steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. Note that the nested use of tools is prohibited. 

The following functions are available for you to call:

(1) FlightSearch[Departure City, Destination City, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City: The city you'll be flying out from.
Destination City: The city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[New York, London, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
Example: GoogleDistanceMatrix[Paris, Lyon, self-driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City]:
Description: Discover accommodations in your desired city.
Parameter: City - The name of the city where you're seeking accommodation.
Example: AccommodationSearch[Rome] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City]:
Description: Explore dining options in a city of your choice.
Parameter: City – The name of the city where you're seeking restaurants.
Example: RestaurantSearch[Tokyo] would show a curated list of restaurants in Tokyo.

(5) AttractionSearch[City]:
Description: Find attractions in a city of your choice.
Parameter: City – The name of the city where you're seeking attractions.
Example: AttractionSearch[London] would return attractions in London.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) Finish[]
Description: Tell the system that you have completed the task and no further actions are needed.
Parameters: None
Example: Finish[] would indicate that you have finished the task.


Each action only calls one function once. Do not add any description in the action.
surround the action with <action> and </action> tags. For example, <action>FlightSearch[New York, London, 2022-10-01]</action>. After each action, the environment will return an observation.

In "breakfast", "lunch", "dinner" and "accommodation" keys, please fill in the location information in the format 'Name, City', with the option to add the state or province in parentheses after the city, like 'Name, City (State)'. For example: 'Cafe Hashtag LoL, Peoria' or 'Disney World, Orlando (Florida)'. Otherwise these information will be considered invalid and be ignored.

The plan should be a json list with each element containing the following keys:
- days: The day number of the trip.
- current_city: The city you are currently in or from A to B.
- transportation: The transportation information for the day, such as flight or driving details. "-" if no transportation is needed.
- breakfast: Breakfast information for the day. "-" if no breakfast is needed.
- attraction: The attractions you plan to visit that day, separated by semicolons. "-" if no attractions are planned.
- lunch: Lunch information for the day. "-" if no lunch is needed.
- dinner: Dinner information for the day. "-" if no dinner is needed.  
- accommodation: Accommodation information for the day. "-" if no accommodation is needed(e.g., the last day of the trip).
Here is an example of the plan:
-----EXAMPLE-----
 [{{
        "days": 1,
        "current_city": "from Dallas to Peoria",
        "transportation": "Flight Number: 4044830, from Dallas to Peoria, Departure Time: 13:10, Arrival Time: 15:01",
        "breakfast": "-",
        "attraction": "Peoria Historical Society, Peoria;Peoria Holocaust Memorial, Peoria;",
        "lunch": "-",
        "dinner": "Tandoor Ka Zaika, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 2,
        "current_city": "Peoria",
        "transportation": "-",
        "breakfast": "Tandoor Ka Zaika, Peoria",
        "attraction": "Peoria Riverfront Park, Peoria;The Peoria PlayHouse, Peoria;Glen Oak Park, Peoria;",
        "lunch": "Cafe Hashtag LoL, Peoria",
        "dinner": "The Curzon Room - Maidens Hotel, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 3,
        "current_city": "from Peoria to Dallas",
        "transportation": "Flight Number: 4045904, from Peoria to Dallas, Departure Time: 07:09, Arrival Time: 09:20",
        "breakfast": "-",
        "attraction": "-",
        "lunch": "-",
        "dinner": "-",
        "accommodation": "-"
    }}]
-----EXAMPLE END-----

You should first reason step-by-step about the current situation, then think carefully which action is the best for answering the query NOW. Then think about what information might help you accomplish your task in the future and should be added to the your memory, whitch is called internal state. Think about how to create your internal state. This reasoning process MUST be enclosed within <think> </think> tags.
After your reasoning, you must create your internal state as your memory. Internal state needs to contain all the information you think will help you accomplish the task in the future, summarize past information and reasons about subsequent actions. Enclose this within <IS> </IS> tags.
Then, you MUST put the action to be taken between <action> and </action> tags. The action should be a single function call with the format: FunctionName[Parameter1, Parameter2, ...].  
Finally, put the generated plan between <plan> and </plan> tags. You can output an incomplete plan <plan></plan> which should be in the correct format in which "-" is used for unfilled values. The plan you output will be used to replace the incomplete plan in the input prompt. Don't output empty <plan></plan> tags!
Use all the tools provided above to gather information for the query. Don't repeat the same action multiple times!!!

Here is your task:
Query: 
{query}
Incomplete Plan:
{plan}

You MUST follow this format:
<think>[Your step-by-step reasoning about the current situation and which action to take]</think>

<action>[Your chosen action from the available options]</action>

<IS>[Your updated internal state including key information to remember for future steps]</IS>

<plan>[Your current plan]</plan>
"""

TRAVELPLANNER_ZEROSHOT_REACT_INSTRUCTION_MEM1 = """
You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

Collect information for a query plan using interleaving <think> <action> and <plan> steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. Note that the nested use of tools is prohibited. 

The following functions are available for you to call:

(1) FlightSearch[Departure City, Destination City, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City: The city you'll be flying out from.
Destination City: The city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[New York, London, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
Example: GoogleDistanceMatrix[Paris, Lyon, self-driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City]:
Description: Discover accommodations in your desired city.
Parameter: City - The name of the city where you're seeking accommodation.
Example: AccommodationSearch[Rome] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City]:
Description: Explore dining options in a city of your choice.
Parameter: City – The name of the city where you're seeking restaurants.
Example: RestaurantSearch[Tokyo] would show a curated list of restaurants in Tokyo.

(5) AttractionSearch[City]:
Description: Find attractions in a city of your choice.
Parameter: City – The name of the city where you're seeking attractions.
Example: AttractionSearch[London] would return attractions in London.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) Finish[]
Description: Tell the system that you have completed the task and no further actions are needed. You must choose the Finish[] action if you only have 1 step left.
Parameters: None
Example: Finish[] would indicate that you have finished the task.


Each action only calls one function once. Do not add any description in the action.
surround the action with <action> and </action> tags. For example, <action>FlightSearch[New York, London, 2022-10-01]</action>. After each action, the environment will return an observation.

The plan should be a json list with each element containing the following keys:
- days: The day number of the trip.
- current_city: The city you are currently in or from A to B.
- transportation: The transportation information for the day, such as flight or driving details. "-" if no transportation is needed.
- breakfast: Breakfast information for the day. "-" if no breakfast is needed.
- attraction: The attractions you plan to visit that day, separated by semicolons. "-" if no attractions are planned.
- lunch: Lunch information for the day. "-" if no lunch is needed.
- dinner: Dinner information for the day. "-" if no dinner is needed.  
- accommodation: Accommodation information for the day. "-" if no accommodation is needed(e.g., the last day of the trip).

In "breakfast", "lunch", "dinner" and "accommodation" keys, please fill in the location information in the format 'Name, City', with the option to add the state or province in parentheses after the city, like 'Name, City (State)'. For example: 'Cafe Hashtag LoL, Peoria' or 'Disney World, Orlando (Florida)'. Otherwise these information will be considered invalid and be ignored.

Here is an example of the plan:
-----EXAMPLE-----
 [{{
        "days": 1,
        "current_city": "from Dallas to Peoria",
        "transportation": "Flight Number: 4044830, from Dallas to Peoria, Departure Time: 13:10, Arrival Time: 15:01",
        "breakfast": "-",
        "attraction": "Peoria Historical Society, Peoria;Peoria Holocaust Memorial, Peoria;",
        "lunch": "-",
        "dinner": "Tandoor Ka Zaika, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 2,
        "current_city": "Peoria",
        "transportation": "-",
        "breakfast": "Tandoor Ka Zaika, Peoria",
        "attraction": "Peoria Riverfront Park, Peoria;The Peoria PlayHouse, Peoria;Glen Oak Park, Peoria;",
        "lunch": "Cafe Hashtag LoL, Peoria",
        "dinner": "The Curzon Room - Maidens Hotel, Peoria",
        "accommodation": "Bushwick Music Mansion, Peoria"
    }},
    {{
        "days": 3,
        "current_city": "from Peoria to Dallas",
        "transportation": "Flight Number: 4045904, from Peoria to Dallas, Departure Time: 07:09, Arrival Time: 09:20",
        "breakfast": "-",
        "attraction": "-",
        "lunch": "-",
        "dinner": "-",
        "accommodation": "-"
    }}]
-----EXAMPLE END-----
You will receive information on Query, Incomplete Plan, Previous internal State, Last Action, and Current Observation. The Query is the travel planning question I pose to you, and you need to meet the requirements I specify in it. The Incomplete Plan is the plan you have not yet completed; you need to fill in its content based on the existing information while ensuring that the content of the plan meets the needs I mentioned in the query. Previous internal state is the memory YOU have summarized earlier, recording information that may be helpful for completing your plan. Therefore, the information in IS is not necessarily correct or complete. You need to update your IS based on current observations. Last Action is the action you took in the previous step, and Current Observation is the feedback from the Last Action.

You should first reason step-by-step about the current situation, then think carefully which action is the best for answering the query. Then think about what information in the observation might help you accomplish your task in the future and should be added to the new internal state, and what information from the previous internal state may no longer be needed. Think about how to update your internal state. This reasoning process MUST be enclosed within <think> </think> tags.
After your reasoning, you must update your internal state based on current observation and your previous internal state. Internal state needs to contain all the information you think will help you accomplish the task in the future, summarize past information and reasons about subsequent actions, instead of just repeating current observation and previous internal state. Enclose this within <IS> </IS> tags.
Then, choose an action and put the action to be taken between <action> and </action> tags. The action should be a single function call with the format: FunctionName[Parameter1, Parameter2, ...].  
Finally, put the generated plan between <plan> and </plan> tags. You can output an incomplete plan <plan></plan> which should be in the correct format in which "-" is used for unfilled values. The plan you output will be used to replace the incomplete plan in the input prompt. Don't output empty <plan></plan> tags! You should always provide a more complete plan than before, unless the current observation is insufficient for you to fill in any results.
Use all the tools provided above to gather information for the query. Don't repeat the same action multiple times!!!

Prior to this step, you have already taken {step_count} step(s), and you have {step_left} step(s) left including current step.
IMPORTANT: If you only have 1 step left, this step is your last step and you MUST choose the Finish[] action whether you've finished your plan or not, otherwise your plan will be deprecated. If you think your plan is completed, you should also choose the Finish[] action.

Here is your task:
Query: 
{query}
Incomplete Plan:
{plan}
Previous internal state:
{previous_internal_state}
Last action (Don't repeat the same action):
{last_action}
Current Observation:
{observation}

You MUST follow this format:
<think>[Your step-by-step reasoning about the current situation and which action to take]</think>

<action>[Your chosen action from the available options]</action>

<IS>[Your updated internal state]</IS>

<plan>[Your current more complete plan]</plan>
"""
