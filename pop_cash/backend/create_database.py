"""
SQLite Database Creator from CSV Files
This script reads all CSV files from the dataset folder and creates an SQLite database.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVToSQLiteConverter:
    """Convert CSV files to SQLite database tables"""
    
    def __init__(self, dataset_folder: str, db_path: str):
        """
        Initialize the converter
        
        Args:
            dataset_folder: Path to folder containing CSV files
            db_path: Path where SQLite database will be created
        """
        self.dataset_folder = Path(dataset_folder)
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """Create connection to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"✓ Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            raise
    
    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")
    
    def get_csv_files(self) -> List[Path]:
        """Get all CSV files from dataset folder"""
        csv_files = list(self.dataset_folder.glob("*.csv"))
        logger.info(f"✓ Found {len(csv_files)} CSV files")
        return csv_files
    
    def infer_sql_type(self, dtype) -> str:
        """
        Infer SQL data type from pandas dtype
        
        Args:
            dtype: Pandas data type
            
        Returns:
            SQL data type as string
        """
        dtype_str = str(dtype)
        
        if 'int' in dtype_str:
            return 'INTEGER'
        elif 'float' in dtype_str:
            return 'REAL'
        elif 'bool' in dtype_str:
            return 'BOOLEAN'
        elif 'datetime' in dtype_str or 'date' in dtype_str:
            return 'DATETIME'
        else:
            return 'TEXT'
    
    def create_table_from_csv(self, csv_path: Path) -> bool:
        """
        Create a table from CSV file
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get table name from filename (remove .csv extension)
            table_name = csv_path.stem
            logger.info(f"\n📊 Processing: {csv_path.name}")
            
            # Read CSV file
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"   Rows: {len(df):,} | Columns: {len(df.columns)}")
            
            # Drop the table if it exists
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create table schema
            columns_def = []
            for col in df.columns:
                # Clean column name (replace spaces and special chars)
                clean_col = col.strip().replace(' ', '_').replace('-', '_')
                sql_type = self.infer_sql_type(df[col].dtype)
                columns_def.append(f'"{clean_col}" {sql_type}')
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(columns_def)}
                )
            """
            
            self.cursor.execute(create_table_sql)
            logger.info(f"   ✓ Table '{table_name}' created")
            
            # Insert data using pandas to_sql (more efficient)
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            logger.info(f"   ✓ Data inserted: {len(df):,} rows")
            
            # Create index on ID columns if they exist
            id_columns = [col for col in df.columns if 'id' in col.lower()]
            for id_col in id_columns:
                clean_col = id_col.strip().replace(' ', '_').replace('-', '_')
                index_name = f"idx_{table_name}_{clean_col}"
                try:
                    self.cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}("{clean_col}")')
                    logger.info(f"   ✓ Index created on '{clean_col}'")
                except Exception as e:
                    logger.warning(f"   ⚠ Could not create index on '{clean_col}': {e}")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"   ✗ Error processing {csv_path.name}: {e}")
            return False
    
    def get_database_summary(self) -> Dict:
        """Get summary of database tables"""
        summary = {}
        
        # Get all tables
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()
        
        for (table_name,) in tables:
            # Get row count
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            # Get column info
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            
            summary[table_name] = {
                'rows': row_count,
                'columns': len(columns),
                'column_names': [col[1] for col in columns]
            }
        
        return summary
    
    def convert_all(self):
        """Convert all CSV files to SQLite database"""
        logger.info("=" * 70)
        logger.info("🚀 Starting CSV to SQLite Conversion")
        logger.info("=" * 70)
        
        # Connect to database
        self.connect_db()
        
        # Get all CSV files
        csv_files = self.get_csv_files()
        
        if not csv_files:
            logger.warning("⚠ No CSV files found in the dataset folder!")
            return
        
        # Process each CSV file
        success_count = 0
        for csv_file in csv_files:
            if self.create_table_from_csv(csv_file):
                success_count += 1
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("📈 CONVERSION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total CSV files: {len(csv_files)}")
        logger.info(f"Successfully converted: {success_count}")
        logger.info(f"Failed: {len(csv_files) - success_count}")
        
        # Get database summary
        summary = self.get_database_summary()
        
        logger.info("\n" + "=" * 70)
        logger.info("📊 DATABASE TABLES")
        logger.info("=" * 70)
        
        total_rows = 0
        for table_name, info in sorted(summary.items()):
            logger.info(f"\n📋 {table_name}")
            logger.info(f"   Rows: {info['rows']:,}")
            logger.info(f"   Columns: {info['columns']}")
            logger.info(f"   Sample columns: {', '.join(info['column_names'][:5])}")
            total_rows += info['rows']
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✅ Database created successfully!")
        logger.info(f"📁 Location: {self.db_path.absolute()}")
        logger.info(f"📊 Total tables: {len(summary)}")
        logger.info(f"📈 Total rows: {total_rows:,}")
        logger.info("=" * 70)
        
        # Close connection
        self.close_db()


def main():
    """Main function"""
    # Configuration
    DATASET_FOLDER = "src/dataset"  # Folder containing CSV files
    DATABASE_PATH = "src/popcash.db"  # Output SQLite database path
    
    # Create converter instance
    converter = CSVToSQLiteConverter(DATASET_FOLDER, DATABASE_PATH)
    
    # Convert all CSV files
    converter.convert_all()


if __name__ == "__main__":
    main()
