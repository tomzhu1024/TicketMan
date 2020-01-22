import configparser
import os
import re
import secrets

import pymysql
from flask import Flask, redirect, request, render_template, url_for, session, jsonify

import mysql_utils

app = Flask(__name__,
            static_url_path="/",
            static_folder="static")

app_setup = False
cfg_filename = 'app.ini'
admin_username = ''
admin_password = ''
cnx = None


# error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', message=e), 404


@app.errorhandler(403)
def access_forbidden(e):
    return render_template('403.html', message=e), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', message=e), 500


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    global app_setup, cnx, admin_username, admin_password
    if app_setup:
        return redirect(url_for('home'))
    if session.get('setup_step', 0) == 0:
        if request.method == 'GET':
            return render_template('setup1.html')
        elif request.method == 'POST':
            try:
                # try to connect to database
                cnx = {'host': request.form.get('address'),
                       'port': int(request.form.get('port')),
                       'user': request.form.get('username'),
                       'password': request.form.get('password'),
                       'autocommit': False,
                       'cursorclass': pymysql.cursors.DictCursor}
                # create database
                error = mysql_utils.create_database(cnx, request.form.get('database'))
                if error:
                    return render_template('setup1.html', error='xto create database: %s' % error)
                # select database
                cnx['database'] = request.form.get('database')
                # create tables
                errors = mysql_utils.create_tables(cnx)
                if errors:
                    return render_template('setup1.html',
                                           error=['Unable to create tables'] + errors)
                # no exception, save configuration
                cp = configparser.RawConfigParser()
                cp.add_section("database")
                cp.set("database", "address", request.form.get('address'))
                cp.set("database", "port", request.form.get('port'))
                cp.set("database", "username", request.form.get('username'))
                cp.set("database", "password", request.form.get('password'))
                cp.set("database", "database", request.form.get('database'))
                with open('app.ini', 'w') as fs:
                    cp.write(fs)
                # redirect to next step
                session['setup_step'] = 1
                return redirect(url_for('setup'))
            except Exception as ex:
                return render_template('setup1.html',
                                       error='Unable to connect to server and create the database: %s' % str(ex))
    elif session.get('setup_step') == 1:
        if request.method == 'GET':
            return render_template('setup2.html')
        elif request.method == 'POST':
            rules = {'username': r'^.+$',
                     'password': r'^[a-zA-Z0-9]{40}$'}
            if not is_strict_match(request.form, rules):
                return render_template('setup2.html', error='Invalid form data.')
            else:
                admin_username = request.form.get('username')
                admin_password = request.form.get('password')
                cp = configparser.RawConfigParser()
                # don't lost previous data
                cp.read('app.ini')
                cp.add_section("admin")
                cp.set("admin", "username", request.form.get('username'))
                cp.set("admin", "password", request.form.get('password'))
                with open('app.ini', 'w') as fs:
                    cp.write(fs)
                # redirect to next step
                session['setup_step'] = 2
                return redirect(url_for('setup'))
    elif session.get('setup_step') == 2:
        # change setup status
        app_setup = True
        return render_template('setup3.html')


@app.route('/')
def home():
    # home navigator
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        return redirect(url_for('manage_flight_airline_staff'))
    elif session.get('isLogin') and session.get('type') == 'admin':
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('search_flight_by_location'))


@app.route('/login/customer', methods=['GET', 'POST'])
def login_customer():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('loginCustomer.html')
    elif request.method == 'POST':
        rules = {'email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$',
                 'password': r'^[a-zA-Z0-9]{40}$'}
        if not is_strict_match(request.form, rules):
            return render_template('loginCustomer.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.login_customer(cnx=cnx,
                                             email=request.form.get('email'),
                                             password=request.form.get('password'))
            if rtn.get('login'):
                session['isLogin'] = True
                session['type'] = 'customer'
                session['email'] = rtn.get('email')
                session['displayName'] = rtn.get('name')
                session['displayType'] = 'Customer'
                return redirect(url_for('home'))
            else:
                return render_template('loginCustomer.html',
                                       error='Either your email is not recognized or your password is incorrect.')


@app.route('/login/bookingAgent', methods=['GET', 'POST'])
def login_booking_agent():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('loginBookingAgent.html')
    elif request.method == 'POST':
        rules = {'email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$',
                 'password': r'^[a-zA-Z0-9]{40}$'}
        if not is_strict_match(request.form, rules):
            return render_template('loginBookingAgent.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.login_booking_agent(cnx=cnx,
                                                  email=request.form.get('email'),
                                                  password=request.form.get('password'))
            if rtn.get('login'):
                session['isLogin'] = True
                session['type'] = 'booking_agent'
                session['email'] = rtn.get('email')
                session['displayName'] = rtn.get('email')
                session['displayType'] = 'Booking Agent'
                return redirect(url_for('home'))
            else:
                return render_template('loginBookingAgent.html',
                                       error='Either your email is not recognized or your password is incorrect.')


@app.route('/login/airlineStaff', methods=['GET', 'POST'])
def login_airline_staff():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('loginAirlineStaff.html')
    elif request.method == 'POST':
        rules = {'username': r'^.+$',
                 'password': r'^[a-zA-Z0-9]{40}$'}
        if not is_strict_match(request.form, rules):
            return render_template('loginAirlineStaff.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.login_airline_staff(cnx=cnx,
                                                  username=request.form.get('username'),
                                                  password=request.form.get('password'))
            if rtn.get('login'):
                session['isLogin'] = True
                session['type'] = 'airline_staff'
                session['username'] = rtn.get('username')
                session['displayName'] = rtn.get('display_name')
                session['displayType'] = 'Airline Staff'
                return redirect(url_for('home'))
            else:
                return render_template('loginAirlineStaff.html',
                                       error='Either your username is not recognized or your password is incorrect.')


@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('loginAdmin.html')
    elif request.method == 'POST':
        rules = {'username': r'^.+$',
                 'password': r'^[a-zA-Z0-9]{40}$'}
        if not is_strict_match(request.form, rules):
            return render_template('loginAdmin.html', error='Invalid form data.')
        elif request.form.get('username') == admin_username and request.form.get('password') == admin_password:
            session['isLogin'] = True
            session['type'] = 'admin'
            session['displayName'] = admin_username
            session['displayType'] = 'Admin'
            return redirect(url_for('home'))
        else:
            return render_template('loginAdmin.html',
                                   error='Either your username is not recognized or your password is incorrect.')


@app.route('/logout')
def logout():
    if not app_setup:
        return redirect(url_for('setup'))
    elif not session.get('isLogin'):
        return redirect(url_for('home'))
    else:
        session['isLogin'] = False
        return render_template('logout.html')


@app.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('registerCustomer.html')
    elif request.method == 'POST':
        rules = {'email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$',
                 'name': r'^.+$',
                 'password': r'^[a-zA-Z0-9]{40}$',
                 'building_number': r'^.+$',
                 'street': r'^.+$',
                 'city': r'^.+$',
                 'state': r'^.+$',
                 'phone_number': r'^\d+$',
                 'date_of_birth': r'^\d{4}\/\d{2}\/\d{2}$',
                 'passport_number': r'^.+$',
                 'passport_country': r'^.+$',
                 'passport_expiration': r'^\d{4}\/\d{2}\/\d{2}$'}
        if not is_strict_match(request.form, rules):
            return render_template('registerCustomer.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.register_customer(cnx=cnx,
                                                email=request.form.get('email'),
                                                name=request.form.get('name'),
                                                password=request.form.get('password'),
                                                building_number=request.form.get('building_number'),
                                                street=request.form.get('street'),
                                                city=request.form.get('city'),
                                                state=request.form.get('state'),
                                                phone_number=request.form.get('phone_number'),
                                                passport_number=request.form.get('passport_number'),
                                                passport_expiration=request.form.get('passport_expiration'),
                                                passport_country=request.form.get('passport_country'),
                                                date_of_birth=request.form.get('date_of_birth'))
            if rtn.get('exec'):
                return render_template('registerCustomer.html', success=True)
            else:
                return render_template('registerCustomer.html', error=rtn.get('error'))


@app.route('/register/bookingAgent', methods=['GET', 'POST'])
def register_booking_agent():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('registerBookingAgent.html')
    elif request.method == 'POST':
        rules = {'email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$',
                 'booking_agent_id': r'^\d+$',
                 'password': r'^[a-zA-Z0-9]{40}$'}
        if not is_strict_match(request.form, rules):
            return render_template('registerBookingAgent.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.register_booking_agent(cnx=cnx,
                                                     email=request.form.get('email'),
                                                     password=request.form.get('password'),
                                                     booking_agent_id=request.form.get('booking_agent_id'))
            if rtn.get('exec'):
                return render_template('registerBookingAgent.html', success=True)
            else:
                return render_template('registerBookingAgent.html', error=rtn.get('error'))


@app.route('/register/airlineStaff', methods=['GET', 'POST'])
def register_airline_staff():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin'):
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('registerAirlineStaff.html')
    elif request.method == 'POST':
        rules = {'username': r'^.+$',
                 'first_name': r'^.+$',
                 'last_name': r'^.+$',
                 'password': r'^[a-zA-Z0-9]{40}$',
                 'date_of_birth': r'^\d{4}\/\d{2}\/\d{2}$',
                 'airline_name': r'^.+$'}
        if not is_strict_match(request.form, rules):
            return render_template('registerAirlineStaff.html', error='Invalid form data.')
        else:
            rtn = mysql_utils.register_airline_staff(cnx=cnx,
                                                     username=request.form.get('username'),
                                                     password=request.form.get('password'),
                                                     first_name=request.form.get('first_name'),
                                                     last_name=request.form.get('last_name'),
                                                     date_of_birth=request.form.get('date_of_birth'),
                                                     airline_name=request.form.get('airline_name'))
            if rtn.get('exec'):
                return render_template('registerAirlineStaff.html', success=True)
            else:
                return render_template('registerAirlineStaff.html', error=rtn.get('error'))


def is_strict_match(form: dict, rules: dict):
    try:
        for key in form.keys():
            if key not in rules:
                return False
        for key in rules.keys():
            if key not in form:
                return False
        for name, regex in rules.items():
            if re.match(regex, form[name]) is None:
                return False
        return True
    except:
        # invalid form, don't fire
        return False


@app.route('/searchFlight/location', methods=['GET', 'POST'])
def search_flight_by_location():
    if not app_setup:
        return redirect(url_for('setup'))
    elif request.method == 'GET':
        return render_template('searchFlightByLocation.html')
    elif request.method == 'POST':
        rules = {
            'source': r'^.+$',
            'destination': r'^.+$',
            'date': r'^\d{4}\/\d{2}\/\d{2}$'
        }
        if not is_strict_match(request.form, rules):
            return render_template('searchFlightByLocation.html',
                                   error='Invalid search parameters. Please modify your search.')
        rtn = mysql_utils.search_flight_by_location(cnx=cnx,
                                                    source=request.form.get('source'),
                                                    destination=request.form.get('destination'),
                                                    date=request.form.get('date'))
        if rtn:
            head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn[0].keys()]
            if session.get('isLogin') and session.get('type') in ('customer', 'booking_agent'):
                data = [list(row.values()) + [
                    url_for('purchase_flight', airline_name=row.get('airline_name'), flight_num=row.get('flight_num'))]
                        for
                        row in rtn]
            else:
                data = [list(row.values()) + [''] for row in rtn]
            return render_template('searchFlightByLocation.html', head=head, data=data)
        else:
            return render_template('searchFlightByLocation.html',
                                   error="Your search found no result. Please modify your search.")


@app.route('/searchFlight/flightNum', methods=['GET', 'POST'])
def search_flight_by_flight_num():
    if not app_setup:
        return redirect(url_for('setup'))
    elif request.method == 'GET':
        return render_template('searchFlightByFlightNum.html')
    elif request.method == 'POST':
        rules = {
            'flight_num': r'^\d+$',
            'date': r'^\d{4}\/\d{2}\/\d{2}$'
        }
        if not is_strict_match(request.form, rules):
            return render_template('searchFlightByFlightNum.html',
                                   error='Invalid search parameters. Please modify your search.')
        rtn = mysql_utils.search_flight_by_flight_num(cnx=cnx,
                                                      flight_num=request.form.get('flight_num'),
                                                      date=request.form.get('date'))
        if rtn:
            head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn[0].keys()]
            if session.get('isLogin'):
                data = [list(row.values()) + [
                    url_for('purchase_flight', airline_name=row.get('airline_name'), flight_num=row.get('flight_num'))]
                        for
                        row in rtn]
            else:
                data = [list(row.values()) + [''] for row in rtn]
            return render_template('searchFlightByFlightNum.html', head=head, data=data)
        else:
            return render_template('searchFlightByFlightNum.html',
                                   error="Your search found no result. Please modify your search.")


@app.route('/purchaseFlight/<airline_name>/<flight_num>', methods=['POST'])
def purchase_flight(airline_name, flight_num):
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') in ('customer', 'booking_agent'):
        if session.get('type') == 'customer':
            rtn = mysql_utils.purchase_flight(cnx=cnx,
                                              customer_email=session.get('email'),
                                              airline_name=airline_name,
                                              flight_num=flight_num)
        else:  # booking_agent
            rules = {'customer_email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$'}
            if not is_strict_match(request.form, rules):
                return render_template('searchFlightByLocation.html', error="Customer email address is invalid.")
            rtn = mysql_utils.purchase_flight(cnx=cnx,
                                              customer_email=request.form.get('customer_email'),
                                              airline_name=airline_name,
                                              flight_num=flight_num,
                                              booking_agent_email=session.get('email'))
        if rtn.get('exec'):
            return render_template('searchFlightByLocation.html', success=True)
        else:
            return render_template('searchFlightByLocation.html', error=rtn.get('error'))
    else:
        return redirect(url_for('home'))


@app.route('/viewMyFlight', methods=['GET', 'POST'])
def view_my_flight():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') in ('customer', 'booking_agent'):
        if session.get('type') == 'customer':
            rtn = mysql_utils.view_my_flight_customer(cnx=cnx,
                                                      email=session.get('email'),
                                                      location=request.form.get('location'),
                                                      start_date=request.form.get('start_date'),
                                                      end_date=request.form.get('end_date'))
        else:
            rtn = mysql_utils.view_my_flight_booking_agent(
                cnx=cnx,
                email=session.get('email'),
                location=request.form.get('location'),
                start_date=request.form.get('start_date'),
                end_date=request.form.get('end_date'))
        if rtn:
            head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn[0].keys()]
            data = [list(row.values()) + [''] for row in rtn]
            return render_template('viewMyFlight.html', head=head, data=data)
        else:
            return render_template('viewMyFlight.html', error='Your search found no result. Please modify your search.')
    else:
        return redirect(url_for('home'))


@app.route('/trackMySpending', methods=['GET', 'POST'])
def track_my_spending():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'customer':
        rtn = mysql_utils.track_my_spending(cnx=cnx,
                                            email=session.get('email'),
                                            start_date=request.form.get('start_date'),
                                            end_date=request.form.get('end_date'))
        if rtn:
            return render_template('trackMySpending.html', statistic=rtn.get('total'),
                                   barchart_x=str(list(rtn.get('detail').keys())),
                                   barchart_data=str(list(rtn.get('detail').values())))
        else:
            return render_template('trackMySpending.html', error='Unable to display the spending statistics.')
    else:
        return redirect(url_for('home'))


@app.route('/viewMyCommission', methods=['GET', 'POST'])
def view_my_commission():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'booking_agent':
        rtn = mysql_utils.view_my_commission(cnx=cnx,
                                             email=session.get('email'),
                                             start_date=request.form.get('start_date'),
                                             end_date=request.form.get('end_date'))
        if rtn:
            return render_template('viewMyCommission.html',
                                   commission=rtn.get('commission'),
                                   flight=rtn.get('flight'),
                                   average=rtn.get('average'))
        else:
            return render_template('viewMyCommission.html', error='Unable to display the commission statistics.')
    else:
        return redirect(url_for('home'))


@app.route('/viewTopCustomers')
def view_top_customers():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'booking_agent':
        rtn = mysql_utils.view_top_customers(cnx=cnx,
                                             email=session.get('email'))
        if rtn:
            return render_template('viewTopCustomers.html',
                                   commission_x=list(rtn.get('commission').keys()),
                                   commission_data=list(rtn.get('commission').values()),
                                   ticket_x=list(rtn.get('ticket').keys()),
                                   ticket_data=list(rtn.get('ticket').values()))
        else:
            return render_template('viewTopCustomers.html', error='Unable to display the top customer statistics.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/manageFlight', methods=['GET', 'POST'])
def manage_flight_airline_staff():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.view_my_flight_airline_staff(cnx=cnx,
                                                       username=session.get('username'),
                                                       location=request.form.get('location'),
                                                       start_date=request.form.get('start_date'),
                                                       end_date=request.form.get('end_date'))
        if rtn:
            head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn[0].keys()]
            data = [list(row.values()) + [
                url_for('view_passengers', airline_name=row.get('airline_name'), flight_num=row.get('flight_num')),
                url_for('update_status', airline_name=row.get('airline_name'), flight_num=row.get('flight_num'))]
                    for
                    row in rtn]
            return render_template('manageMyFlight.html', head=head, data=data)
        else:
            return render_template('manageMyFlight.html', error='Unable to display flight data.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/viewPassengers/<airline_name>/<flight_num>')
def view_passengers(airline_name, flight_num):
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.view_passengers(cnx=cnx,
                                          airline_staff_username=session.get('username'),
                                          airline_name=airline_name,
                                          flight_num=flight_num)
        if rtn:
            return render_template('viewPassengers.html', airline_name=airline_name, flight_num=flight_num, data=rtn)
        else:
            return render_template('viewPassengers.html', airline_name=airline_name, flight_num=flight_num,
                                   error='Either you have no permission to view this flight information or your query returned nothing.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/addFlight', methods=['POST'])
def add_flight():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rules = {'departure_airport': r'^.+$',
                 'departure_time': r'^\d{3,4}\/\d{2}\/\d{2} \d{1,2}\:\d{2}$',
                 'arrival_airport': r'^.+$',
                 'arrival_time': r'^\d{3,4}\/\d{2}\/\d{2} \d{1,2}\:\d{2}$',
                 'flight_num': r'^\d+$',
                 'price': r'^[0-9|.]+$',
                 'status': r'^.+$',
                 'airplane_id': r'^\d+$'}
        if not is_strict_match(request.form, rules):
            return render_template('addFlight.html',
                                   error='Unable to add flight due to invalid form data.')
        else:
            rtn = mysql_utils.add_flight(cnx=cnx,
                                         airline_staff_username=session.get('username'),
                                         flight_num=request.form.get('flight_num'),
                                         departure_airport=request.form.get('departure_airport'),
                                         departure_time=request.form.get('departure_time'),
                                         arrival_airport=request.form.get('arrival_airport'),
                                         arrival_time=request.form.get('arrival_time'),
                                         price=request.form.get('price'),
                                         status=request.form.get('status'),
                                         airplane_id=request.form.get('airplane_id'))
            if rtn.get('exec'):
                return render_template('addFlight.html', success='You have added the flight.')
            else:
                return render_template('addFlight.html',
                                       error='Unable to add flight: %s' % rtn.get('error'))
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/updateStatus/<airline_name>/<flight_num>', methods=['POST'])
def update_status(airline_name, flight_num):
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        if not request.form.get('new_status'):
            return render_template('updateStatus.html', error='New status cannot be empty.')
        rtn = mysql_utils.update_status(cnx=cnx,
                                        airline_staff_username=session.get('username'),
                                        airline_name=airline_name,
                                        flight_num=flight_num,
                                        new_status=request.form.get('new_status'))
        if rtn.get('exec'):
            return render_template('updateStatus.html', success='You have updated the flight status.')
        else:
            return render_template('updateStatus.html',
                                   error='Unable to update the flight status: %s' % rtn.get('error'))
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/addAirplane', methods=['GET', 'POST'])
def add_airplane():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        if request.method == 'GET':
            rtn_query = mysql_utils.get_airplane(cnx=cnx,
                                                 airline_staff_username=session.get('username'))
            if rtn_query:
                head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn_query[0].keys()]
                data = [list(row.values()) for row in rtn_query]
                return render_template('addAirplane.html', head=head, data=data)
            else:  # nothing returned
                return render_template('addAirplane.html', error='There is no airplane information to display.')
        elif request.method == 'POST':
            rules = {'airplane_id': r'^\d+$',
                     'seats': r'^\d+$'}
            if not is_strict_match(request.form, rules):
                return render_template('addAirplane.html', error='Unable to add airplane due to invalid form data.')
            rtn_exec = mysql_utils.add_airplane(cnx=cnx,
                                                airline_staff_username=session.get('username'),
                                                airplane_id=request.form.get('airplane_id'),
                                                seats=request.form.get('seats'))
            if rtn_exec.get('exec'):
                return render_template('addAirplane.html', success=True)
            else:
                return render_template('addAirplane.html', error='Unable to add airplane: %s' % rtn_exec.get('error'))
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/addAirport', methods=['GET', 'POST'])
def add_airport():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        if request.method == 'GET':
            rtn_query = mysql_utils.get_airport(cnx=cnx)
            if rtn_query:
                head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn_query[0].keys()]
                data = [list(row.values()) for row in rtn_query]
                return render_template('addAirport.html', head=head, data=data)
            else:  # nothing returned
                return render_template('addAirport.html', error='There is no airport information to display.')
        elif request.method == 'POST':
            rules = {'airport_name': r'^.+$',
                     'airport_city': r'^.+$'}
            if not is_strict_match(request.form, rules):
                return render_template('addAirport.html', error='Unable to add airport due to invalid form data.')
            rtn_exec = mysql_utils.add_airport(cnx=cnx,
                                               airport_name=request.form.get('airport_name'),
                                               airport_city=request.form.get('airport_city'))
            if rtn_exec.get('exec'):
                return render_template('addAirport.html', success=True)
            else:
                return render_template('addAirport.html', error='Unable to add airport: %s' % rtn_exec.get('error'))
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/viewTopBookingAgents')
def view_top_booking_agents():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.view_top_booking_agents(cnx=cnx,
                                                  airline_staff_username=session.get('username'))
        if rtn.get('ticket_month'):
            htm = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn.get('ticket_month')[0].keys()]
            dtm = [list(row.values()) for row in rtn.get('ticket_month')]
            hty = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn.get('ticket_year')[0].keys()]
            dty = [list(row.values()) for row in rtn.get('ticket_year')]
            hc = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn.get('commission')[0].keys()]
            dc = [list(row.values()) for row in rtn.get('commission')]
            return render_template('viewTopBookingAgents.html',
                                   htm=htm, dtm=dtm,
                                   hty=hty, dty=dty,
                                   hc=hc, dc=dc)
        else:
            return render_template('viewTopBookingAgents.html', error='Unable to display top booking agents data.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/viewFrequentCustomer')
def view_frequent_customer():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.view_frequent_customer(cnx=cnx,
                                                 airline_staff_username=session.get('username'))
        if rtn:
            return render_template('viewFrequentCustomer.html', email=rtn)
        else:
            return render_template('viewFrequentCustomer.html',
                                   error='Unable to display the most frequent customer data.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/viewCustomerFlightHistory', methods=['GET', 'POST'])
def view_customer_flight_history():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        if request.method == 'GET':
            return render_template('viewCustomerFlightHistory.html')
        elif request.method == 'POST':
            rules = {'customer_email': r'^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$'}
            if not is_strict_match(request.form, rules):
                return render_template('viewCustomerFlightHistory.html',
                                       error='Unable to display history due to invalid email address.')
            rtn = mysql_utils.view_customer_flight_history(cnx=cnx,
                                                           airline_staff_username=session.get('username'),
                                                           customer_email=request.form.get('customer_email'))
            if rtn:
                head = [' '.join(w.capitalize() for w in s.split('_')) for s in rtn[0].keys()]
                data = [list(row.values()) for row in rtn]
                return render_template('viewCustomerFlightHistory.html', head=head, data=data)
            else:
                return render_template('viewCustomerFlightHistory.html',
                                       error='Unable to display customer flight history.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/totalTicketSold', methods=['GET', 'POST'])
def total_ticket_sold():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn_my = mysql_utils.total_ticket(cnx=cnx,
                                          airline_staff_username=session.get('username'))
        rtn_g = mysql_utils.total_ticket_sold(cnx=cnx,
                                              airline_staff_username=session.get('username'),
                                              start_date=request.form.get('start_date'),
                                              end_date=request.form.get('end_date'))
        if rtn_my or rtn_g:
            return render_template('totalTicketSold.html', barchart_x=str(list(rtn_g.keys())),
                                   barchart_data=str(list(rtn_g.values())), month=rtn_my.get('last_month'),
                                   year=rtn_my.get('last_year'))
        else:
            return render_template('totalTicketSold.html', error='Unable to display total ticket sold data.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/compareRevenue')
def compare_revenue():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.compare_revenue(cnx=cnx,
                                          airline_staff_username=session.get('username'))
        if rtn:
            return render_template('compareRevenue.html',
                                   md=rtn.get('md'),
                                   mi=rtn.get('mi'),
                                   yd=rtn.get('yd'),
                                   yi=rtn.get('yi'))
        else:
            return render_template('compareRevenue.html', error='Unable to display revenue data.')
    else:
        return redirect(url_for('home'))


@app.route('/airlineStaff/viewTopDestinations')
def view_top_destinations():
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'airline_staff':
        rtn = mysql_utils.view_top_destinations(cnx=cnx,
                                                airline_staff_username=session.get('username'))
        if rtn.get('month'):
            return render_template('viewTopDestinations.html', month=rtn.get('month'), year=rtn.get('year'))
        else:
            return render_template('viewTopDestinations.html', error='Unable to display top destinations data.')
    else:
        return redirect(url_for('home'))


# general api
@app.route('/getAllAirlines', methods=['POST'])
def get_all_airlines():
    if app_setup:
        return jsonify(mysql_utils.get_all_airlines(cnx=cnx))
    else:
        return jsonify([])


@app.route('/getAllCitiesAndAirports', methods=['POST'])
def get_all_cities_and_airports():
    if app_setup:
        return jsonify(mysql_utils.get_all_cities_and_airports(cnx=cnx))
    else:
        return jsonify([])


@app.route('/getAllCustomerEmails', methods=['POST'])
def get_all_customer_emails():
    if app_setup and session.get('isLogin') and session.get('type') in ('booking_agent', 'airline_staff'):
        return jsonify(mysql_utils.get_all_customer_emails(cnx=cnx))
    else:
        return jsonify([])


@app.route('/getAllAirports', methods=['POST'])
def get_all_airports():
    if app_setup and session.get('isLogin') and session.get('type') == 'airline_staff':
        return jsonify(mysql_utils.get_all_airports(cnx=cnx))
    else:
        return jsonify([])


@app.route('/getAllAirplaneId', methods=['POST'])
def get_all_airplane_id():
    if app_setup and session.get('isLogin') and session.get('type') == 'airline_staff':
        return jsonify(mysql_utils.get_all_airplane_id(cnx=cnx))
    else:
        return jsonify([])


# admin management
@app.route('/adminPanel', methods=['GET', 'POST'])
def admin_panel():
    global app_setup, cnx
    if not app_setup:
        return redirect(url_for('setup'))
    elif session.get('isLogin') and session.get('type') == 'admin':
        if request.method == 'GET':
            return render_template('adminPanel.html')
        elif request.method == 'POST':
            if request.form.get('action') == 'import_test_data':
                errors = mysql_utils.import_test_data(cnx=cnx)
                if not errors:
                    return render_template('adminPanelMsg.html', success='Test data have been imported.')
                else:
                    return render_template('adminPanelMsg.html', error=errors)
            elif request.form.get('action') == 'purge_all_data':
                try:
                    os.remove('app.ini')
                    conn = pymysql.connect(**cnx)
                    cursor = conn.cursor()
                    cursor.execute("DROP DATABASE %s" % conn.escape_string(cnx.get('database')))
                    cursor.close()
                    conn.close()
                    # re-generate secret key to reset all sessions
                    app.secret_key = secrets.token_urlsafe(16)
                    app_setup = False
                    cnx = None
                    return redirect(url_for('home'))
                except Exception as ex:
                    return render_template('adminPanelMsg.html', error=[str(ex)])
    else:
        return redirect(url_for('home'))


if __name__ == '__main__':
    # detect config file
    if os.path.exists(cfg_filename):
        try:
            cp = configparser.RawConfigParser()
            cp.read(cfg_filename)
            db_address = cp.get("database", "address")
            db_port = int(cp.get("database", "port"))
            db_username = cp.get("database", "username")
            db_password = cp.get("database", "password")
            db_database = cp.get("database", "database")
            admin_username = cp.get("admin", "username")
            admin_password = cp.get("admin", "password")
            app_setup = True
            cnx = {'host': db_address,
                   'port': db_port,
                   'user': db_username,
                   'password': db_password,
                   'database': db_database,
                   'autocommit': False,
                   'cursorclass': pymysql.cursors.DictCursor}
        except configparser.Error:
            pass
    # generate secret key for session
    app.secret_key = secrets.token_urlsafe(16)
    app.run(host="127.0.0.1",
            port=5000,
            debug=False)
