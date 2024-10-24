import sqlite3
import logger_config

def execute(query, values=None, type='getAll'):
    conn = None  # Initialize conn variable outside the try block
    try:
        logger_config.info("Getting Database Connection...")
        conn = sqlite3.connect('ContentData/entries.db')
        logger_config.info("Connection Success")
        cursor = conn.cursor()

        logger_config.info(f"Trying Query execution query:: {query} value:: {values} Success")

        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        logger_config.info(f"Query execution query:: {query} value:: {values} Success")

        if type == 'getAll':
            return cursor.fetchall()  # Return all results for 'get' type
        if type == 'get':
            return cursor.fetchone()  # Return all results for 'get' type

        return None
    except Exception as e:
        logger_config.error(f'Error in databasecon.execute:: {str(e)}')
    finally:
        if conn:  # Check if conn was successfully created
            conn.commit()
            conn.close()

# if __name__ == "__main__":
#     # Correctly format the execute call with proper type
#     results = execute("get", "SELECT audioPath FROM entries WHERE generatedVideoPath IS NULL OR generatedVideoPath = ''")
#     if results:
#         for row in results:
#             print(row)  # Print the results