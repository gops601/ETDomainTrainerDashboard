import pymysql
from config import Config

def migrate():
    config = Config()
    try:
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Add is_training column
        try:
            cursor.execute("ALTER TABLE training_entries ADD COLUMN is_training BOOLEAN DEFAULT TRUE")
            print("Added is_training column.")
        except Exception as e:
            print(f"is_training column might already exist: {e}")
            
        # Add duration column
        try:
            cursor.execute("ALTER TABLE training_entries ADD COLUMN duration FLOAT DEFAULT 0.0")
            print("Added duration column.")
        except Exception as e:
            print(f"duration column might already exist: {e}")
            
        # Make ou_id and training_type_id nullable for non-training activities
        try:
            cursor.execute("ALTER TABLE training_entries MODIFY ou_id INTEGER NULL")
            cursor.execute("ALTER TABLE training_entries MODIFY training_type_id INTEGER NULL")
            print("Modified ou_id and training_type_id to be NULLable.")
        except Exception as e:
            print(f"Error modifying columns in training_entries: {e}")
            
        # Drop date column if it exists
        try:
            cursor.execute("ALTER TABLE training_entries DROP COLUMN date")
            print("Dropped date column from training_entries.")
        except Exception as e:
            # 1091 is error code for "Can't DROP 'column'; check that column/key exists"
            if '1091' not in str(e):
                print(f"Error dropping date column: {e}")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == '__main__':
    migrate()
