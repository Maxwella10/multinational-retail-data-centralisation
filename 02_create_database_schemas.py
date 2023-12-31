'''
AiCore Multinational Retail Data Centralisation Project

Milestone 3: Create the database schema

Develop the star-based schema of the database, ensuring that columns 
have the correct data types.

Author: Maxwell Acha
Date: 20-11-2023
'''

# %%

import pandas as pd
import re
from data_ingestion.database_utils import DatabaseConnector
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from utilities.decorators import time_it


@time_it
def add_foreign_key(engine, fk_table, pk_table, *columns):
    '''Set foreign key in table to the specified column(s).

    Arguments:
        engine (SQLAlchemy engine)
        fk_table (string): table being updated with foreign key
        pk_table (string): table being referenced
        columns (strings): column names

    Returns:
        None
    '''

    columns = ', '.join(columns)
    constraint_name = 'fk_' + re.sub('^dim_', '', pk_table)

    sql = f'''ALTER TABLE {fk_table}
        ADD CONSTRAINT {constraint_name} FOREIGN KEY ({columns}) REFERENCES {pk_table} ({columns});'''

    print('Executing SQL: ' + sql)
    with engine.connect() as con:
        con.execute(text(sql))


@time_it
def add_primary_key(engine, table_name, *columns):
    '''Set primary key in table to the specified column(s).

    Arguments:
        engine (SQLAlchemy engine)
        table_name (string)
        columns (strings): column names

    Returns:
        None
    '''

    columns = ', '.join(columns)
    constraint_name = 'unique_' + re.sub('^dim_', '', table_name)
    sql = f'ALTER TABLE {table_name} ADD PRIMARY KEY ({columns});'
    print('Executing SQL: ' + sql)
    sql = f'ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} UNIQUE ({columns});'
    print('Executing SQL: ' + sql)
    with engine.connect() as con:
        con.execute(text(sql))


@time_it
def change_data_type(engine, table_name, column, data_type):
    '''Change data type for the specified column.

    Arguments:
        engine (SQLAlchemy engine)
        table_name (string)
        column (string)
        data_type (string)

    Returns:
        None
    '''
    sql = f'ALTER TABLE {table_name} ALTER COLUMN {column} TYPE {data_type};'
    print('Executing SQL: ' + sql)
    with engine.connect() as con:
        con.execute(text(sql))


def get_column_names(engine, table_name):
    '''Get a list of column names in a database table.
    If column names are not in snake_case, enclose them
    in double quotes; this will allow them to be used in SQL.

    Arguments:
        engine (SQLAlchemy engine)
        table_name (string)

    Returns:
        list of strings
    '''
    with engine.connect() as con:
        sql = f'SELECT * FROM {table_name} WHERE 0 = 1;'
        column_names = list(con.execute(text(sql)).keys())

        for i, col in enumerate(column_names):
            if re.search(r'[^a-z0-9_]', col):
                column_names[i] = '"' + col + '"'
        return column_names


def get_data_type(engine, table_name, column):
    '''Get the required data type for the specified column.
    For most VARCHAR columns, the max length is set to the length
    of the longest value found in the column.

    Arguments:
        engine (SQLAlchemy engine)
        table_name (string)
        column (string)

    Returns:
        string
    '''
    varchar = 'VARCHAR({})'
    uuid = 'UUID USING {}::uuid'
    bool_type = 'BOOL USING {}::boolean'
    float_type = 'FLOAT USING {}::double precision'

    data_types = {'card_number': varchar,
                  'continent': varchar,
                  'country_code': varchar,
                  'date_added': 'DATE',
                  'date_of_birth': 'DATE',
                  'date_payment_confirmed': 'DATE',
                  'date_uuid': uuid,
                  'day': varchar,
                  '"EAN"': varchar,
                  'expiry_date': varchar,
                  'first_name': varchar,
                  'join_date': 'DATE',
                  'last_name': varchar,
                  'latitude': float_type,
                  'locality': varchar,
                  'longitude': float_type,
                  'month': varchar,
                  'opening_date': 'DATE',
                  'product_code': varchar,
                  'product_price': float_type,
                  'product_quantity': 'SMALLINT',
                  'staff_numbers': 'SMALLINT',
                  'still_available': bool_type,
                  'store_code': varchar,
                  'store_type': varchar,
                  'time_period': varchar,
                  'user_uuid': uuid,
                  'uuid': uuid,
                  'weight': float_type,
                  'weight_class': varchar,
                  'year': varchar
                  }

    data_type = data_types.get(column, varchar)
    if 'VARCHAR' in data_type:

        # Set max varchar length of field to 255, or max length of value
        if column in ['first_name', 'last_name', 'locality', 'continent', 'store_type']:
            max_len = 255
        else:
            max_len = get_max_length(engine, table_name, column)
        data_type = data_type.format(max_len)

        # store_type column is nullable
        if column == 'store_type':
            data_type += f';\nALTER TABLE {table_name} ALTER COLUMN {column} DROP NOT NULL'

        return data_type.format(max_len)

    return data_type.format(column)


def get_max_length(engine, table_name, column):
    '''Run SQL to get maximum length of value in column.

    Arguments:
        engine (SQLAlchemy engine)
        table_name (string)
        column (string)

    Returns:
        int
    '''
    with engine.connect() as con:
        sql = F'SELECT MAX(LENGTH(CAST({column} AS TEXT))) from {table_name};'
        cur = con.execute(text(sql))
        return cur.fetchall()[0][0]


@time_it
def update_tables(engine):
    '''Update tables to prepare for analysis.
    dim_store_details:
        - Merge LAT and LATITUDE columns in DIM_STORE_DETAILS table; drop the LAT column. 
        - Set null locality for web-based stores to 'N/A'.
    dim_products:
        - Remove currency symbol from product_price column
        - Derive weight_class from weight.
        - Rename the removed column to still_available; change its data type to bool.

    Arguments:
        engine (SQLAlchemy engine)

    Returns:
        None
    '''

    print('\nUpdating tables')
    with engine.connect() as con:

        def execute(x): con.execute(text(x))

        print('Updating dim_store_details; merging lat and latitude')
        sql = '''UPDATE dim_store_details
                SET latitude = COALESCE(latitude, lat);
                ALTER TABLE dim_store_details
                DROP COLUMN lat;'''
        execute(sql)

        print('Updating dim_store_details; setting locality to N/A for web stores')
        sql = '''UPDATE dim_store_details
                SET locality = 'N/A'
                WHERE LOWER(store_type) LIKE 'web%'
                AND locality IS NULL;'''
        execute(sql)

        print('Updating dim_products; removing £ from product_price')
        sql = '''UPDATE dim_products
                SET product_price = REPLACE(product_price, '£', '');'''
        execute(sql)

        print('Updating dim_products; deriving weight_class from weight')
        sql = '''ALTER TABLE dim_products
                ALTER COLUMN weight TYPE FLOAT USING weight::double precision;
                ALTER TABLE dim_products 
                ADD COLUMN weight_class VARCHAR(20) NULL;
                UPDATE dim_products
                SET weight_class = (
                    SELECT CASE 
                        WHEN weight < 2 THEN 'Light'
                        WHEN weight < 40 THEN 'Mid_Sized'
                        WHEN weight < 140 THEN 'Heavy'
                        WHEN weight >= 140 THEN 'Truck_Required'
                        ELSE 'UNKNOWN'
                    END);'''
        execute(sql)

        print('Updating dim_products; renaming removed to still_available')
        sql = '''ALTER TABLE dim_products
                RENAME COLUMN removed TO still_available;
                UPDATE dim_products
                SET still_available = (
                    CASE 
                        WHEN LOWER(TRIM(still_available)) = 'still_available' THEN True
                        ELSE False
                    END);'''
        execute(sql)


if __name__ == '__main__':

    db_connector = DatabaseConnector("data_ingestion\db_local_creds.yaml")
    db_connector.init_db_engine(autocommit=True)
    engine = db_connector.engine
    try:
        update_tables(db_connector.engine)
    except ProgrammingError:
        print('Schema has already been updated; no action taken. Exiting.')
        exit()

    table_to_column_mapping = dict()
    tables = db_connector.list_db_tables()

    for table_name in tables:
        print('\nUpdating data types for table: ' + table_name)

        column_names = get_column_names(engine, table_name)
        table_to_column_mapping[table_name] = column_names

        for column in column_names:
            data_type = get_data_type(engine, table_name, column)
            change_data_type(engine, table_name, column, data_type)

    print('\nSetting primary and foreign keys')
    orders_table_columns = table_to_column_mapping['orders_table']
    for table, columns in table_to_column_mapping.items():
        if table == 'orders_table':
            continue
        cols = set(columns) & set(orders_table_columns) - {'index'}
        add_primary_key(engine, table, *cols)
        add_foreign_key(engine, 'orders_table', table, *cols)