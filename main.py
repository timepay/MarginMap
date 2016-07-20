############## Imports #################
from flask import Flask, render_template, redirect, request, url_for, g, session, flash, abort
from flask_bootstrap import Bootstrap
from wtforms import Form, BooleanField, TextField, PasswordField, validators, DecimalField, SelectField
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import decimal
import random
import locale
import psycopg2
import os
import urllib.parse
locale.setlocale(locale.LC_ALL, '')

############ Boilerplate ###################

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
Bootstrap(app)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

############ DB Table Models #############################

class User(db.Model):
    __tablename__ =  'user'
    id = db.Column('id', db.Integer, primary_key = True, autoincrement=1)
    username = db.Column('username', db.String(20), unique=True)
    password = db.Column('password', db.String(100))

    def __init__(self , username, password):
        #self.id = User.query.count() + 1
        self.username = username
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % self.username

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


db.create_all()

############## WTForms Classes #######################

class Login(Form):
    password = PasswordField('Password <br><i>(Case Sensitive)</i>:', [validators.InputRequired(message=None)])

class Margin(Form):
    pass

class MarginCalculate(Form):
    client = SelectField(u'Client:', choices=[('Cetera Financial'), ('DiTech'), ('Fairview'), ('Farm Bureau'), ('Guide One'),('Hy-Vee'),('Integrated Behavior Health Network'),('Lifespace Communities'),('Lifetouch'), ('Merrill'), ('MoneyGram'), ('Nationstar'), ('Pioneer'), ('Hybrid'), ('Prime'), ('Principal Financial'), ('Securian'), ('State of Iowa'), ('State of Minnesota'), ('Unity Point Wellmark'), ('Wells Fargo')])
    billingRate = DecimalField('Billing Rate:', [validators.InputRequired(message=None)], default=55.00)
    payRate = DecimalField('Pay Rate:', [validators.InputRequired(message=None)], default=58000)
    payType = SelectField(u'Pay Type:', choices=[('Salary','Salary'), ('W2', 'W2'), ('IC', 'IC')], default="Salary")

class BillingCalculate(Form):
    client = SelectField(u'Client:', choices=[('Cetera Financial'), ('DiTech'), ('Fairview'), ('Farm Bureau'), ('Guide One'),('Hy-Vee'),('Integrated Behavior Health Network'),('Lifespace Communities'),('Lifetouch'), ('Merrill'), ('MoneyGram'), ('Nationstar'), ('Pioneer'), ('Hybrid'), ('Prime'), ('Principal Financial'), ('Securian'), ('State of Iowa'), ('State of Minnesota'), ('Unity Point Wellmark'), ('Wells Fargo')])
    targetMargin = DecimalField('Target Margin:', [validators.InputRequired(message=None)], default=26.86)
    payRate = DecimalField('Pay Rate:', [validators.InputRequired(message=None)], default=58000)
    payType = SelectField(u'Pay Type:', choices=[('Salary','Salary'), ('W2', 'W2'), ('IC', 'IC')], default="Salary")

class PayCalculate(Form):
    client = SelectField(u'Client:', choices=[('Cetera Financial'), ('DiTech'), ('Fairview'), ('Farm Bureau'), ('Guide One'),('Hy-Vee'),('Integrated Behavior Health Network'),('Lifespace Communities'),('Lifetouch'), ('Merrill'), ('MoneyGram'), ('Nationstar'), ('Pioneer'), ('Hybrid'), ('Prime'), ('Principal Financial'), ('Securian'), ('State of Iowa'), ('State of Minnesota'), ('Unity Point Wellmark'), ('Wells Fargo')])
    billingRate = DecimalField('Billing Rate:', [validators.InputRequired(message=None)], default=55.00)
    targetMargin = DecimalField('Target Margin:', [validators.InputRequired(message=None)], default=26.86)
    payType = SelectField(u'Pay Type:', choices=[('Salary','Salary'), ('W2', 'W2'), ('IC', 'IC')], default="Salary")

##### Back End Decorators #####

@app.before_request
def before_request():
    g.user = current_user
    #print(current_user.id)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

##### Route Decorators #####

#////////////// Navigation /////////////////#

@app.route('/')
@app.route('/index')
def index():
    form = Login(request.form)
    return render_template('index.html', form=form)

def rando(type):
    if type == "IC":
        return .01

    elif type == "Salary":
        return .4

    elif type == "W2":
        return .2

@app.route('/calculate_margin')

#@login_required
def calculate_margin():

    form = MarginCalculate(request.form)
    billing_rate = form.billingRate.data
    pay_rate = form.payRate.data
    type = form.payType.data
    client = form.client.data
    VMS_fee = clients[client]['VMS_fee']  ####
    discount = clients[client]['discount'] ####

    net_billing_rate = billing_rate - (billing_rate * VMS_fee) - (billing_rate * discount)

    if type == "IC":
        loaded_cost = pay_rate * loaded_costs["IC"]

    elif type == "Salary":
        loaded_cost = pay_rate * loaded_costs["W2"]

    elif type == "W2":
        loaded_cost = (pay_rate / 2080) * loaded_costs["Salary"]

    margin_dollars = net_billing_rate / loaded_cost
    margin_percent = margin_dollars / loaded_cost

    return render_template('calculate_margin.html', form=form)

@app.route('/calculate_billing_rate', methods=['GET','POST'])
#@login_required
def calculate_billing_rate():
    form = BillingCalculate(request.form)

    pay_rate = form.payRate.data
    type = form.type.data
    target_margin = form.target_margin.data
    client = form.client.data
    VMS_fee = clients[client][VMS_fee]  ####
    discount = clients[client][discount] ####
    total_discounts_and_fees = VMS_fee + discount


    if type == "IC":
        loaded_cost = pay_rate * loaded_costs["IC"]

    elif type == "Salary":
        loaded_cost = pay_rate * loaded_costs["W2"]


    elif type == "W2":
        loaded_cost = (pay_rate / 2080) * loaded_costs["Salary"]


    if total_discounts_and_fees > 0:
        billing_rate = loaded_cost / (1 - (target_margin + total_discounts_and_fees))

    elif total_discounts_and_fees < 0:
        billing_rate = loaded_cost / (1 - target_margin)


    net_billing_rate = billing_rate - (billing_rate * VMS_fee) - (billing_rate * discount)
    margin_dollars = net_billing_rate - loaded_cost

    return render_template('calculate_billing_rate.html', form=form)

@app.route('/calculate_pay_rate', methods=['GET','POST'])
#@login_required
def calculate_pay_rate():

    form = PayCalculate(request.form)

    pay_rate = form.payRate.data
    type = form.type.data
    target_margin = form.target_margin.data
    client = form.client.data
    VMS_fee = clients[client][VMS_fee]  ####
    discount = clients[client][discount] ####


    #net_billing_rate = billing_rate - (billing_rate * VMS_fee) - (billing_rate * discount)

    if type == "IC":
        loaded_cost = pay_rate * loaded_costs["IC"]


    elif type == "Salary":
        loaded_cost = pay_rate * loaded_costs["W2"]

    elif type == "W2":
        loaded_cost = (pay_rate / 2080) * loaded_costs["Salary"]


    if type == "Salary":
        pay_rate = net_billing_rate * (1 - margin) / ((1 + rando(type)) * 2080)
    else:
        pay_rate = net_billing_rate * (1 - margin) / (1 + rando(type))

    margin_dollars = net_billing_rate - loaded_cost

    return render_template('calculate_pay_rate.html', form = form)

@app.route('/login', methods=['GET','POST'])
def login(*args):
    valid_registration=request.args.get('valid_registration')
    form = Login(request.form)
    if request.method == 'GET':
        if 'error' in locals():
            print(error)
            return render_template('login.html', error=error, form=form)
        error = False
        return render_template('login.html', form=form, valid_registration=valid_registration)
    username = "keyot"
    password = form.password.data
    print(User.query.filter_by(username=username).all())
    registered_user = User.query.filter_by(username=username).first()
    if registered_user.check_password(password) == False:
        print("here")
        flash('Password is invalid' , 'error')
        error = True
        return render_template('/login.html', error=error, form=form)

    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('account'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

######## App Startup ###########

if __name__ == '__main__':
    loaded_costs = {"W2" : 1.2, "Salary" : 1.4, "IC" : 1.01}

    clients = {
    'Cetera Financial' : {'VMS_fee' : 0, 'discount' : 0 },
    'DiTech' : {'VMS_fee' : 3.00, 'discount' : 0 },
    'Fairview' : {'VMS_fee' : 3.00, 'discount' : 0 },
    'Farm Bureau' : {'VMS_fee' : 0, 'discount' : 0 },
    'Guide One' : {'VMS_fee' : 0, 'discount' : 0 },
    'Hy-Vee' : {'VMS_fee' : 0, 'discount' : 0 },
    'Integrated Behavior Health Network' : {'VMS_fee' : 0, 'discount' : 0 },
    'Lifespace Communities' : {'VMS_fee' : 0, 'discount' : 0 },
    'Lifetouch' : {'VMS_fee' : 0, 'discount' : 0 },
    'Merrill' : {'VMS_fee' : 0, 'discount' : 0 },
    'MoneyGram' : {'VMS_fee' : 0, 'discount' : 0 },
    'Nationstar' : {'VMS_fee' : 2.95, 'discount' : 0 },
    'Pioneer Hybrid' : {'VMS_fee' : 0, 'discount' : 0 },
    'Prime' : {'VMS_fee' : 0, 'discount' : 3.00 },
    'Principal Financial' : {'VMS_fee' : 0, 'discount' : 0 },
    'Securian' : {'VMS_fee' : 0, 'discount' : 0 },
    'State of Iowa' : {'VMS_fee' : 0, 'discount' : 1.00 },
    'State of Minnesota' : {'VMS_fee' : 0, 'discount' : 1.00 },
    'Unity Point' : {'VMS_fee' : 0, 'discount' : 0 },
    'Wellmark' : {'VMS_fee' : 0, 'discount' : 0 },
    'Wells Fargo' : {'VMS_fee' : 2.00, 'discount' : 0 }
    
    }

    app.run()
