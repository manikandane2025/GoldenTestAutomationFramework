import json
import requests
from jsonschema import validate, ValidationError


class SimpleJSONClient:
    def __init__(self):
        pass

    # Load JSON from file or API
    def load_json_from_file(self, file_path: str):
        """Load JSON data from a file."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            raise Exception(f"Error loading file: {e}")

    def load_json_from_api(self, url: str, params: dict = None, headers: dict = None):
        """Load JSON data from an API."""
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error fetching from API: {e}")

    # Pretty print JSON
    def pretty_print_json(self, json_data):
        """Pretty print JSON."""
        try:
            return json.dumps(json_data, indent=4)
        except Exception as e:
            raise Exception(f"Error printing JSON: {e}")

    # Extract value from JSON (handles both dict and list)
    def extract_value(self, json_data, key: str):
        """Extract value from JSON using key (supports nested keys)."""
        try:
            if isinstance(json_data, dict):
                return self._extract_from_dict(json_data, key)
            elif isinstance(json_data, list):
                return self._extract_from_list(json_data, key)
            else:
                raise ValueError("Data is neither a dictionary nor a list.")
        except Exception as e:
            raise Exception(f"Error extracting value: {e}")

    def _extract_from_dict(self, json_data, key):
        """Extract from dict."""
        keys = key.split('.')
        for k in keys:
            if k in json_data:
                json_data = json_data[k]
            else:
                raise KeyError(f"Key '{key}' not found.")
        return json_data

    def _extract_from_list(self, json_data, key):
        """Extract from list."""
        if isinstance(json_data, list):
            if key.isdigit():
                index = int(key)
                return json_data[index] if index < len(json_data) else None
            else:
                if isinstance(json_data[0], dict):
                    return [item for item in json_data if key in item]
                else:
                    raise ValueError("Invalid key for list access.")
        else:
            raise ValueError("Expected a list, but got a different data type.")

    # Bulk Update multiple keys in the JSON
    def bulk_update(self, json_data, updates: dict):
        """Bulk update multiple keys in the JSON."""
        for key, value in updates.items():
            self.update_value(json_data, key, value)
        return json_data

    def update_value(self, json_data, key: str, new_value):
        """Update a value in JSON data by key."""
        try:
            if isinstance(json_data, dict):
                return self._update_in_dict(json_data, key, new_value)
            elif isinstance(json_data, list):
                return self._update_in_list(json_data, key, new_value)
            else:
                raise ValueError("Input data is neither a dictionary nor a list.")
        except Exception as e:
            raise Exception(f"Error updating value: {e}")

    def _update_in_dict(self, json_data, key, new_value):
        """Update value in a dictionary."""
        keys = key.split('.')
        for k in keys[:-1]:
            json_data = json_data.get(k, {})
        json_data[keys[-1]] = new_value
        return json_data

    def _update_in_list(self, json_data, key, new_value):
        """Update a value in a list based on index or field name."""
        try:
            index = int(key)
            json_data[index] = new_value
        except ValueError:
            raise ValueError(f"Invalid key '{key}' for list update. Use index or field name.")
        return json_data

    # Bulk Delete multiple keys in the JSON
    def bulk_delete(self, json_data, keys: list):
        """Delete multiple keys in JSON."""
        for key in keys:
            self.delete_key(json_data, key)
        return json_data

    # Delete a key from the JSON
    def delete_key(self, json_data, key: str):
        """Delete a key-value pair from JSON."""
        try:
            if isinstance(json_data, dict):
                keys = key.split('.')
                for k in keys[:-1]:
                    json_data = json_data.get(k, {})
                del json_data[keys[-1]]
            elif isinstance(json_data, list):
                index = int(key)
                del json_data[index]
            else:
                raise ValueError("Input data is neither a dictionary nor a list.")
            return json_data
        except Exception as e:
            raise Exception(f"Error deleting key: {e}")

    # Value Assertions
    def assert_value(self, json_data, key: str, expected_value):
        """Assert the value extracted from JSON matches the expected value."""
        actual_value = self.extract_value(json_data, key)
        assert actual_value == expected_value, f"Assertion failed: expected '{expected_value}', got '{actual_value}'"

    # Existence Assertions
    def assert_exists(self, json_data, key: str):
        """Assert that the key exists in the JSON data."""
        try:
            self.extract_value(json_data, key)
        except KeyError:
            raise AssertionError(f"Key '{key}' does not exist in the JSON data.")

    # JSON Schema Validation
    def validate_json_schema(self, json_data, schema):
        """Validate if JSON data matches a schema."""
        try:
            validate(instance=json_data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"JSON schema validation error: {e.message}")

    # Dynamic Field Extraction from Lists
    def dynamic_extract(self, json_data, condition: dict):
        """Extract elements from a list based on dynamic conditions."""
        try:
            if isinstance(json_data, list):
                key, value = list(condition.items())[0]
                return [item for item in json_data if isinstance(item, dict) and item.get(key) == value]
            else:
                raise ValueError("Expected list data type.")
        except Exception as e:
            raise Exception(f"Error in dynamic extraction: {e}")

    # Key Renaming
    def rename_key(self, json_data, old_key: str, new_key: str):
        """Rename a key in the JSON data."""
        if isinstance(json_data, dict):
            if old_key in json_data:
                json_data[new_key] = json_data.pop(old_key)
            else:
                raise KeyError(f"Key '{old_key}' not found.")
        return json_data

    # Create Nested JSON Structure
    def create_nested_json(self, *args):
        """Create a nested JSON structure from a list of keys and values."""
        json_data = {}
        for i in range(0, len(args), 2):
            key = args[i]
            value = args[i + 1]
            keys = key.split('.')
            temp = json_data
            for key_part in keys[:-1]:
                temp = temp.setdefault(key_part, {})
            temp[keys[-1]] = value
        return json_data

    # Create Empty JSON
    def create_empty_json(self):
        """Create an empty JSON object."""
        return {}

    # Merge JSON Objects
    def merge_json(self, json1, json2):
        """Merge two JSON objects. json2 will overwrite json1's values."""
        json1.update(json2)
        return json1


# Example Usage
client = SimpleJSONClient()

# 1. Create Nested JSON
nested_json = client.create_nested_json(
    'user.name', 'John',
    'user.address.city', 'New York',
    'user.address.zip', '10001'
)
print("Nested JSON:", json.dumps(nested_json, indent=4))

# 2. Create Empty JSON
empty_json = client.create_empty_json()
print("Empty JSON:", json.dumps(empty_json, indent=4))

# 3. Merge JSON
json_data_1 = {"user": {"name": "John", "age": 30}}
json_data_2 = {"user": {"age": 25, "city": "New York"}}
merged_json = client.merge_json(json_data_1, json_data_2)
print("Merged JSON:", json.dumps(merged_json, indent=4))

# 4. Validate JSON schema
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"]
}
json_data = {"name": "John", "age": 30}
client.validate_json_schema(json_data, schema)

# 5. Perform assertion on value
client.assert_value(json_data, "name", "John")

# 6. Bulk update keys in JSON
json_data = {"name": "John", "age": 30}
updated_json = client.bulk_update(json_data, {"name": "Jane", "age": 25})
print("Updated JSON:", json.dumps(updated_json, indent=4))

# 7. Dynamic extraction from list
json_data = [{"user": "John", "status": "active"}, {"user": "Jane", "status": "inactive"}]
extracted_data = client.dynamic_extract(json_data, {"status": "active"})
print("Extracted Data:", extracted_data)

# 8. Rename a key in JSON
renamed_json = client.rename_key(json_data, "name", "full_name")
print("Renamed JSON:", json.dumps(renamed_json, indent=4))
