from __future__ import print_function
import sqlite3

from check_temperature import get_local_db


if __name__ == '__main__':
    conn = get_local_db()
    print(conn.execute('select * from temps order by time desc').fetchmany(5))