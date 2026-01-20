import sys
import datetime
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QRadioButton, QButtonGroup, QDateEdit,
    QComboBox, QPushButton, QScrollArea, QFrame, QFileDialog, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QSettings, QThread
from automation_logic import Automation_Worker

class SubjectRow(QWidget):
    """과목 정보 한 줄을 관리하는 커스텀 위젯"""
    def __init__(self, parent_layout, subject="", teacher_idx=0, teacher_name=""):
        super().__init__()
        self.parent_layout = parent_layout
        self.init_data = (subject, teacher_idx, teacher_name) # 초기값 저장
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. 과목 이름 입력
        self.subject_name = QLineEdit()
        self.subject_name.setPlaceholderText("과목명 (예: 국어)")
        self.subject_name.setText(self.init_data[0])
        
        # 2. 담임/비담임 선택 드롭다운
        self.teacher_type = QComboBox()
        self.teacher_type.addItems(["담임", "전담(직접 입력)"])
        self.teacher_type.setCurrentIndex(self.init_data[1])
        self.teacher_type.currentIndexChanged.connect(self.toggle_teacher_input)

        # 3. 전담 선생님 이름 입력 (초기에는 숨김 or 비활성)
        self.teacher_name = QLineEdit()
        self.teacher_name.setPlaceholderText("선생님 성함")
        self.teacher_name.setText(self.init_data[2])
        
        # 초기 상태 설정
        self.toggle_teacher_input(self.init_data[1])

        # 4. 삭제 버튼
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setFixedWidth(50)
        self.delete_btn.setStyleSheet("""
            QPushButton { background-color: #ff6b6b; color: white; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #fa5252; }
        """)
        self.delete_btn.clicked.connect(self.delete_row)

        layout.addWidget(self.subject_name, 2)
        layout.addWidget(self.teacher_type, 2)
        layout.addWidget(self.teacher_name, 2)
        layout.addWidget(self.delete_btn, 0)
        self.setLayout(layout)

    def toggle_teacher_input(self, index):
        # 0: 담임, 1: 전담(입력)
        if index == 0:
            self.teacher_name.setEnabled(False)
            self.teacher_name.setStyleSheet("background-color: #f0f0f0;")
            # self.teacher_name.clear() # 저장된 값을 유지하기 위해 clear는 하지 않음 (선택 사항)
        else:
            self.teacher_name.setEnabled(True)
            self.teacher_name.setStyleSheet("background-color: white;")

    def delete_row(self):
        # 부모 레이아웃에서 나 자신을 제거하고 삭제
        self.parent_layout.removeWidget(self)
        self.deleteLater()
    
    def get_data(self):
        """현재 입력된 데이터를 반환 (저장용)"""
        return {
            "subject": self.subject_name.text(),
            "type_idx": self.teacher_type.currentIndex(),
            "teacher": self.teacher_name.text()
        }


class AutoUploaderUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("주간학습안내 자동 업로더")
        self.setGeometry(100, 100, 550, 700)
        
        # 설정 관리자 초기화 (회사명, 앱이름)
        self.settings = QSettings("MySchoolApp", "AutoUploader")
        
        self.init_ui()
        self.apply_stylesheet()
        
        # 프로그램 시작 시 설정 불러오기
        self.load_settings()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # --- 1. API 선택 섹션 ---
        self.create_api_section()

        # --- 2. 나이스 정보 섹션 ---
        self.create_neis_section()

        # --- 3. 날짜 및 주차 섹션 ---
        self.create_date_section()

        # --- 4. 과목 정보 섹션 (동적 추가) ---
        self.create_subject_section()

        # --- 5. 파일 경로 섹션 ---
        self.create_file_section()

        # --- 6. 업로드 버튼 ---
        self.upload_btn = QPushButton("업로드 시작")
        self.upload_btn.setFixedHeight(50)
        self.upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_btn.setObjectName("UploadBtn")
        self.upload_btn.clicked.connect(self.on_upload_click)
        self.main_layout.addWidget(self.upload_btn)

        # 빈 공간 채우기
        self.main_layout.addStretch()

        # --- 7. 상태 표시줄 ---
        self.statusBar().setStyleSheet("QStatusBar { padding: 5px; background-color: #e6e6e6; }")
        # 클릭 가능한 저작권 라벨 생성
        copyright_label = QLabel()
        target_url = "https://moobosu.vercel.app/"
        copyright_label.setText(f'© 2025. tcherlwh@gmail.com All rights reserved.  <a href="{target_url}" style="color: #0000FF; text-decoration: underline; margin-left: 10px;">웹페이지 방문</a>')
        copyright_label.setOpenExternalLinks(True)  # 외부 브라우저 허용
        copyright_label.setStyleSheet("font-size: 9pt; color: #555; font-weight: normal;")
        # 상태 표시줄에 영구 위젯으로 추가 (오른쪽 정렬)
        self.statusBar().addPermanentWidget(copyright_label)

    def create_api_section(self):
        group = QFrame()
        group.setObjectName("Card")
        layout = QVBoxLayout(group)

        # 라디오 버튼
        radio_layout = QHBoxLayout()
        self.radio_dev = QRadioButton("개발자 API 사용")
        self.radio_private = QRadioButton("개인 API 사용")
        self.radio_dev.setChecked(True)
        
        self.btn_group = QButtonGroup()
        self.btn_group.addButton(self.radio_dev)
        self.btn_group.addButton(self.radio_private)
        
        radio_layout.addWidget(self.radio_dev)
        radio_layout.addWidget(self.radio_private)
        layout.addLayout(radio_layout)

        # 상태 메시지 / 입력창
        self.lbl_dev_msg = QLabel("⚠️ 개발자 API는 하루에 3회로 이용이 제한됩니다.")
        self.lbl_dev_msg.setStyleSheet("color: #e67e22; font-weight: bold; margin-top: 5px;")
        
        self.input_private_key = QLineEdit()
        self.input_private_key.setPlaceholderText("개인 API Key를 입력하세요")
        self.input_private_key.setVisible(False)

        layout.addWidget(self.lbl_dev_msg)
        layout.addWidget(self.input_private_key)

        # 시그널 연결
        self.radio_dev.toggled.connect(self.toggle_api_ui)

        self.main_layout.addWidget(group)

    def toggle_api_ui(self):
        is_dev = self.radio_dev.isChecked()
        self.lbl_dev_msg.setVisible(is_dev)
        self.input_private_key.setVisible(not is_dev)

    def create_neis_section(self):
        group = QFrame()
        group.setObjectName("Card")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("나이스 정보"))

        form_layout = QHBoxLayout()
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("이름")
        
        self.input_pw = QLineEdit()
        self.input_pw.setPlaceholderText("비밀번호")
        self.input_pw.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_pw_toggle = QPushButton("👁️")
        self.btn_pw_toggle.setFixedWidth(30)
        self.btn_pw_toggle.setCheckable(True)
        self.btn_pw_toggle.clicked.connect(self.toggle_password)

        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_pw)
        form_layout.addWidget(self.btn_pw_toggle)

        layout.addLayout(form_layout)
        self.main_layout.addWidget(group)

    def toggle_password(self):
        if self.btn_pw_toggle.isChecked():
            self.input_pw.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_pw_toggle.setText("🔒")
        else:
            self.input_pw.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_pw_toggle.setText("👁️")

    def create_date_section(self):
        group = QFrame()
        group.setObjectName("Card")
        layout = QVBoxLayout(group)
        
        # 1. 섹션 제목 (가운데 정렬)
        lbl_semester = QLabel("학기 정보")
        lbl_semester.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_semester.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_semester)

        # 2. 날짜와 주차를 담을 컨테이너 (가운데 정렬을 위해)
        container_layout = QHBoxLayout()
        container_layout.addStretch(1) # 왼쪽 여백

        # [학기 시작 날짜] 그룹
        date_group = QVBoxLayout()
        lbl_date = QLabel("학기 시작 날짜")
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_date.setStyleSheet("font-size: 12px; color: #555;")
        
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate())
        self.date_start.setFixedWidth(130) # 적절한 너비
        self.date_start.setStyleSheet("padding: 5px;")
        self.date_start.dateChanged.connect(self.calculate_week)
        
        date_group.addWidget(lbl_date)
        date_group.addWidget(self.date_start)
        container_layout.addLayout(date_group)

        # 화살표 아이콘 (간격 조정)
        container_layout.addSpacing(20)
        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("font-size: 18px; color: #888; margin-top: 15px;") # 위치 미세 조정
        container_layout.addWidget(lbl_arrow)
        container_layout.addSpacing(20)

        # [주차 선택] 그룹
        week_group = QVBoxLayout()
        lbl_week = QLabel("업로드 할 주차")
        lbl_week.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_week.setStyleSheet("font-size: 12px; color: #555;")

        self.combo_week = QComboBox()
        self.combo_week.addItems([f"{i}주차" for i in range(1, 33)])
        self.combo_week.setFixedWidth(100)
        self.combo_week.setStyleSheet("padding: 5px;")
        # setEditable(False)가 기본값이므로 숫자 외 입력 불가 (드롭다운 선택만 가능)

        week_group.addWidget(lbl_week)
        week_group.addWidget(self.combo_week)
        container_layout.addLayout(week_group)

        container_layout.addStretch(1) # 오른쪽 여백
        
        layout.addLayout(container_layout)
        self.main_layout.addWidget(group)

    def calculate_week(self):
        start_date = self.date_start.date().toPyDate()
        today = datetime.date.today()
        
        delta = today - start_date
        current_week = (delta.days // 7) + 1
        target_week = current_week + 1
        
        if 1 <= target_week <= 32:
            self.combo_week.setCurrentIndex(target_week - 1)
        else:
            self.combo_week.setCurrentIndex(0)

    def create_subject_section(self):
        group = QFrame()
        group.setObjectName("Card")
        layout = QVBoxLayout(group)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("과목 정보"))
        header_layout.addStretch()
        
        btn_add_subject = QPushButton("+ 과목 추가")
        btn_add_subject.setStyleSheet("background-color: #2ecc71; color: white; border: none; border-radius: 4px; padding: 5px 10px;")
        btn_add_subject.clicked.connect(lambda: self.add_subject_row()) # 인자 없이 호출
        header_layout.addWidget(btn_add_subject)
        
        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setFixedHeight(200)
        
        scroll_content = QWidget()
        self.subject_list_layout = QVBoxLayout(scroll_content)
        self.subject_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 초기 행 추가는 load_settings에서 처리하므로 여기서는 제거

        grade_layout = QHBoxLayout()
        grade_layout.addWidget(QLabel("학년:"))
        self.combo_grade = QComboBox()
        self.combo_grade.addItems([f"{i}학년" for i in range(1, 7)])
        self.combo_grade.setFixedWidth(80)
        grade_layout.addWidget(self.combo_grade)
        
        grade_layout.addSpacing(20) 

        # 2. 반 입력
        grade_layout.addWidget(QLabel("반:"))
        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("숫자만 입력")
        self.input_class.setFixedWidth(80)
        self.input_class.setAlignment(Qt.AlignmentFlag.AlignCenter) # 가운데 정렬
        grade_layout.addWidget(self.input_class)
        grade_layout.addWidget(QLabel("반")) # '반' 텍스트 추가

        grade_layout.addStretch()
        
        layout.addLayout(grade_layout)
        self.main_layout.addWidget(group)

    def add_subject_row(self, subject="", teacher_idx=0, teacher_name=""):
        # 저장된 값이 있으면 그 값으로, 없으면 빈 값으로 행 추가
        row = SubjectRow(self.subject_list_layout, subject, teacher_idx, teacher_name)
        self.subject_list_layout.addWidget(row)

    def create_file_section(self):
        group = QFrame()
        group.setObjectName("Card")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("파일 경로"))

        file_layout = QHBoxLayout()
        
        self.combo_file = QComboBox()
        self.combo_file.setEditable(True)
        self.combo_file.setPlaceholderText("pdf 파일로 올려주세요!")
        self.combo_file.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btn_browse = QPushButton("찾아보기...")
        btn_browse.clicked.connect(self.browse_file)

        file_layout.addWidget(self.combo_file)
        file_layout.addWidget(btn_browse)

        layout.addLayout(file_layout)
        self.main_layout.addWidget(group)

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "PDF 파일 선택", "", "PDF Files (*.pdf);;All Files (*)")
        if file_name:
            self.combo_file.insertItem(0, file_name)
            self.combo_file.setCurrentIndex(0)

    def update_status_and_count(self, msg):
        """Worker의 진행률 메시지를 상태표시줄에 표시하고, API 사용 횟수를 카운트합니다."""
        if msg == "GEMINI_API_SUCCESS":
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            last_use_date = self.settings.value("dev_api_last_use_date", "")
            count = self.settings.value("dev_api_use_count", 0, type=int)

            if last_use_date == today_str:
                self.settings.setValue("dev_api_use_count", count + 1)
            else: # 날짜가 다르면 새로 카운트
                self.settings.setValue("dev_api_last_use_date", today_str)
                self.settings.setValue("dev_api_use_count", 1)
            self.statusBar().showMessage("Gemini API 사용 횟수를 기록했습니다.")
        else:
            self.statusBar().showMessage(msg)

    def on_upload_click(self):
        # 1. UI에서 데이터 수집
        options = {
            "use_dev_api": self.radio_dev.isChecked(),
            "private_api_key": self.input_private_key.text(),
            "neis_name": self.input_name.text(),
            "neis_pw": self.input_pw.text(),
            "start_date": self.date_start.date().toString("yyyy-MM-dd"),
            "week_text": self.combo_week.currentText(),
            "grade_text": self.combo_grade.currentText(),
            "class_number": self.input_class.text().strip(),
            "file_path": self.combo_file.currentText(),
            "subjects": []
        }
        
        # 개발자 API 사용 제한 확인
        if options["use_dev_api"]:
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            last_use_date = self.settings.value("dev_api_last_use_date", "")
            count = self.settings.value("dev_api_use_count", 0, type=int)

            if last_use_date == today_str and count >= 3:
                QMessageBox.warning(self, "사용량 초과", "개발자 API는 하루에 3회까지 사용할 수 있습니다.\n내일 다시 시도해주세요.")
                return

        # 2. 과목 정보 리스트 수집
        for i in range(self.subject_list_layout.count()):
            widget = self.subject_list_layout.itemAt(i).widget()
            if isinstance(widget, SubjectRow):
                options["subjects"].append(widget.get_data())

        # 3. 세팅 확인
        if not options["neis_name"] or not options["neis_pw"]:
            QMessageBox.warning(self, "나이스 정보를 확인해주세요.")
        if not options['file_path']:
            QMessageBox.warning(self, "파일 경로를 확인해주세요")
        if not options["use_dev_api"] and not options["private_api_key"]:
            QMessageBox.warning(self, "api 정보를 확인해주세요.")
            self.input_private_key.setFocus()
        if not options['class_number']:
            QMessageBox.warning(self, "입력 오류", "반 정보를 입력해주세요.")
            self.input_class.setFocus()

        print("수집된 데이터:", options)

        self.thread = QThread()
        self.worker = Automation_Worker(options)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        self.worker.progress.connect(self.update_status_and_count)
        self.worker.error.connect(self.handle_worker_error) # 에러 처리 메서드 연결
        self.worker.finished.connect(self.handle_worker_finished) # 완료 처리 메서드 연결

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # 작업 완료/실패 시 상태표시줄 메시지 초기화
        self.worker.finished.connect(lambda: self.statusBar().clearMessage())
        self.worker.error.connect(lambda msg, browser: self.statusBar().clearMessage())

        self.upload_btn.setEnabled(False)
        self.upload_btn.setText("작업 중... (취소 불가)")
        self.thread.start()

    def handle_worker_error(self, error_msg, browser):
        """작업 중 에러가 발생했을 때"""
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("업로드 시작")
        self.statusBar().clearMessage()
        QMessageBox.critical(self, "오류 발생", error_msg)
        if browser: 
            try:
                browser.quit()
            except Exception:
                pass

    def handle_worker_finished(self, browser):
        """작업이 성공적으로 끝났을 때"""
        self.upload_btn.setEnabled(True)
        self.upload_btn.setText("업로드 시작")
        self.statusBar().clearMessage()
        QMessageBox.information(self, "성공", "모든 작업이 완료되었습니다!")
        
        if browser:
            reply = QMessageBox.question(self, '작업 완료', 
                                         '브라우저 창을 닫으시겠습니까?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                browser.quit()

    def closeEvent(self, event):
        """프로그램 종료 시 설정 저장"""
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        """현재 UI 상태를 레지스트리/설정파일에 저장"""
        self.settings.setValue("use_dev_api", self.radio_dev.isChecked())
        self.settings.setValue("private_api_key", self.input_private_key.text())
        self.settings.setValue("neis_name", self.input_name.text())
        self.settings.setValue("neis_pw", self.input_pw.text())
        self.settings.setValue("start_date", self.date_start.date().toString("yyyy-MM-dd"))
        self.settings.setValue("grade_index", self.combo_grade.currentIndex())
        self.settings.setValue("class_number", self.input_class.text())
        self.settings.setValue("last_file_path", self.combo_file.currentText())
        
        # 과목 정보 리스트 저장 (JSON 변환)
        subjects = []
        for i in range(self.subject_list_layout.count()):
            widget = self.subject_list_layout.itemAt(i).widget()
            if isinstance(widget, SubjectRow):
                subjects.append(widget.get_data())
        self.settings.setValue("subjects", json.dumps(subjects))

    def load_settings(self):
        """저장된 설정을 불러와 UI에 반영"""
        # 1. API 설정
        use_dev = self.settings.value("use_dev_api", True, type=bool)
        self.radio_dev.setChecked(use_dev)
        self.radio_private.setChecked(not use_dev)
        self.input_private_key.setText(self.settings.value("private_api_key", ""))
        self.toggle_api_ui()

        # 2. 나이스 정보
        self.input_name.setText(self.settings.value("neis_name", ""))
        self.input_pw.setText(self.settings.value("neis_pw", ""))

        # 3. 날짜 (저장된 날짜가 없으면 오늘 날짜)
        date_str = self.settings.value("start_date", QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_start.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        # 날짜를 불러온 후, 자동으로 이번 주 주차를 계산해서 선택함 (요구사항 반영)
        self.calculate_week()

        # 4. 과목 정보
        self.combo_grade.setCurrentIndex(self.settings.value("grade_index", 0, type=int))
        self.input_class.setText(self.settings.value("class_number", ""))
        
        # 저장된 과목 리스트 복원
        subjects_json = self.settings.value("subjects", "[]")
        try:
            subjects = json.loads(subjects_json)
            if not subjects: # 저장된 게 없으면 기본 2줄
                self.add_subject_row()
                self.add_subject_row()
            else:
                for subj in subjects:
                    self.add_subject_row(subj["subject"], subj["type_idx"], subj["teacher"])
        except json.JSONDecodeError:
            self.add_subject_row()
            self.add_subject_row()

        # 5. 파일 경로
        last_file = self.settings.value("last_file_path", "")
        if last_file:
            self.combo_file.setCurrentText(last_file)

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f6f9;
            }
            QLabel {
                font-size: 14px;
                color: #333;
                font-weight: 600;
            }
            QLineEdit, QDateEdit, QComboBox {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border: 2px solid #3498db;
            }
            QFrame#Card {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton#UploadBtn {
                background-color: #3498db;
                font-size: 16px;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoUploaderUI()
    window.show()
    sys.exit(app.exec())