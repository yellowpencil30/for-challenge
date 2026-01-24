import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'attendance.db')

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("나이스 출결 비서 - [풀네임 강제 저장 적용]")
        self.resize(1000, 500)
        self.setStyleSheet("background-color: #f8f9fa;") 
        
        font = QFont("Malgun Gothic", 12)
        self.setFont(font)

        self.init_ui()
        self.date_edit.setDate(datetime.now().date())
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20) 
        main_layout.setSpacing(15)

        # 1. 상단: 날짜 선택
        top_layout = QHBoxLayout()
        date_label = QLabel("📅 오늘 날짜:")
        date_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        top_layout.addWidget(date_label)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("background-color: white; border: 1px solid #ced4da; border-radius: 5px; padding: 5px; font-size: 18px;")
        top_layout.addWidget(self.date_edit)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # 2. 중앙 상단: 입력 바
        input_container = QWidget()
        input_container.setStyleSheet("background-color: white; border: 1px solid #e9ecef; border-radius: 10px;")
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(15, 10, 15, 10) 
        input_layout.setSpacing(10)

        input_style = "QLineEdit { font-size: 18px; background-color: #f1f3f5; border: 1px solid #ced4da; border-radius: 8px; padding: 5px; color: #495057; font-weight: bold; } QLineEdit:focus { border: 2px solid #4dabf7; background-color: white; }"
        widget_height = 55 

        self.no_input = QLineEdit()
        self.no_input.setPlaceholderText("번호")
        self.no_input.setFixedWidth(70)
        self.no_input.setFixedHeight(widget_height)
        self.no_input.setAlignment(Qt.AlignCenter)
        self.no_input.setStyleSheet(input_style)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("이름")
        self.name_input.setFixedWidth(150)
        self.name_input.setFixedHeight(widget_height)
        self.name_input.setAlignment(Qt.AlignCenter)
        self.name_input.setStyleSheet(input_style)

        self.type_combo = QComboBox()
        self.type_combo.setFixedHeight(widget_height)
        self.type_combo.setFixedWidth(200)
        self.setup_colored_combobox()
        
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("사유 (예: 독감)")
        self.reason_input.setFixedHeight(widget_height)
        self.reason_input.setStyleSheet(input_style)
        self.reason_input.setFixedWidth(250)

        self.add_btn = QPushButton("➕ 추가 (Enter)")
        self.add_btn.setFixedHeight(widget_height)
        self.add_btn.setStyleSheet("QPushButton { background-color: #339af0; color: white; font-size: 20px; font-weight: bold; border-radius: 8px; } QPushButton:hover { background-color: #228be6; }")

        input_layout.addWidget(self.no_input)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.type_combo)
        input_layout.addWidget(self.reason_input)
        input_layout.addWidget(self.add_btn)
        input_layout.addStretch()
        input_container.setLayout(input_layout)
        main_layout.addWidget(input_container)

        # [팝업 위젯]
        self.name_popup = QListWidget(self)
        self.name_popup.setWindowFlags(Qt.Popup) 
        self.name_popup.setStyleSheet("QListWidget { background-color: white; border: 2px solid #4dabf7; border-radius: 5px; font-size: 16px; font-weight: bold; } QListWidget::item { padding: 8px; } QListWidget::item:selected { background-color: #e7f5ff; color: #1864ab; }")
        self.name_popup.hide()

        # 3. 중앙: 오늘 변동 명단 테이블
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["번호", "이름", "출결 종류", "사유", "⚠️ 참고사항"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #dee2e6; border-radius: 10px; gridline-color: #f1f3f5; font-size: 16px; }
            QHeaderView::section { font-size: 16px; background-color: #f8f9fa; color: #495057; font-weight: bold; border: none; border-bottom: 2px solid #dee2e6; padding: 5px; }
            QTableWidget::item { padding: 8px; }
        """)
        
        self.table.setFixedHeight(250)
        main_layout.addWidget(self.table)
        main_layout.addStretch() 

        # 4. 하단: 저장 버튼
        self.save_btn = QPushButton("💾 오늘 출결 DB에 저장하기")
        self.save_btn.setFixedHeight(65)
        self.save_btn.setStyleSheet("QPushButton { background-color: #40c057; color: white; font-size: 22px; font-weight: bold; border-radius: 10px; } QPushButton:hover { background-color: #37b24d; }")
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)

        # 이벤트 연결
        self.no_input.textChanged.connect(self.find_student_name)
        self.name_input.textChanged.connect(self.find_student_no) 
        
        self.reason_input.returnPressed.connect(self.add_to_table)
        self.add_btn.clicked.connect(self.add_to_table)

        self.name_popup.itemClicked.connect(self.select_student_from_popup) 
        self.save_btn.clicked.connect(self.save_to_db) 

    def setup_colored_combobox(self):
        model = QStandardItemModel()
        items = [
            ("🟢 출석인정 결석", "#2e7d32", "white"), ("🟢 출석인정 지각", "#43a047", "white"), ("🟢 출석인정 조퇴", "#66bb6a", "black"), ("🟢 출석인정 결과", "#a5d6a7", "black"),
            ("🔴 질병 결석", "#c62828", "white"), ("🔴 질병 지각", "#e53935", "white"), ("🔴 질병 조퇴", "#ef5350", "black"), ("🔴 질병 결과", "#ffcdd2", "black"),
            ("⚫ 미인정 결석", "#212121", "white"), ("⚫ 미인정 지각", "#616161", "white"), ("⚫ 미인정 조퇴", "#9e9e9e", "white"), ("⚫ 미인정 결과", "#e0e0e0", "black"),
            ("🟣 기타 결석", "#4527a0", "white"), ("🟣 기타 지각", "#5e35b1", "white"), ("🟣 기타 조퇴", "#7e57c2", "white"), ("🟣 기타 결과", "#b39ddb", "black")
        ]
        for text, bg_color, text_color in items:
            item = QStandardItem(text)
            item.setBackground(QColor(bg_color))
            item.setForeground(QColor(text_color))
            item.setFont(QFont("Malgun Gothic", 16, QFont.Bold))
            model.appendRow(item)
        self.type_combo.setModel(model)
        self.type_combo.setStyleSheet("QComboBox { font-size: 18px; background-color: white; border: 1px solid #ced4da; border-radius: 8px; padding: 5px; font-weight: bold; } QComboBox::drop-down { border: none; }")

    def find_student_name(self):
        no_text = self.no_input.text()
        if not no_text: 
            self.name_input.blockSignals(True)
            self.name_input.clear()
            self.name_input.blockSignals(False)
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_no = ? AND status = '재학'", (no_text,))
            result = cursor.fetchone()
            conn.close()

            if result:
                self.name_input.blockSignals(True)
                self.name_input.setText(result[0])
                self.name_input.blockSignals(False)
        except Exception:
            pass

    # ★ [기능 강화] 이름 일부만 쳐도 팝업이 무조건 뜨도록 변경
    def find_student_no(self):
        name_text = self.name_input.text()
        if not name_text: 
            self.no_input.blockSignals(True)
            self.no_input.clear()
            self.no_input.blockSignals(False)
            self.name_popup.hide()
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # 이름에 입력한 글자가 '포함'된 모든 학생 검색
            cursor.execute("SELECT student_no, name FROM students WHERE name LIKE ? AND status = '재학'", (f"%{name_text}%",))
            results = cursor.fetchall()
            conn.close()

            if results:
                # 1명이든 여러 명이든 무조건 팝업을 띄워서 명부상 이름을 보여줌
                self.name_popup.clear()
                for r in results:
                    self.name_popup.addItem(f"{r[0]}번 {r[1]}") # 명부상 풀네임 표시
                
                # 팝업 위치 고정
                global_pos = self.name_input.mapToGlobal(self.name_input.rect().bottomLeft())
                self.name_popup.setGeometry(global_pos.x(), global_pos.y(), self.name_input.width(), 100)
                self.name_popup.show()
                self.name_popup.setCurrentRow(0)

                # 단, 검색된 사람이 딱 1명이면 편의를 위해 번호/이름 자동 완성 (센서 끄고)
                if len(results) == 1:
                    self.no_input.blockSignals(True)
                    self.no_input.setText(str(results[0][0]))
                    self.no_input.blockSignals(False)
            else:
                self.name_popup.hide()

        except Exception:
            pass

    def select_student_from_popup(self, item):
        selected_text = item.text() 
        parts = selected_text.split("번 ")
        
        self.no_input.blockSignals(True)
        self.name_input.blockSignals(True)
        # ★ [핵심] 팝업에서 선택한 명부상 진짜 '풀네임'이 입력창에 박힘
        self.no_input.setText(parts[0]) 
        self.name_input.setText(parts[1]) 
        self.name_input.blockSignals(False)
        self.no_input.blockSignals(False)

        self.name_popup.hide() 
        self.type_combo.setFocus() 

    def keyPressEvent(self, event):
        if self.name_popup.isVisible() and event.key() == Qt.Key_Return:
            current_item = self.name_popup.currentItem()
            if current_item:
                self.select_student_from_popup(current_item)
        else:
            super().keyPressEvent(event)

    # ★ [최종 방어] 테이블에 넣을 때 한 번 더 풀네임 검사!
    def add_to_table(self):
        no = self.no_input.text()
        entered_name = self.name_input.text() # 현재 화면에 입력된 이름 (예: '철수')
        att_type = self.type_combo.currentText()
        reason = self.reason_input.text()

        if not entered_name or not no:
            QMessageBox.warning(self, "알림", "번호와 이름을 확인해주세요.")
            return

        # ★ DB를 다시 조회해서 정확한 풀네임으로 교체 (나이스 매크로용 방어)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_no = ? AND status = '재학'", (no,))
            result = cursor.fetchone()
            conn.close()

            if result:
                real_full_name = result[0] # DB에 있는 진짜 풀네임 (예: '김철수')
            else:
                QMessageBox.warning(self, "알림", "존재하지 않는 번호입니다.")
                return
        except Exception:
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # entered_name 대신 무조건 real_full_name(DB상 풀네임)을 테이블에 저장
        for col, text in enumerate([no, real_full_name, att_type, reason]):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)
            
        alert_item = QTableWidgetItem("💡 2일 연속 결석" if "질병 결석" in att_type else "")
        alert_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, alert_item)

        self.no_input.blockSignals(True)
        self.name_input.blockSignals(True)
        self.no_input.clear()
        self.name_input.clear()
        self.no_input.blockSignals(False)
        self.name_input.blockSignals(False)
        self.reason_input.clear()
        self.no_input.setFocus()

    def save_to_db(self):
        row_count = self.table.rowCount()
        if row_count == 0:
            QMessageBox.information(self, "알림", "저장할 데이터가 없습니다.")
            return

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        saved_count = 0
        for row in range(row_count):
            student_no = self.table.item(row, 0).text()
            att_type = self.table.item(row, 2).text()
            reason = self.table.item(row, 3).text()

            cursor.execute("SELECT id FROM students WHERE student_no = ? AND status = '재학'", (student_no,))
            student_data = cursor.fetchone()

            if student_data:
                student_id = student_data[0]
                cursor.execute('INSERT INTO attendance (date, student_id, attendance_type, reason) VALUES (?, ?, ?, ?)', (date_str, student_id, att_type, reason))
                saved_count += 1

        conn.commit()
        conn.close()

        QMessageBox.information(self, "저장 완료", f"{saved_count}건 저장 완료!")
        self.table.setRowCount(0)
        self.no_input.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AttendanceApp()
    ex.show()
    sys.exit(app.exec_())
