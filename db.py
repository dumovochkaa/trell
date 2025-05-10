import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',  # replace with your MySQL username
                password='',  # replace with your MySQL password
                database='Trello'
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
                return self.connection
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return None

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection is closed")

    def execute_query(self, query, params=None, fetch=False):
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor:
                cursor.close()