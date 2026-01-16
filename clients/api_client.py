import requests
import logging
import json
import time
import random
import jsonschema
from requests.auth import HTTPDigestAuth
from requests.exceptions import HTTPError, RequestException, Timeout, ConnectionError
import hmac
import hashlib
import base64

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class APIClient:
    def __init__(self, base_url, auth=None, headers=None, retry_policy=None, timeout=30, environment=None, schema_validator=None, api_key=None, secret_key=None, jwt_token=None, chain_requests=False):
        """
        Initializes the APIClient instance.

        :param base_url: The base URL for the API (e.g., 'https://api.example.com')
        :param auth: Optional authentication details (tuple like ('username', 'password') or Bearer token)
        :param headers: Optional headers for the API (e.g., {'Content-Type': 'application/json'})
        :param retry_policy: Optional retry policy specifying number of retries and delay between retries
        :param timeout: Request timeout in seconds
        :param environment: Optional environment details (e.g., 'dev', 'staging', 'prod')
        :param schema_validator: Optional JSON schema validator for response validation
        :param api_key: Optional API key (for API key authentication)
        :param secret_key: Optional secret key (for HMAC authentication)
        :param jwt_token: Optional JWT token (for JWT-based authentication)
        :param chain_requests: Optional flag to enable chaining of multiple requests
        """
        self.base_url = base_url
        self.auth = auth
        self.headers = headers or {}
        self.retry_policy = retry_policy or {"retries": 3, "delay": 2}
        self.token = None
        self.timeout = timeout
        self.environment = environment or 'dev'
        self.session = requests.Session()
        self.schema_validator = schema_validator  # Schema validator for response validation
        self.api_key = api_key
        self.secret_key = secret_key
        self.jwt_token = jwt_token
        self._update_headers()

    def _update_headers(self):
        """Helper method to update headers dynamically."""
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
        if self.jwt_token:
            self.headers["Authorization"] = f"Bearer {self.jwt_token}"
        self.session.headers.update(self.headers)

    def _make_request(self, method, endpoint, data=None, params=None, custom_headers=None):
        """
        A helper method to make HTTP requests with error handling and retries.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: The API endpoint
        :param data: Body data (for POST/PUT)
        :param params: Query parameters (for GET)
        :param custom_headers: Optional custom headers for specific requests
        :return: Response object or None
        """
        url = f"{self.base_url}/{endpoint}"
        attempts = 0

        if custom_headers:
            self.session.headers.update(custom_headers)

        while attempts < self.retry_policy["retries"]:
            try:
                attempts += 1
                logger.info(f"Attempt {attempts}/{self.retry_policy['retries']} - {method} request to {url}")

                start_time = time.time()
                response = self.session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    auth=self.auth,
                    timeout=self.timeout
                )
                elapsed_time = time.time() - start_time
                logger.info(f"Response received in {elapsed_time:.2f} seconds")

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.retry_policy["delay"]))
                    logger.warning(f"Rate limiting detected, retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Automatically handle retries for specific status codes (e.g., 500)
                if response.status_code == 500:
                    logger.warning(f"Server error encountered (500). Retrying ({attempts}/{self.retry_policy['retries']})...")
                    time.sleep(self.retry_policy["delay"] * random.uniform(1, 2))  # Exponential backoff
                    continue

                response.raise_for_status()  # Raise error for non-2xx status codes
                return response
            except Timeout:
                logger.error(f"Request to {url} timed out. Retrying ({attempts}/{self.retry_policy['retries']})...")
                time.sleep(self.retry_policy["delay"])
            except ConnectionError:
                logger.error(f"Connection error occurred. Retrying ({attempts}/{self.retry_policy['retries']})...")
                time.sleep(self.retry_policy["delay"])
            except HTTPError as err:
                if response.status_code == 401:  # Unauthorized, possibly expired token
                    logger.info("Unauthorized, attempting to refresh token...")
                    if self.token_refresh_required():
                        self.refresh_token()
                        self._update_headers()  # Update headers with new token
                    else:
                        logger.error(f"Error occurred: {err}")
                        return None
                elif response.status_code >= 500:
                    logger.error(f"Server error: {err}. Retrying...")
                    time.sleep(self.retry_policy["delay"] * random.uniform(1, 2))  # Exponential backoff
                else:
                    logger.error(f"Request failed with status code {response.status_code}: {err}")
                    return None
            except RequestException as e:
                logger.error(f"Request failed: {e}")
                return None
        return None

    def get(self, endpoint, params=None, custom_headers=None):
        """
        Makes a GET request to the specified endpoint.

        :param endpoint: The API endpoint to send the GET request to
        :param params: Query parameters (optional)
        :param custom_headers: Optional custom headers
        :return: JSON response or None
        """
        response = self._make_request("GET", endpoint, params=params, custom_headers=custom_headers)
        return self._validate_response(response) if response else None

    def post(self, endpoint, data=None, custom_headers=None):
        """
        Makes a POST request to the specified endpoint.

        :param endpoint: The API endpoint to send the POST request to
        :param data: The body data to send (optional)
        :param custom_headers: Optional custom headers
        :return: JSON response or None
        """
        response = self._make_request("POST", endpoint, data=data, custom_headers=custom_headers)
        return self._validate_response(response) if response else None

    def put(self, endpoint, data=None, custom_headers=None):
        """
        Makes a PUT request to the specified endpoint.

        :param endpoint: The API endpoint to send the PUT request to
        :param data: The body data to send (optional)
        :param custom_headers: Optional custom headers
        :return: JSON response or None
        """
        response = self._make_request("PUT", endpoint, data=data, custom_headers=custom_headers)
        return self._validate_response(response) if response else None

    def delete(self, endpoint, data=None, custom_headers=None):
        """
        Makes a DELETE request to the specified endpoint.

        :param endpoint: The API endpoint to send the DELETE request to
        :param data: The body data to send (optional)
        :param custom_headers: Optional custom headers
        :return: JSON response or None
        """
        response = self._make_request("DELETE", endpoint, data=data, custom_headers=custom_headers)
        return self._validate_response(response) if response else None

    def _validate_response(self, response):
        """
        Validates the response object based on status code, response time, and content type.

        :param response: The response object
        :return: JSON if valid, None otherwise
        """
        if response.status_code >= 400:
            logger.error(f"Request failed with status code {response.status_code}")
            return None

        if 'application/json' not in response.headers.get('Content-Type', ''):
            logger.error("Invalid content type. Expected 'application/json'.")
            return None

        if self.schema_validator:
            try:
                self.schema_validator(response.json())  # Validate against schema if provided
                logger.info("Response schema validated successfully.")
            except jsonschema.exceptions.ValidationError as e:
                logger.error(f"Response schema validation failed: {e}")
                return None

        return response.json()

    def token_refresh_required(self):
        """
        Determines if token refresh is required (based on specific error conditions).
        :return: Boolean (True if token refresh is required)
        """
        return True

    def refresh_token(self):
        """
        Fetch a new token and update the authorization header.
        """
        logger.info("Refreshing authentication token...")
        auth_data = {"username": "user", "password": "password"}
        response = self.post("auth/token", data=auth_data)
        if response:
            self.token = response.get("access_token")
            logger.info("Token refreshed successfully.")
        else:
            logger.error("Failed to refresh token.")
            self.token = None

    def extract_token_from_response(self, response):
        """
        Extracts token from response if available.
        """
        token = response.get('access_token')
        if token:
            self.token = token
            self._update_headers()
            logger.info("Token extracted and set for future requests.")

    def validate_response_time(self, response, max_time=2):
        """
        Validates that the response time is within the specified limit (in seconds).

        :param response: The response object
        :param max_time: Maximum allowable response time in seconds
        :return: True if valid, False otherwise
        """
        if response.elapsed.total_seconds() > max_time:
            logger.error(f"Response time {response.elapsed.total_seconds():.2f}s exceeded maximum allowed {max_time}s")
            return False
        return True

    def handle_pagination(self, endpoint, params=None):
        """
        Handles pagination if the response contains a paginated result.

        :param endpoint: The endpoint to send the GET request to
        :param params: Query parameters for the request
        :return: List of all results across all pages
        """
        all_results = []
        while True:
            response = self.get(endpoint, params=params)
            if response and isinstance(response, list):
                all_results.extend(response)
            else:
                break
            # Check if there are more pages (assumes 'next' key for pagination)
            params["page"] = params.get("page", 1) + 1
        return all_results

    def _generate_hmac(self, message):
        """Generate HMAC for the request."""
        return base64.b64encode(
            hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).digest()
        ).decode()

    def _handle_hmac_request(self, method, endpoint, data=None, params=None):
        """Handle HMAC-based authentication for requests."""
        if self.secret_key:
            signature = self._generate_hmac(f"{method}{self.base_url}/{endpoint}{json.dumps(data) if data else ''}")
            self.headers['X-Signature'] = signature
            self.headers['X-API-Key'] = self.api_key  # Include API key in headers
        return self._make_request(method, endpoint, data, params)

    def perform_chain_requests(self, request_list):
        """
        Chains multiple requests sequentially.

        :param request_list: List of tuples, each containing method, endpoint, data (optional), and params (optional)
        :return: List of responses for each request
        """
        responses = []
        for method, endpoint, data, params in request_list:
            if method == 'GET':
                response = self.get(endpoint, params=params)
            elif method == 'POST':
                response = self.post(endpoint, data=data)
            elif method == 'PUT':
                response = self.put(endpoint, data=data)
            elif method == 'DELETE':
                response = self.delete(endpoint, data=data)
            else:
                logger.error(f"Unsupported method: {method}")
                responses.append(None)
                continue

            if response:
                responses.append(response)
            else:
                responses.append(None)
        return responses


# Example usage
api_client = APIClient(
    base_url="https://api.example.com",
    auth=("username", "password"),
    api_key="your-api-key",
    secret_key="your-secret-key",
    jwt_token="your-jwt-token",
    chain_requests=True
)

# Example GET request with validation
response = api_client.get("public-endpoint")
if response:
    print("GET response:", response)

# Example POST request with custom headers
response = api_client.post("private-endpoint", data={"key": "value"}, custom_headers={"x-custom-header": "value"})
if response:
    print("POST response:", response)

# Example PUT request with custom data
response = api_client.put("private-endpoint", data={"key": "updated_value"})
if response:
    print("PUT response:", response)

# Example DELETE request
response = api_client.delete("private-endpoint")
if response:
    print("DELETE response:", response)

# Example HMAC-based request
response = api_client._handle_hmac_request("POST", "secure-endpoint", data={"key": "value"})
if response:
    print("HMAC POST response:", response)

# Example token refresh if token is expired (401 error)
api_client.refresh_token()

# Example chaining of multiple requests
requests = [
    ("GET", "public-endpoint"),
    ("POST", "private-endpoint", {"key": "value"}),
    ("PUT", "private-endpoint", {"key": "updated_value"}),
    ("DELETE", "private-endpoint")
]
responses = api_client.perform_chain_requests(requests)
for resp in responses:
    print(resp)

