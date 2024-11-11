import logging
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import json
import csv
from airflow.providers.mysql.hooks.mysql import MySqlHook
import re


default_args = {
    'owner': 'admin',
    'start_date': datetime(2023, 12, 28),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


@dag(
    dag_id='pipeline',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 28),
    catchup=False
)
def pipeline():
    @task()
    def fetch_data_from_mongo():
        try:
            # Initialize the Mongo hook and get the MongoDB connection
            hook = MongoHook(mongo_conn_id='mongo_default')
            client = hook.get_conn()

            # Access your MongoDB database and collection
            collection = client['bigdata']['journals']

            # Fetch data from the collection
            cursor = collection.find()  # This returns a cursor to iterate over the documents

            # Convert the documents to a list of dictionaries and serialize ObjectId
            data_list = []
            for document in cursor:
                document['_id'] = str(document['_id'])  # Convert ObjectId to string
                data_list.append(document)

            # Print the data in JSON format
            print(json.dumps(data_list, indent=4))  # Pretty print the JSON
             
            return data_list  # This can be returned if needed for further tasks

        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return None

    @task()
    def fetch_data_from_postgres():
        try:
            # Initialize the Postgres hook
            postgres_hook = PostgresHook(postgres_conn_id='postgres_default')

            # SQL query to fetch data from users table
            sql_query = "SELECT * FROM journals;"

            # Execute the query
            connection = postgres_hook.get_conn()
            cursor = connection.cursor()
            cursor.execute(sql_query)

            # Fetch and print the data
            data = cursor.fetchall()
            for row in data:
                print(row)

            return data  # Return data for potential further processing

        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None

    @task()
    def fetch_data_from_json():
        try:
            json_file_path = 'C:/Users/mohammed/Desktop/Airflow/Data-Engineering-Pipeline/airflow/data_set/journals.json'

            # Open and load JSON data
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # Print or process the JSON data
            print(json.dumps(data, indent=4))
            return data  # Return data if needed for further tasks

        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return None

    @task()
    def fetch_data_from_csv():
        try:
            # Define the path to your CSV file
            csv_file_path = 'C:/Users/mohammed/Desktop/Airflow/Data-Engineering-Pipeline/airflow/data_set/journals.csv'

            # Initialize an empty list to store the rows
            data_list = []

            # Open the CSV file and read the contents
            with open(csv_file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)  # Read as a dictionary (headers as keys)
                for row in reader:
                    data_list.append(row)  # Append each row to the data list

            # Print the data (optional)
            print(json.dumps(data_list, indent=4))  # Pretty print the CSV data

            return data_list
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None



    @task()
    def insert_data_into_data_warehouse(data):

        print(data)
        mysql_hook = MySqlHook(mysql_conn_id="mysql_default")

        def verify_and_convert_structure(t):
            result = []

            for item in t:
                # Si la structure correspond à la première, nous n'avons rien à faire.
                if isinstance(item, dict) and "Title" in item and "DOI" in item and "Authors" in item:
                    # Ajouter tel quel
                    result.append(item)
                else:
                    # Sinon, nous convertissons la structure vers la première structure attendue
                    article = {
                        "Title": item[1],
                        "DOI": item[2],
                        "Authors": item[3].split(', '),  # Séparer les auteurs en liste
                        "Publication Date": item[4].replace('Date of Publication: ', ''),
                        "ISSN": item[5],
                        "Link": item[6],
                        "Quartils": item[7] if isinstance(item[7], str) else "Journal pas indexé Scopus",
                        # Si Quartils est une chaîne, on le garde, sinon on assigne une valeur par défaut
                        "journal_main": f"Published in: {item[1]}",
                        "abstract": item[8] if len(item) > 8 else None  # Si l'index 8 existe, on l'assigne, sinon None
                    }
                    result.append(article)

            return result
        data = verify_and_convert_structure(data)
        print(data)

        def add_authors(authors):
            try:
                with mysql_hook.get_conn() as conn:
                    with conn.cursor() as cursor:
                        author_ids = []

                        # Loop through authors list
                        for author_name in authors:
                            # Check if the author already exists
                            cursor.execute(
                                "SELECT AuthorID FROM Authors WHERE AuthorName = %s",
                                (author_name,)
                            )
                            result = cursor.fetchone()

                            if result:
                                # Author exists, use the existing AuthorID
                                author_id = result[0]
                                logging.info(f"Author '{author_name}' already exists with ID {author_id}.")
                            else:
                                # Author does not exist, insert a new record with None for Affiliation and Country
                                cursor.execute(
                                    """
                                    INSERT INTO Authors (AuthorName, Affiliation, Country)
                                    VALUES (%s, NULL, NULL)
                                    """,
                                    (author_name,)
                                )
                                conn.commit()
                                author_id = cursor.lastrowid
                                logging.info(f"Author '{author_name}' added with ID {author_id}.")

                            author_ids.append(author_id)

                        return author_ids  # Return list of author IDs

            except Exception as e:
                logging.error(f"Error adding authors: {e}")
                return None

        # Function to get or create a journal entry
        def determine_quartile_from_citescore(citescore):
            """Déterminer le quartil basé sur le CiteScore."""
            if citescore >= 4.0:
                return "Q1"
            elif citescore >= 2.0:
                return "Q2"
            elif citescore >= 1.0:
                return "Q3"
            else:
                return "Q4"

        def process_quartil(quartil_value):
            """Vérifier si le quartil est un nombre et le transformer en quartil valide."""
            try:
                # Si le quartil est un nombre, déterminer le quartil approprié
                quartil_float = float(quartil_value)

                # Retourner le quartil basé sur la valeur numérique
                return determine_quartile_from_citescore(quartil_float)
            except ValueError:
                # Si ce n'est pas un nombre, il doit être déjà sous forme de quartil (par exemple "Q1", "Q2", ...)
                return quartil_value  # Retourner le quartil tel quel s'il est valide (Q1, Q2, etc.)

        def get_or_create_journal(journal_main, issn, quartils):
            try:
                with mysql_hook.get_conn() as conn:
                    with conn.cursor() as cursor:

                        # Extraire l'ISSN électronique
                        electronic_issn = 'Non disponible'
                        if isinstance(issn, dict):
                            electronic_issn = issn.get('Electronic ISSN', 'Non disponible')
                        elif isinstance(issn, str):
                            electronic_issn = issn

                        # Vérifier si le journal existe déjà
                        cursor.execute("SELECT JournalID FROM Journal WHERE JournalMain = %s", (journal_main,))
                        result = cursor.fetchone()

                        if result:
                            journal_id = result[0]
                        else:
                            # Insérer le journal si il n'existe pas
                            if isinstance(quartils, list):
                                print("quartils est une liste")
                                cursor.execute(
                                    "INSERT INTO Journal (JournalMain, ISSN, Quartils) VALUES (%s, %s, %s)",
                                    (journal_main, electronic_issn, 'indexe')
                                )
                                conn.commit()
                                journal_id = cursor.lastrowid
                            elif isinstance(quartils, str):
                                print("quartils est une chaîne de caractères")
                                cursor.execute(
                                    "INSERT INTO Journal (JournalMain, ISSN, Quartils) VALUES (%s, %s, %s)",
                                    (journal_main, electronic_issn, 'pas indexe')
                                )
                                conn.commit()
                                journal_id = cursor.lastrowid

                        # Insérer chaque quartil associé à ce journal dans la table Quartils
                        for quartil in quartils:
                            annee = quartil.get('année')
                            quartil_value = quartil.get('quartil')
                            print("================> " + str(quartil))

                            # Vérification et transformation du quartil
                            quartil_value = process_quartil(quartil_value)

                            # Log avant insertion
                            logging.info(
                                f"Insertion du Quartil - Annee: {annee}, Quartil: {quartil_value}, JournalID: {journal_id}")

                            cursor.execute(
                                "INSERT INTO Quartils (annee, quartil, id_journal) VALUES (%s, %s, %s) "
                                "ON DUPLICATE KEY UPDATE quartil = VALUES(quartil)",
                                (annee, quartil_value, journal_id)
                            )

                        conn.commit()

                        return journal_id

            except Exception as e:
                logging.error(f"Error creating or retrieving journal '{journal_main}': {e}")
                return None

        def extract_journal_name(journal_main):
            # Regular expression to capture the journal name
            match = re.search(r"Published in:\s*([^(\n]+)", journal_main)
            if match:
                journal_name = match.group(1).strip()  # Capture the matched group and strip any surrounding whitespace
                return journal_name
            return None  # Return None if no match is found

        # Function to insert a publication entry
        def insert_publication(title, doi, publication_date, link, abstract, journal_id, last_quartil):
            try:
                with mysql_hook.get_conn() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO Publications (Title, DOI, PublicationDate, Link, Abstract, JournalID, Quartils)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (title, doi, publication_date, link, abstract, journal_id, last_quartil)
                        )
                        conn.commit()
                        logging.info(f"Publication '{title}' inserted successfully.")
            except Exception as e:
                logging.error(f"Error inserting publication '{title}': {e}")

        # Iterate over each publication in the data
        for entry in data:
            try:
                journal_main = extract_journal_name(entry.get('journal_main', '')) 
                issn = entry.get('ISSN', {})
                quartils = entry.get('Quartils', [])
                Authors = entry.get('Authors', [])
                add_authors(Authors)
                publication_date_str = entry.get('Publication Date', '').replace("Date of Publication: ", "")
                publication_date = datetime.strptime(publication_date_str,
                                                     "%d %B %Y").date() if publication_date_str else None
                doi = entry.get('DOI', '')
                title = entry.get('Title', '')
                link = entry.get('Link', '')
                abstract = entry.get('abstract', '')

                # Get or create the journal entry and retrieve the JournalID
                journal_id = get_or_create_journal(journal_main, issn, quartils)
                if not journal_id:
                    logging.warning(f"Journal '{journal_main}' was not inserted.")
                    continue

                # Insert the publication entry with retrieved JournalID
                last_quartil = quartils[-1].get('quartil', 'Non disponible') if quartils else 'Non disponible'
                insert_publication(title, doi, publication_date, link, abstract, journal_id, last_quartil)

            except Exception as e:
                logging.error(f"Error processing publication '{entry.get('Title', '')}': {e}")

    # Define task dependencies
    mongo_data = fetch_data_from_mongo()
    postgres_data = fetch_data_from_postgres()
    json_data = fetch_data_from_json()
    csv_data = fetch_data_from_csv()

    insert_data_task_from_mongo  = insert_data_into_data_warehouse(mongo_data)
    insert_data_task_from_postgres  = insert_data_into_data_warehouse(postgres_data)
    # Set the order of execution

    
    mongo_data  >> insert_data_task_from_mongo  >> postgres_data >> insert_data_task_from_postgres  >> json_data >> csv_data
     
     


# Set the DAG to run
pipeline()