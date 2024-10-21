from logger_config import setup_logging
import sqlite3

logging = setup_logging()

def execute(query, values=None, type='getAll'):
    conn = None  # Initialize conn variable outside the try block
    try:
        logging.info("Getting Database Connection...")
        conn = sqlite3.connect('ContentData/entries.db')
        logging.info("Connection Success")
        cursor = conn.cursor()

        logging.info(f"Trying Query execution query:: {query} value:: {values} Success")

        if values:
            cursor.execute(query, values)
        else:
            cursor.execute(query)

        logging.info(f"Query execution query:: {query} value:: {values} Success")

        if type == 'getAll':
            return cursor.fetchall()  # Return all results for 'get' type
        if type == 'get':
            return cursor.fetchone()  # Return all results for 'get' type

        return None
    except Exception as e:
        logging.error(f'Error in databasecon.execute:: {str(e)}', exc_info=True)
    finally:
        if conn:  # Check if conn was successfully created
            conn.commit()
            conn.close()

if __name__ == "__main__":
    # Correctly format the execute call with proper type
    results = execute("get", "SELECT audioPath FROM entries WHERE generatedVideoPath IS NULL OR generatedVideoPath = ''")
    if results:
        for row in results:
            print(row)  # Print the results