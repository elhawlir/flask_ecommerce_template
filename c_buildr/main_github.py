from . import app, login_manager, db
from .config_github import (
    TWILIO_AUTH_TOKEN,
    SECRET_KEY,
    TWILIO_ACCOUNT_SID,
)

from .config_github import STRIPE_PUBLISHABLE_KEY_TEST, STRIPE_SECRET_KEY_TEST
import stripe

# flask environment
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    make_response,
    g,
    jsonify,
)
import flask_login
from flask_login import login_user, logout_user, login_required
from .models import User, Messages

# User Model
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from forms import EmailForm, PasswordForm

# import sqlalchemy
import re
import os
import pymysql
from urllib.parse import urlencode
from operator import add, index, itemgetter
import json
import requests

from twilio.rest import Client
from oauthlib.oauth2 import WebApplicationClient
import pandas as pd
from .number_cleaning import number_clean, clean_mobile_input, final_text
import tempfile
import pickle
import shutil

# emails
# from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import sendgrid
from sendgrid.helpers.mail import Mail

# from flask_oauth import OAuth

BASE_URL = "http://127.0.0.1:5000"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SECRET_KEY"] = SECRET_KEY

# create tokens for email confirmation
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# email settings
load_dotenv(os.path.join(basedir, "sendgrid.env"))
app.config["MAIL_SERVER"] = "smtp.sendgrid.net"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "apikey"
app.config["SENDGRID_API_KEY"] = os.environ.get("SENDGRID_API_KEY")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

sg = sendgrid.SendGridAPIClient(api_key=app.config["SENDGRID_API_KEY"])

# stripe keys
stripe_keys = {
    "secret_key" : STRIPE_SECRET_KEY_TEST,
    "publishable_key" : STRIPE_PUBLISHABLE_KEY_TEST,
    "endpoint_secret": "", # use this link https://dashboard.stripe.com/test/webhooks/create?endpoint_location=local to get this value
}

stripe.api_key = stripe_keys['secret_key']


def send_email(
    subject,
    recipients,
    html,
    sender=app.config["MAIL_DEFAULT_SENDER"],
    reply_to=app.config["MAIL_DEFAULT_SENDER"],
):

    msg = Mail(
        from_email=sender, to_emails=recipients, subject=subject, html_content=html
    )
    try:
        response = sg.send(msg)
        print(response.status_code)
    except Exception as e:
        print(e)


@app.route("/")
def welcome():
    return render_template("front_page.html")


# help reduce initial latency
@app.route("/_ah/warmup")
def warmup():
    return "", 200, {}


# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route("/login/", methods=["GET", "POST"])
def login():
    # Output message if something goes wrong...
    msg = ""

    # Bypass if user is logged in
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("home"))

    # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == "POST" and "email" in request.form:
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.check_password(request.form["password"]):
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            msg = "you've been successfully logged in!"
            return redirect(url_for("home"))
        if user is None:
            msg = "Incorrect email/password"
    # Account doesnt exist
    # msg = 'Incorrect email/password!'
    return render_template("index.html", msg=msg)


@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash("You must be logged in to view that page.")
    return redirect(url_for("login"))


@app.route("/reset", methods=["GET", "POST"])
def reset():
    # enter email to reset password
    if request.method == "POST" and "email" in request.form:
        user = User.query.filter_by(email=request.form["email"]).first()
        if user:
            subject = "Password reset requested for your account"

            token = ts.dumps(user.email, salt="recover-key")

            recover_url = url_for("reset_with_token", token=token, _external=True)

            html = render_template(
                "email_templates/reset_password_email.html", recover_url=recover_url
            )
            send_email(subject, user.email, html)
            return redirect(url_for("login"))

        else:
            msg = "There is no account with this email address"
            return render_template("register.html", msg=msg)
    return render_template("reset_password.html")


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    # after user receives token in their email and is ready to change their password
    try:
        email = ts.loads(
            token, salt="recover-key", max_age=7200
        )  # token only valid for 2 hours
    except Exception as e:
        print(e)

    user = User.query.filter_by(email=email).first()
    password = user.password
    # print(password)
    if request.method == "POST":
        new_password = request.form["password"]
        user.set_password(new_password)
        db.session.add(user)
        db.session.commit()
        login_user(
            user, remember=True
        )  # automatically login user after they've changed their password
        # msg = "You've successfully changed your password!"
        return redirect(url_for("home"))

    return render_template("email_templates/reset_with_token.html", token=token)


# http://localhost:5000/login/logout - this will be the logout page
@app.route("/logout")
@login_required
def logout():
    # Remove session data, this will log the user out
    logout_user()
    msg = "You've been successfully logged out"
    # Redirect to login page
    return render_template("index.html", msg=msg)


# http://localhost:5000/login/register - this will be the registration page, we need to use both GET and POST requests
@app.route("/register", methods=["GET", "POST"])
def register():
    # Output message if something goes wrong...
    msg = ""
    # Check if "email" and "password" POST requests exist (user submitted form)
    if (
        request.method == "POST"
        and "first_name" in request.form
        and "last_name" in request.form
        and "email" in request.form
        and "password" in request.form
    ):
        # Create variables for easy access
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if account exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            user = User(first_name=first_name, last_name=last_name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # send confirmation email using token
            subject = "Confirm your email used to register with example.com"
            token = ts.dumps(user.email, salt="email-confirm-key")

            confirm_url = url_for("confirm_email", token=token, _external=True)

            html = render_template(
                "email_templates/email_verification.html", confirm_url=confirm_url
            )

            send_email(subject, user.email, html)
            # return redirect(url_for('home'))
            return render_template(
                "email_templates/verify_email.html", email=user.email
            )

        # If account exists show error and validation checks
        if existing_user:
            msg = "Account already exists!"
            # user already logged in so redirect to login page
            return redirect(url_for("login"))
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email address!"
        elif not email or not password:
            msg = "Please fill in the missing details!"

    elif request.method == "POST":
        # Form is empty... (no POST data)
        msg = "Please fill out the form!"
    # Show registration form with message (if any)
    return render_template("register.html", msg=msg)


@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=7200)
    except:
        abort(404)

    user = User.query.filter_by(email=email).first()

    if user:
        db.session.add(user)
        db.session.commit()
        login_user(user)

        return redirect(url_for("home"))
    return render_template(
        "register.html",
        msg="Try registering again. Something's gone wrong with your registration token",
    )


# http://localhost:5000/login/home - this will be the home page, only accessible for loggedin users
@app.route("/home")
@login_required
def home():
    # Check if user is loggedin
    if flask_login.current_user.is_authenticated:
        return render_template("login_home.html", account=flask_login.current_user)

    # User is not loggedin redirect to login page
    return redirect(url_for("login"))


# http://localhost:5000/login/profile - this will be the profile page, only accessible for loggedin users
@app.route("/profile")
@login_required
def profile():
    # Check if user is loggedin
    if flask_login.current_user.is_authenticated:
    #     messages = db.session.execute(f"""select user_id, sum(number_of_messages_sent), 
    #      month(date_sent) 
    #      from messages 
    #      where user_id = {flask_login.current_user.id}
    #      group by user_id, month(date_sent)
         
    # """)
        # monthly_number = [i[1] for i in messages]
        return render_template("profile.html", account=flask_login.current_user, messages_sent=monthly_number)

    # User is not loggedin redirect to login page
    return redirect(url_for("login"))


@app.route("/send_txt", methods=["GET", "POST"])
@login_required
def send_txt():
    
    msg = ""

    # twilio account details
    account_sid = TWILIO_ACCOUNT_SID 
    auth_token = TWILIO_AUTH_TOKEN

    main_client = Client(account_sid, auth_token)

    # upload csv
    if "data_file" in request.files.keys():
        csv_file = request.files["data_file"]
        if not csv_file:
            msg = "Don't forget to upload a CSV file!"
            return render_template("send_txt.html", msg=msg)
        
        csv_file = pd.read_csv(csv_file)
        columns = csv_file.columns
        csv_file = csv_file.dropna(how="all")  # remove empty records
        print(len(csv_file))
        
        session['tempdir'] = tempfile.mkdtemp()
        with open(f"{session['tempdir']}/tmp.pkl", 'wb') as outfile:
            tmp_file = csv_file.to_dict('list')
            pickle.dump(tmp_file, outfile)
        outfile.close()

        return render_template("send_txt.html", columns=columns)

    # extract text and selected column to output df[selected_column]
    if "text" in request.form.keys():
        text = request.form["text"].strip()
        if not text:
            df.clear()
            msg = "You haven't written anything yet"
            return render_template("send_txt.html", msg=msg)

    # return chosen column_df
    if "columns" in request.form.keys() or "twilio_number" in request.form.keys():
        selected_column = request.form["columns"]
        twilio_number = request.form["twilio_number"].strip()
        if not selected_column:
            df.clear()
            msg = "You haven't chosen a column yet"
            return render_template("send_txt.html", msg=msg)

        with open(f"{session['tempdir']}/tmp.pkl", 'rb') as infile:
            mylist = pickle.load(infile)
        print('pickle file')

        numbers_df = mylist[selected_column]
        numbers_df = [str(int(numbers_df[i])) if (isinstance(r, float)) and r==r else r for i,r in enumerate(numbers_df)] # convert float numbers to mobile number strings

        # remove spaces between numbers
        re_df = [re.sub(r"(\d)\s+(\d)", r"\1\2", str(i)) for i in numbers_df if i==i] # 0412 345 678 becomes 0412345678

        # clean and ready mobile numbers to be sent using Twilio api
        try:
            re_df = [str(int(i)) for i in re_df if i == i]
        except:
            msg = f"You're selected column is {selected_column}. You sure that's the correct column?"
            return render_template("send_txt.html", msg=msg)

        clean_numbers = number_clean(re_df)
        clean_numbers = clean_mobile_input(clean_numbers)

        # send final message
        if twilio_number:
            msg = final_text(clean_numbers, text, main_client, twilio_number) # sending live messages
            
        infile.close()

        # must remove temp directory, file and clear session
        shutil.rmtree(session['tempdir'])
        session.pop('tempdir', None)
        
    return render_template("send_txt.html", msg=msg)

# shopping for products
@app.route("/products")
def products():
    return render_template('products.html')

# processing payments using Stripe
@app.route("/config")
@login_required
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)

# checkout session
@app.route("/create-checkout-session", methods=['POST'])
@login_required
def create_checkout_session():
    domain_url = BASE_URL

    item_quantity200 = request.form.get('quantity-200')
    item_quantity400 = request.form.get('quantity-400')
    item_quantity1000 = request.form.get('quantity-1000')

    line_items_list = []

    if int(item_quantity200) > 0:
        line_items_list.append(
            {
                    'price': '', # Use stripe to get the Price key for each product
                    'adjustable_quantity': {
                        'enabled': True,
                        'minimum': 0,
                        'maximum': 5,
                    },
                    'quantity': item_quantity200,
            }
        )

    if int(item_quantity400) > 0:
        line_items_list.append(
            {
                    'price': '', 
                    'adjustable_quantity': {
                        'enabled': True,
                        'minimum': 0,
                        'maximum': 5,
                    },
                    'quantity': item_quantity400,
            }
        )
    
    if int(item_quantity1000) > 0:
        line_items_list.append(
            {
                    'price': '',
                    'adjustable_quantity': {
                        'enabled': True,
                        'minimum': 0,
                        'maximum': 5,
                    },
                    'quantity': item_quantity1000,
            }
        )

    if len(line_items_list) == 0:
        msg = "You haven't chosen any items to checkout"
        return render_template('products.html', msg=msg)

    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [payment_intent_data] - capture the payment later
        # [customer_email] - prefill the email input in the form
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        checkout_session = stripe.checkout.Session.create(
            client_reference_id=flask_login.current_user.id if flask_login.current_user.is_authenticated else None,
            line_items=line_items_list,            
            payment_method_types=["card"],
            mode="payment",
            # success_url=domain_url + "/success?session_id={CHECKOUT_SESSION_ID}",
            success_url=domain_url + "/success",
            cancel_url=domain_url + "/cancelled",            
        )
        # return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)

@app.route("/success")
@login_required
def success():
    return render_template("payments/success.html")


@app.route("/cancelled")
@login_required
def cancelled():
    return render_template("payments/cancel.html")

# stripe webhook indicating successful payment
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")
        # TODO: run some custom code here

    return "Success", 200
