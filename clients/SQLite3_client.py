import sqlite3
import logging
import os
from contextlib import contextmanager
from runner import logger


class SQLiteClient:
    def __init__(self, db_path):
        """
        Initialize the SQLite client to interact with the database.

        :param db_path: The full path of the SQLite database (folder + database name).
        """
        self.db_path = db_path
        self.db_folder, self.db_name = os.path.split(db_path)  # Split path into folder and file name

        # Ensure the folder exists
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
            logger.info(f"Created folder: {self.db_folder}")

        # Check if the database file exists
        if not os.path.exists(self.db_path):
            logger.info(f"Database {self.db_name} does not exist. It will be created now.")
        else:
            logger.info(f"Database {self.db_name} already exists.")

        # Establish connection to SQLite database (it creates the file if it doesn't exist)
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    @contextmanager
    def _get_connection(self):
        """Context manager for managing database connections."""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        try:
            yield connection, cursor
        finally:
            cursor.close()
            connection.close()

    def create_table(self, table_name, columns):
        """
        Dynamically create a table with the specified columns.

        :param table_name: The name of the table to be created.
        :param columns: A dictionary where keys are column names and values are column types.
        """
        column_defs = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        self._execute_query(query)

    def insert(self, table_name, data):
        """
        Insert a record into the specified table.

        :param table_name: The name of the table to insert into.
        :param data: A dictionary where keys are column names and values are the data to be inserted.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self._execute_query(query, tuple(data.values()))

    def update(self, table_name, data, condition):
        """
        Update records in the specified table based on a condition.

        :param table_name: The name of the table to update.
        :param data: A dictionary where keys are column names and values are the data to be updated.
        :param condition: A string condition to identify records to update (e.g., "id = 1").
        """
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self._execute_query(query, tuple(data.values()))

    def delete(self, table_name, condition):
        """
        Delete records from the specified table based on a condition.

        :param table_name: The name of the table to delete from.
        :param condition: A string condition to identify records to delete (e.g., "id = 1").
        """
        query = f"DELETE FROM {table_name} WHERE {condition}"
        self._execute_query(query)

    def select(self, table_name, columns="*", condition=None):
        """
        Select records from the specified table with an optional condition.

        :param table_name: The name of the table to select from.
        :param columns: The columns to select (default: "*").
        :param condition: An optional condition (e.g., "id = 1").
        :return: A list of tuples containing the selected rows.
        """
        query = f"SELECT {columns} FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        return self._fetch_all(query)

    def select_one(self, table_name, columns="*", condition=None):
        """
        Select one record from the specified table with an optional condition.

        :param table_name: The name of the table to select from.
        :param columns: The columns to select (default: "*").
        :param condition: An optional condition (e.g., "id = 1").
        :return: A tuple representing the selected record, or None if not found.
        """
        result = self.select(table_name, columns, condition)
        return result[0] if result else None

    def count(self, table_name, condition=None):
        """
        Count the number of records in a table with an optional condition.

        :param table_name: The name of the table to count records in.
        :param condition: An optional condition (e.g., "status = 'active'").
        :return: The count of records.
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        result = self._fetch_one(query)
        return result[0] if result else 0

    def begin_transaction(self):
        """
        Begin a new transaction.
        """
        with self._get_connection() as (connection, cursor):
            connection.isolation_level = None  # Start a transaction
            cursor.execute("BEGIN")

    def commit_transaction(self):
        """
        Commit the current transaction.
        """
        with self._get_connection() as (connection, cursor):
            connection.commit()
            logger.info("Transaction committed.")

    def rollback_transaction(self):
        """
        Rollback the current transaction.
        """
        with self._get_connection() as (connection, cursor):
            connection.rollback()
            logger.info("Transaction rolled back.")

    def _execute_query(self, query, params=None):
        """
        Execute a query (INSERT, UPDATE, DELETE) with optional parameters.

        :param query: The SQL query to execute.
        :param params: The parameters to bind to the query (default: None).
        """
        try:
            with self._get_connection() as (connection, cursor):
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                connection.commit()
                logger.info(f"Executed query: {query}")
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            with self._get_connection() as (connection, cursor):
                connection.rollback()

    def _fetch_all(self, query):
        """
        Fetch all results for a SELECT query.

        :param query: The SQL SELECT query to execute.
        :return: A list of tuples containing the results.
        """
        try:
            with self._get_connection() as (connection, cursor):
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching data: {e}")
            return []

    def _fetch_one(self, query):
        """
        Fetch a single result for a SELECT query.

        :param query: The SQL SELECT query to execute.
        :return: A tuple containing the result, or None if no result.
        """
        try:
            with self._get_connection() as (connection, cursor):
                cursor.execute(query)
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error fetching data: {e}")
            return None

    def view_columns(self, table_name):
        """
        View columns of a table by querying the sqlite_master.

        :param table_name: The name of the table whose columns are to be viewed.
        :return: List of columns in the table.
        """
        query = f"PRAGMA table_info({table_name});"
        result = self._fetch_all(query)
        return result

    def run_raw_query(self, query, params=None):
        """
        Run a raw SQL query (SELECT, INSERT, UPDATE, DELETE) directly after basic syntax validation.

        :param query: The raw SQL query to execute.
        :param params: The parameters to bind to the query (default: None).
        :return: A list of rows for SELECT queries, or None for other queries.
        """
        # Basic SQL syntax checks
        if not self._is_valid_sql(query):
            logger.error(f"Invalid SQL syntax detected: {query}")
            return None

        try:
            with self._get_connection() as (connection, cursor):
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                connection.commit()
                logger.info(f"Executed raw query: {query}")
                if query.lower().startswith("select"):
                    return cursor.fetchall()  # Return results for SELECT queries
                return None  # No results for non-SELECT queries
        except sqlite3.Error as e:
            logger.error(f"Error executing raw query: {e}")
            return None

    def _is_valid_sql(self, query):
        """
        Perform basic validation on the SQL query to check for common syntax issues.

        :param query: The raw SQL query to check.
        :return: True if the query appears valid, False otherwise.
        """
        # Strip extra spaces and lowercase the query for easier comparison
        query = query.strip().lower()

        # Check for common SQL keywords to see if query starts correctly
        if query.startswith(("select", "insert", "update", "delete", "create", "drop", "alter")):
            # Check if SELECT queries contain a FROM clause
            if query.startswith("select") and "from" not in query:
                logger.error("SELECT query must contain a 'FROM' clause.")
                return False
            # Check if INSERT queries contain VALUES
            elif query.startswith("insert") and "values" not in query:
                logger.error("INSERT query must contain a 'VALUES' clause.")
                return False
            # Check if UPDATE queries contain a SET clause
            elif query.startswith("update") and "set" not in query:
                logger.error("UPDATE query must contain a 'SET' clause.")
                return False
            # Check if DELETE queries contain a WHERE clause (optional but recommended)
            elif query.startswith("delete") and "where" not in query:
                logger.warning("DELETE query doesn't contain a 'WHERE' clause, all rows may be deleted.")
            # If it's a CREATE or ALTER query, additional checks can be added for specific syntax as needed
            return True
        else:
            logger.error(f"Unsupported SQL operation in query: {query}")
            return False

    def close(self):
        """
        Close the SQLite client and release resources.
        """
        self.connection.close()
        logger.info(f"SQLite client for {self.db_name} closed.")

    @staticmethod
    def main():
        """
        Main method for user understanding purpose.
        This method demonstrates how to create a database, create a table, and insert data.
        """
        db_path = "../FrameworkTestDataDatabase/BehaveTestAutomationFramework.db"

        # Initialize SQLiteClient instance
        client = SQLiteClient(db_path)

        # Create a table
        table_name = "test_table"
        columns = {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "age": "INTEGER"
        }
        client.create_table(table_name, columns)

        # Insert a record into the table
        data = {
            "name": "John Doe",
            "age": 30
        }
        client.insert(table_name, data)

        # Query the table to verify the insert
        result = client.select(table_name)
        logger.info(f"Data in {table_name}: {result}")

        # Run a raw query (SELECT example)
        raw_query_result = client.run_raw_query("SELECT * FROM test_table")
        logger.info(f"Raw query result: {raw_query_result}")

        # Close the client
        client.close()


# Example usage:
if __name__ == "__main__":
    SQLiteClient.main()
