#!/usr/bin/env python

#-----------------------------------------------------------------------
# runserver.py
# Author: Ranajoy Gupta
#-----------------------------------------------------------------------

"""Flask web server for the Registrar application."""

import sys
import argparse
import sqlite3
import contextlib
import flask

app = flask.Flask(__name__, template_folder='.')

DATABASE_URL = 'file:reg.sqlite?mode=ro'
GENERIC_ERROR_MSG = (
    "A server error occurred. "
    "Please contact the system administrator."
)

def escape_wildcards(user_input):
    """Escapes SQLite wildcards for LIKE clauses."""
    escaped = user_input.replace('\\', '\\\\')
    escaped = escaped.replace('%', '\\%')
    escaped = escaped.replace('_', '\\_')
    return f"%{escaped}%"

def get_overviews(criteria):
    """Queries database for class overviews."""
    dept = escape_wildcards(criteria.get('dept', ''))
    coursenum = escape_wildcards(criteria.get('coursenum', ''))
    area = escape_wildcards(criteria.get('area', ''))
    title = escape_wildcards(criteria.get('title', ''))

    stmt = """
        SELECT classid, dept, coursenum, area, title
        FROM courses, crosslistings, classes
        WHERE (courses.courseid = crosslistings.courseid)
        AND (courses.courseid = classes.courseid)
        AND (dept LIKE ? ESCAPE '\\')
        AND (coursenum LIKE ? ESCAPE '\\')
        AND (area LIKE ? ESCAPE '\\')
        AND (title LIKE ? ESCAPE '\\')
        ORDER BY dept, coursenum, classid
    """

    with contextlib.closing(sqlite3.connect(
            DATABASE_URL, isolation_level=None, uri=True
    )) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(stmt, [dept, coursenum, area, title])
            rows = cursor.fetchall()

            payload = []
            for row in rows:
                payload.append({
                    'classid': row[0],
                    'dept': row[1] or "",
                    'coursenum': row[2] or "",
                    'area': row[3] or "",
                    'title': row[4] or ""
                })
            return payload

def get_details(classid):
    """Queries database for specific class details."""
    with contextlib.closing(sqlite3.connect(
            DATABASE_URL, isolation_level=None, uri=True
    )) as connection:
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute('''
                SELECT courseid, days, starttime, endtime, bldg, roomnum
                FROM classes WHERE classid = ?
            ''', [classid])
            class_row = cursor.fetchone()

            if class_row is None:
                return None

            courseid = class_row[0]

            cursor.execute('''
                SELECT dept, coursenum FROM crosslistings
                WHERE courseid = ? ORDER BY dept, coursenum
            ''', [courseid])
            deptcoursenums = [
                f"{row[0]} {row[1]}" for row in cursor.fetchall()
            ]

            cursor.execute('''
                SELECT area, title, descrip, prereqs
                FROM courses WHERE courseid = ?
            ''', [courseid])
            course_row = cursor.fetchone()

            cursor.execute('''
                SELECT profname FROM coursesprofs, profs
                WHERE coursesprofs.profid = profs.profid
                AND coursesprofs.courseid = ? ORDER BY profname
            ''', [courseid])
            profnames = [row[0] for row in cursor.fetchall()]

            payload = {
                'classid': classid,
                'courseid': courseid,
                'days': class_row[1] or "",
                'starttime': class_row[2] or "",
                'endtime': class_row[3] or "",
                'bldg': class_row[4] or "",
                'roomnum': class_row[5] or "",
                'deptcoursenums': deptcoursenums,
                'area': course_row[0] or "",
                'title': course_row[1] or "",
                'descrip': course_row[2] or "",
                'prereqs': course_row[3] or "",
                'profnames': profnames
            }
            return payload

@app.route('/', methods=['GET'])
@app.route('/regoverviews', methods=['GET'])
def overviews():
    """Route for the class overviews search page."""
    try:
        if 'dept' in flask.request.args:
            dept = flask.request.args.get('dept', '')
            coursenum = flask.request.args.get('coursenum', '')
            area = flask.request.args.get('area', '')
            title = flask.request.args.get('title', '')
        else:
            dept = flask.request.cookies.get('dept', '')
            coursenum = flask.request.cookies.get('coursenum', '')
            area = flask.request.cookies.get('area', '')
            title = flask.request.cookies.get('title', '')

        criteria = {
            'dept': dept.strip(),
            'coursenum': coursenum.strip(),
            'area': area.strip(),
            'title': title.strip()
        }

        classes = get_overviews(criteria)

        html_code = flask.render_template(
            'overviews.html',
            classes=classes,
            dept=dept,
            coursenum=coursenum,
            area=area,
            title=title
        )

        response = flask.make_response(html_code)
        response.set_cookie('dept', dept)
        response.set_cookie('coursenum', coursenum)
        response.set_cookie('area', area)
        response.set_cookie('title', title)

        return response

    except Exception as ex:
        print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
        html_code = flask.render_template(
            'error.html',
            message=GENERIC_ERROR_MSG
        )
        return flask.make_response(html_code)

@app.route('/regdetails', methods=['GET'])
def details():
    """Route for the class details page."""
    try:
        classid_str = flask.request.args.get('classid')

        if classid_str is None or classid_str.strip() == '':
            html_code = flask.render_template(
                'error.html',
                message="missing classid"
            )
            return flask.make_response(html_code)

        try:
            classid = int(classid_str)
        except ValueError:
            html_code = flask.render_template(
                'error.html',
                message="non-integer classid"
            )
            return flask.make_response(html_code)

        class_details = get_details(classid)

        if class_details is None:
            html_code = flask.render_template(
                'error.html',
                message=f"no class with classid {classid} exists"
            )
            return flask.make_response(html_code)

        html_code = flask.render_template(
            'details.html',
            details=class_details
        )
        return flask.make_response(html_code)

    except Exception as ex:
        print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
        html_code = flask.render_template(
            'error.html',
            message=GENERIC_ERROR_MSG
        )
        return flask.make_response(html_code)

def main():
    """Parses command-line arguments and runs the Flask server."""
    parser = argparse.ArgumentParser(
        description="The registrar application"
    )
    parser.add_argument('port', metavar='port', type=int,
                        help='the port at which the server '
                             'should listen')

    args = parser.parse_args()

    try:
        app.run(host='0.0.0.0', port=args.port, debug=False)
    except Exception as ex:
        print(f"{sys.argv[0]}: {ex}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
