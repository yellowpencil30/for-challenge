import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'attendance.db')

def update_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # attendance 테이블에 is_uploaded 컬럼 추가 (기본값 0: 미완료)
        cursor.execute("ALTER TABLE attendance ADD COLUMN is_uploaded INTEGER DEFAULT 0")
        conn.commit()
        print("✅ 성공: attendance 테이블에 'is_uploaded' 컬럼이 추가되었습니다.")
    except sqlite3.OperationalError:
        # 이미 컬럼이 있는 경우 에러가 나므로 예외 처리
        print("⚠️ 알림: 이미 'is_uploaded' 컬럼이 존재합니다.")
        
    conn.close()

if __name__ == "__main__":
    update_database()