import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def fetch_current_schema():
    """Fetches all tables and their columns from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    schema_dict = {}
    for table, column, data_type in rows:
        if table not in schema_dict:
            schema_dict[table] = []
        schema_dict[table].append(f"{column} ({data_type})")
    
    cursor.close()
    conn.close()
    
    # Format nicely for the LLM
    schema_str = "Current Database Schema:\n"
    for table, columns in schema_dict.items():
        schema_str += f"- Table: {table}\n  Columns: {', '.join(columns)}\n"
        
    return schema_str

def execute_sql(sql_query: str):
    """Executes a raw SQL command against the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        conn.commit()
        return True, "Execution successful!"
    except Exception as e:
        conn.rollback() # Safety net: undo if there's an error
        return False, str(e)
    finally:
        cursor.close()
        conn.close()