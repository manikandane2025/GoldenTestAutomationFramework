from __future__ import absolute_import
import base64
import six
from behave.formatter.base import Formatter
from behave.model_core import Status
from datetime import datetime
from Utility.frameworkDataContext import CustomContext

try:
    import json
except ImportError:
    import simplejson as json


class CustomJSONFormatter(Formatter):
    name = "json"
    description = "JSON dump of test run"
    dumps_kwargs = {}
    split_text_into_lines = True

    json_number_types = six.integer_types + (float,)
    json_scalar_types = json_number_types + (six.text_type, bool, type(None))

    def __init__(self, stream_opener, config):
        super(CustomJSONFormatter, self).__init__(stream_opener, config)
        self.stream = self.open()
        self.feature_count = 0
        self.current_feature = None
        self.current_feature_data = None
        self.current_scenario = None
        self._step_index = 0
        self.user_data = {}
        self.customContext = CustomContext()

    def reset(self):
        self.current_feature = None
        self.current_feature_data = None
        self.current_scenario = None
        self._step_index = 0

    # -- FORMATTER API:
    def uri(self, uri):
        pass

    def feature(self, feature):
        self.reset()
        self.current_feature = feature
        self.current_feature_data = {
            "keyword": feature.keyword,
            "name": feature.name,
            "tags": list(feature.tags),
            "location": six.text_type(feature.location),
            "status": None,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
        }
        element = self.current_feature_data
        if feature.description:
            element["description"] = feature.description

    def background(self, background):
        # FIX: Call generic finalizer for the previous element (if any)
        self.finish_previous_element_data()

        element = self.add_feature_element({
            "type": "background",
            "keyword": background.keyword,
            "name": background.name,
            "location": six.text_type(background.location),
            "status": "",  # Background status is determined by its step statuses
            "steps": [],
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
            "tags": []
        })
        if background.name:
            element["name"] = background.name
        self._step_index = 0

        for step_ in background.steps:
            self.step(step_)

    def scenario(self, scenario):
        # FIX: Call generic finalizer for the previous element (which might be the Background)
        self.finish_previous_element_data()
        self.current_scenario = scenario
        retry_attempts = getattr(scenario, 'retry_attempts', 0)
        element = self.add_feature_element({
            "type": "scenario",
            "keyword": scenario.keyword,
            "name": scenario.name,
            "tags": scenario.tags,
            "location": six.text_type(scenario.location),
            "steps": [],
            "status": None,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
            "retry_attempts": retry_attempts
        })
        if scenario.description:
            element["description"] = scenario.description
        self._step_index = 0

    @classmethod
    def make_table(cls, table):
        table_data = {
            "headings": table.headings,
            "rows": [list(row) for row in table.rows]
        }
        return table_data

    def step(self, step):
        s = {
            "keyword": step.keyword,
            "step_type": step.step_type,
            "name": step.name,
            "location": six.text_type(step.location),
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": None,
        }

        if step.text:
            text = step.text
            if self.split_text_into_lines and "\n" in text:
                text = text.splitlines()
            s["text"] = text
        if step.table:
            s["table"] = self.make_table(step.table)

        element = self.current_feature_element
        element["steps"].append(s)

    def match(self, match):
        args = []
        for argument in match.arguments:
            argument_value = argument.value
            if not isinstance(argument_value, self.json_scalar_types):
                argument_value = argument.original
            assert isinstance(argument_value, self.json_scalar_types)
            arg = {
                "value": argument_value,
            }
            if argument.name:
                arg["name"] = argument.name
            if argument.original != argument_value:
                arg["original"] = argument.original
            args.append(arg)

        match_data = {
            "location": six.text_type(match.location) or "",
            "arguments": args,
        }
        if match.location:
            steps = self.current_feature_element["steps"]
            steps[self._step_index]["match"] = match_data

    def result(self, step):
        # Fetch input and output data from CustomContext
        input_data = {}
        output_data = {}
        screenshot_data = {}

        for key in CustomContext().user_data.keys():
            if key.startswith('inputdata'):
                input_data[key] = CustomContext.get_user_data(key)

        for key in CustomContext().user_data.keys():
            if key.startswith('outputdata'):
                output_data[key] = CustomContext.get_user_data(key)

        for key in CustomContext().user_data.keys():
            if key.startswith('screenshot'):
                screenshot_data[key] = CustomContext.get_user_data(key)

        CustomContext.set_user_data("Input Data", input_data)
        CustomContext.set_user_data("Output Data", output_data)
        CustomContext.set_user_data("Screenshot Data", screenshot_data)

        rounded_duration = round(step.duration, 2)

        steps = self.current_feature_element["steps"]

        steps[self._step_index]["Test_data"] = input_data
        steps[self._step_index]["Test_Output_data"] = output_data
        steps[self._step_index]["Screenshot_data"] = screenshot_data

        steps[self._step_index]["result"] = {
            "status": step.status.name,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": rounded_duration,
        }

        if step.error_message and step.status == Status.failed:
            error_message = step.error_message
            if self.split_text_into_lines and "\n" in error_message:
                error_message = error_message.splitlines()
            result_element = steps[self._step_index]["result"]
            result_element["error_message"] = error_message

        if step.error_message and step.status == Status.error:
            error_message = step.error_message
            if self.split_text_into_lines and "\n" in error_message:
                error_message = error_message.splitlines()
            result_element = steps[self._step_index]["result"]
            result_element["error_message"] = error_message

        self._step_index += 1

        if input_data:
            CustomContext.reset_user_data("inputdata")
        if output_data:
            CustomContext.reset_user_data("outputdata")
        if screenshot_data:
            CustomContext.reset_user_data("screenshot")

    def embedding(self, mime_type, data):
        step = self.current_feature_element["steps"][self._step_index]
        if "embeddings" not in step:
            step["embeddings"] = []
        step["embeddings"].append({
            "mime_type": mime_type,
            "data": base64.b64encode(data).decode(self.stream.encoding or "utf-8"),
        })

    def eof(self):
        """
        End of feature
        """
        if not self.current_feature_data:
            return

        self.finish_previous_element_data()  # Finalize the last element of the feature
        self.update_status_data()

        if self.feature_count == 0:
            self.write_json_header()
        else:
            self.write_json_feature_separator()

        self.write_json_feature(self.current_feature_data)
        self.reset()
        self.feature_count += 1

    def close(self):
        if self.feature_count == 0:
            self.write_json_header()
        self.write_json_footer()
        self.close_stream()

    # -- JSON-DATA COLLECTION:
    def add_feature_element(self, element):
        assert self.current_feature_data is not None
        if "elements" not in self.current_feature_data:
            self.current_feature_data["elements"] = []
        self.current_feature_data["elements"].append(element)
        return element

    @property
    def current_feature_element(self):
        assert self.current_feature_data is not None
        return self.current_feature_data["elements"][-1]

    def update_status_data(self):
        assert self.current_feature
        assert self.current_feature_data
        self.current_feature_data["status"] = self.current_feature.status.name
        self.current_feature_data["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def finish_previous_element_data(self):
        """
        Safely sets the final status, end time, and retry attempts for the completed element
        (Scenario or Background). Only Scenario elements get explicit status fields.
        """
        if not self.current_feature_data or "elements" not in self.current_feature_data:
            return

        element = self.current_feature_data["elements"][-1]

        # Only process Scenario elements for status, end time, and retries. Backgrounds are ignored here.
        if element.get("type") == "scenario" and self.current_scenario:
            status_name = getattr(self.current_scenario.status, 'name', 'untested') if hasattr(self.current_scenario,
                                                                                               'status') else 'untested'
            retry_attempts = getattr(self.current_scenario, 'retry_attempts', 0)

            # Set required keys on the scenario element
            element["status"] = status_name
            element["end_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")

            # Include retry attempts
            element["retry_attempts"] = retry_attempts

    # -- JSON-WRITER:
    def write_json_header(self):
        self.stream.write("[\n")

    def write_json_footer(self):
        self.stream.write("\n]\n")

    def write_json_feature(self, feature_data):
        self.stream.write(json.dumps(feature_data, **self.dumps_kwargs))
        self.stream.flush()

    def write_json_feature_separator(self):
        self.stream.write(",\n\n")

    def get_step_input_data(self, step):
        """Capture the input data for the step."""
        input_data = {}
        if hasattr(step, 'context'):
            context = step.context

            if hasattr(context, 'input_data'):
                input_data = context.input_data
                print(f"Input data: {input_data}")

            elif hasattr(context, 'user_data'):
                input_data = context.user_data
                print(f"user_data: {input_data}")

        return input_data

    def get_step_output_data(self, step):
        """Capture the output data for the step."""
        output_data = {}
        if hasattr(step, 'context') and hasattr(step.context, 'processed_data'):
            output_data = step.context.processed_data
        return output_data

    def step_event(self, context, step, result, exception):

        current_user = context.user_data.get("testdata")

        retry_attempts = getattr(context, 'retry_attempts', 0)

        step_result = {
            "status": result.status.name,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": result.duration
        }

        if result.status == Status.failed and result.error_message:
            step_result["error_message"] = result.error_message

        steps = self.current_feature_element["steps"]
        steps[self._step_index]["result"] = step_result
        super().step_event(context, step, result, exception)

    def get_user_data(self, step):
        """Retrieve user data from context."""
        if hasattr(step.context, 'user_data'):
            return step.context.user_data
        else:
            return {}