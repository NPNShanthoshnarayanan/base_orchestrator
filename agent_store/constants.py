class GraphConstants:
    """Constants for graph-based workflows"""

    # Node names
    class Nodes:
        """Graph node identifiers"""

        PREPARE_CONTEXT = "prepare_context"
        GENERATE = "generate"
        TOOLS = "tools"
        VALIDATE = "validate"
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