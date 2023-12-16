# multinational-retail-data-centralisation

Collate and analyse data from various sources, to create a local, centralised PostgreSQL sales database which acts as a single source of truth for sales data. Query the data to extract business metrics.

This is a project from AiCore based on the scenario that I am working for a multinational company that sells various goods across the globe and thus the sales data is spread in various data sources. The main aim of this project is to get sales data accessible to one centralised location or database so that the data is easily accessible or analysable by current members of the team. And hence query the database to get up-to-date metrics for the business.

In this project we are using pgAdmin4 to store the data in the database postgres and postgreSQL for querying. This database will store all the company information once you extract it for the various data sources.


## IMPORTANT
The following YAML files are expected to exist in your root directory:

db_local_creds.yaml
db_creds.yaml
These files contain credentials for connecting to the local PostgreSQL database, and the AWS RDS database containing orders data, respectively. The YAML files should contain the following keys:

HOST

PASSWORD

USER

DATABASE

PORT






## ETL Process
The data is fetched from various sources. This data is cleaned and then stored into the database for analysis The are 3 python scripts used for this purpose namely

data_extraction.py: In this script we create a DataExtractor class. This class will work as a utility class, in it you will be creating methods that help extract data from different data sources. The methods contained will be fit to extract data from a particular data source, these sources will include CSV files, an API and an S3 bucket.
data_cleaning.py: In this script we create a DataCleaning class with methods to clean data from each of the data sources.
database_utils.py In this script we create a DatabaseConnector class which we will use to connect with and upload data to the database.
