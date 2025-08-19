from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_CONFIG = {
    'host': 'de17.spaceify.eu',
    'port': 3306,
    'user': 'u31736_4YAaThHXdg',
    'password': 'LSd5Xo77Ve=WK=ZyhvOQ.TUh',
    'database': 's31736_a_db_baby',
    'charset': 'utf8mb4'
}

# Asia/Colombo timezone (UTC+05:30)
COLOMBO_TZ = pytz.timezone('Asia/Colombo')


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def convert_timestamp_to_colombo(timestamp_ms):
    """Convert millisecond timestamp to Asia/Colombo timezone"""
    if not timestamp_ms or timestamp_ms == 0:
        return None

    try:
        # Convert string to int if needed, then milliseconds to seconds
        timestamp_seconds = int(timestamp_ms) / 1000

        # Create UTC datetime
        utc_dt = datetime.fromtimestamp(timestamp_seconds, tz=pytz.UTC)

        # Convert to Asia/Colombo timezone
        colombo_dt = utc_dt.astimezone(COLOMBO_TZ)

        return colombo_dt.strftime('%d %B %Y, %H:%M:%S')
    except Exception as e:
        print(f"Error converting timestamp {timestamp_ms}: {e}")
        return None


def calculate_punishment_duration(start_ms, end_ms):
    """Calculate the duration between start and end timestamps"""
    if not start_ms or not end_ms:
        return None

    try:
        start_seconds = int(start_ms) / 1000
        end_seconds = int(end_ms) / 1000

        duration_seconds = end_seconds - start_seconds
        duration_days = duration_seconds / (24 * 60 * 60)

        if duration_days >= 1:
            return f"{int(duration_days)} days"
        elif duration_seconds >= 3600:
            hours = int(duration_seconds / 3600)
            return f"{hours} hours"
        elif duration_seconds >= 60:
            minutes = int(duration_seconds / 60)
            return f"{minutes} minutes"
        else:
            return f"{int(duration_seconds)} seconds"

    except Exception as e:
        print(f"Error calculating duration: {e}")
        return None


@app.route('/api/punishments', methods=['GET'])
def get_all_punishments():
    """Get all punishment records from PunishmentHistory table"""

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, uuid, reason, operator, punishmentType, start, end, calculation
        FROM PunishmentHistory
        ORDER BY id ASC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        punishments = []
        for result in results:
            # Convert timestamps to Asia/Colombo timezone
            start_time = convert_timestamp_to_colombo(result['start']) if result['start'] else None
            end_time = convert_timestamp_to_colombo(result['end']) if result['end'] else None

            # Calculate punishment duration
            duration = calculate_punishment_duration(result['start'], result['end']) if result['start'] and result[
                'end'] else None

            punishment = {
                'id': result['id'],
                'name': result['name'],
                'uuid': result['uuid'],
                'reason': result['reason'],
                'operator': result['operator'],
                'punishmentType': result['punishmentType'],
                'start': start_time,
                'end': end_time,
                'duration': duration,
                'calculation': result['calculation']
            }

            punishments.append(punishment)

        return jsonify({
            'total_records': len(punishments),
            'punishments': punishments
        })

    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/punishments/<int:punishment_id>', methods=['GET'])
def get_punishment_by_id(punishment_id):
    """Get a specific punishment record by ID"""

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, uuid, reason, operator, punishmentType, start, end, calculation
        FROM PunishmentHistory
        WHERE id = %s
        """

        cursor.execute(query, (punishment_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'error': f'Punishment with ID {punishment_id} not found'}), 404

        # Convert timestamps to Asia/Colombo timezone
        start_time = convert_timestamp_to_colombo(result['start']) if result['start'] else None
        end_time = convert_timestamp_to_colombo(result['end']) if result['end'] else None

        # Calculate punishment duration
        duration = calculate_punishment_duration(result['start'], result['end']) if result['start'] and result[
            'end'] else None

        punishment = {
            'id': result['id'],
            'name': result['name'],
            'uuid': result['uuid'],
            'reason': result['reason'],
            'operator': result['operator'],
            'punishmentType': result['punishmentType'],
            'start': start_time,
            'end': end_time,
            'duration': duration,
            'calculation': result['calculation']
        }

        return jsonify(punishment)

    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/punishments/player/<string:player_name>', methods=['GET'])
def get_punishments_by_player(player_name):
    """Get all punishment records for a specific player"""

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, uuid, reason, operator, punishmentType, start, end, calculation
        FROM PunishmentHistory
        WHERE name = %s
        ORDER BY start DESC
        """

        cursor.execute(query, (player_name,))
        results = cursor.fetchall()

        if not results:
            return jsonify({'error': f'No punishments found for player {player_name}'}), 404

        punishments = []
        for result in results:
            # Convert timestamps to Asia/Colombo timezone
            start_time = convert_timestamp_to_colombo(result['start']) if result['start'] else None
            end_time = convert_timestamp_to_colombo(result['end']) if result['end'] else None

            # Calculate punishment duration
            duration = calculate_punishment_duration(result['start'], result['end']) if result['start'] and result[
                'end'] else None

            punishment = {
                'id': result['id'],
                'name': result['name'],
                'uuid': result['uuid'],
                'reason': result['reason'],
                'operator': result['operator'],
                'punishmentType': result['punishmentType'],
                'start': start_time,
                'end': end_time,
                'duration': duration,
                'calculation': result['calculation']
            }

            punishments.append(punishment)

        return jsonify({
            'player': player_name,
            'total_punishments': len(punishments),
            'punishments': punishments
        })

    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/punishments/type/<string:punishment_type>', methods=['GET'])
def get_punishments_by_type(punishment_type):
    """Get all punishment records by punishment type"""

    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, uuid, reason, operator, punishmentType, start, end, calculation
        FROM PunishmentHistory
        WHERE punishmentType = %s
        ORDER BY start DESC
        """

        cursor.execute(query, (punishment_type,))
        results = cursor.fetchall()

        if not results:
            return jsonify({'error': f'No punishments found for type {punishment_type}'}), 404

        punishments = []
        for result in results:
            # Convert timestamps to Asia/Colombo timezone
            start_time = convert_timestamp_to_colombo(result['start']) if result['start'] else None
            end_time = convert_timestamp_to_colombo(result['end']) if result['end'] else None

            # Calculate punishment duration
            duration = calculate_punishment_duration(result['start'], result['end']) if result['start'] and result[
                'end'] else None

            punishment = {
                'id': result['id'],
                'name': result['name'],
                'uuid': result['uuid'],
                'reason': result['reason'],
                'operator': result['operator'],
                'punishmentType': result['punishmentType'],
                'start': start_time,
                'end': end_time,
                'duration': duration,
                'calculation': result['calculation']
            }

            punishments.append(punishment)

        return jsonify({
            'punishment_type': punishment_type,
            'total_punishments': len(punishments),
            'punishments': punishments
        })

    except Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM PunishmentHistory")
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'total_punishments': count,
                'timezone': 'Asia/Colombo (UTC+05:30)'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'connected but query failed',
                'error': str(e)
            }), 500
    else:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True)