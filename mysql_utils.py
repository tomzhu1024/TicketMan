import logging

import pymysql

from colored_logger import ColoredLogger

# run when being imported as a module
# initiate logger
# for debug
logging.setLoggerClass(ColoredLogger)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# setup functions
# implemented already, don't modify
def create_database(cnx, db_name):
    error = None
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("drop database if exists %s" % cnx.escape_string(db_name))
        cursor.execute("create database %s" % cnx.escape_string(db_name))
        cnx.commit()
        cursor.close()
        cnx.close()
    except Exception as ex:
        logger.error(str(ex))
        error = str(ex)
    return error


def create_tables(cnx):
    cnx = pymysql.connect(**cnx)
    cursor = cnx.cursor()
    errors = []
    with open('create_tables.sql', 'r') as fs:
        sql_commands = fs.read().split(';')
        for cmd in sql_commands:
            if cmd:
                try:
                    cursor.execute(cmd)
                except Exception as ex:
                    logger.error(str(ex))
                    errors.append(str(ex))
    cnx.commit()
    cursor.close()
    cnx.close()
    return errors


# helper function
def _str_datetime(val):
    return val.strftime('%Y') + '/' + val.strftime('%m') + '/' + val.strftime(
        '%d') + ' ' + val.strftime('%H') + ':' + val.strftime('%M') + ':' + val.strftime('%S')


# login functions
# exec means whether sql executed successfully, if not, error means error message from sql
# login means whether user validation passed
def login_customer(cnx, email, password):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select count(distinct email) as number from customer where email = %s and password = %s",
                       (email, password))
        u = cursor.fetchall()[0]['number']
        if u > 0:
            cursor.execute("select name from customer where email = %s", (email,))
            name = cursor.fetchall()[0]['name']
            return {
                'login': True,
                'email': email,
                'name': name
            }
        elif u == 0:
            return {
                'login': False
            }
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {
            'login': False
        }
    finally:
        cursor.close()
        cnx.close()


def login_booking_agent(cnx, email, password):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select count(distinct email) as number from booking_agent where email = %s and password = %s",
                       (email, password))
        u = cursor.fetchall()[0]['number']
        if u > 0:
            return {
                'login': True,
                'email': email
            }
        elif u == 0:
            return {
                'login': False
            }
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {
            'login': False
        }
    finally:
        cursor.close()
        cnx.close()


def login_airline_staff(cnx, username, password):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute(
            "select count(distinct username) as number, CONCAT(first_name,' ',last_name) AS `name` from airline_staff where username = %s and password = %s",
            (username, password))
        u = cursor.fetchall()[0]
        display_name = u.get('name')
        u = u.get('number')
        if u > 0:
            return {
                'login': True,
                'username': username,
                'display_name': display_name
            }
        elif u == 0:
            return {
                'login': False
            }
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {
            'login': False
        }
    finally:
        cursor.close()
        cnx.close()


# register functions
# exec means whether sql executed successfully, if not, error means error message from sql
# error means register failed, no need to add more properties
def register_customer(cnx, email, name, password, building_number, street, city, state, phone_number, passport_number,
                      passport_expiration, passport_country, date_of_birth):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("insert into `customer` values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
            email, name, password, building_number, street, city, state, phone_number, passport_number,
            passport_expiration, passport_country, date_of_birth))
        cnx.commit()
        return {
            'exec': True
        }
    except pymysql.Error as ex:
        logger.error(str(ex))
        cnx.rollback()
        return {
            'exec': False,
            'error': str(ex)
        }
    finally:
        cursor.close()
        cnx.close()


def register_booking_agent(cnx, email, password, booking_agent_id):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("insert into booking_agent values(%s,%s,%s)", (email, password, booking_agent_id))
        cnx.commit()
        return {
            'exec': True
        }
    except pymysql.Error as ex:
        logger.error(str(ex))
        cnx.rollback()
        return {
            'exec': False,
            'error': str(ex)
        }
    finally:
        cursor.close()
        cnx.close()


def register_airline_staff(cnx, username, password, first_name, last_name, date_of_birth, airline_name):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("insert into airline_staff values(%s,%s,%s,%s,%s,%s)",
                       (username, password, first_name, last_name, date_of_birth, airline_name))
        cnx.commit()
        return {
            'exec': True
        }
    except pymysql.Error as ex:
        logger.error(str(ex))
        cnx.rollback()
        return {
            'exec': False,
            'error': str(ex)
        }
    finally:
        cursor.close()
        cnx.close()


# helper function
# Additional functions for some of the following functions
def _all_cities(mtplx_cnx):
    try:
        cursor = mtplx_cnx.cursor()
        cursor.execute("select distinct airport_city from airport")
        return [name['airport_city'] for name in cursor.fetchall()]
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()


# return empty list if nothing is found or error occurred
# normally return list of dict
def search_flight_by_location(cnx, source, destination, date):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        command = "select * from flight where status = 'upcoming' and %s between date_sub(departure_time, INTERVAL 1 DAY) and arrival_time "
        if source in _all_cities(cnx):
            command += "and departure_airport in (select airport_name from airport where airport_city = %s) "
        else:
            command += "and departure_airport = %s "
        if destination in _all_cities(cnx):
            command += "and arrival_airport in (select airport_name from airport where airport_city = %s)"
        else:
            command += "and arrival_airport = %s"
        cursor.execute(command, (date, source, destination))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            dic['departure_time'] = _str_datetime(dic['departure_time'])
            dic['arrival_time'] = _str_datetime(dic['arrival_time'])
            dic['price'] = int(dic['price'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()
        cnx.close()


def search_flight_by_flight_num(cnx, flight_num, date):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute(
            "select * from flight where flight_num = %s and %s between date_sub(departure_time,interval 1 day) and arrival_time",
            (flight_num, date))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            dic['departure_time'] = _str_datetime(dic['departure_time'])
            dic['arrival_time'] = _str_datetime(dic['arrival_time'])
            dic['price'] = int(dic['price'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


# helper function
# Needed in purchase_flight function
def _check_airplane_full(mtplx_cnx, flight_number, airline):
    try:
        cursor = mtplx_cnx.cursor()
        cursor.execute("select seats from flight natural join airplane where airline_name = %s and flight_num = %s",
                       (airline, flight_number))
        outcome = cursor.fetchall()
        if len(outcome) > 0:
            total = int(outcome[0]['seats'])
        else:
            return None
        cursor.execute("select count(ticket_id) as count from ticket where airline_name = %s and flight_num = %s",
                       (airline, flight_number))
        occupied = int(cursor.fetchall()[0]['count'])
        if total > occupied:
            return "available"
        else:
            return "full"
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()


# helper function
def _generate_ticket(mtplx_cnx, ticket_id, airline, flight_number):
    try:
        check = _check_airplane_full(mtplx_cnx, flight_number, airline)
        cursor = mtplx_cnx.cursor()
        if check == 'full':
            return 'full'
        elif check == 'available':
            cursor.execute("insert into ticket values (%s,%s,%s)", (ticket_id, airline, flight_number))
            mtplx_cnx.commit()
            return 'successfully inserted'
        else:
            return check
    except pymysql.Error as ex:
        logger.error(str(ex))
        mtplx_cnx.rollback()
        return str(ex)
    finally:
        cursor.close()


def purchase_flight(cnx, customer_email, airline_name, flight_num, booking_agent_email=None):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select max(ticket_id) as max from ticket")
        max_ticket_id = cursor.fetchall()
        if len(max_ticket_id) > 0 and max_ticket_id[0]['max'] != None:
            ticket_id = max_ticket_id[0]['max'] + 1
        else:
            ticket_id = 1
        ticket = _generate_ticket(cnx, ticket_id, airline_name, flight_num)
        if ticket == 'successfully inserted':
            if not booking_agent_email:
                cursor = cnx.cursor()
                cursor.execute("insert into purchases values(%s,%s,null,current_date)", (ticket_id, customer_email))
                cnx.commit()
                return {'exec': True}
            else:
                cursor = cnx.cursor()
                cursor.execute("select booking_agent_id from booking_agent where email = %s", (booking_agent_email,))
                dic = cursor.fetchall()
                if len(dic) > 0:
                    booking_agent_id = dic[0]['booking_agent_id']
                else:
                    return {'exec': False,
                            'error': 'no such booking agent'}
                cursor.execute("insert into purchases values(%s,%s,%s,current_date)",
                               (ticket_id, customer_email, booking_agent_id))
                cnx.commit()
                return {'exec': True}
        elif ticket == 'full':
            return {'exec': False,
                    'error': 'this flight is full'}
        else:
            return {'exec': False,
                    'error': ticket}
    except pymysql.Error as ex:
        logger.error(str(ex))
        cnx.rollback()
        return {'exec': False,
                'error': str(ex)}
    finally:
        cursor.close()
        cnx.close()


def view_my_flight_customer(cnx, email, location, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cities = _all_cities(cnx)
        cursor = cnx.cursor()
        if not location and not start_date and not end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE status = 'upcoming' and (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s)",
                (email,))
        elif location and not start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s))",
                    (email, location, location))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport = %s or arrival_airport = %s)",
                    (email, location, location))
        elif not location and start_date and not end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and departure_time >= %s",
                (email, start_date))
        elif not location and not start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and arrival_time <= %s",
                (email, end_date))
        elif location and start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s",
                    (email, location, location, start_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s",
                    (email, location, location, start_date))
        elif location and not start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and arrival_time <= %s",
                    (email, location, location, end_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport = %s or arrival_airport = %s) and arrival_time <= %s",
                    (email, location, location, end_date))
        elif not location and start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and %s <= departure_time and arrival_time <= %s ",
                (email, start_date, end_date))
        elif location and start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s and arrival_time <= %s",
                    (email, location, location, start_date, end_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases where customer_email = %s) and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s and arrival_time <= %s",
                    (email, location, location, start_date, end_date))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            dic['departure_time'] = _str_datetime(dic['departure_time'])
            dic['arrival_time'] = _str_datetime(dic['arrival_time'])
            dic['price'] = int(dic['price'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


# todo: add column of customer email
def view_my_flight_booking_agent(cnx, email, location, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cities = _all_cities(cnx)
        cursor = cnx.cursor()
        if not location and not start_date and not end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE status = 'upcoming' and (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s)",
                (email,))
        elif location and not start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport in (select all airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s))",
                    (email, location, location))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport = %s or arrival_airport = %s)",
                    (email, location, location))
        elif not location and start_date and not end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and departure_time >= %s",
                (email, start_date))
        elif not location and not start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and arrival_time <= %s",
                (email, end_date))
        elif location and start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s",
                    (email, location, location, start_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s",
                    (email, location, location, start_date))
        elif location and not start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and arrival_time <= %s",
                    (email, location, location, end_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport = %s or arrival_airport = %s) and arrival_time <= %s",
                    (email, location, location, end_date))
        elif not location and start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and %s <= departure_time and arrival_time <= %s ",
                (email, start_date, end_date))
        elif location and start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s and arrival_time <= %s",
                    (email, location, location, start_date, end_date))
            else:
                cursor.execute(
                    "select * from flight where (flight_num,airline_name) in (select flight_num,airline_name from ticket natural join purchases natural join booking_agent where email = %s) and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s and arrival_time <= %s",
                    (email, location, location, start_date, end_date))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            dic['departure_time'] = _str_datetime(dic['departure_time'])
            dic['arrival_time'] = _str_datetime(dic['arrival_time'])
            dic['price'] = int(dic['price'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def view_my_flight_airline_staff(cnx, username, location, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cities = _all_cities(cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (username,))
        result = cursor.fetchall()
        if not result or result[0]['airline_name'] == None:
            return []
        airline_name = result[0]['airline_name']
        if not location and not start_date and not end_date:
            cursor.execute("SELECT * FROM flight WHERE status = 'upcoming' and airline_name = %s", (airline_name,))
        elif location and not start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport in (select all airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s))",
                    (airline_name, location, location))
            else:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport = %s or arrival_airport = %s)",
                    (airline_name, location, location))
        elif not location and start_date and not end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE airline_name = %s and departure_time >= %s",
                (airline_name, start_date))
        elif not location and not start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE airline_name = %s and arrival_time <= %s",
                (airline_name, end_date))
        elif location and start_date and not end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s",
                    (airline_name, location, location, start_date))
            else:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s",
                    (airline_name, location, location, start_date))
        elif location and not start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and arrival_time <= %s",
                    (airline_name, location, location, end_date))
            else:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport = %s or arrival_airport = %s) and arrival_time <= %s",
                    (airline_name, location, location, end_date))
        elif not location and start_date and end_date:
            cursor.execute(
                "SELECT * FROM flight WHERE airline_name = %s and %s <= departure_time and arrival_time <= %s ",
                (airline_name, start_date, end_date))
        elif location and start_date and end_date:
            if location in cities:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport in (select airport_name from airport where airport_city = %s) or arrival_airport in (select airport_name from airport where airport_city = %s)) and departure_time >= %s and arrival_time <= %s",
                    (airline_name, location, location, start_date, end_date))
            else:
                cursor.execute(
                    "select * from flight where airline_name = %s and (departure_airport = %s or arrival_airport = %s) and departure_time >= %s and arrival_time <= %s",
                    (airline_name, location, location, start_date, end_date))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            dic['departure_time'] = _str_datetime(dic['departure_time'])
            dic['arrival_time'] = _str_datetime(dic['arrival_time'])
            dic['price'] = int(dic['price'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


# if start and end are none, then it means last 6 months
def track_my_spending(cnx, email, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        if not start_date and not end_date:
            cursor.execute(
                "select sum(price) as total_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date > date_sub(current_date,interval 6 month)",
                (email,))
        elif not start_date and end_date:
            cursor.execute(
                "select sum(price) as total_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date <= %s",
                (email, end_date))
        elif start_date and not end_date:
            cursor.execute(
                "select sum(price) as total_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date >= %s",
                (email, start_date))
        elif start_date and end_date:
            cursor.execute(
                "select sum(price) as total_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date between %s and %s",
                (email, start_date, end_date))
        result = cursor.fetchall()
        if result[0]['total_spending'] and len(result) > 0:
            total = int(result[0]['total_spending'])
        else:
            total = 0
        if not start_date and not end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,sum(price) as monthly_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date >= date_sub(current_date,interval 6 month) group by month",
                (email,))
        elif not start_date and end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,sum(price) as monthly_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date <= %s group by month",
                (email, end_date))
        elif start_date and not end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,sum(price) as monthly_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date >= %s group by month",
                (email, start_date))
        elif start_date and end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,sum(price) as monthly_spending from flight natural join ticket natural join purchases where customer_email = %s and purchase_date between %s and %s group by month",
                (email, start_date, end_date))
        detail = {}
        dic = cursor.fetchone()
        while dic != None:
            detail[str(dic['month'])] = int(dic['monthly_spending'])
            dic = cursor.fetchone()
        return {'total': total, 'detail': detail}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


def view_my_commission(cnx, email, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        if not start_date and not end_date:
            cursor.execute(
                "select sum(price)/10 as total_commission from flight natural join ticket natural join purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s)",
                (email,))
        elif start_date and not end_date:
            cursor.execute(
                "select sum(price)/10 as total_commission from flight natural join ticket natural join purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date >= %s",
                (email, start_date))
        elif not start_date and end_date:
            cursor.execute(
                "select sum(price)/10 as total_commission from flight natural join ticket natural join purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date <= %s",
                (email, end_date))
        elif start_date and end_date:
            cursor.execute(
                "select sum(price)/10 as total_commission from flight natural join ticket natural join purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date between %s and %s",
                (email, start_date, end_date))
        list_of_dic = cursor.fetchall()
        if list_of_dic[0]['total_commission'] is not None:
            commission = int(list_of_dic[0]['total_commission'])
        else:
            commission = 0
        if not start_date and not end_date:
            cursor.execute(
                "select count(distinct ticket_id) as num from purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s)",
                (email,))
        elif start_date and not end_date:
            cursor.execute(
                "select count(distinct ticket_id) as num from purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date >= %s",
                (email, start_date))
        elif not start_date and end_date:
            cursor.execute(
                "select count(distinct ticket_id) as num from purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date <= %s",
                (email, end_date))
        elif start_date and end_date:
            cursor.execute(
                "select count(distinct ticket_id) as num from purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date between %s and %s",
                (email, start_date, end_date))
        flight = int(cursor.fetchall()[0]['num'])
        if flight != 0:
            return {'commission': commission, 'flight': flight, 'average': '%.2f' % (commission / flight)}
        else:
            return {'commission': 0, 'flight': 0, 'average': 0}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


def view_top_customers(cnx, email):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        command = "select customer_email,count(distinct ticket_id) as number_of_ticket from purchases where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date between date_sub(CURRENT_DATE,interval 6 month) and CURRENT_DATE group by customer_email order by number_of_ticket DESC"
        cursor.execute(command, (email,))
        dic = cursor.fetchone()
        ticket = {}
        while dic is not None and len(ticket) < 5:
            ticket[dic['customer_email']] = int(dic['number_of_ticket'])
            dic = cursor.fetchone()
        command = "select customer_email,sum(price)/10 as commission from purchases natural join ticket natural join flight where booking_agent_id in (select booking_agent_id from booking_agent where email = %s) and purchase_date between date_sub(CURRENT_DATE,interval 6 month) and CURRENT_DATE group by customer_email order by commission DESC"
        cursor.execute(command, (email,))
        dic = cursor.fetchone()
        commission = {}
        while dic is not None and len(commission) < 5:
            commission[dic['customer_email']] = int(dic['commission'])
            dic = cursor.fetchone()
        return {'commission': commission, 'ticket': ticket}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()
        cnx.close()


def view_passengers(cnx, airline_staff_username, airline_name, flight_num):
    # must check if the airline really has permission to view passenger
    # if airline_staff_username --> airline_name doesn't match the airline_name, then return empty list
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        outcome = cursor.fetchall()
        if len(outcome) > 0:
            staff_airline = outcome[0]['airline_name']
        else:
            return []
        if airline_name != staff_airline:
            return []
        cursor.execute(
            "select customer_email from purchases natural join ticket where flight_num = %s and airline_name = %s",
            (flight_num, airline_name))
        result = []
        dic = cursor.fetchone()
        while dic is not None:
            result.append(dic['customer_email'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def add_flight(cnx, airline_staff_username, flight_num, departure_airport, departure_time, arrival_airport,
               arrival_time, price,
               status, airplane_id):
    # the airline_name should be obtained from airline_staff_username
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if len(list_of_dic) > 0:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {'exec': False,
                    'error': "the username doesn't exist"}
        cursor.execute("insert into flight values (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
            staff_airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price, status,
            airplane_id))
        cnx.commit()
        return {'exec': True}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()
        cnx.close()


def update_status(cnx, airline_staff_username, airline_name, flight_num, new_status):
    # must check if the airline really has permission to view passenger
    # if airline_staff_username --> airline_name doesn't match the airline_name, then return exec=False
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        outcome = cursor.fetchall()
        if len(outcome) > 0:
            staff_airline = outcome[0]['airline_name']
        else:
            return {'exec': False,
                    'error': 'no permission oops'}
        if staff_airline != airline_name:
            return {'exec': False,
                    'error': 'no permission oops'}
        else:
            cursor.execute("update flight set status = %s where airline_name = %s and flight_num = %s",
                           (new_status, airline_name, flight_num))
            cnx.commit()
            return {'exec': True}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()
        cnx.close()


def get_airplane(cnx, airline_staff_username):
    # get the airplanes info where the airline staff works
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute(
            "select airplane_id,seats from airplane where airline_name in (select airline_name from airline_staff where username = %s)",
            (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            return list_of_dic
        else:
            return []
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {'exec': False, 'error': str(ex)}
    finally:
        cursor.close()
        cnx.close()


def add_airplane(cnx, airline_staff_username, airplane_id, seats):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {'exec': False,
                    'error': 'username not exists'}
        cursor.execute("insert into airplane values (%s,%s,%s)", (staff_airline, airplane_id, seats))
        cnx.commit()
        return {'exec': True}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {'exec': False, 'error': str(ex)}
    finally:
        cursor.close()
        cnx.close()


def get_airport(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select * from airport")
        return cursor.fetchall()
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


def add_airport(cnx, airport_name, airport_city):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("insert into airport values (%s,%s)", (airport_name, airport_city))
        cnx.commit()
        return {'exec': True}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {'exec': False, 'error': str(ex)}
    finally:
        cursor.close()
        cnx.close()


def view_top_booking_agents(cnx, airline_staff_username):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            logger.error("username doesn't exist")
            return {}
        cursor.execute(
            "select email,count(ticket_id) as ticket from booking_agent natural join purchases natural join ticket natural join flight where purchase_date >= date_sub(CURRENT_DATE,interval 1 year) and airline_name = %s group by email order by ticket DESC",
            (staff_airline,))
        outcome1 = cursor.fetchall()
        if outcome1 and len(outcome1) > 5:
            outcome1 = outcome1[0:5]
        cursor.execute(
            "select email,count(ticket_id) as ticket from booking_agent natural join purchases natural join ticket natural join flight where purchase_date >= date_sub(CURRENT_DATE,interval 1 month) and airline_name = %s group by email order by ticket DESC",
            (staff_airline,))
        outcome2 = cursor.fetchall()
        if outcome2 and len(outcome2) > 5:
            outcome2 = outcome2[0:5]
        cursor.execute(
            "select email,sum(price)/10 as commission from booking_agent natural join purchases natural join ticket natural join flight where purchase_date >= date_sub(CURRENT_DATE,interval 1 year) and airline_name = %s group by email AND booking_agent_id order by commission DESC",
            (staff_airline,))
        outcome3 = cursor.fetchall()
        if outcome3 and len(outcome3) > 5:
            outcome3 = outcome3[0:5]
        return {'ticket_year': outcome1, 'ticket_month': outcome2, 'commission': outcome3}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


def view_frequent_customer(cnx, airline_staff_username):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return []
        cursor.execute(
            "select email from customer where (select count(distinct ticket_id) from purchases natural join ticket natural join flight where customer_email = email and airline_name = %s) >= all (select count(distinct ticket_id) from purchases natural join ticket natural join flight where airline_name = %s group by customer_email)",
            (staff_airline, staff_airline))
        dic = cursor.fetchone()
        result = []
        while dic is not None:
            result.append(dic['email'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def view_customer_flight_history(cnx, airline_staff_username, customer_email):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return []
        cursor.execute(
            "select airline_name,flight_num from flight natural join ticket natural join purchases where customer_email = %s and airline_name = %s",
            (customer_email, staff_airline))
        dic = cursor.fetchone()
        result = []
        while dic != None:
            dic['flight_num'] = int(dic['flight_num'])
            result.append(dic)
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def total_ticket_sold(cnx, airline_staff_username, start_date, end_date):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {}
        if not start_date and not end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,count(distinct ticket_id,customer_email) as num_of_ticket from purchases natural join ticket natural join flight where airline_name = %s group by month",
                (staff_airline,))
        elif start_date and not end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,count(distinct ticket_id,customer_email) as num_of_ticket from purchases natural join ticket natural join flight where purchase_date >= %s and airline_name = %s group by month",
                (start_date, staff_airline))
        elif not start_date and end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,count(distinct ticket_id,customer_email) as num_of_ticket from purchases natural join ticket natural join flight where purchase_date <= %s and airline_name = %s group by month",
                (end_date, staff_airline))
        elif start_date and end_date:
            cursor.execute(
                "select extract(year_month from purchase_date) as month,count(distinct ticket_id,customer_email) as num_of_ticket from purchases natural join ticket natural join flight where purchase_date between %s and %s and airline_name = %s group by month",
                (start_date, end_date, staff_airline))
        dic = cursor.fetchone()
        result = {}
        while dic is not None:
            result[dic['month']] = int(dic['num_of_ticket'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.commit()


def total_ticket(cnx, airline_staff_username):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {}
        cursor.execute(
            "select count(ticket_id) as total from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 month)",
            (staff_airline,))
        last_month = int(cursor.fetchall()[0]['total'])
        cursor.execute(
            "select count(ticket_id) as total from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 year)",
            (staff_airline,))
        last_year = int(cursor.fetchall()[0]['total'])
        return {'last_month': last_month, 'last_year': last_year}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.commit()


def compare_revenue(cnx, airline_staff_username):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {}
        cursor.execute(
            "select sum(price) as total_revenue from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 month) and booking_agent_id is null",
            (staff_airline,))
        md = cursor.fetchall()[0]['total_revenue']
        if md:
            md = int(md)
        else:
            return {}
        cursor.execute(
            "select sum(price) as total_revenue from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 month) and booking_agent_id is not null",
            (staff_airline,))
        mi = cursor.fetchall()[0]['total_revenue']
        cursor.execute(
            "select sum(price) as total_revenue from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 year) and booking_agent_id is null",
            (staff_airline,))
        yd = int(cursor.fetchall()[0]['total_revenue'])
        cursor.execute(
            "select sum(price) as total_revenue from purchases natural join ticket natural join flight where airline_name = %s and purchase_date >= date_sub(current_date,interval 1 year) and booking_agent_id is not null",
            (staff_airline,))
        yi = int(cursor.fetchall()[0]['total_revenue'])
        return {'md': md, 'mi': mi, 'yd': yd, 'yi': yi}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


def view_top_destinations(cnx, airline_staff_username):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select airline_name from airline_staff where username = %s", (airline_staff_username,))
        list_of_dic = cursor.fetchall()
        if list_of_dic:
            staff_airline = list_of_dic[0]['airline_name']
        else:
            return {}
        cursor.execute(
            "select distinct airport_city from airport A order by (select count(ticket_id) from purchases natural join ticket natural join flight where airline_name = %s and purchase_date > date_sub(current_date,interval 3 month) and arrival_airport in (select airport_name from airport where airport_city = A.airport_city))",
            (staff_airline,))
        month_result = []
        dic = cursor.fetchone()
        while dic is not None and len(month_result) < 3:
            month_result.append(dic['airport_city'])
            dic = cursor.fetchone()
        cursor.execute(
            "select distinct airport_city from airport A order by (select count(ticket_id) from purchases natural join ticket natural join flight where airline_name = %s and purchase_date > date_sub(current_date,interval 1 year) and arrival_airport in (select airport_name from airport where airport_city = A.airport_city))",
            (staff_airline,))
        year_result = []
        dic = cursor.fetchone()
        while dic is not None and len(year_result) < 3:
            year_result.append(dic['airport_city'])
            dic = cursor.fetchone()
        return {'month': month_result, 'year': year_result}
    except pymysql.Error as ex:
        logger.error(str(ex))
        return {}
    finally:
        cursor.close()
        cnx.close()


# general api
# normally returns empty list if error occurred
def get_all_airlines(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select distinct airline_name from airline")
        dic = cursor.fetchone()
        result = []
        while dic is not None:
            result.append(dic['airline_name'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return str(ex)
    finally:
        cursor.close()
        cnx.close()


def get_all_cities_and_airports(cnx):
    try:
        mtplx_cnx = pymysql.connect(**cnx)
        return _all_cities(mtplx_cnx) + get_all_airports(cnx)
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        mtplx_cnx.close()


def get_all_customer_emails(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select distinct email from customer")
        dic = cursor.fetchone()
        result = []
        while dic is not None:
            result.append(dic['email'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.commit()


def get_all_airports(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select distinct airport_name from airport")
        dic = cursor.fetchone()
        result = []
        while dic is not None:
            result.append(dic['airport_name'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def get_all_airplane_id(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        cursor.execute("select distinct airplane_id from airplane")
        dic = cursor.fetchone()
        result = []
        while dic is not None:
            result.append(dic['airplane_id'])
            dic = cursor.fetchone()
        return result
    except pymysql.Error as ex:
        logger.error(str(ex))
        return []
    finally:
        cursor.close()
        cnx.close()


def import_test_data(cnx):
    try:
        cnx = pymysql.connect(**cnx)
        cursor = cnx.cursor()
        errors = []
        with open('import_test_data.sql', 'r') as fs:
            sql_commands = fs.read().split(';')
            for cmd in sql_commands:
                cmd = cmd.strip()
                if cmd:
                    try:
                        cursor.execute(cmd)
                    except Exception as ex:
                        logger.error(str(ex))
                        errors.append(str(ex))
        cnx.commit()
        cursor.close()
        cnx.close()
        logger.info('test data imported')
        return errors
    except pymysql.Error as ex:
        logger.error(str(ex))
        return [str(ex)]
