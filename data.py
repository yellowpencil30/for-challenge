import sqlite3

def insert_dummy_data():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # 가상의 학생 4명 데이터 (번호, 이름, 상태, 변동일자)
    students_data = [
        (1, '김철수', '재학', None),
        (2, '이영희', '재학', None),
        (3, '박지훈', '전출', '2026-01-22'), # 전출 간 학생 (테스트용)
        (4, '최수아', '재학', None),
        (5, '이철수', '재학', None),
        (6, '김민정', '전입', '2026-01-22')
    ]

    # 데이터베이스에 넣기
    cursor.executemany('''
    INSERT INTO students (student_no, name, status, status_date)
    VALUES (?, ?, ?, ?)
    ''', students_data)

    conn.commit()
    conn.close()

def deleste_student_data(target_id):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (target_id,))
    conn.commit()
    conn.close

def check_data():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    print("------[현재 학생 명단]-----")
    cursor.execute("SELECT id, student_no, name FROM students")
    for row in cursor.fetchall():
        print(f"고유 ID: {row[0]} | 학급 번호: {row[1]} | 이름: {row[2]}")
    print("------[현재 출결 사항 누적]-----")
    cursor.execute("SELECT id, date, student_id, attendance_type FROM attendance")
    for row in cursor.fetchall():
        print(f"고유 ID: {row[0]} | 날짜: {row[1]} | 번호: {row[2]} | 출결사항: {row[3]}")

def deleste_attendance_data(target_id):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE id = ?", (target_id,))
    conn.commit()
    conn.close

if __name__ == "__main__":
    check_data()