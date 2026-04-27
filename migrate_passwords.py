import pymysql
from config import Config

def migrate_passwords():
    config = Config()
    try:
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Add must_change_password column
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE")
            print("Added must_change_password column.")
        except Exception as e:
            print(f"must_change_password column might already exist: {e}")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == '__main__':
    migrate_passwords()
