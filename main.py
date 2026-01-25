import sys
import os
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QEvent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'attendance.db')

class AttendanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("나이스 출결 비서 - [학생 관리 고도화]")
        self.resize(1100, 850)
        self.setStyleSheet("background-color: #f8f9fa;")
        self.setFont(QFont("Malgun Gothic", 12))

        self.main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { font-size: 16px; font-weight: bold; padding: 12px 30px; background: #e9ecef; border: 1px solid #dee2e6; border-top-left-radius: 10px; border-top-right-radius: 10px; }
            QTabBar::tab:selected { background: white; border-bottom-color: white; color: #1c7ed6; }
        """)

        # 탭 구성
        self.attendance_tab = QWidget()
        self.init_attendance_tab()
        self.tabs.addTab(self.attendance_tab, "📝 출결입력")

        self.student_mgmt_tab = QWidget()
        self.init_student_mgmt_tab()
        self.tabs.addTab(self.student_mgmt_tab, "👥 학생 명단 관리")

        self.main_layout.addWidget(self.tabs)
        
        # 데이터 초기화
        self.load_today_attendance()
        self.load_all_students()

    # ---------------------------------------------------------
    # [탭 1] 출결 입력 UI 구성 (기존 기능)
    # ---------------------------------------------------------
    def init_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 날짜 선택
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("📅 오늘 날짜:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("background-color: white; border: 1px solid #ced4da; padding: 5px; font-size: 18px;")
        self.date_edit.dateChanged.connect(self.load_today_attendance)
        top_layout.addWidget(self.date_edit)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 입력 바
        input_container = QWidget()
        input_container.setStyleSheet("background-color: white; border: 1px solid #e9ecef; border-radius: 10px;")
        input_layout = QHBoxLayout(input_container)
        input_style = "QLineEdit { font-size: 18px; background-color: #f1f3f5; border: 1px solid #ced4da; border-radius: 8px; padding: 5px; font-weight: bold; }"
        
        self.no_input = QLineEdit(); self.no_input.setPlaceholderText("번호"); self.no_input.setFixedWidth(70); self.no_input.setFixedHeight(55); self.no_input.setAlignment(Qt.AlignCenter); self.no_input.setStyleSheet(input_style)
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("이름"); self.name_input.setFixedWidth(150); self.name_input.setFixedHeight(55); self.name_input.setAlignment(Qt.AlignCenter); self.name_input.setStyleSheet(input_style)
        self.name_input.installEventFilter(self)

        self.type_combo = QComboBox(); self.type_combo.setFixedHeight(55); self.type_combo.setFixedWidth(200); self.setup_colored_combobox()
        self.reason_input = QLineEdit(); self.reason_input.setPlaceholderText("사유"); self.reason_input.setFixedHeight(55); self.reason_input.setFixedWidth(250); self.reason_input.setStyleSheet(input_style)
        self.add_btn = QPushButton("➕ 추가 (Enter)"); self.add_btn.setFixedHeight(55); self.add_btn.setStyleSheet("background-color: #339af0; color: white; font-size: 18px; font-weight: bold; border-radius: 8px;")

        input_layout.addWidget(self.no_input); input_layout.addWidget(self.name_input); input_layout.addWidget(self.type_combo); input_layout.addWidget(self.reason_input); input_layout.addWidget(self.add_btn); input_layout.addStretch()
        layout.addWidget(input_container)

        # 동명이인 팝업
        self.name_popup = QListWidget(self)
        self.name_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint); self.name_popup.setAttribute(Qt.WA_ShowWithoutActivating); self.name_popup.setFocusPolicy(Qt.NoFocus); self.name_popup.hide()

        # 대기 명단
        draft_group = QGroupBox("📝 입력 대기 명단 (저장 전)")
        draft_layout = QVBoxLayout(draft_group)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["번호", "이름", "출결 종류", "사유", "⚠️ 참고사항", "삭제"])
        header = self.table.horizontalHeader(); header.setSectionResizeMode(QHeaderView.Stretch); header.setSectionResizeMode(5, QHeaderView.Fixed); self.table.setColumnWidth(5, 70)
        self.table.setFixedHeight(180)
        draft_layout.addWidget(self.table)
        layout.addWidget(draft_group)

        # 저장 버튼
        self.save_btn = QPushButton("⬇️ 저장하고 확정 현황으로 보내기 ⬇️")
        self.save_btn.setFixedHeight(50); self.save_btn.setStyleSheet("background-color: #40c057; color: white; font-size: 18px; font-weight: bold; border-radius: 10px;")
        layout.addWidget(self.save_btn)

        # 확정 현황
        saved_group = QGroupBox("✅ 오늘 확정된 출결 현황 (DB 저장 완료)")
        saved_layout = QVBoxLayout(saved_group)
        self.saved_table = QTableWidget(0, 5)
        self.saved_table.setHorizontalHeaderLabels(["번호", "이름", "출결 종류", "사유", "나이스 업로드"])
        self.saved_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.saved_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.saved_table.setFixedHeight(220)
        saved_layout.addWidget(self.saved_table)
        layout.addWidget(saved_group)

        # 이벤트 연결
        self.no_input.textChanged.connect(self.find_student_name)
        self.name_input.textChanged.connect(self.find_student_no) 
        self.reason_input.returnPressed.connect(self.add_to_table)
        self.add_btn.clicked.connect(self.add_to_table)
        self.name_popup.itemClicked.connect(self.select_student_from_popup) 
        self.save_btn.clicked.connect(self.save_to_db)

    # ---------------------------------------------------------
    # [탭 2] 학생 명단 관리 UI 구성 (신규 기능)
    # ---------------------------------------------------------
    def init_student_mgmt_tab(self):
        layout = QVBoxLayout(self.student_mgmt_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 상단 입력 바 (엔터 기능 추가)
        mgmt_input_group = QGroupBox("➕ 신규 학생 등록 및 전입")
        mgmt_input_layout = QHBoxLayout(mgmt_input_group)
        
        self.new_no_input = QLineEdit(); self.new_no_input.setPlaceholderText("번호"); self.new_no_input.setFixedWidth(80); self.new_no_input.setFixedHeight(45)
        self.new_name_input = QLineEdit(); self.new_name_input.setPlaceholderText("학생 이름"); self.new_name_input.setFixedWidth(150); self.new_name_input.setFixedHeight(45)
        
        # ★ [요구사항 1] 엔터 키 누르면 등록 기능 연결
        self.new_no_input.returnPressed.connect(self.add_new_student)
        self.new_name_input.returnPressed.connect(self.add_new_student)

        self.add_student_btn = QPushButton("등록하기 (Enter)")
        self.add_student_btn.setFixedHeight(45); self.add_student_btn.setStyleSheet("background-color: #1c7ed6; color: white; font-weight: bold; padding: 0 20px; border-radius: 5px;")
        self.add_student_btn.clicked.connect(self.add_new_student)

        mgmt_input_layout.addWidget(QLabel("번호:")); mg_input_layout = mgmt_input_layout
        mg_input_layout.addWidget(self.new_no_input); mg_input_layout.addWidget(QLabel("이름:")); mg_input_layout.addWidget(self.new_name_input)
        mg_input_layout.addWidget(self.add_student_btn); mg_input_layout.addStretch()
        layout.addWidget(mgmt_input_group)

        # 중앙: 학생 명단 테이블
        list_group = QGroupBox("📋 전체 학생 명부 (상태 클릭 시 변경 가능)")
        list_layout = QVBoxLayout(list_group)
        
        # 상태 변경일 컬럼 포함
        self.student_list_table = QTableWidget(0, 4)
        self.student_list_table.setHorizontalHeaderLabels(["학급 번호", "이름", "상태 (클릭하여 변경)", "상태 변경일"])
        self.student_list_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_list_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        list_layout.addWidget(self.student_list_table)
        layout.addWidget(list_group)

        # 하단 새로고침 버튼만 유지 (전출 버튼 삭제)
        self.refresh_btn = QPushButton("🔄 명단 새로고침"); self.refresh_btn.setFixedHeight(45)
        self.refresh_btn.clicked.connect(self.load_all_students)
        layout.addWidget(self.refresh_btn)

    # ---------------------------------------------------------
    # 학생 관리 탭 기능 로직 (상태 드롭다운 및 재전입 처리)
    # ---------------------------------------------------------
    def load_all_students(self):
        self.student_list_table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("SELECT student_no, name, status, status_date, id FROM students ORDER BY student_no ASC")
            rows = cursor.fetchall(); conn.close()

            for r in rows:
                row_idx = self.student_list_table.rowCount()
                self.student_list_table.insertRow(row_idx)
                
                # 번호, 이름
                for col in [0, 1]:
                    item = QTableWidgetItem(str(r[col])); item.setTextAlignment(Qt.AlignCenter)
                    self.student_list_table.setItem(row_idx, col, item)
                
                # ★ [요구사항 3] 상태 드롭다운 (재학, 전출, 면제)
                status_combo = QComboBox()
                status_combo.addItems(["재학", "전출", "면제"])
                status_combo.setCurrentText(r[2])
                # 학생 고유 ID를 콤보박스 속성에 숨겨둠
                status_combo.setProperty("student_id", r[4])
                status_combo.currentTextChanged.connect(self.update_student_status_db)
                self.student_list_table.setCellWidget(row_idx, 2, status_combo)

                # 상태 변경일
                date_item = QTableWidgetItem(str(r[3]) if r[3] else "-")
                date_item.setTextAlignment(Qt.AlignCenter)
                self.student_list_table.setItem(row_idx, 3, date_item)
        except Exception as e: print(f"명단 로드 오류: {e}")

    def update_student_status_db(self, new_status):
        """콤보박스 변경 시 즉시 DB 반영"""
        combo = self.sender()
        student_id = combo.property("student_id")
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("UPDATE students SET status = ?, status_date = ? WHERE id = ?", (new_status, today, student_id))
            conn.commit(); conn.close()
            # 날짜 표시 갱신을 위해 새로고침 없이 해당 행의 날짜만 살짝 변경 (UX)
            self.load_all_students() 
        except Exception as e: QMessageBox.critical(self, "오류", f"상태 변경 실패: {e}")

    def add_new_student(self):
        """학생 추가 (재전입 로직 포함)"""
        no = self.new_no_input.text(); name = self.new_name_input.text()
        if not no or not name: return
        
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            
            # ★ [요구사항 4] 재전입 학생인지 확인 (이름과 번호가 일치하는 전출/면제자 검색)
            cursor.execute("SELECT id, status FROM students WHERE student_no = ? AND name = ?", (no, name))
            existing = cursor.fetchone()
            
            if existing:
                student_id, current_status = existing
                if current_status != '재학':
                    reply = QMessageBox.question(self, "재전입 확인", 
                        f"[{name}] 학생은 현재 '{current_status}' 상태입니다.\n이 기록을 사용하여 '재학' 상태로 변경(재전입)하시겠습니까?", 
                        QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        cursor.execute("UPDATE students SET status = '재학', status_date = ? WHERE id = ?", (today, student_id))
                        conn.commit(); conn.close()
                        self.load_all_students(); self.new_no_input.clear(); self.new_name_input.clear(); return

            # 중복이 아니면 신규 등록
            cursor.execute("INSERT INTO students (student_no, name, status, status_date) VALUES (?, ?, '재학', ?)", (no, name, today))
            conn.commit(); conn.close()
            self.new_no_input.clear(); self.new_name_input.clear()
            self.load_all_students()
        except Exception as e: QMessageBox.critical(self, "오류", f"등록 실패: {e}")

    def process_transfer_out(self):
        """선택된 학생을 전출 상태로 변경"""
        selected = self.student_list_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "알림", "전출 처리할 학생을 목록에서 선택해주세요."); return
        
        student_name = self.student_list_table.item(selected, 1).text()
        student_id = self.student_list_table.item(selected, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(self, "확인", f"[{student_name}] 학생을 전출 처리하시겠습니까?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
                cursor.execute("UPDATE students SET status = '전출', status_date = ? WHERE id = ?", (today, student_id))
                conn.commit(); conn.close()
                self.load_all_students() # 리스트 갱신
            except Exception as e: QMessageBox.critical(self, "오류", f"처리 실패: {e}")

    # (이하 기존 출결 입력 및 DB 연동 함수들은 이전과 동일하게 유지... 생략 없이 포함)
    def setup_colored_combobox(self):
        model = QStandardItemModel()
        items = [
            ("🟢 출석인정 결석", "#2e7d32", "white"), ("🟢 출석인정 지각", "#43a047", "white"), ("🟢 출석인정 조퇴", "#66bb6a", "black"), ("🟢 출석인정 결과", "#a5d6a7", "black"),
            ("🔴 질병 결석", "#c62828", "white"), ("🔴 질병 지각", "#e53935", "white"), ("🔴 질병 조퇴", "#ef5350", "black"), ("🔴 질병 결과", "#ffcdd2", "black"),
            ("⚫ 미인정 결석", "#212121", "white"), ("⚫ 미인정 지각", "#616161", "white"), ("⚫ 미인정 조퇴", "#9e9e9e", "white"), ("⚫ 미인정 결과", "#e0e0e0", "black"),
            ("🟣 기타 결석", "#4527a0", "white"), ("🟣 기타 지각", "#5e35b1", "white"), ("🟣 기타 조퇴", "#7e57c2", "white"), ("🟣 기타 결과", "#b39ddb", "black")
        ]
        for text, bg_color, text_color in items:
            item = QStandardItem(text); item.setBackground(QColor(bg_color)); item.setForeground(QColor(text_color)); item.setFont(QFont("Malgun Gothic", 16, QFont.Bold)); model.appendRow(item)
        self.type_combo.setModel(model)
        self.type_combo.setStyleSheet("QComboBox { font-size: 18px; background-color: white; border: 1px solid #ced4da; border-radius: 8px; padding: 5px; font-weight: bold; }")

    def eventFilter(self, obj, event):
        if obj == self.name_input and event.type() == QEvent.KeyPress and self.name_popup.isVisible():
            key = event.key()
            if key == Qt.Key_Down:
                cur = self.name_popup.currentRow()
                if cur < self.name_popup.count()-1: self.name_popup.setCurrentRow(cur+1)
                return True
            elif key == Qt.Key_Up:
                cur = self.name_popup.currentRow()
                if cur > 0: self.name_popup.setCurrentRow(cur-1)
                return True
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                item = self.name_popup.currentItem()
                if item: self.select_student_from_popup(item)
                return True
        return super().eventFilter(obj, event)

    def find_student_name(self):
        no = self.no_input.text()
        if not no: self.name_input.blockSignals(True); self.name_input.clear(); self.name_input.blockSignals(False); return
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("SELECT name FROM students WHERE student_no = ? AND status = '재학'", (no,))
            res = cursor.fetchone(); conn.close()
            if res: self.name_input.blockSignals(True); self.name_input.setText(res[0]); self.name_input.blockSignals(False)
        except: pass

    def find_student_no(self):
        name = self.name_input.text()
        if not name: self.no_input.blockSignals(True); self.no_input.clear(); self.no_input.blockSignals(False); self.name_popup.hide(); return
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
            cursor.execute("SELECT student_no, name FROM students WHERE name LIKE ? AND status = '재학'", (f"%{name}%",))
            res = cursor.fetchall(); conn.close()
            if res:
                self.name_popup.clear()
                for r in res: self.name_popup.addItem(f"{r[0]}번 {r[1]}")
                pos = self.name_input.mapToGlobal(self.name_input.rect().bottomLeft())
                self.name_popup.setGeometry(pos.x(), pos.y(), self.name_input.width(), 100); self.name_popup.show(); self.name_popup.setCurrentRow(0)
                if len(res) == 1: self.no_input.blockSignals(True); self.no_input.setText(str(res[0][0])); self.no_input.blockSignals(False)
            else: self.name_popup.hide()
        except: pass

    def select_student_from_popup(self, item):
        p = item.text().split("번 ")
        self.no_input.blockSignals(True); self.name_input.blockSignals(True)
        self.no_input.setText(p[0]); self.name_input.setText(p[1])
        self.no_input.blockSignals(False); self.name_input.blockSignals(False)
        self.name_popup.hide(); self.type_combo.setFocus()

    def add_to_table(self):
        no = self.no_input.text(); name = self.name_input.text(); t = self.type_combo.currentText(); r_text = self.reason_input.text()
        if not name or not no: return
        try:
            conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
            cur.execute("SELECT name FROM students WHERE student_no = ? AND status = '재학'", (no,))
            res = cur.fetchone(); conn.close()
            if res: full_n = res[0]
            else: return
        except: return
        r = self.table.rowCount(); self.table.insertRow(r)
        for c, txt in enumerate([no, full_n, t, r_text]):
            item = QTableWidgetItem(txt); item.setTextAlignment(Qt.AlignCenter); self.table.setItem(r, c, item)
        alert = QTableWidgetItem("💡 2일 연속 결석" if "질병 결석" in t else "")
        alert.setTextAlignment(Qt.AlignCenter); self.table.setItem(r, 4, alert)
        d_btn = QPushButton("❌"); d_btn.setStyleSheet("background-color: #ffc9c9; color: #c92a2a; font-weight: bold; border-radius: 5px;")
        d_btn.clicked.connect(self.delete_row); self.table.setCellWidget(r, 5, d_btn)
        self.no_input.blockSignals(True); self.name_input.blockSignals(True); self.no_input.clear(); self.name_input.clear()
        self.no_input.blockSignals(False); self.name_input.blockSignals(False); self.reason_input.clear(); self.no_input.setFocus()

    def delete_row(self):
        idx = self.table.indexAt(self.sender().pos())
        if idx.isValid(): self.table.removeRow(idx.row())

    def load_today_attendance(self):
        dt = self.date_edit.date().toString("yyyy-MM-dd"); self.saved_table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
            cur.execute("SELECT s.student_no, s.name, a.attendance_type, a.reason, a.is_uploaded FROM attendance a JOIN students s ON a.student_id = s.id WHERE a.date = ? ORDER BY s.student_no ASC", (dt,))
            res = cur.fetchall(); conn.close()
            for r in res:
                row = self.saved_table.rowCount(); self.saved_table.insertRow(row)
                for c, txt in enumerate([str(r[0]), r[1], r[2], r[3]]):
                    it = QTableWidgetItem(txt); it.setTextAlignment(Qt.AlignCenter); self.saved_table.setItem(row, c, it)
                s_txt = "✅ 완료" if r[4] == 1 else "⏳ 대기"
                s_it = QTableWidgetItem(s_txt); s_it.setTextAlignment(Qt.AlignCenter)
                if r[4] == 1: s_it.setForeground(QColor("#2b8a3e"))
                self.saved_table.setItem(row, 4, s_it)
        except: pass

    def save_to_db(self):
        cnt = self.table.rowCount()
        if cnt == 0: return
        dt = self.date_edit.date().toString("yyyy-MM-dd"); conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        for r in range(cnt):
            no = self.table.item(r, 0).text(); t = self.table.item(r, 2).text(); reas = self.table.item(r, 3).text()
            cur.execute("SELECT id FROM students WHERE student_no = ? AND status = '재학'", (no,))
            s_data = cur.fetchone()
            if s_data: cur.execute('INSERT INTO attendance (date, student_id, attendance_type, reason) VALUES (?, ?, ?, ?)', (dt, s_data[0], t, reas))
        conn.commit(); conn.close()
        self.table.setRowCount(0); self.load_today_attendance(); self.no_input.setFocus()

if __name__ == '__main__':
    app = QApplication(sys.argv); ex = AttendanceApp(); ex.show(); sys.exit(app.exec_())