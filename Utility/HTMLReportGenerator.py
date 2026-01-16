import json
import os
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from constants import TEMPLATES_DIR

# Configure the Jinja2 environment and load templates
templates_folder = TEMPLATES_DIR
template_loader = FileSystemLoader(searchpath=templates_folder)
template_env = Environment(loader=template_loader, autoescape=True)


def handle_none_values(value):
    """Handles None and empty data gracefully."""
    if value is None:
        return 'N/A'
    elif isinstance(value, (dict, list)) and len(value) == 0:
        return 'No Data Available'
    return value


def handle_nested_data(data):
    """Recursively handles nested dictionaries or lists."""
    if isinstance(data, dict):
        return {key: handle_nested_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [handle_nested_data(item) for item in data]
    else:
        return data


def format_datetime(data, date_format="%Y-%m-%d %H:%M:%S"):
    """Formats datetime values."""
    if isinstance(data, datetime):
        return data.strftime(date_format)
    return data


def generate_html_report(data, metadata=None, automation_run_id=None, output_directory="reports", date_format="%Y-%m-%d %H:%M:%S"):
    """Generates an HTML report from the given data."""
    if not automation_run_id:
        automation_run_id = str(uuid.uuid4())  # Unique Automation Run ID

    # Handle nested structures and None values
    data = handle_nested_data(data)
    data = handle_none_values(data)
    data = format_datetime(data, date_format)

    # Report Metadata
    report_generated_date = datetime.now().strftime(date_format)

    # Load the HTML template
    template = template_env.get_template('SubModuleReport_template.html')

    # Render HTML
    html_output = template.render(
        data=data,
        metadata=metadata,  # Pass metadata to the template
        report_generated_date=report_generated_date,
        automation_run_id=automation_run_id
    )

    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Set the report filename and path
    report_filename = f"html_report_{automation_run_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    report_path = os.path.join(output_directory, report_filename)

    # Save the HTML report to file
    with open(report_path, 'w') as file:
        file.write(html_output)

    return report_path


def load_json_from_file(file_path):
    """Loads JSON data from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def json_to_html(json_data, output_directory="reports"):
    data = json.loads(json_data)
    return generate_html_report(data, output_directory=output_directory)


# Test data
test_data = {'RFM-EXCH-SENDER-ID': [{'json_key': 'data.consumers.medicaidOrganizationId', 'extracted_value_json': 'LAMEDICAID', 'extracted_value_memb16': 'LAMEDICAID', 'expected_value': 'LAMEDICAID', 'copybook_name': 'RFM-EXCH-SENDER-ID', 'start_pos': 9158, 'length': 20, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-EXCH-ISSUER-ID': [{'json_key': 'data.consumers.medicaidOrganizationId', 'extracted_value_json': 'LAMEDICAID', 'extracted_value_memb16': 'LAMEDICAID', 'expected_value': 'LAMEDICAID', 'copybook_name': 'RFM-EXCH-ISSUER-ID', 'start_pos': 9178, 'length': 20, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-TRANS-DT': [{'json_key': 'data.enrollmentApplicationSubmission.informationEffectiveTimestamp', 'extracted_value_json': '2024-07-26T03:13:27Z', 'extracted_value_memb16': '2024-07-26', 'expected_value': '2024-07-26', 'copybook_name': 'RFM-TRANS-DT', 'start_pos': 42, 'length': 10, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-SIGN-DT': [{'json_key': 'data.enrollmentApplicationSubmission.informationEffectiveTimestamp', 'extracted_value_json': '2024-07-26T03:13:27Z', 'extracted_value_memb16': '2024-07-26', 'expected_value': '2024-07-26', 'copybook_name': 'RFM-SIGN-DT', 'start_pos': 1028, 'length': 10, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-MARKET-RECEIPT-DT': [{'json_key': 'data.enrollmentApplicationSubmission.informationEffectiveTimestamp', 'extracted_value_json': '2024-07-26T03:13:27Z', 'extracted_value_memb16': '2024-07-26', 'expected_value': '2024-07-26', 'copybook_name': 'RFM-MARKET-RECEIPT-DT', 'start_pos': 1018, 'length': 10, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-TRANS-TIME': [{'json_key': 'data.enrollmentApplicationSubmission.informationEffectiveTimestamp', 'extracted_value_json': '2024-07-26T03:13:27Z', 'extracted_value_memb16': '03.13.29', 'expected_value': '03.13.27', 'copybook_name': 'RFM-TRANS-TIME', 'start_pos': 52, 'length': 8, 'result': 'Fail', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-TRANS-TYPE': [{'json_key': 'data.transactionMetadata.maintenanceTypeCode', 'extracted_value_json': '021', 'extracted_value_memb16': 'A', 'expected_value': 'A', 'copybook_name': 'RFM-TRANS-TYPE', 'start_pos': 41, 'length': 1, 'result': 'Pass', 'mapping_condition': {'condition': 'data.transactionMetadata.maintenanceTypeCode', 'when': [{'when': "data.transactionMetadata.maintenanceTypeCode = '4'", 'then': 'F'}, {'when': "data.transactionMetadata.maintenanceTypeCode = '30'", 'then': 'F'}, {'when': "data.transactionMetadata.maintenanceTypeCode = '001'", 'then': 'C'}, {'when': "data.transactionMetadata.maintenanceTypeCode = '025'", 'then': 'R'}, {'when': "data.transactionMetadata.maintenanceTypeCode = '021'", 'then': 'A'}, {'when': "data.transactionMetadata.maintenanceTypeCode = '024'", 'then': 'T'}], 'else': ' '}, 'error': 'N/A'}], 'RFM-MAINT-REAS-CD': [{'json_key': 'data.transactionMetadata.maintenanceReasonCode', 'extracted_value_json': '28', 'extracted_value_memb16': '28', 'expected_value': '28', 'copybook_name': 'RFM-MAINT-REAS-CD', 'start_pos': 60, 'length': 2, 'result': 'Pass', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-EMPL-STAT-CD': [{'json_key': 'data.consumers.employmentStatus', 'extracted_value_json': 'FT', 'extracted_value_memb16': 'FT', 'expected_value': 'FT', 'copybook_name': 'RFM-EMPL-STAT-CD', 'start_pos': 1230, 'length': 4, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.employmentStatus', 'when': [{'when': "data.consumers.employmentStatus = 'FT'", 'then': 'FT'}, {'when': "data.consumers.employmentStatus = 'TE'", 'then': 'TE'}], 'else': '    '}, 'error': 'N/A'}], 'RFM-MBR-DISABILITY-IND': [{'json_key': 'data.consumers.conditions.hasDisability', 'extracted_value_json': False, 'extracted_value_memb16': '', 'expected_value': 'N', 'copybook_name': 'RFM-MBR-DISABILITY-IND', 'start_pos': 870, 'length': 1, 'result': 'Fail', 'mapping_condition': {'condition': 'data.consumers.conditions.hasDisability', 'when': [{'when': 'data.consumers.conditions.hasDisability=True', 'then': 'Y'}, {'when': 'data.consumers.conditions.hasDisability=False', 'then': 'N'}], 'else': ' '}, 'error': 'N/A'}], 'RFM-LA-HCAP-IND': [{'json_key': 'data.consumers.conditions.hasDisability', 'extracted_value_json': False, 'extracted_value_memb16': 'N', 'expected_value': 'N', 'copybook_name': 'RFM-LA-HCAP-IND', 'start_pos': 7868, 'length': 1, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.conditions.hasDisability', 'when': [{'when': 'data.consumers.conditions.hasDisability=True', 'then': 'Y'}, {'when': 'data.consumers.conditions.hasDisability=False', 'then': 'N'}], 'else': ' '}, 'error': 'N/A'}], 'RFM-MBR-DECEASE-DT': [{'json_key': 'data.consumers.deceasedDate', 'extracted_value_json': None, 'extracted_value_memb16': '', 'expected_value': 'None', 'copybook_name': 'RFM-MBR-DECEASE-DT', 'start_pos': 340, 'length': 10, 'result': 'Fail', 'mapping_condition': None, 'error': 'N/A'}], 'RFM-MBR-SSN': [{'json_key': 'data.consumers.officialIdentifiers.identifierCode', 'extracted_value_json': '661452309', 'extracted_value_memb16': '661452309', 'expected_value': '661452309', 'copybook_name': 'RFM-MBR-SSN', 'start_pos': 313, 'length': 9, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.officialIdentifiers.identifierCode', 'when': [{'when': "data.consumers.officialIdentifiers.identifierCode = 'SS'", 'then': 'data.consumers.officialIdentifiers.identifierValue', 'value_key': 'identifierValue'}], 'else': '         '}, 'error': 'N/A'}], 'RFM-MCAID-ID': [{'json_key': 'data.consumers.officialIdentifiers.identifierCode', 'extracted_value_json': '2465672057540', 'extracted_value_memb16': '2465672057540', 'expected_value': '2465672057540', 'copybook_name': 'RFM-MCAID-ID', 'start_pos': 1821, 'length': 20, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.officialIdentifiers.identifierCode', 'when': [{'when': "data.consumers.officialIdentifiers.identifierCode = 'MA' AND data.consumers.officialIdentifiers.identifierIssuingAuthority = 'Louisiana Medicaid'", 'then': 'data.consumers.officialIdentifiers.identifierValue', 'value_key': 'identifierValue'}], 'else': '                    '}, 'error': 'N/A'}], 'RFM-SUBSCR-ID': [{'json_key': 'data.consumers.officialIdentifiers.identifierCode', 'extracted_value_json': '2465672057540', 'extracted_value_memb16': '2465672057540', 'expected_value': '2465672057540', 'copybook_name': 'RFM-SUBSCR-ID', 'start_pos': 72, 'length': 36, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.officialIdentifiers.identifierCode', 'when': [{'when': "data.consumers.officialIdentifiers.identifierCode = 'MA'", 'then': 'data.consumers.officialIdentifiers.identifierValue'}], 'else': '                                    '}, 'error': 'N/A'}], 'RFM-MBR-ID': [{'json_key': 'data.consumers.officialIdentifiers.identifierCode', 'extracted_value_json': '2465672057540', 'extracted_value_memb16': '2465672057540', 'expected_value': '2465672057540', 'copybook_name': 'RFM-MBR-ID', 'start_pos': 117, 'length': 36, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.officialIdentifiers.identifierCode', 'when': [{'when': "data.consumers.officialIdentifiers.identifierCode = 'MA'", 'then': 'data.consumers.officialIdentifiers.identifierValue'}], 'else': '                                    '}, 'error': 'N/A'}], 'RFM-MCARE-ID': [{'json_key': 'data.consumers.officialIdentifiers.identifierCode', 'extracted_value_json': '', 'extracted_value_memb16': '', 'expected_value': '', 'copybook_name': 'RFM-MCARE-ID', 'start_pos': 1971, 'length': 12, 'result': 'Pass', 'mapping_condition': {'condition': 'data.consumers.officialIdentifiers.identifierCode AND data.consumers.officialIdentifiers.identifierIssuingAuthority', 'when': [{'when': "data.consumers.officialIdentifiers.identifierCode = 'MC' AND data.consumers.officialIdentifiers.identifierIssuingAuthority = 'CMS'", 'then': 'data.consumers.officialIdentifiers.identifierValue'}], 'else': '            '}, 'error': 'N/A'}]}

test_data1 = json.dumps(test_data)

meta_data = {'file':'res.json', 'path':'c:'}

# Generate the HTML report using the test data
report_path = generate_html_report(test_data, metadata = meta_data, output_directory='generated_reports')
# report_path = json_to_html(test_data1, output_directory='generated_reports')

# Print the report path to confirm the location of the generated report
print(f"HTML report generated at: {report_path}")
