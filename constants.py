import os

# Adjust BASE_DIR to point to the root of the project (PythonAutomationFramework)
BASE_DIR = os.path.dirname((__file__)) # Three levels up
PROJECT_NAME = "SBC"
# Directories
ARTIFACTS_DIR = os.path.join(BASE_DIR, "reports")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")  # Directory to store reports
FEATURES_DIR = os.path.join(BASE_DIR, "features")  # Directory containing feature files
STEPS_DIR = os.path.join(FEATURES_DIR, "steps")  # 'steps' folder inside 'features'
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")  # Directory for report templates

# Input/Output Folders for managing files used in the tests
INPUT_DIR = os.path.join(BASE_DIR, "input")  # Directory for input files used in tests (e.g., test data, config files)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")  # Directory for output files generated from tests (e.g., results, processed files)

# Logs Folder
LOGS_DIR = os.path.join(BASE_DIR, "logs")  # Directory for storing log files

# Default Environment (Can be overridden in Framework configuration)
DEFAULT_ENV = "dev"

# Paths to Configuration Files
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
FRAMEWORK_CONFIG_FILE = os.path.join(CONFIG_DIR, "framework_config.yaml")  # General framework configurations (parallel run, logging, etc.)
DEV_CONFIG_FILE = os.path.join(CONFIG_DIR, "dev_config.yaml")  # Configuration file for the dev environment
QA_CONFIG_FILE = os.path.join(CONFIG_DIR, "qa_config.yaml")  # Configuration file for the QA environment
INT_CONFIG_FILE = os.path.join(CONFIG_DIR, "int_config.yaml")  # Configuration file for the INT environment
BROWSER_SETTINGS_FILE = os.path.join(CONFIG_DIR, "browser_settings.yaml")

cwd = os.path.dirname(os.path.abspath(__file__))

# Remove the drive letter and the colon, and then replace backslashes with dots
if cwd[1] == ':':  # Check if the path starts with a drive letter
    path = cwd[2:].replace("\\", ".")  # Remove C: and replace backslashes with dots
else:
    path = cwd.replace("\\", ".")

# Default Behave settings: format should use the path as a module
# BEHAVE_FORMAT = f"{path}.CustomJsonReportFormatter.custom_json_formatter:CustomJSONFormatter"
BEHAVE_FORMAT = "CustomJsonReportFormatter.custom_json_formatter:CustomJSONFormatter"
BEHAVE_OUTPUT_DIR = os.path.join(REPORTS_DIR, "behave_reports")  # Directory for Behave JSON output
BEHAVE_SHOW_SKIPPED_TESTS_IN_REPORTS = False

# Logging Configuration
LOGGING_LEVEL = "INFO"  # Default logging level for the framework (can be overridden in framework_config.yaml)
LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Log format for the framework
LOGGING_FILE = os.path.join(LOGS_DIR, "test_execution.log")  # Path to the log file for framework execution

# Test Tags (e.g., smoke, regression)
DEFAULT_TAGS = ["playwrighttests"]  # Default tags to filter tests by (can be overridden in framework_config.yaml)

# Timeout for tests (seconds)
DEFAULT_TIMEOUT = 60  # Default timeout for each test (can be overridden in framework_config.yaml)

#Scenario Retry
SCENARIO_MAX_RETRIES = 1
SCENARIO_RETRY_DELAY = 2

#Parallel Execution at Feature File level
PARALLEL_RUN=False
MAX_PARALLEL_JOBS=2

Framework_Database_Folder = os.path.join(BASE_DIR, "FrameworkTestDataDatabase")
Framework_Database_Name = "BehaveTestAutomationFramework.db"
Framework_Database_Path = os.path.join(Framework_Database_Folder, Framework_Database_Name)