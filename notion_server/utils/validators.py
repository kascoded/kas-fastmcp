"""
Property Validators
Validates Notion property values against database schemas.
"""

from typing import Dict, Any, List, Optional, Tuple


class PropertyValidator:
    """
    Validates Notion properties against schema definitions.
    
    Usage:
        validator = PropertyValidator(schema)
        is_valid, errors = validator.validate_properties(properties)
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize validator with a schema.
        
        Args:
            schema: Database schema from SchemaManager.get_schema()
        """
        self.schema = schema
    
    def validate_properties(
        self, 
        properties: Dict[str, Any],
        strict: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate properties against schema.
        
        Args:
            properties: Properties dict to validate
            strict: If True, require all required properties
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check each property
        for prop_name, prop_value in properties.items():
            # Check if property exists in schema
            if prop_name not in self.schema:
                errors.append(
                    f"Property '{prop_name}' not found in schema. "
                    f"Available: {list(self.schema.keys())}"
                )
                continue
            
            # Get schema definition
            prop_schema = self.schema[prop_name]
            prop_type = prop_schema.get("type")
            
            # Validate based on type
            error = self._validate_property(prop_name, prop_value, prop_schema)
            if error:
                errors.append(error)
        
        # Check for required properties (if strict)
        if strict:
            for prop_name, prop_schema in self.schema.items():
                if prop_schema.get("required") and prop_name not in properties:
                    errors.append(f"Required property '{prop_name}' is missing")
        
        return len(errors) == 0, errors
    
    def _validate_property(
        self, 
        prop_name: str, 
        prop_value: Any, 
        prop_schema: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate a single property.
        
        Returns:
            Error message if invalid, None if valid
        """
        prop_type = prop_schema.get("type")
        
        # Title
        if prop_type == "title":
            return self._validate_title(prop_name, prop_value)
        
        # Rich text
        elif prop_type == "rich_text":
            return self._validate_rich_text(prop_name, prop_value)
        
        # Number
        elif prop_type == "number":
            return self._validate_number(prop_name, prop_value)
        
        # Select
        elif prop_type == "select":
            return self._validate_select(prop_name, prop_value, prop_schema)
        
        # Multi-select
        elif prop_type == "multi_select":
            return self._validate_multi_select(prop_name, prop_value, prop_schema)
        
        # Status
        elif prop_type == "status":
            return self._validate_status(prop_name, prop_value, prop_schema)
        
        # Date
        elif prop_type == "date":
            return self._validate_date(prop_name, prop_value)
        
        # Checkbox
        elif prop_type == "checkbox":
            return self._validate_checkbox(prop_name, prop_value)
        
        # URL
        elif prop_type == "url":
            return self._validate_url(prop_name, prop_value)
        
        # Email
        elif prop_type == "email":
            return self._validate_email(prop_name, prop_value)
        
        # Phone number
        elif prop_type == "phone_number":
            return self._validate_phone(prop_name, prop_value)
        
        # Relation, people, files - accept as-is (complex validation)
        elif prop_type in ["relation", "people", "files"]:
            return None
        
        # Read-only types - should not be in input
        elif prop_type in ["created_time", "created_by", "last_edited_time", "last_edited_by", "formula", "rollup"]:
            return f"Property '{prop_name}' is read-only (type: {prop_type})"
        
        # Unknown type
        else:
            return None  # Allow unknown types (forward compatibility)
    
    def _validate_title(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate title property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (title) must be a dict with 'title' array"
        
        if "title" not in value:
            return f"Property '{prop_name}' (title) missing 'title' key"
        
        if not isinstance(value["title"], list):
            return f"Property '{prop_name}' (title) 'title' must be an array"
        
        return None
    
    def _validate_rich_text(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate rich text property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (rich_text) must be a dict"
        
        if "rich_text" not in value:
            return f"Property '{prop_name}' (rich_text) missing 'rich_text' key"
        
        if not isinstance(value["rich_text"], list):
            return f"Property '{prop_name}' (rich_text) must be an array"
        
        return None
    
    def _validate_number(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate number property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (number) must be a dict"
        
        if "number" not in value:
            return f"Property '{prop_name}' (number) missing 'number' key"
        
        num = value["number"]
        if num is not None and not isinstance(num, (int, float)):
            return f"Property '{prop_name}' (number) value must be a number or null"
        
        return None
    
    def _validate_select(self, prop_name: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate select property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (select) must be a dict"
        
        if "select" not in value:
            return f"Property '{prop_name}' (select) missing 'select' key"
        
        select = value["select"]
        if select is None:
            return None  # Null is valid
        
        if not isinstance(select, dict):
            return f"Property '{prop_name}' (select) value must be a dict or null"
        
        # Check if option is valid (if schema has options)
        options = schema.get("options", [])
        if options and "name" in select:
            if select["name"] not in options:
                return (
                    f"Property '{prop_name}' (select) invalid option '{select['name']}'. "
                    f"Valid options: {options}"
                )
        
        return None
    
    def _validate_multi_select(self, prop_name: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate multi-select property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (multi_select) must be a dict"
        
        if "multi_select" not in value:
            return f"Property '{prop_name}' (multi_select) missing 'multi_select' key"
        
        multi_select = value["multi_select"]
        if not isinstance(multi_select, list):
            return f"Property '{prop_name}' (multi_select) value must be an array"
        
        # Check if options are valid (if schema has options)
        options = schema.get("options", [])
        if options:
            for item in multi_select:
                if isinstance(item, dict) and "name" in item:
                    if item["name"] not in options:
                        return (
                            f"Property '{prop_name}' (multi_select) invalid option '{item['name']}'. "
                            f"Valid options: {options}"
                        )
        
        return None
    
    def _validate_status(self, prop_name: str, value: Any, schema: Dict[str, Any]) -> Optional[str]:
        """Validate status property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (status) must be a dict"
        
        if "status" not in value:
            return f"Property '{prop_name}' (status) missing 'status' key"
        
        status = value["status"]
        if status is None:
            return None
        
        if not isinstance(status, dict):
            return f"Property '{prop_name}' (status) value must be a dict or null"
        
        # Check if option is valid
        options = schema.get("options", [])
        if options and "name" in status:
            if status["name"] not in options:
                return (
                    f"Property '{prop_name}' (status) invalid option '{status['name']}'. "
                    f"Valid options: {options}"
                )
        
        return None
    
    def _validate_date(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate date property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (date) must be a dict"
        
        if "date" not in value:
            return f"Property '{prop_name}' (date) missing 'date' key"
        
        date = value["date"]
        if date is None:
            return None
        
        if not isinstance(date, dict):
            return f"Property '{prop_name}' (date) value must be a dict or null"
        
        if "start" not in date:
            return f"Property '{prop_name}' (date) missing 'start' key"
        
        return None
    
    def _validate_checkbox(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate checkbox property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (checkbox) must be a dict"
        
        if "checkbox" not in value:
            return f"Property '{prop_name}' (checkbox) missing 'checkbox' key"
        
        if not isinstance(value["checkbox"], bool):
            return f"Property '{prop_name}' (checkbox) value must be boolean"
        
        return None
    
    def _validate_url(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate URL property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (url) must be a dict"
        
        if "url" not in value:
            return f"Property '{prop_name}' (url) missing 'url' key"
        
        url = value["url"]
        if url is not None and not isinstance(url, str):
            return f"Property '{prop_name}' (url) value must be string or null"
        
        return None
    
    def _validate_email(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate email property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (email) must be a dict"
        
        if "email" not in value:
            return f"Property '{prop_name}' (email) missing 'email' key"
        
        email = value["email"]
        if email is not None and not isinstance(email, str):
            return f"Property '{prop_name}' (email) value must be string or null"
        
        return None
    
    def _validate_phone(self, prop_name: str, value: Any) -> Optional[str]:
        """Validate phone number property."""
        if not isinstance(value, dict):
            return f"Property '{prop_name}' (phone_number) must be a dict"
        
        if "phone_number" not in value:
            return f"Property '{prop_name}' (phone_number) missing 'phone_number' key"
        
        phone = value["phone_number"]
        if phone is not None and not isinstance(phone, str):
            return f"Property '{prop_name}' (phone_number) value must be string or null"
        
        return None


def quick_validate(properties: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Quick validation helper that raises exception on error.
    
    Args:
        properties: Properties to validate
        schema: Database schema
        
    Raises:
        ValueError: If validation fails
    """
    validator = PropertyValidator(schema)
    is_valid, errors = validator.validate_properties(properties)
    
    if not is_valid:
        raise ValueError(
            f"Property validation failed:\n" +
            "\n".join(f"  • {error}" for error in errors)
        )
