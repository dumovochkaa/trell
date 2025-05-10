import MySQLdb

def get_connection():
    return MySQLdb.connect(
        host="MySQL-8.0",
        user="root",
        passwd="",  # замените на ваш пароль
        db="Trello",
        charset="utf8"
    )
