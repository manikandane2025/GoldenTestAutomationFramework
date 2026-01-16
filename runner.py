import argparse
import json
import os
import logging
import subprocess
import sys
import time
import traceback
import uuid
import zipfile
from datetime import datetime
import jinja2
from multiprocessing import Pool
import sqlite3
from behave.__main__ import main as behave_main
import yaml
from jinja2 import Environment, FileSystemLoader

import constants
# Import constants from constants.py
from constants import FEATURES_DIR, REPORTS_DIR, TEMPLATES_DIR, DEFAULT_TAGS, LOGGING_LEVEL, DEV_CONFIG_FILE, \
    QA_CONFIG_FILE, INT_CONFIG_FILE, BEHAVE_FORMAT, LOGS_DIR, PARALLEL_RUN, MAX_PARALLEL_JOBS, \
    BEHAVE_SHOW_SKIPPED_TESTS_IN_REPORTS, ARTIFACTS_DIR, Framework_Database_Path, PROJECT_NAME

json_report_file = None

TEST_EXECUTION_RUN_ID = str(uuid.uuid4())
TEST_EXECUTION_START_TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
ARTIFACTS_DIR_PATH = os.path.join(os.getcwd(), ARTIFACTS_DIR)
ARTIFACTS_ZIP_NAME = f"Test_Results_Artifacts_{TEST_EXECUTION_START_TIMESTAMP}.zip"
ARTIFACTS_ZIP_PATH = os.path.join(ARTIFACTS_DIR_PATH, ARTIFACTS_ZIP_NAME)
ARTIFACTS_RUN_PATH = os.path.join(ARTIFACTS_ZIP_PATH, TEST_EXECUTION_RUN_ID)
ARTIFACTS_SUPPORTING_FILES_PATH = os.path.join(ARTIFACTS_ZIP_PATH, "Supporting_Files")
LOG_FILE_NAME = f"test_execution_{TEST_EXECUTION_START_TIMESTAMP}.log"
LOG_FILE_PATH = os.path.join(os.getcwd(), LOGS_DIR, LOG_FILE_NAME)
HTML_REPORT_FILE = os.path.join(REPORTS_DIR, f'Test_report_{TEST_EXECUTION_START_TIMESTAMP}.html')


def configure_logging(log_level=LOGGING_LEVEL):
    logger = logging.getLogger("TestAutomationLogger")
    try:
        if logger.hasHandlers():
            return logger
        logs_folder = os.path.join(os.getcwd(), LOGS_DIR)
        if not os.path.exists(logs_folder):
            os.makedirs(logs_folder)
        timestamp = datetime.now().strftime(TEST_EXECUTION_START_TIMESTAMP)
        log_file = os.path.join(logs_folder, LOG_FILE_NAME)
        formatter = logging.Formatter(
            f"%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s - Line: %(lineno)d - %(message)s")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(log_level)
        logger.info(f"Test execution started with Run ID: {TEST_EXECUTION_RUN_ID}, log level: {log_level}")
        return logger
    except Exception as e:
        print(f"Error configuring logging: {str(e)}")
        raise


logger = configure_logging()


def save_instance_to_file():
    try:
        instance_data = {
            "TEST_EXECUTION_RUN_ID": TEST_EXECUTION_RUN_ID,
            "TEST_EXECUTION_START_TIMESTAMP": TEST_EXECUTION_START_TIMESTAMP,
            "ARTIFACTS_ZIP_NAME": ARTIFACTS_ZIP_NAME,
            "ARTIFACTS_ZIP_PATH": ARTIFACTS_ZIP_PATH,
            "ARTIFACTS_DIR_PATH": ARTIFACTS_DIR_PATH,
            "ARTIFACTS_RUN_PATH": ARTIFACTS_RUN_PATH,
            "ARTIFACTS_SUPPORTING_FILES_PATH": ARTIFACTS_SUPPORTING_FILES_PATH,
            "LOG_FILE_NAME": LOG_FILE_NAME,
            "LOG_FILE_PATH": LOG_FILE_PATH,
            "HTML_REPORT_FILE": HTML_REPORT_FILE,
            "TEST_ENVIRONMENT_NAME": os.environ.get("ENVIRONMENT", "dev"),
        }
        retries = 5
        delay = 1  # seconds
        for attempt in range(retries):
            try:
                with open("test_runner_instance.json", "w") as f:
                    json.dump(instance_data, f)
                logger.info("TestRunner instance data saved successfully.")
                break  # Exit the loop if successful
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} to save instance data failed: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.critical("Failed to save TestRunner instance data after multiple attempts.")
                    raise
    except Exception as e:
        logger.error(f"Error saving instance data: {str(e)}")
        exit(2)


save_instance_to_file()


def load_instance_from_file():
    try:
        if os.path.exists("test_runner_instance.json"):
            retries = 5
            delay = 1
            for attempt in range(retries):
                try:
                    with open("test_runner_instance.json", "r") as f:
                        instance_data = json.load(f)
                    logger.info("TestRunner instance data loaded successfully.")
                    return instance_data
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} to load instance data failed: {str(e)}")
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        logger.critical("Failed to load TestRunner instance data after multiple attempts.")
    except Exception as e:
        logger.error(f"Error loading instance data: {str(e)}")
        exit(3)


load_instance_from_file()


def create_folder_in_zip(zip_path, folder_name):
    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'a') as zipf:
                folder_path = f"{folder_name}/"
                zipf.writestr(folder_path, "")
            logger.info(f"Created folder '{folder_name}' in ZIP: {zip_path}")
        except Exception as e:
            logger.error(f"Error creating folder '{folder_name}' in ZIP: {str(e)}")
            raise


def create_artifacts_zip():
    try:
        os.makedirs(ARTIFACTS_DIR_PATH, exist_ok=True)
        with zipfile.ZipFile(ARTIFACTS_ZIP_PATH, "w") as zipf:
            run_id_folder = f"{TEST_EXECUTION_RUN_ID}/"
            zipf.writestr(run_id_folder, "")
        logger.info(f"Created test artifacts ZIP: {ARTIFACTS_ZIP_PATH}")
        create_folder_in_zip(ARTIFACTS_ZIP_PATH, os.path.basename(ARTIFACTS_SUPPORTING_FILES_PATH))
    except Exception as e:
        logger.error(f"Error creating artifacts ZIP: {str(e)}")
        raise


def add_file_to_artifacts(file_path, archive_name=None):
    """
    Adds a file to the artifact ZIP under the test run ID folder.

    :param file_path: Absolute path of the file to add.
    :param archive_name: Optional name inside the ZIP. Defaults to original filename.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found, skipping: {file_path}")
            return

        with zipfile.ZipFile(ARTIFACTS_ZIP_PATH, "a") as zipf:
            zip_archive_path = f"{TEST_EXECUTION_RUN_ID}/{archive_name if archive_name else os.path.basename(file_path)}"
            zipf.write(file_path, zip_archive_path)

        logger.info(f"Added file to artifacts: {file_path} as {zip_archive_path}")

    except Exception as e:
        logger.error(f"Error adding file to artifacts: {str(e)}")
        raise


def create_or_retrieve_framework_database(Database_Path=None):
    """Creates or retrieves a SQLite database for the framework."""
    try:
        if Database_Path is not None:
            framework_database = Database_Path
            if os.path.exists(framework_database):
                logger.info(f"Using existing framework database at: {framework_database}")
                return framework_database
            else:
                logger.error(f"Database Not Exists: {str(framework_database)}")
                return None
        else:
            framework_database = Framework_Database_Path
            if not os.path.exists(framework_database):
                logger.info(f"Creating new framework database at: {framework_database}")
                try:
                    framework_database_dir = os.path.dirname(framework_database)
                    if not os.path.exists(framework_database_dir):
                        os.makedirs(framework_database_dir)
                        logger.info(f"Created directory for database at: {framework_database_dir}")
                    conn = sqlite3.connect(framework_database)
                    logger.info(f"Framework database created at: {framework_database}")
                    conn.close()
                    return framework_database
                except Exception as e:
                    logger.error(f"Error creating framework database: {str(e)}")
                    raise
        return framework_database
    except Exception as e:
        logger.error(f"Error in create_or_retrieve_framework_database: {str(e)}")
        raise


database = create_or_retrieve_framework_database()


class FrameworkExecutionConfig:
    """Handles loading and accessing framework configuration from a YAML file.
    """

    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = None

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                self.config_data = yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found!")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {self.config_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config file {self.config_file}: {str(e)}")
            raise

    def get(self, key, default=None):
        """Retrieves a configuration value by key, returning a default if the key is not found."""
        if self.config_data is None:
            self.load_config()
        return self.config_data.get(key, default)


class TestRunnerConfig:
    """ Singleton class to manage test runner configuration and state.
    """

    def __init__(self, env="dev"):
        self.env = env
        self.config = None
        self.load_environment_config(env)

    def load_environment_config(self, env="dev"):
        """Loads the configuration for the specified environment.
        Args:   env (str): The environment for which the configuration should be loaded (default is "dev")."""
        # Define a mapping of environment names to config files
        env_config_map = {
            "dev": DEV_CONFIG_FILE,
            "qa": QA_CONFIG_FILE,
            "int": INT_CONFIG_FILE
        }

        # If the provided environment is not recognized, default to "dev"
        config_file = env_config_map.get(env.lower(), DEV_CONFIG_FILE)

        # Log the environment and configuration file being used
        if config_file != env_config_map.get(env.lower()):
            logger.warning(f"Unknown environment '{env}'. Defaulting to 'dev'. Using configuration file: {config_file}")
        else:
            logger.info(f"Loading configuration for environment '{env}' from {config_file}")
            os.environ["Test_Environment"] = env

        # Load the configuration
        try:
            self.config = FrameworkExecutionConfig(config_file)
            self.config.load_config()  # This will load the actual configuration data
        except Exception as e:
            logger.error(f"Error loading configuration for environment '{env}': {str(e)}")
            raise

    def get_config(self):
        return self.config


config = TestRunnerConfig(env=os.getenv("ENVIRONMENT", "dev")).get_config()


def construct_behave_args(test_tags=DEFAULT_TAGS, feature_files=None):
    behave_args = []
    # If test_tags is not provided, use DEFAULT_TAGS
    if test_tags:
        effective_tags = list(set(DEFAULT_TAGS + test_tags))  # Merging the tags and removing duplicates
        behave_args.append(f"--tags={','.join(effective_tags)}")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    # Generate timestamps for reports
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # Define the output path for JSON report (separate JSON for each test run)
    json_report_file = os.path.join(REPORTS_DIR, f'behave_report_{timestamp}.json')
    html_report_file = HTML_REPORT_FILE

    ## Add the --format=json option and specify the json report file using --outfile
    behave_args.append("--no-capture")
    if feature_files:
        return behave_args, json_report_file, html_report_file, feature_files
    return behave_args, json_report_file, html_report_file


def merge_json_reports(json_report_files):
    """Merges multiple JSON report files into a single list of results.
    Args:   json_report_files (list of str): List of file paths to JSON reports.
    Returns:    list: A merged list of results from all valid JSON files.
    Raises:     ValueError: If merged data structure is not a list.
     """
    merged_results = []

    for file in json_report_files:
        if os.path.isfile(file):
            try:
                with open(file, 'r') as f:
                    try:
                        report_data = json.load(f)

                        # Validate if the loaded report data is a list
                        if isinstance(report_data, list):
                            merged_results.extend(report_data)
                        else:
                            logging.warning(f"Report in {file} is not a list, skipping this file.")

                    except json.JSONDecodeError as e:
                        logging.error(f"Error decoding JSON in report {file}: {str(e)}")
                    except Exception as e:
                        logging.error(f"Unexpected error while processing {file}: {str(e)}")

            except OSError as e:
                logging.error(f"Error opening file {file}: {str(e)}")
            except Exception as e:
                logging.error(f"Error processing file {file}: {str(e)}")

        else:
            logging.warning(f"Report file {file} not found or is not a valid file.")

    # Validate that the merged data is still a list after all the merging
    if not isinstance(merged_results, list):
        raise ValueError("Merged results should be a list.")

    return merged_results


def get_feature_dirs(base_dir=FEATURES_DIR):
    """Recursively find all feature files in the specified directory and its subdirectories.
    Parameters: base_dir (str): The base directory to start the search for feature files.
    Returns:    list: A list of full paths to feature files found in the directory.
    """
    feature_files = []

    # Ensure the base directory exists before proceeding
    if not os.path.isdir(base_dir):
        logging.error(f"The specified directory does not exist: {base_dir}")
        return feature_files  # Return an empty list if the directory doesn't exist

    # Walk through the directory and its subdirectories
    try:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                # Check if the file ends with '.feature' extension
                if file.endswith(".feature"):
                    feature_files.append(os.path.join(root, file))

    except Exception as e:
        logging.error(f"Error while scanning directories in {base_dir}: {str(e)}")

    if not feature_files:
        logging.warning(f"No feature files found in directory: {base_dir}")

    return feature_files


def generate_report_statistics(merged_results):
    passed, failed, skipped, errors = 0, 0, 0, 0
    for result in merged_results:
        for scenario in result.get('elements', []):
            scenario_status = scenario.get('status', 'unknown')

            if scenario_status == 'passed':
                passed += 1
            elif scenario_status == 'failed':
                failed += 1
            elif scenario_status == 'skipped':
                skipped += 1
            elif scenario_status == 'undefined':  # Undefined steps
                errors += 1

    return passed, failed, skipped, errors


def run_behave_test(behave_args, test_run_id, feature_files):
    """Runs the Behave tests and handles the report generation, logging, and exceptions."""
    logger = logging.getLogger("TestAutomationLogger")
    json_report_file = None
    try:
        instance_data = load_instance_from_file()
        if instance_data:
            test_run_id = instance_data["TEST_EXECUTION_RUN_ID"]
            TEST_EXECUTION_START_TIMESTAMP = instance_data["TEST_EXECUTION_START_TIMESTAMP"]
            ARTIFACTS_DIR_PATH = instance_data["ARTIFACTS_DIR_PATH"]
            ARTIFACTS_ZIP_NAME = instance_data["ARTIFACTS_ZIP_NAME"]
            ARTIFACTS_ZIP_PATH = instance_data["ARTIFACTS_ZIP_PATH"]
            ARTIFACTS_RUN_PATH = instance_data["ARTIFACTS_RUN_PATH"]
            ARTIFACTS_SUPPORTING_FILES_PATH = instance_data["ARTIFACTS_SUPPORTING_FILES_PATH"]
            LOG_FILE_NAME = instance_data["LOG_FILE_NAME"]
            TEST_ENVIRONMENT_NAME = instance_data["TEST_ENVIRONMENT_NAME"]
            HTML_REPORT_FILE = instance_data["HTML_REPORT_FILE"]
            LOG_FILE_PATH = instance_data["LOG_FILE_PATH"]
            logger.info(
                f"Loaded TestRunner details: {test_run_id}, {TEST_EXECUTION_START_TIMESTAMP}, {ARTIFACTS_DIR_PATH}, {LOG_FILE_NAME}, {TEST_ENVIRONMENT_NAME}, {HTML_REPORT_FILE}, {LOG_FILE_PATH}")
        else:
            logger.error("Failed to load TestRunner instance data.")
            raise Exception("Failed to load TestRunner instance data.")
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        json_report_file = os.path.join(REPORTS_DIR, f'behave_report_{timestamp}.json')

        # Initialize the report file if it doesn't exist
        if not os.path.exists(json_report_file):
            logger.info(f"Creating new JSON report file: {json_report_file}")
            with open(json_report_file, 'w') as f:
                f.write('[]')

        # Set Environment variable for Behave report file
        os.environ["JSON_REPORT_FILE"] = json_report_file
        full_args = behave_args + feature_files + [f"--format={BEHAVE_FORMAT}", f"--outfile={json_report_file}"]
        logger.info(f"Running Behave with arguments: {' '.join(full_args)}")
        if not BEHAVE_SHOW_SKIPPED_TESTS_IN_REPORTS:
            full_args.append("--no-skipped")
        logger.info(f"Final Behave arguments: {' '.join(full_args)}")
        logger.info(f"Starting Behave test run with Run ID: {test_run_id}")
        result = behave_main(full_args)
        if result != 0:
            logger.error(f"Behave tests failed with exit code: {result}")
        else:
            logger.info(f"Behave tests completed successfully with return code {result}.")
        return json_report_file, result
    except Exception as e:
        logger.exception(f"Exception during Behave test execution: {str(e)}")
        return json_report_file, 1


def run_behave_tests(parallel_run=PARALLEL_RUN, max_parallel_jobs=MAX_PARALLEL_JOBS, test_tags=DEFAULT_TAGS):
    logger.info(
        f"Starting Behave tests with parallel_run={parallel_run}, max_parallel_jobs={max_parallel_jobs}, test_tags={test_tags}")
    start_time = datetime.now()
    logger.info(f"Test execution started at: {start_time}")
    try:
        feature_dirs = get_feature_dirs()
        behave_args, json_report_file, html_report_file, feature_dirs = construct_behave_args(test_tags=test_tags,
                                                                                              feature_files=feature_dirs)
        logger.info(f"Running Behave with arguments: {behave_args} and feature files: {feature_dirs}")
        json_report_files = []
        overall_return_code = 0
        total_features = len(feature_dirs)
        logger.info(f"Total feature files to execute: {total_features}")
        if parallel_run and total_features >= max_parallel_jobs:
            logger.info(f"Running tests in parallel with {max_parallel_jobs} jobs.")
            feature_dirs_split = [feature_dirs[i::max_parallel_jobs] for i in range(max_parallel_jobs)]
            # Run in parallel using multiprocessing Pool
            with Pool(max_parallel_jobs) as pool:
                results = pool.starmap(run_behave_test, [(behave_args, idx, feature_files) for idx, feature_files in
                                                         enumerate(feature_dirs_split)])
            for report_file, return_code in results:
                json_report_files.append(report_file)
                if return_code != 0:
                    overall_return_code = return_code

        else:
            logger.info("Running tests sequentially (max_parallel_jobs =1 or not enough features for parallel)...")
            report_file, return_code = run_behave_test(behave_args, 0, feature_dirs)
            json_report_files.append(report_file)
            if return_code != 0:
                overall_return_code = return_code
        merged_results = merge_json_reports(json_report_files)
        if merged_results:
            passed, failed, skipped, errors = generate_report_statistics(merged_results)
            logger.info(f"Test Summary: Passed: {passed}, Failed: {failed}, Skipped: {skipped}, Errors: {errors}")
            report_timestamp = start_time.strftime('%Y-%m-%d_%H-%M-%S')
            write_merged_json_report(merged_results, report_timestamp)
            render_html_report(merged_results, start_time.strftime('%Y-%m-%d %H:%M:%S'),
                               datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end_time = datetime.now()
        logger.info(f"Test execution ended at: {end_time}")
        logger.info(f"Total execution time: {end_time - start_time}")
        return overall_return_code
    except Exception as e:
        logger.error(f"Test Execution Failed: {str(e)}")
        logger.error(f"Traceback details:\n{traceback.format_exc()}")
        raise


def extract_report_details(merged_results):
    """Extracts detailed information from merged test results for reporting.
    Args:
        merged_results (list): Merged list of test results from multiple JSON reports."""
    features = []
    tags = set()
    passed_features = failed_features = skipped_features = error_features = 0
    passed_scenarios = failed_scenarios = skipped_scenarios = error_scenarios = 0
    for feature in merged_results:
        feature_data = {
            'name': feature['name'],
            'status': feature['status'],
            'location': feature['location'],
            'tags': feature['tags'],
            'scenarios': []
        }
        if feature['status'] == 'passed':
            passed_features += 1
        elif feature['status'] == 'failed':
            failed_features += 1
        elif feature['status'] == 'skipped':
            skipped_features += 1
        else:
            error_features += 1

        for scenario in feature['elements']:
            scenario_data = {
                'name': scenario['name'],
                'status': scenario['status'],
                'start_time': scenario['start_time'],
                'end_time': scenario['end_time'],
                'scenario_duration': calculate_duration(scenario),
                'scenario_tags': scenario['tags'],
                'steps': []
            }

            # Add Scenario status to count
            if scenario['status'] == 'passed':
                passed_scenarios += 1
            elif scenario['status'] == 'failed':
                failed_scenarios += 1
            elif scenario['status'] == 'skipped':
                skipped_scenarios += 1
            else:
                error_scenarios += 1

            for step in scenario['steps']:
                step_data = {
                    'name': step['name'],
                    'keyword': step['step_type'].upper(),
                    'result': step.get('result', 'N/A'),
                    'test_data': step.get('Test_data', 'N/A'),
                    'test_output_data': step.get('Test_Output_data', 'N/A'),
                    'screenshot': step.get('Screenshot_data', None),
                    'table': step.get('table', 'N/A'),
                    'failure_reason': ' '.join(step.get('result', {}).get('error_message', [])) or 'N/A',
                }
                scenario_data['steps'].append(step_data)
                # Collect all unique tags
            tags.update(scenario['tags'])
            feature_data['scenarios'].append(scenario_data)
        features.append(feature_data)
    return {
        'features': features,
        'tags': list(tags),
        'passed_features': passed_features,
        'failed_features': failed_features,
        'skipped_features': skipped_features,
        'error_features': error_features,
        'passed_scenarios': passed_scenarios,
        'failed_scenarios': failed_scenarios,
        'skipped_scenarios': skipped_scenarios,
        'error_scenarios': error_scenarios,
        'feature_count': len(features),
        'scenario_count': passed_scenarios + failed_scenarios + skipped_scenarios + error_scenarios
    }


def calculate_duration(scenario):
    """Calculates the duration of a scenario based on its start and end times.
    Args:
        scenario (dict): A dictionary representing a scenario with 'start_time' and 'end_time' keys.
    Returns:
        float: The duration of the scenario in seconds. Returns 0 if times are not available or invalid.
    """
    try:
        start_time = parse_time(scenario.get('start_time'))
        end_time = parse_time(scenario.get('end_time'))
        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
            return f"{duration:.2f} seconds"
        else:
            return "N/A"
    except Exception as e:
        logger.error(f"Error calculating duration for scenario '{scenario.get('name', 'N/A')}': {str(e)}")
        return "N/A"


def parse_time(time_str):
    """Parses a time string into a datetime object.
    Args:
        time_str (str): A string representing the time in ISO format.
    Returns:
        datetime or None: A datetime object if parsing is successful, otherwise None.
    """
    formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def render_html_report(merged_results, start_time, end_time):
    """Renders an HTML report using Jinja2 templating.
    Args:
        merged_results (list): Merged list of test results from multiple JSON reports.
        start_time (str): The start time of the test execution.
        end_time (str): The end time of the test execution.
    """
    try:
        report_details = extract_report_details(merged_results)
        start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        duration = end_time_obj - start_time_obj

        # setup Jinja2 environment
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
        template = env.get_template('report_template_v2.html')

        # Render the template with data
        report_html = template.render(
            project_name=PROJECT_NAME,
            report_generated_date=datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'),
            test_execution_start_date=start_time,
            test_execution_end_date=end_time,
            test_execution_duration=str(duration),
            test_environment=os.getenv("Test_Environment", "dev"),
            **report_details
        )

        file_name = os.path.basename(HTML_REPORT_FILE)
        with zipfile.ZipFile(ARTIFACTS_ZIP_PATH, 'a') as zipf:
            zipf.writestr(file_name, report_html.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error rendering HTML report: {str(e)}")
        raise


def write_merged_json_report(merged_results, timestamp):
    """Writes the merged JSON report to a file and adds it to the artifacts ZIP.
    Args:
        merged_results (list): Merged list of test results from multiple JSON reports.
        timestamp (str): Timestamp string to include in the report filename.
    """
    try:
        merged_report_file = os.path.join(REPORTS_DIR, f'Consolidated_Test_report_{timestamp}.json')
        with open(merged_report_file, 'w') as f:
            json.dump(merged_results, f, indent=4)
        logger.info(f"Merged JSON report written to: {merged_report_file}")
    except Exception as e:
        logger.error(f"Error writing merged JSON report: {str(e)}")
        raise


if __name__ == '__main__':
    allowed_environments = ["dev", "qa", "int"]
    parser = argparse.ArgumentParser(description="Run Behave tests with custom configurations.")
    parser.add_argument('--env', type=str, choices=allowed_environments, default='dev',
                        help='Environment to run tests against (default: dev)')
    parser.add_argument('--tags', type=str, nargs='+', default=DEFAULT_TAGS, help=f'List of tags to filter tests (default: {constants.DEFAULT_TAGS})')
    parser.add_argument('--no-parallel', default='--no-parallel', action = 'store_true', help='Disable parallel execution of tests')

    args = parser.parse_args()
    if args.no_parallel:
        PARALLEL_RUN = False
    if args.tags:
        tags = args.tags
    if args.env:
        os.environ["ENVIRONMENT"] = args.env
    else:
        os.environ["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "dev")

    config = TestRunnerConfig(env=os.environ["ENVIRONMENT"]).get_config()
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get('PYTHONPATH', '')

    Zipfile = create_artifacts_zip()
    overall_return_code = run_behave_tests(parallel_run=PARALLEL_RUN, test_tags=DEFAULT_TAGS)

    if overall_return_code == 0:
        logger.info("All tests passed successfully with Exit Code 0.")
        sys.exit(0)
    else:
        logger.error(f"Some tests failed with Exit Code {overall_return_code}.")
        sys.exit(overall_return_code)
