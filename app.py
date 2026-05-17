from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            mathematics INTEGER NOT NULL,
            electronic_devices INTEGER NOT NULL,
            signals_systems INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            grade TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized!")

def calculate_grade(percentage):
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'

def get_db():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/students', methods=['GET'])
def get_students():
    conn = get_db()
    students = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@app.route('/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        name = data['name']
        roll = data['roll_number']
        mathematics = int(data['mathematics'])
        electronic_devices = int(data['electronic_devices'])
        signals_systems = int(data['signals_systems'])

        for mark in [mathematics, electronic_devices, signals_systems]:
            if mark < 0 or mark > 100:
                return jsonify({"error": "Marks must be between 0 and 100"}), 400

        total = mathematics + electronic_devices + signals_systems
        percentage = round(total / 3, 2)
        grade = calculate_grade(percentage)
        status = 'Pass' if percentage >= 35 else 'Fail'

        conn = get_db()
        conn.execute('''
            INSERT INTO students
            (name, roll_number, mathematics, electronic_devices, signals_systems, total, percentage, grade, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, roll, mathematics, electronic_devices, signals_systems, total, percentage, grade, status))
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Student added successfully",
            "grade": grade,
            "percentage": percentage,
            "status": status
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    try:
        data = request.get_json()
        mathematics = int(data['mathematics'])
        electronic_devices = int(data['electronic_devices'])
        signals_systems = int(data['signals_systems'])

        for mark in [mathematics, electronic_devices, signals_systems]:
            if mark < 0 or mark > 100:
                return jsonify({"error": "Marks must be between 0 and 100"}), 400

        total = mathematics + electronic_devices + signals_systems
        percentage = round(total / 3, 2)
        grade = calculate_grade(percentage)
        status = 'Pass' if percentage >= 35 else 'Fail'

        conn = get_db()
        conn.execute('''
            UPDATE students
            SET mathematics=?, electronic_devices=?, signals_systems=?,
                total=?, percentage=?, grade=?, status=?
            WHERE id=?
        ''', (mathematics, electronic_devices, signals_systems, total, percentage, grade, status, id))
        conn.commit()
        conn.close()

        return jsonify({
            "message": "Student updated successfully",
            "grade": grade,
            "percentage": percentage,
            "status": status
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Student deleted successfully"})

@app.route('/students/search', methods=['GET'])
def search_student():
    query = request.args.get('q', '')
    conn = get_db()
    students = conn.execute(
        'SELECT * FROM students WHERE name LIKE ? OR roll_number LIKE ?',
        (f'%{query}%', f'%{query}%')
    ).fetchall()
    conn.close()
    return jsonify([dict(s) for s in students])

@app.route('/export', methods=['GET'])
def export_csv():
    conn = get_db()
    students = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    conn.close()

    csv = 'ID,Name,Roll Number,Mathematics,Electronic Devices,Signals Systems,Total,Percentage,Grade,Status\n'
    for s in students:
        csv += f"{s['id']},{s['name']},{s['roll_number']},{s['mathematics']},{s['electronic_devices']},{s['signals_systems']},{s['total']},{s['percentage']},{s['grade']},{s['status']}\n"

    from flask import Response
    return Response(
        csv,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=student_results.csv'}
    )

@app.route('/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    students = conn.execute('SELECT grade FROM students').fetchall()
    conn.close()

    grades = {'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for s in students:
        grade = s['grade']
        if grade in grades:
            grades[grade] += 1

    return jsonify(grades)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)