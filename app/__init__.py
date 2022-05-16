from flask import Flask
import os, sqlalchemy
from yaml import load, Loader
import app.utils as utils

app = Flask(__name__)
app.secret_key = "thisIsTheKeyForTeam24CS411" #needed for making sessions which store current user's info


def init_connection_engine():
    """ initialize database setup
    Takes in os variables from environment if on GCP
    Reads in local variables that will be ignored in public repository.
    Returns:
        pool -- a connection to GCP MySQL
    """


    # detect env local or gcp
    if os.environ.get('GAE_ENV') != 'standard':
        try:
            variables = load(open("app.yaml"), Loader=Loader)
        except OSError as e:
            print(e)
            print("Make sure you have the app.yaml file setup")
            os._exit(1)

        env_variables = variables['env_variables']
        for var in env_variables:
            os.environ[var] = env_variables[var]

    pool = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=os.environ.get('MYSQL_USER'),
            password=os.environ.get('MYSQL_PASSWORD'),
            database=os.environ.get('MYSQL_DB'),
            host=os.environ.get('MYSQL_HOST')
        )
    )

    return pool

#Establish connection to DB
db = init_connection_engine()
queries = utils.Query()


#cyclic import 
from app import routes