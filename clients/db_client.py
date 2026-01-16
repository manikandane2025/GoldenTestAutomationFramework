import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pymongo import MongoClient
from typing import List, Dict, Union, Optional, Any
import asyncio
from asyncio import Future
import requests

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class StrongDMClient:
    """
    A dedicated client for interacting with the StrongDM API for managing access to resources (databases, servers).
    """

    def __init__(self, api_url: str, api_key: str, retries: int = 3, retry_delay: int = 2):
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _handle_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None):
        url = f"{self.api_url}/{endpoint}"
        attempts = 0
        while attempts < self.retries:
            try:
                if method == "GET":
                    response = self.session.get(url, params=params)
                elif method == "POST":
                    response = self.session.post(url, json=data)
                elif method == "PUT":
                    response = self.session.put(url, json=data)
                elif method == "DELETE":
                    response = self.session.delete(url, json=data)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 401:  # Unauthorized
                    logger.error("Unauthorized request - Check API key or token.")
                    return None
                if response.status_code == 429:  # Rate limiting
                    retry_after = int(response.headers.get("Retry-After", self.retry_delay))
                    logger.warning(f"Rate limited, retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                if response.status_code >= 500:  # Server errors
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    time.sleep(self.retry_delay)
                    continue

                logger.error(f"Request failed with status code {response.status_code}: {response.text}")
                return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                attempts += 1
                time.sleep(self.retry_delay)

        return None

    def get_access(self, resource: str) -> Dict[str, Any]:
        logger.info(f"Checking access for resource: {resource}")
        return self._handle_request("GET", f"access/{resource}")

    def grant_access(self, resource: str, user: str) -> bool:
        logger.info(f"Granting access to resource: {resource} for user: {user}")
        data = {"user": user, "resource": resource}
        response = self._handle_request("POST", "access/grant", data=data)
        return response is not None

    def revoke_access(self, resource: str, user: str) -> bool:
        logger.info(f"Revoking access to resource: {resource} for user: {user}")
        data = {"user": user, "resource": resource}
        response = self._handle_request("POST", "access/revoke", data=data)
        return response is not None


class DBClient:
    """
    A base class for handling database connections and queries for both traditional and modern databases.
    """

    def __init__(self, strongdm_client: StrongDMClient):
        self.strongdm_client = strongdm_client

    def connect(self):
        """Establish a connection to the database. Must be implemented in child classes."""
        raise NotImplementedError("Connect method must be implemented by subclasses.")

    def execute_query(self, query: str, params: Union[Dict, None] = None):
        """Execute a query and return the result."""
        raise NotImplementedError("Execute query method must be implemented by subclasses.")

    def fetch_one(self, query: str, params: Union[Dict, None] = None):
        """Fetch a single record from the database."""
        raise NotImplementedError("Fetch one method must be implemented by subclasses.")

    def fetch_all(self, query: str, params: Union[Dict, None] = None):
        """Fetch multiple records from the database."""
        raise NotImplementedError("Fetch all method must be implemented by subclasses.")

    def close(self):
        """Close the database connection."""
        raise NotImplementedError("Close method must be implemented by subclasses.")

    def validate_single_record(self, record: Dict) -> bool:
        """Validates that the record is a single, valid dictionary."""
        if not isinstance(record, dict):
            logger.error("Invalid record format. Expected a dictionary.")
            return False
        return True

    def validate_multiple_records(self, records: List[Dict]) -> bool:
        """Validates that the records are a list of valid dictionaries."""
        if not isinstance(records, list):
            logger.error("Invalid format. Expected a list of records.")
            return False
        for record in records:
            if not isinstance(record, dict):
                logger.error("Invalid record format within list. Expected a dictionary.")
                return False
        return True

    def validate_query_time(self, start_time: float, max_time: float = 2) -> bool:
        """Validates that the query execution time is within the allowed time."""
        elapsed_time = time.time() - start_time
        if elapsed_time > max_time:
            logger.warning(f"Query took {elapsed_time:.2f}s, exceeding maximum allowed {max_time}s")
            return False
        return True


class SQLClient(DBClient):
    """
    A class to handle connections and queries for traditional SQL databases (e.g., MySQL, PostgreSQL).
    """

    def __init__(self, strongdm_client: StrongDMClient, db_url: str, max_retries: int = 3, retry_delay: int = 2):
        super().__init__(strongdm_client)
        self.db_url = db_url
        self.engine = None
        self.Session = None
        self.session = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def connect(self):
        """Establish connection to the SQL database after checking access."""
        if not self.strongdm_client.get_access(self.db_url):
            logger.error(f"Access to {self.db_url} not granted.")
            return False
        try:
            self.engine = create_engine(self.db_url, echo=True, pool_size=10, max_overflow=20)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            logger.info("Connected to SQL database.")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error connecting to SQL database: {e}")
            return False

    def execute_query(self, query: str, params: Union[Dict, None] = None):
        """Execute an arbitrary SQL query."""
        start_time = time.time()
        retries = 0
        while retries < self.max_retries:
            try:
                result = self.session.execute(text(query), params or {})
                self.session.commit()
                self.validate_query_time(start_time)
                return result
            except SQLAlchemyError as e:
                retries += 1
                logger.error(f"Error executing query: {e}. Retrying ({retries}/{self.max_retries})...")
                self.session.rollback()
                time.sleep(self.retry_delay)
        return None

    def fetch_one(self, query: str, params: Union[Dict, None] = None):
        """Fetch a single record from the SQL database."""
        try:
            result = self.session.execute(text(query), params or {}).fetchone()
            if result:
                return dict(result)
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def fetch_all(self, query: str, params: Union[Dict, None] = None):
        """Fetch multiple records from the SQL database."""
        try:
            result = self.session.execute(text(query), params or {}).fetchall()
            if result:
                return [dict(row) for row in result]
            return []
        except SQLAlchemyError as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()
            logger.info("SQL session closed.")
        if self.engine:
            self.engine.dispose()


class NoSQLClient(DBClient):
    """
    A class to handle connections and queries for modern NoSQL databases (e.g., MongoDB).
    """

    def __init__(self, strongdm_client: StrongDMClient, db_url: str, db_name: str, max_retries: int = 3, retry_delay: int = 2):
        super().__init__(strongdm_client)
        self.db_url = db_url
        self.db_name = db_name
        self.client = None
        self.db = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def connect(self):
        """Establish connection to the MongoDB database after checking access."""
        if not self.strongdm_client.get_access(self.db_url):
            logger.error(f"Access to {self.db_url} not granted.")
            return False
        retries = 0
        while retries < self.max_retries:
            try:
                self.client = MongoClient(self.db_url)
                self.db = self.client[self.db_name]
                logger.info(f"Connected to MongoDB database: {self.db_name}")
                return True
            except Exception as e:
                retries += 1
                logger.error(f"Error connecting to MongoDB database: {e}. Retrying ({retries}/{self.max_retries})...")
                time.sleep(self.retry_delay)
        return False

    def execute_query(self, collection_name: str, query: Dict, update_data: Dict = None, operation: str = "find"):
        """Execute a query operation on a MongoDB collection."""
        collection = self.db[collection_name]
        start_time = time.time()
        retries = 0
        while retries < self.max_retries:
            try:
                if operation == "find":
                    result = collection.find(query)
                elif operation == "insert":
                    result = collection.insert_one(query)
                elif operation == "update":
                    result = collection.update_one(query, {"$set": update_data})
                elif operation == "delete":
                    result = collection.delete_one(query)
                self.validate_query_time(start_time)
                return result
            except Exception as e:
                retries += 1
                logger.error(f"Error executing query: {e}. Retrying ({retries}/{self.max_retries})...")
                time.sleep(self.retry_delay)
        return None

    def fetch_one(self, collection_name: str, query: Dict):
        """Fetch a single document from MongoDB."""
        collection = self.db[collection_name]
        try:
            result = collection.find_one(query)
            if result:
                return result
            return None
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def fetch_all(self, collection_name: str, query: Dict):
        """Fetch all documents from MongoDB."""
        collection = self.db[collection_name]
        try:
            result = list(collection.find(query))
            return result
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")


# Example usage:

# Initialize StrongDM Client
strongdm_client = StrongDMClient(api_url="https://api.strongdm.com", api_key="your-strongdm-api-key")

# Create a SQL Client
sql_client = SQLClient(strongdm_client, "postgresql://username:password@localhost/testdb")
sql_client.connect()
single_record = sql_client.fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
print("Single record:", single_record)
sql_client.close()

# Create a MongoDB Client
async def async_mongo_operations():
    mongo_client = NoSQLClient(strongdm_client, "mongodb://localhost:27017", "testdb")
    await mongo_client.connect()  # Async connect (retries handled)
    single_doc = await mongo_client.fetch_async("users", {"id": 1})
    print("Async Single document:", single_doc)
    multiple_docs = await mongo_client.fetch_async("users", {"age": {"$gt": 20}})
    print("Async Multiple documents:", multiple_docs)
    mongo_client.close()

# Running async MongoDB operations
asyncio.run(async_mongo_operations())
