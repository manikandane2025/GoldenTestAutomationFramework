import yaml
import os
import json
from typing import Any, Dict, List
import copy
from jsonschema import validate as js_validate, ValidationError


class YAMLClient:
    def __init__(self, file_path: str = None):
        """Initialize the YAMLClient."""
        self.file_path = file_path
        self.data = {}

        if self.file_path:
            self.load(file_path)

    def load(self, file_path: str):
        """Load a YAML file into the client."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML file {file_path} not found.")

        with open(file_path, 'r') as file:
            self.data = yaml.safe_load(file)
        print(f"Loaded YAML data from {file_path}")

    def save(self, file_path: str = None):
        """Save the current data to a YAML file."""
        if not file_path:
            file_path = self.file_path
        if not file_path:
            raise ValueError("No file path provided for saving.")

        with open(file_path, 'w') as file:
            yaml.dump(self.data, file, default_flow_style=False)
        print(f"Data saved to {file_path}")

    def get(self, path: str) -> Any:
        """Retrieve data from the YAML structure using dot notation path."""
        keys = path.split(".")
        data = self.data

        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            else:
                raise KeyError(f"Path '{path}' not found in the data.")
        return data

    def set(self, path: str, value: Any):
        """Set data at a specific path in the YAML structure."""
        keys = path.split(".")
        data = self.data

        for key in keys[:-1]:
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            else:
                raise KeyError(f"Path '{path}' not found in the data.")
        data[keys[-1]] = value
        print(f"Set '{value}' at path '{path}'")

    def append(self, path: str, value: Any):
        """Append a value to a list at a specific path in the YAML structure."""
        keys = path.split(".")
        data = self.data

        for key in keys[:-1]:
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            else:
                raise KeyError(f"Path '{path}' not found in the data.")

        if isinstance(data[keys[-1]], list):
            data[keys[-1]].append(value)
            print(f"Appended '{value}' to list at path '{path}'")
        else:
            raise TypeError(f"The target path '{path}' does not point to a list.")

    def delete(self, path: str):
        """Delete an element from the YAML data using a path."""
        keys = path.split(".")
        data = self.data

        for key in keys[:-1]:
            if isinstance(data, dict) and key in data:
                data = data[key]
            elif isinstance(data, list) and key.isdigit():
                data = data[int(key)]
            else:
                raise KeyError(f"Path '{path}' not found in the data.")
        del data[keys[-1]]
        print(f"Deleted element at path '{path}'")

    def validate(self, schema: Dict):
        """Validate the YAML data against a provided schema."""
        try:
            js_validate(instance=self.data, schema=schema)
            print("YAML data is valid.")
        except ValidationError as e:
            print(f"Validation error: {e.message}")
            raise e

    def deep_copy(self):
        """Return a deep copy of the current YAML data."""
        return copy.deepcopy(self.data)

    def to_dict(self) -> Dict:
        """Return the data as a Python dictionary."""
        return self.data

    def to_yaml(self) -> str:
        """Return the data as a YAML formatted string."""
        return yaml.dump(self.data, default_flow_style=False)

    def replace_placeholders(self, replacements: Dict[str, str]):
        """Replace placeholders in the YAML data with the provided values."""

        def recursive_replace(data):
            if isinstance(data, str):
                for key, value in replacements.items():
                    data = data.replace(f"{{{{{key}}}}}", value)
            elif isinstance(data, dict):
                for key, value in data.items():
                    data[key] = recursive_replace(value)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    data[i] = recursive_replace(item)
            return data

        self.data = recursive_replace(self.data)

    def merge(self, other_data: Dict):
        """Merge data from another YAML (or dictionary) into the current data."""
        if not isinstance(other_data, dict):
            raise ValueError("The data to merge must be a dictionary.")

        def deep_merge(original, new_data):
            """Recursively merge dictionaries."""
            for key, value in new_data.items():
                if isinstance(value, dict) and key in original:
                    original[key] = deep_merge(original.get(key, {}), value)
                else:
                    original[key] = value
            return original

        self.data = deep_merge(self.data, other_data)
        print("Merged data with the provided data.")

    def yaml_to_json(self) -> str:
        """Convert the loaded YAML data to JSON format."""
        return json.dumps(self.data, indent=2)

    def json_to_yaml(self, json_str: str):
        """Convert a JSON string to YAML format and update the client's data."""
        self.data = json.loads(json_str)
        print("Converted JSON to YAML and updated the data.")
