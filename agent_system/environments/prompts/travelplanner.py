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
