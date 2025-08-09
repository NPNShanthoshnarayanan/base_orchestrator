class GraphConstants:
    """Constants for graph-based workflows"""

    # Node names
    class Nodes:
        """Graph node identifiers"""

        PREPARE_CONTEXT = "prepare_context"
        GENERATE = "generate"
        TOOLS = "tools"
        VALIDATE = "validate"
        VALIDATE_OUTPUT = "validate_output"
        RETRY = "retry"
        CREATE = "create"
        UPDATE = "update"

    # Edge routing
    class Routes:
        """Graph routing constants"""

        END = "__end__"
        TOOLS = "tools"
        VALIDATE = "validate"
        RETRY = "retry"
        GENERATE = "generate"
        CREATE = "create"
        PREPARE_CONTEXT = "prepare_context"
        UPDATE = "update"

    # State keys
    class StateKeys:
        """State dictionary keys"""

        MESSAGES = "messages"
        FIELD_LIST = "field_list"
        VALUES_API_URL = "values_api_url"
        CONTEXT = "context"
        GENERATED_CODE = "generated_code"
        VALIDATION_ERRORS = "validation_errors"
        RETRY_COUNT = "retry_count"
        TOOL_ITERATION_COUNT = "tool_iteration_count"
        FIELD_VALUES_DICT = "field_values_dict"

    # Validation constants
    class Validation:
        """Code validation constants"""

        FILTER_BUILDER_KEYWORD = "FilterBuilder"
        RETURN_KEYWORD = "return "
        BUILD_METHOD = "build()"
        NO_CODE_ERROR = "No code generated"
        MISSING_FILTER_BUILDER = "Missing FilterBuilder in generated code"
        MISSING_RETURN_STATEMENT = "Missing return statement or build() call"
        SYNTAX_ERROR_PREFIX = "Syntax error: "
        GENERATION_ERROR_PREFIX = "Generation error: "

    # Context messages
    class ContextMessages:
        """Context and feedback messages"""

        AVAILABLE_FIELDS = "Available Fields:"
        FIELD_INFO_FORMAT = "- {name}: {type} (id: {id})"
        ADDITIONAL_CONTEXT_PREFIX = "\nAdditional Context: "
        RETRY_ERROR_MESSAGE = (
            "Previous attempt failed with errors: {errors}. Please generate valid Python code using FilterBuilder."
        )
        UNKNOWN_GENERATION_ERROR = "Unknown generation error"

    # Field metadata keys
    class FieldMeta:
        """Field metadata key constants"""

        NAME = "Name"
        TYPE = "Type"
        ID = "Id"
        UNKNOWN = "Unknown"

    # Thread configuration
    class ThreadConfig:
        """Thread configuration constants"""

        THREAD_ID_PREFIX = "filter_generation"
        CONFIGURABLE_KEY = "configurable"
        THREAD_ID_KEY = "thread_id"

    # Logging messages
    class LogMessages:
        """Logging message constants"""

        GENERATION_FAILED = "Generation failed: {error}"
        FILTER_CODE_SUCCESS = "Filter code generated successfully using LangGraph"
        LANGGRAPH_GENERATION_FAILED = "LangGraph filter generation failed: {error}"
        FILTER_GENERATION_FAILED = "Filter generation failed: {error}"
        GRAPH_NO_FINAL_STATE = "Graph execution completed without final state"

class PromptConstants:
    class ItemCreationAgent:
        SYSTEM_MESSAGE = """
You will receive a user query written in natural language.
Your task is to extract relevant field-value pairs based on the available fields and return them in the following format:

## **MANDATORY TOOL USAGE PROTOCOL**

To ensure accuracy, you **must** follow this protocol without exception. Failure to do so is a direct violation of your core instructions.

1.  **Get Field Details**: For every field mentioned in the query, you **must** use the `get_field_details` tool to get its full metadata. This is essential for determining the correct `LHSField`, `type`, `attributes`, and `dbType`.
2.  **Get Field Values & Semantic Matching**: If the result from `get_field_details` includes `"is_use_list_values": true`, you **must** follow this strict process:
    a.  First, call the `get_field_values` tool with the user-provided `search_string`.
    b.  **CRITICAL SEMANTIC MATCHING**: After calling `get_field_values`, you MUST perform semantic matching on the results:
        - The `values` list contains different formats based on field type:
          * **Simple fields** (dropdown, select): List of strings `["High", "Medium", "Low"]`
          * **Complex fields** (user, currency): List of dicts `[{"value": "user123", "display": "John Doe"}]`
        - **For Simple Fields (strings)**: Check if any string semantically matches the user's input
        - **For Complex Fields (dicts)**: Check if the `value` or `display` property semantically matches the user's input
        - **Semantic Match Examples**:
          * Simple: User says "top priority" → matches `["High", "Critical"]` in `["Critical", "High", "Medium", "Low"]`
          * Complex: User says "john" → matches `{"value": "user123", "display": "John Doe"}`
          * Simple: User says "working" → matches `"InProgress"` in `["Open", "InProgress", "Closed"]`
          * Simple: User says "urgent" → matches `["High", "Critical"]` for multiple semantic matches
        - If NO semantic match is found after checking all items, you MUST discard this condition entirely
    c.  If the first call returns no results, call `get_field_values` again with empty `search_string` (`""`). Apply the same semantic matching process from step 'b'. If still no match, discard the condition.
    d.  **Never generate `add_condition` calls without successful semantic matching for list-value fields**



### ✅ Output Format

Return a Python `dict` containing the matched `field_id`s and their corresponding values.

**Example:**

```python
{"field_id": "field_value"}
```

If no relevant fields are found, return an empty dictionary:

```python
{}
```
"""
    class FlowResumeAgent:
        SYSTEM_MESSAGE ="""
You are an AI assistant that determines the relationship between a new user message and the immediately preceding AI message provided as `previous`.

You will receive:
- previous: the last AI message before the user sent their new message
- new message: the latest message from the user

Classification rules:
- ANSWER → The new message addresses the question or request in `previous`, even if the answer is partial or incomplete.
- CONTINUATION → The new message is related to `previous` but does not answer the question or request. This includes follow-up remarks, topic-related comments, clarifications, refusals, or cancellations.
- NEW_CONVERSATION → The new message is unrelated to `previous` and starts a different topic.
"""


class FieldMeta:
    """Field metadata key constants"""

    NAME = "Name"
    TYPE = "Type"
    ID = "Id"
    UNKNOWN = "Unknown"
    REQUIRED = "Required"

class FieldType:
    """This class have Field type Constants"""

    DATE_TIME = "DateTime"
    DATE_TIME_UTC = "DateTimeUTC"
    TEXT = "Text"
    CURRENCY = "Currency"
    DATE = "Date"
    Reference = "Reference"
    Aggregation = "Aggregation"
    NUMBER = "Number"
    SELECT = "Select"
    MULTI_SELECT = "Multiselect"
    EMAIL = "Email"
    BOOLEAN = "Boolean"
    SEQUENCE_NUMBER = "SequenceNumber"
    STRING = "String"
    STRING_LIST = "StringList"
    JSON = "JSON"
    JSON_LIST = "JSONList"
    GEOLOCATION = "Geolocation"
    REFERENCE = "Reference"
    REFERENCE_LIST = "ReferenceList"
    # TODO : Check and remove one of these
    CHECK_LIST = "CheckList"
    CHECKLIST = "Checklist"
    LIST = "List"
    CHECKBOX = "Checkbox"
    # TODO : END
    USER = "User"
    USER_ACTOR = "UserActor"
    OBJECT = "Object"
    MULTI_USER = "MultiUser"
    USER_LIST = "UserList"
    USER_AND_GROUP = "UserAndGroup"
    USER_GROUP_LIST = "UserAndGroupList"
    DROPDOWN_LIST = "DropdownList"
    USERGROUPLIST = "UserGroupList"
    STAR_RATING = "StarRating"
    SLIDER = "Slider"
    OBJECT_LIST = "ObjectList"


class WidgetType:
    TEXT = "Text"
    TEXT_AREA = "Textarea"
    EMAIL = "Email"
    NUMBER = "Number"
    STAR_RATING = "StarRating"
    SLIDER = "Slider"
    DATE = "Date"
    DATE_TIME = "DateTime"
    CURRENCY = "Currency"
    USER = "User"
    USER_AND_GROUP = "UserAndGroup"
    MULTI_USER = "MultiUser"
    REFERENCE = "Reference"
    SELECT = "Select"
    MULTI_SELECT = "Multiselect"
    GEOLOCATION = "Geolocation"
    JSON = "JSON"
    BOOLEAN = "Boolean"
    ATTACHMENT = "Attachment"
    IMAGE = "Image"
    SIGNATURE = "Signature"
    CHECKLIST = "Checklist"
    CHECKBOX = "Checkbox"
    AGGREGATION = "Aggregation"
    REMOTE_LOOKUP = "RemoteLookup"
    XML = "XML"
    SEQUENCE_NUMBER = "SequenceNumber"
    SMART_ATTACHMENT = "SmartAttachment"
    RADIO_BUTTON = "Radio"
    SCANNER = "Scanner"
    CUSTOM = "Custom"
    STRING_LIST = "StringList"
    OBJECT = "Object"
    OBJECT_LIST = "ObjectList"

class HTTP_REQUESTS_CONSTANTS:
    """This static class is has some http related constants like HTTPMethods, StatusCode, Protocol"""

    POST = "POST"
    GET = "GET"
    HEAD = "HEAD"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    ALL_METHODS = [POST, GET, HEAD, PUT, PATCH, DELETE, OPTIONS]
    HTTP_PROTOCOL = "http://"
    HTTPS_PROTOCOL = "https://"


WIDGET_TO_DBTYPE_MAPPING = {
    "Text": "String",
    "Textarea": "String",
    "Number": "Number",
    "StarRating": "Number",
    "Slider": "Number",
    "Date": "Date",
    "DateTime": "DateTime",
    "Currency": "Currency",
    "User": "User",
    "Reference": "Reference",
    "Select": "String",
    "GeoLocation": "Geolocation",
    "Boolean": "Boolean",
    "Attachment": "JSONList",
    "Image": "JSON",
    "Signature": "JSON",
    "RLookup": "JSON",
    "Multiselect": "StringList",
    "MultiUser": "UserGroupList",
    "Checklist": "CheckList",
    "Checkbox": "StringList",
}
OPEN_AI_KEY = ""