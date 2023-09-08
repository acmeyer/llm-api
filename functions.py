import sqlite3

def get_database_schema():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    schema = ""
    for table_name in tables:
        table_name = table_name[0]
        schema += f"Table: {table_name}\n"
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for column in columns:
            schema += f"  Column: {column[1]} Type: {column[2]}\n"

    conn.close()
    return schema

def get_functions():
    return [{
        "name": "use_database",
        "description": "This function runs a SQL query against a SQLite database. Use this function to insert, read, update, or delete data from the database. This is the current schema of the database:\n\n" + get_database_schema(),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL query to run."
                }
            }
        },
    }, {
        "name": "run_code",
        "description": "This function runs arbitrary Python code. Use this function to do anything that you can do in Python.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to run."
                }
            }
        },
    }]


def use_database(query: str):
    try:
        print("Using database", query)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return results
    except Exception as e:
        return {
            "error": e.args[0]
        }


def run_code(code: str):
    try:
        print("Running code", code)
        return exec(code)
    except Exception as e:
        return {
            "error": e.args[0]
        }
    
