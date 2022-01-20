import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))

# Uncomment line below for a new 16 character secret key everytime you launch your web app
# SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits,k=16))

SECRET_KEY = "ANY RANDOM LETTERS YOU CHOOSE TO USE"
# print(SECRET_KEY)

# DB details based on Google Cloud MySQL Auth Proxy Setup
CLOUD_SQL_USERNAME = ""
CLOUD_SQL_PASSWORD = ""
CLOUD_SQL_DATABASE_NAME = ""
CLOUD_SQL_CONNECTION_NAME = ""

# when deploying, be sure to change .flaskenv variable 'FLASK_ENV' to 'production'
if os.environ.get("FLASK_ENV") == "production":
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{CLOUD_SQL_USERNAME}:{CLOUD_SQL_PASSWORD}@/{CLOUD_SQL_DATABASE_NAME}?unix_socket=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"
else:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{CLOUD_SQL_USERNAME}:{CLOUD_SQL_PASSWORD}@127.0.0.1:3306/{CLOUD_SQL_DATABASE_NAME}"
SQLALCHEMY_ECHO = False


# twilio auth details for messaging function
ACCOUNT_SID = ""
AUTH_TOKEN = ""

# stripe integration details, use test keys unless running in production/live mode
STRIPE_PUBLISHABLE_KEY_TEST = ""
STRIPE_SECRET_KEY_TEST = ""