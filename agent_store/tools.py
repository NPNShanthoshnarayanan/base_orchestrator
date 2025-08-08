"""
Field information retrieval tools for Agent Store with InjectedState support
"""

import logging, requests
from typing import Any, Dict, List

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated

from agent_store.constants import HTTP_REQUESTS_CONSTANTS, WIDGET_TO_DBTYPE_MAPPING, FieldType, WidgetType, FieldMeta


@tool
def get_field_details(field_ids: List[str], state: Annotated[dict, InjectedState]) -> List[Dict[str, Any]]:
    """
    Retrieve metadata of multiple fields using their unique identifiers.

    This tool provides full details about fields, including their type, and
    is_use_list_values. This information is necessary to correctly construct filters.
    Always expects a list of field_ids to reduce number of tool calls.

    Args:
        field_ids: List of field IDs to retrieve metadata for (even for single field, pass as [field_id])

    Returns:
        List of dicts containing field metadata for each field
        Error format: [{"error": "message"}] for each failed field
    """

    # field_ids is always a list
    field_ids_list = field_ids

    results = []

    for field_id in field_ids_list:
        try:
            # Search for field in field_list from injected state
            field_list = state.get("field_list", [])
            field_info = next((f for f in field_list if f.get(FieldMeta.ID) == field_id), None)

            if not field_info:
                error_result = {"error": f"Field ID '{field_id}' not found in the provided field list."}
                results.append(error_result)
                continue

            # Get widget type following v2 pattern
            widget_type = field_info.get(FieldMeta.TYPE, WidgetType.TEXT)

            # Create enhanced field info following v2 pattern
            enhanced_field_info = field_info.copy()

            # Determine if field uses list-based values (following v2 logic exactly)
            enhanced_field_info["is_use_list_values"] = widget_type in {
                WidgetType.SELECT,
                WidgetType.MULTI_SELECT,
                WidgetType.USER,
                WidgetType.MULTI_USER,
                WidgetType.REFERENCE,
            } or field_id in {
                "_status_name",
                "_priority_name",
                "_state_name",
                "_category",
            }

            # Map widget type to standardized database field type (following v2 pattern)
            enhanced_field_info[FieldMeta.TYPE] = WIDGET_TO_DBTYPE_MAPPING.get(widget_type, FieldType.STRING)

            # Add additional metadata for enhancements
            enhanced_field_info["widget_type"] = widget_type
            enhanced_field_info["db_type"] = enhanced_field_info[FieldMeta.TYPE]

            # Get and include field attributes directly in the metadata
            enhanced_field_info["attributes"] = _get_field_attributes_internal(enhanced_field_info, widget_type)

            results.append(enhanced_field_info)

        except Exception as e:
            logging.error(f"Error retrieving field details for {field_id}: {e}")
            error_result = {"error": f"Failed to retrieve field details for '{field_id}': {str(e)}"}
            results.append(error_result)

    # Always return list
    return results if results else [{"error": "No field processed"}]


@tool
def get_field_values(field_id: str, state: Annotated[dict, InjectedState], search_string: str = "") -> Dict[str, Any]:
    """
    Retrieves values for a selectable field like dropdowns, user pickers, or references.

    Useful for identifying possible RHS values when the field uses a predefined value list.
    For each field with is_use_list_values=True, call this tool to retrieve its values.

    Args:
        field_id: The ID of the form field to fetch values for
        search_string: Optional fuzzy search query to narrow value results

    Returns:
        Dict containing matching field values and metadata, or error message
    """
    values_api_url = state.get("values_api_url")
    if values_api_url:
        base_url = values_api_url.format(field_id=field_id)
        url = f"{base_url}?q={search_string}" if search_string else base_url

        try:
            headers = {
                'X-Access-Key-Id': 'Ake37d7f93-508e-4519-8c46-ef7233799148',
                'X-Access-Key-Secret': 'jBArtyElNxWzr03Y04ZewH6pe8eCnpxg3JqRYxsl8NZG7RvogE0FCDuTwUfp7dg7552bWs6BgbsL3Q9fUbhcg'
            }

            field_values = requests.request("GET", url, headers=headers, verify=False).json()
            logging.debug(f"{field_values=}")
            return field_values
        except Exception as ex:
            logging.exception(f"Exception while fetching field values for field_id={field_id} {ex}")
            return {"error": f"Failed to fetch values for field ID '{field_id}'."}
    else:
        # Return mock values if no API URL provided
        return _get_mock_values_by_field_type_with_state(field_id, state)


def _get_field_attributes_internal(field_details: Dict, widget_type: str) -> List[Dict[str, str]]:
    """
    Internal function to get field attributes based on widget type.

    This is called from get_field_details to include attributes directly in field metadata.

    Args:
        field_details: Field details dictionary
        widget_type: Widget type of the field

    Returns:
        List of attribute dicts with Id, Name, and Type following v2 format
    """
    try:
        # Follow v2 attribute patterns exactly
        if widget_type == WidgetType.CURRENCY:
            return [
                {FieldMeta.ID: "Unit", FieldMeta.NAME: "Unit", FieldMeta.TYPE: "CurrencyUnit"},
                {FieldMeta.ID: "Value", FieldMeta.NAME: "Value", FieldMeta.TYPE: "Number"},
            ]
        elif widget_type == WidgetType.USER:
            return [
                {FieldMeta.ID: "Name", FieldMeta.NAME: "Name", FieldMeta.TYPE: "Text"},
                {FieldMeta.ID: "Email", FieldMeta.NAME: "Email address", FieldMeta.TYPE: "Text"},
                {FieldMeta.ID: "Manager", FieldMeta.NAME: "Manager", FieldMeta.TYPE: "User"},
                {FieldMeta.ID: "Status", FieldMeta.NAME: "Status", FieldMeta.TYPE: "Text"},
                {FieldMeta.ID: "Designation", FieldMeta.NAME: "Job Title", FieldMeta.TYPE: "Text"},
            ]
        else:
            # Check if field has custom attributes
            custom_attributes = field_details.get("Attributes", [])
            if custom_attributes:
                return custom_attributes
            else:
                return []  # Return empty list instead of error for non-complex fields

    except Exception as e:
        logging.error(f"Error getting field attributes: {e}")
        return []


def _get_mock_values_by_field_type_with_state(field_id: str, state: dict) -> Dict[str, Any]:
    """Generate mock values based on field type and name with state access"""
    try:
        # Find field details from state
        field_list = state.get("field_list", [])
        field_details = next(
            (
                f
                for f in field_list
                if f.get(FieldMeta.ID) == field_id or f.get("id") == field_id or f.get("Id") == field_id
            ),
            {},
        )

        field_name = field_details.get(FieldMeta.NAME, field_details.get("name", "")).lower()
        widget_type = field_details.get("widget_type", field_details.get(FieldMeta.TYPE, WidgetType.TEXT))

        # Status field special handling following v2
        if "status" in field_name or field_id == "_status_name":
            values = [
                {"value": "Open", "label": "Open"},
                {"value": "Closed", "label": "Closed"},
                {"value": "In Progress", "label": "In Progress"},
            ]
        elif "priority" in field_name or field_id == "_priority_name":
            values = [
                {"value": "High", "label": "High"},
                {"value": "Medium", "label": "Medium"},
                {"value": "Low", "label": "Low"},
            ]
        elif widget_type == WidgetType.BOOLEAN:
            values = [{"value": True, "label": "Yes"}, {"value": False, "label": "No"}]
        elif widget_type in [WidgetType.USER, WidgetType.MULTI_USER]:
            current_user_id = state.get("current_user_id", "current_user")
            values = [
                {"_id": "user1", "Name": "John Doe", "Email": "john@example.com"},
                {"_id": "user2", "Name": "Jane Smith", "Email": "jane@example.com"},
                {"_id": current_user_id, "Name": "Current User", "Email": "current@example.com"},
            ]
        elif widget_type in [WidgetType.SELECT, WidgetType.MULTI_SELECT]:
            values = [
                {"value": "Option 1", "label": "Option 1"},
                {"value": "Option 2", "label": "Option 2"},
                {"value": "Option 3", "label": "Option 3"},
            ]
        else:
            values = [
                {"value": "Sample Value 1", "label": "Sample Value 1"},
                {"value": "Sample Value 2", "label": "Sample Value 2"},
            ]

        return {"status": "success", "field_id": field_id, "values": values, "count": len(values), "is_mock": True}

    except Exception as e:
        logging.error(f"Error generating mock values for {field_id}: {e}")
        return {"status": "error", "error": str(e), "field_id": field_id, "values": []}

def get_field_list(flow_id):
    return [{'Id': '_item_id', 'Name': 'Item Id', 'Type': 'Text', 'IsSystemField': True, 'Model': 'Leave_Request_Board',
             'Widget': None, 'Required': False, 'IsInternal': False, 'IsComputedField': False},
            {'Id': '_counter', 'Name': 'Counter', 'Type': 'Number', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': True,
             'Decimalpoint': None, 'IsComputedField': False},
            {'Id': 'Name', 'Name': 'Title', 'Type': 'Text', 'IsSystemField': True, 'Model': 'Leave_Request_Board',
             'Widget': None, 'Required': False, 'IsInternal': False, 'IsComputedField': True},
            {'Id': 'AssignedTo', 'Name': 'Assignee', 'Type': 'User', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'SourceFlowId': 'UserAbstract', 'SourceFlowType': None,
             'Attributes': [{'Id': 'Status', 'Name': 'Status', 'Type': 'DropdownList'},
                            {'Id': 'FirstName', 'Name': 'First name', 'Type': 'Text'},
                            {'Id': 'LastName', 'Name': 'Last name', 'Type': 'Text'},
                            {'Id': 'ProfilePicture', 'Name': 'Profile picture', 'Type': 'ProfilePicture'}],
             'IsComputedField': False}, {'Id': '_category', 'Name': 'Category', 'Type': 'Text', 'IsSystemField': True,
                                         'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False,
                                         'IsInternal': True, 'IsComputedField': False},
            {'Id': '_status_name', 'Name': 'Status', 'Type': 'Text', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': '_priority_name', 'Name': 'Priority', 'Type': 'Text', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False}, {'Id': 'DueDate', 'Name': 'Due date', 'Type': 'DateTime', 'IsSystemField': True,
                                         'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False,
                                         'IsInternal': False, 'IsComputedField': False},
            {'Id': '_start_date', 'Name': 'Start date', 'Type': 'DateTime', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False}, {'Id': 'Requester', 'Name': 'Requester', 'Type': 'User', 'IsSystemField': True,
                                         'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False,
                                         'IsInternal': False, 'SourceFlowId': 'UserAbstract', 'SourceFlowType': None,
                                         'Attributes': [{'Id': 'Status', 'Name': 'Status', 'Type': 'DropdownList'},
                                                        {'Id': 'FirstName', 'Name': 'First name', 'Type': 'Text'},
                                                        {'Id': 'LastName', 'Name': 'Last name', 'Type': 'Text'},
                                                        {'Id': 'ProfilePicture', 'Name': 'Profile picture',
                                                         'Type': 'ProfilePicture'}], 'IsComputedField': False},
            {'Id': 'Summary', 'Name': 'Reason for leave', 'Type': 'Text', 'IsSystemField': False,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': True, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': 'Attachment', 'Name': 'Proof Docs', 'Type': 'Attachment', 'IsSystemField': False,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': '_resolved_at', 'Name': 'Resolved at', 'Type': 'DateTime', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': '_resolution_time', 'Name': 'Resolution time', 'Type': 'Number', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'Decimalpoint': None, 'IsComputedField': False},
            {'Id': '_created_by', 'Name': 'Created by', 'Type': 'User', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'SourceFlowId': 'UserAbstract', 'SourceFlowType': None,
             'Attributes': [{'Id': 'Status', 'Name': 'Status', 'Type': 'DropdownList'},
                            {'Id': 'FirstName', 'Name': 'First name', 'Type': 'Text'},
                            {'Id': 'LastName', 'Name': 'Last name', 'Type': 'Text'},
                            {'Id': 'ProfilePicture', 'Name': 'Profile picture', 'Type': 'ProfilePicture'}],
             'IsComputedField': False},
            {'Id': '_created_at', 'Name': 'Created at', 'Type': 'DateTime', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': '_modified_by', 'Name': 'Modified by', 'Type': 'User', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'SourceFlowId': 'UserAbstract', 'SourceFlowType': None,
             'Attributes': [{'Id': 'Status', 'Name': 'Status', 'Type': 'DropdownList'},
                            {'Id': 'FirstName', 'Name': 'First name', 'Type': 'Text'},
                            {'Id': 'LastName', 'Name': 'Last name', 'Type': 'Text'},
                            {'Id': 'ProfilePicture', 'Name': 'Profile picture', 'Type': 'ProfilePicture'}],
             'IsComputedField': False},
            {'Id': '_modified_at', 'Name': 'Modified at', 'Type': 'DateTime', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': '_subitem_title', 'Name': 'Subitem title', 'Type': 'Text', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False, 'IsSubitemField': True},
            {'Id': '_subitem_description', 'Name': 'Subitem description', 'Type': 'Text', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False, 'IsSubitemField': True},
            {'Id': '_state_name', 'Name': 'Subitem state', 'Type': 'Text', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': True,
             'IsComputedField': False, 'IsSubitemField': True},
            {'Id': '_estimated_time', 'Name': 'Estimated time', 'Type': 'Number', 'IsSystemField': True,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'Decimalpoint': None, 'IsComputedField': False},
            {'Id': 'Start_Date', 'Name': 'Start Date', 'Type': 'DateTime', 'IsSystemField': False,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': True, 'IsInternal': False,
             'IsComputedField': False},
            {'Id': 'End_Date', 'Name': 'End Date', 'Type': 'DateTime', 'IsSystemField': False,
             'Model': 'Leave_Request_Board', 'Widget': None, 'Required': False, 'IsInternal': False,
             'IsComputedField': False}]
