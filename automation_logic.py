import os
from pyhwpx import Hwp
import winreg
import tempfile
import requests
from helium import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pyautogui
import time

from google import genai
from google.genai import types
from google.cloud import storage

from PyQt6.QtCore import pyqtSignal, QObject
import json
import ast

class Automation_Worker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str, object)
    progress = pyqtSignal(str)

    def __init__(self, options):
        super().__init__()
        self.options = options
        self.browser = None
        self.is_running = True
        self.driver_path = None
        self.extracted_subjects = None

    def run(self):
        try:
            self.progress.emit("업로드 작업을 시작합니다.")
            # 웹페이지 활성화
            if not self._start_browser("https://ice.eduptl.kr/bpm_lgn_lg00_001.do"):
                return
            if not self.is_running: return
            # 로그인
            if not self.log_in():
                return
            if not self.is_running: return
            # 학급 시간표로 이동
            if not self.get_class_cur():
                return
            if not self.is_running: return
            # 시간표 추출
            if not self.extract_next_week_cur():
                return
            if not self.is_running: return
            # 시간표 입력
            if not self.send_week_cur():
                return
            if not self.is_running: return
            self.progress.emit("모든 작업을 완료했습니다.")
            self.finished.emit(self.browser)
        except Exception as e:
            self.error.emit(f"작업 중 알 수 없는 오류가 발생했습니다: {e}", self.browser)
            self.is_running = False


    def _get_webdriver(self):
        # 윈도우 버전 추출
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        local_version = version.split('.')[0]
        winreg.CloseKey(key)
        # 임시파일 생성
        temp_dir = tempfile.gettempdir()
        driver_path = os.path.join(temp_dir, "chromedriver.exe")
        # 클라우드에서 다운
        try:
            storage_URL = f"https://storage.googleapis.com/school_chrome_webdriver/{local_version}/chromedriver.exe"
            self.progress.emit('서버에서 크롬 드라이버를 다운받습니다.')
            response = requests.get(storage_URL)
            response.raise_for_status()
            with open(driver_path, "wb") as f:
                f.write(response.content)
            return driver_path
        except :
            self.error.emit("크롬 드라이버가 정상적으로 다운되지 않았습니다. 크롬 버전을 업데이트 주세요.", None)
            return None
        
# 크롬 설정, 사이트 접속
    def _start_browser(self, site):
        local_driver_path = self._get_webdriver()
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        service = Service(executable_path=local_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.progress.emit('나이스에 접속합니다.')
        try:
            # 여기를 수정해도 된다고?
            set_driver(driver)
            go_to(site)
            return True
        except Exception as e:
            self.error.emit(f'나이스 접속에 실패했습니다.{e}', None)
            return False

    def log_in(self):
        # 로컬네트워크 허용을 위한 시간
        time.sleep(10)
        password = self.options.get("neis_pw")
        try:
            self.progress.emit('로그인합니다.')
            click(S('//*[@id="btnLgn"]'))
            wait_until(S('//*[@id="kc_content_default"]/table/tbody/tr/td[2]/div/div[1]/table/tbody/tr/td[2]/input').exists)
            write(password, into=S('//*[@id="kc_content_default"]/table/tbody/tr/td[2]/div/div[1]/table/tbody/tr/td[2]/input'))
            press(ENTER)
            # try:
            #     wait_until(Text("로그아웃").exists, timeout_secs=10) 
            #     time.sleep(5) # 임시 대기 (실제 요소 확인으로 교체 권장)
            #     self.progress.emit('로그인 성공!')
            #     return True
            # except Exception:
            #     raise Exception("로그인 후 메인 화면으로 진입하지 못했습니다.")
        except Exception as e:
            self.error.emit(f"로그인에 실패하였습니다. 비밀번호를 확인해주세요.", None)
            return False

    def get_class_cur(self):
        self.progress.emit('학급 시간표로 이동합니다.')
        target_week = self.options.get("week_text")
        try:
            wait_until(S('//*[@id="https://ice.neis.go.kr/cmc_fcm_lg01_000.do?data=W0lPZDhSZ0JNWmlSTGhIakc1ZURyaUVKZ1h6c0xRV3B4NlpYU0ZHMWc0UHFxN2lVOWZuaUFTbUhFak1TT3dwV2RYYXRZUmpTRnp3VmN3eUM5L3N2MWRoQVl2YWNQOVNVY0JFa25iNFkwTWVwZ2JlTVJKYjJPOThnekwrVXJ5bTdYOFNjam9FRk9lQkJCN0tvUnF3MmpORXZ5blRURTMxdngrNzZyaXJoM3dzdz0="]').exists)
            click(S('//*[@id="https://ice.neis.go.kr/cmc_fcm_lg01_000.do?data=W0lPZDhSZ0JNWmlSTGhIakc1ZURyaUVKZ1h6c0xRV3B4NlpYU0ZHMWc0UHFxN2lVOWZuaUFTbUhFak1TT3dwV2RYYXRZUmpTRnp3VmN3eUM5L3N2MWRoQVl2YWNQOVNVY0JFa25iNFkwTWVwZ2JlTVJKYjJPOThnekwrVXJ5bTdYOFNjam9FRk9lQkJCN0tvUnF3MmpORXZ5blRURTMxdngrNzZyaXJoM3dzdz0="]'))
            click('학급담임')
            click('시간표관리')
            click('학급시간표관리')
            wait_until(Button('조회').exists)
            click('조회')
            if target_week >=15:
                click('13주차')
                time.sleep(1)
                # 가능하면 수정
                pyautogui.press('pagedown')
                click(str(target_week))
            else: click(str(target_week))
            return True
        except Exception as e:
            self.error.emit(f"학급 시간표로 이동하지 못하였습니다.", None)
            return False

# gemini 관련
    def _get_dev_api_key(self):
        try:
            api_key = None
            key_file_name = "gen-lang-client-0927426011-d03a25f67853.json"
            key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), key_file_name)
            storage_client = storage.Client.from_service_account_json(key_path)
            bucket_name = "secrets-key"
            secret_file_name = "secrets.json"
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(secret_file_name)
            secrets_string = blob.download_as_string()
            secrets_data = json.loads(secrets_string)
            return secrets_data.get("gemini_api_key")
        except Exception as e:
            self.error.emit(f"개발자 API 키 로드 실패", None)
            return False
        
#  pdf로 변환하는 코드
    def hwp_pdf_converter(self, original_path):
        self.progress.emit('파일 확장자를 확인합니다.')
        try:
            temp_dir = tempfile.gettempdir()
            pdf_name = "temp.pdf"
            temp_pdf_path = os.path.join(temp_dir, pdf_name)
            # 실제 변환 코드
            hwp = Hwp(visible=False)
            hwp.open(original_path)
            hwp.save_as(temp_pdf_path, format="PDF")
            time.sleep(1)
            hwp.quit()
            return temp_pdf_path
        except Exception as e:
            self.error.emit("파일 변환 실패. pdf로 변환해서 시도해주세요", None)
            return None

    def extract_next_week_cur(self):
        self.progress.emit('Gemini로 시간표 추출을 시작합니다.')
        target_file = self.options.get("file_path")
        target_class = self.options.get("class_number")
        ext = os.path.splitext(target_file)[1].lower()
        # 변환 여부 확인
        if ext in ['.hwp', '.hwpx']:
            converted_path = self.hwp_pdf_converter(target_file)
            if converted_path is None:
                self.error.emit('변환에 실패하여 종료합니다', None)
                return
            target_file = converted_path
        # Gemini 실행
        if self.options['use_dev_api']:
            api_key = self._get_dev_api_key()
            self.progress.emit("GEMINI_API_SUCCESS")
        else:
            api_key = self.options.get('private_api_key')
        try:
            with open(target_file, 'rb') as f:
                next_week_cur = f.read()
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-pro', contents=[types.Part.from_bytes(data=next_week_cur, mime_type ='application/pdf',), 
                                                    f"Analyze the timetable for {target_class}반 at the bottom of the file. The result must be a Python list in raw text format, without any other explanations or Markdown code blocks (```). 출력 예시: [['사회', '과학'], ['국어', '체육']]You must follow the rules below:The final result must contain exactly 5 inner lists (for Monday to Friday). If the content of the timetable is an event and not a subject, output an empty list [] for the day result.To emphasize again, the output must only be the list string that starts with a bracket [ and ends with a bracket ]. 과목 이름이 '자율'이면 '자율활동', '동아리'면 '동아리활동', '봉사'면 '봉사활동', '진로'면 진로활동'으로 출력해."
                                                    ]
                                                    )
            result = response.text
            result = result.strip('\n')
            result = ast.literal_eval(result)
            self.extracted_subjects = result
            self.progress.emit(f'시간표 추출을 완료했습니다. 해당 파일의 시간표는 \n{result}\n입니다.')
        except Exception as e:
            self.error.emit(f"Gemini 사용 중 오류가 발생하였습니다. api를 확인하거나 다시 시도해보세요.", None)
            return False
        finally:
            try:
                os.remove(target_file)
            except: pass
        return True
    
    def send_week_cur(self):
        self.progress.emit('NEIS에 시간표 입력을 시작합니다.')
        # 기본 정보 변수
        weekdays = ['월', '화', '수', '목', '금']
        sub_list = self.extracted_subjects
        sub_info = {item['subject']: item for item in self.options['subjects']}
        neis_name = self.options.get('neis_name')
        # 하나씩 꺼내서 추출
        for day_idx, daily_subjects in enumerate(sub_list):
            for period_idx, target_subject in enumerate(daily_subjects):
                found_info = sub_info.get(target_subject)
                # 예외 처리: 만약 과목 자체를 못 찾으면
                if not found_info:
                    sub_name = f"{target_subject}({neis_name}"
                else:
                    if found_info['type_idx'] == 0:
                        sub_name = f"{target_subject}({neis_name}"
                    else:
                        sub_name = f"{target_subject}({found_info['teacher']}"
                self.progress.emit(f'{sub_name}을 입력합니다.')
                # 실제 입력
                try: 
                    cell_xpath = f"//div[@aria-label='{period_idx+1}행 {weekdays[day_idx]}   ']"
                    rightclick(S(cell_xpath))
                    sub_xpath = f"//div[@class='cl-text' and contains(text(), '{sub_name}')]"
                    click(S(sub_xpath))
                except Exception as e:
                    self.error.emit(f"시간표 입력에 실패하였습니다. 시간표와 과목 정보를 확인해주세요.", None)
                    return False
        try:
            self.progress.emit('입력한 내용을 저장합니다.')
            click('저장')
            click('확인')
            click('확인')
        except Exception as e:
            self.error.emit("저장에 실패하였습니다. 입력된 내용을 확인한 뒤 직접 클릭하여 저장해주세요.", None)
        return True