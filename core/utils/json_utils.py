"""
JSON Utilities - JSON manipulation and validation
"""

import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import jsonschema
from datetime import datetime

class JSONUtils:
    """JSON manipulation utilities"""
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], 
                           schema: Dict[str, Any]) -> List[str]:
        """
        Validate JSON data against schema
        
        Args:
            data: JSON data to validate
            schema: JSON schema
            
        Returns:
            List of validation errors (empty if valid)
        """
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        error_messages = []
        for error in errors:
            error_messages.append(f"{error.json_path}: {error.message}")
            
        return error_messages
        
    @staticmethod
    def load_json_safe(filepath: Union[str, Path], 
                      default: Any = None) -> Any:
        """
        Load JSON file safely with fallback
        
        Args:
            filepath: Path to JSON file
            default: Default value if loading fails
            
        Returns:
            Parsed JSON data or default value
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load JSON from {filepath}: {e}")
            return default
            
    @staticmethod
    def save_json_safe(filepath: Union[str, Path], 
                      data: Any,
                      indent: int = 2,
                      ensure_ascii: bool = False) -> bool:
        """
        Save data to JSON file safely
        
        Args:
            filepath: Path to save JSON file
            data: Data to save
            indent: JSON indentation
            ensure_ascii: Whether to ensure ASCII output
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, 
                         ensure_ascii=ensure_ascii, 
                         default=JSONUtils._json_serializer)
            return True
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")
            return False
            
    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer for unsupported types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
            
    @staticmethod
    def merge_json(*json_objects: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple JSON objects
        
        Args:
            *json_objects: JSON objects to merge
            
        Returns:
            Merged JSON object
        """
        result = {}
        for obj in json_objects:
            if obj:
                result.update(obj)
        return result
        
    @staticmethod
    def deep_merge(base: Dict[str, Any], 
                  update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two JSON objects
        
        Args:
            base: Base JSON object
            update: JSON object to merge into base
            
        Returns:
            Deep merged JSON object
        """
        result = base.copy()
        
        for key, value in update.items():
            if (key in result and isinstance(result[key], dict) 
                and isinstance(value, dict)):
                result[key] = JSONUtils.deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
        
    @staticmethod
    def filter_json(data: Dict[str, Any], 
                   include_keys: Optional[List[str]] = None,
                   exclude_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Filter JSON object by keys
        
        Args:
            data: JSON object to filter
            include_keys: Keys to include (None = all)
            exclude_keys: Keys to exclude
            
        Returns:
            Filtered JSON object
        """
        if include_keys is not None:
            return {k: v for k, v in data.items() if k in include_keys}
        elif exclude_keys is not None:
            return {k: v for k, v in data.items() if k not in exclude_keys}
        else:
            return data.copy()
            
    @staticmethod
    def flatten_json(data: Dict[str, Any], 
                    separator: str = '.',
                    prefix: str = '') -> Dict[str, Any]:
        """
        Flatten nested JSON object
        
        Args:
            data: JSON object to flatten
            separator: Key separator for nested keys
            prefix: Prefix for keys
            
        Returns:
            Flattened JSON object
        """
        items = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                items.update(JSONUtils.flatten_json(value, separator, new_key))
            else:
                items[new_key] = value
                
        return items
        
    @staticmethod
    def unflatten_json(data: Dict[str, Any], 
                      separator: str = '.') -> Dict[str, Any]:
        """
        Unflatten JSON object
        
        Args:
            data: Flattened JSON object
            separator: Key separator used during flattening
            
        Returns:
            Nested JSON object
        """
        result = {}
        
        for key, value in data.items():
            parts = key.split(separator)
            current = result
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
        return result
        
    @staticmethod
    def json_path_get(data: Dict[str, Any], 
                     path: str, 
                     default: Any = None) -> Any:
        """
        Get value from JSON using path notation
        
        Args:
            data: JSON object
            path: Path to value (e.g., "user.address.city")
            default: Default value if path not found
            
        Returns:
            Value at path or default
        """
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
        
    @staticmethod
    def json_path_set(data: Dict[str, Any], 
                     path: str, 
                     value: Any) -> Dict[str, Any]:
        """
        Set value in JSON using path notation
        
        Args:
            data: JSON object
            path: Path to set value
            value: Value to set
            
        Returns:
            Updated JSON object
        """
        parts = path.split('.')
        current = data
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
            
        current[parts[-1]] = value
        return data
        
    @staticmethod
    def json_diff(obj1: Dict[str, Any], 
                 obj2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find differences between two JSON objects
        
        Args:
            obj1: First JSON object
            obj2: Second JSON object
            
        Returns:
            Dictionary with added, removed, and changed keys
        """
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # Find added and changed keys
        for key in obj2:
            if key not in obj1:
                diff["added"][key] = obj2[key]
            elif obj1[key] != obj2[key]:
                diff["changed"][key] = {
                    "old": obj1[key],
                    "new": obj2[key]
                }
                
        # Find removed keys
        for key in obj1:
            if key not in obj2:
                diff["removed"][key] = obj1[key]
                
        return diff
        
    @staticmethod
    def json_pretty_print(data: Any, 
                         indent: int = 2) -> str:
        """
        Pretty print JSON data
        
        Args:
            data: JSON data to print
            indent: Indentation level
            
        Returns:
            Pretty printed JSON string
        """
        return json.dumps(data, indent=indent, 
                         ensure_ascii=False,
                         default=JSONUtils._json_serializer)
                         
    @staticmethod
    def json_minify(data: Any) -> str:
        """
        Minify JSON data
        
        Args:
            data: JSON data to minify
            
        Returns:
            Minified JSON string
        """
        return json.dumps(data, separators=(',', ':'),
                         ensure_ascii=False,
                         default=JSONUtils._json_serializer)
                         
    @staticmethod
    def json_to_csv(data: List[Dict[str, Any]]) -> str:
        """
        Convert JSON array to CSV
        
        Args:
            data: List of JSON objects
            
        Returns:
            CSV string
        """
        if not data:
            return ""
            
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
            
        keys = sorted(all_keys)
        
        # Create CSV header
        csv_lines = [','.join(keys)]
        
        # Create CSV rows
        for item in data:
            row = []
            for key in keys:
                value = item.get(key, "")
                # Escape quotes and commas
                if isinstance(value, str):
                    value = value.replace('"', '""')
                    if ',' in value or '"' in value:
                        value = f'"{value}"'
                row.append(str(value))
            csv_lines.append(','.join(row))
            
        return '\n'.join(csv_lines)
        
    @staticmethod
    def json_schema_from_data(data: Any) -> Dict[str, Any]:
        """
        Generate JSON schema from data
        
        Args:
            data: Sample data
            
        Returns:
            Generated JSON schema
        """
        def _generate_schema(obj: Any) -> Dict[str, Any]:
            if isinstance(obj, dict):
                properties = {}
                required = []
                
                for key, value in obj.items():
                    properties[key] = _generate_schema(value)
                    required.append(key)
                    
                return {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            elif isinstance(obj, list):
                if obj:
                    return {
                        "type": "array",
                        "items": _generate_schema(obj[0])
                    }
                else:
                    return {
                        "type": "array",
                        "items": {}
                    }
            elif isinstance(obj, str):
                return {"type": "string"}
            elif isinstance(obj, (int, float)):
                return {"type": "number"}
            elif isinstance(obj, bool):
                return {"type": "boolean"}
            elif obj is None:
                return {"type": "null"}
            else:
                return {"type": "string"}
                
        return _generate_schema(data)
        
    @staticmethod
    def json_sort_keys(data: Dict[str, Any],
                      recursive: bool = True) -> Dict[str, Any]:
        """
        Sort JSON keys alphabetically
        
        Args:
            data: JSON object
            recursive: Whether to sort recursively
            
        Returns:
            JSON object with sorted keys
        """
        if not isinstance(data, dict):
            return data
            
        sorted_data = {k: data[k] for k in sorted(data.keys())}
        
        if recursive:
            for key, value in sorted_data.items():
                if isinstance(value, dict):
                    sorted_data[key] = JSONUtils.json_sort_keys(value, True)
                elif isinstance(value, list):
                    sorted_data[key] = [
                        JSONUtils.json_sort_keys(item, True) 
                        if isinstance(item, dict) else item
                        for item in value
                    ]
                    
        return sorted_data
        
    @staticmethod
    def json_remove_nulls(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove null values from JSON
        
        Args:
            data: JSON object
            
        Returns:
            JSON object without null values
        """
        if not isinstance(data, dict):
            return data
            
        result = {}
        for key, value in data.items():
            if value is not None:
                if isinstance(value, dict):
                    cleaned = JSONUtils.json_remove_nulls(value)
                    if cleaned:  # Only add if not empty after cleaning
                        result[key] = cleaned
                elif isinstance(value, list):
                    cleaned_list = [
                        JSONUtils.json_remove_nulls(item) 
                        if isinstance(item, dict) else item
                        for item in value if item is not None
                    ]
                    if cleaned_list:
                        result[key] = cleaned_list
                else:
                    result[key] = value
                    
        return result
        
    @staticmethod
    def json_extract_values(data: Dict[str, Any], 
                           key_to_find: str) -> List[Any]:
        """
        Extract all values for a specific key from nested JSON
        
        Args:
            data: JSON object
            key_to_find: Key to extract values for
            
        Returns:
            List of values
        """
        values = []
        
        def _extract(obj: Any):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == key_to_find:
                        values.append(value)
                    _extract(value)
            elif isinstance(obj, list):
                for item in obj:
                    _extract(item)
                    
        _extract(data)
        return values