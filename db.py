import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Ab271642",
        database="my_database",
        port=3307
    )
