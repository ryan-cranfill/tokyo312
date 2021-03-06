import subprocess
import re
import random
import logging
import sys
# import psycopg2
import sqlite3
import json

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
DEBUG = True


def get_settings():
    # todo: make this go to the right os.join place
    try:
        with open('local_settings.json') as f:
            return json.load(f)
    except:
        return {'room_name': 'conf'}


def check_temperature(debug=False):
    temp_re = re.compile(r': (\d.*\d).*: (\d.*\d)')  # not great, i know

    try:
        temp_str = subprocess.check_output(['temperx'])
    except:
        temp_str = 'Temperature: {}   Humidity: {}\n'.format(random.random() * 30, random.random() * 30)

    logging.debug(temp_str)

    hits = temp_re.findall(temp_str)

    if hits:
        temp, hum = map(float, hits[0])
    else:
        # ughhhhh we didn't see anything
        temp, hum = -1., -1.

    return temp, hum


def get_local_db():
    return sqlite3.connect('local.db')


def sqlite_insert(conn, table, row):
    cols = ', '.join('"{}"'.format(col) for col in row.keys())
    vals = ', '.join(':{}'.format(col) for col in row.keys())
    sql = 'INSERT INTO "{0}" ({1}) VALUES ({2})'.format(table, cols, vals)
    conn.cursor().execute(sql, row)
    conn.commit()


def create_temps_table(conn):
    query = """
    create table if not exists temps(
      id integer primary key,
      room text default "default",
      temperature real,
      humidity real,
      time datetime default current_timestamp
      )
    """
    conn.execute(query)


def insert_temp_hum(conn, temp, hum, room='default'):
    vals = {'temperature': temp, 'humidity': hum, 'room': room}
    sqlite_insert(conn, 'temps', vals)


if __name__ == '__main__':
    temp, hum = check_temperature(DEBUG)
    settings = get_settings()
    room = settings.get('room_name', 'chicken')

    conn = get_local_db()
    create_temps_table(conn)
    insert_temp_hum(conn, temp, hum, room)

