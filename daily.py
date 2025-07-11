import random
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def get_random_problem_id(min_id=1000, max_id=2000):
    """1000~2000 사이의 랜덤 문제 ID 생성"""
    return random.randint(min_id, max_id)

def get_problem_difficulty(problem_id):
    """Solved.ac API로 문제 난이도 확인 (티어 1~30)"""
    url = f"https://solved.ac/api/v3/problem/lookup?problemIds={problem_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            level = data[0].get("level", 0)
            return level  # 티어 (1: 브론즈 V, 10: 실버 I, 15: 골드 I 등)
        return None
    except Exception as e:
        print(f"Solved.ac API 오류: {str(e)}")
        return None

def fetch_problem_page(problem_id):
    """Selenium으로 문제 페이지 가져오기"""
    url = f"https://www.acmicpc.net/problem/{problem_id}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
    options.add_argument("accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    
    # ChromeDriver 경로 지정 (본인 환경에 맞게 수정)
    # service = Service('/path/to/chromedriver')
    driver = webdriver.Chrome(options=options)  # PATH에 ChromeDriver가 있으면 service 불필요
    
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))  # 페이지 로드 대기
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup
    except Exception as e:
        print(f"Selenium 실패: {str(e)}")
        return None
    finally:
        driver.quit()

def extract_problem_details(soup):
    """문제 제목, 설명, 입력, 출력 추출"""
    title_tag = soup.select_one("#problem_title")
    if not title_tag:
        raise RuntimeError("문제 제목을 찾을 수 없습니다.")
    title = title_tag.get_text(strip=True)

    desc_div = soup.select_one("#problem_description")
    input_div = soup.select_one("#problem_input")
    output_div = soup.select_one("#problem_output")

    if not (desc_div and input_div and output_div):
        raise RuntimeError("설명/입력/출력 중 하나라도 누락되었습니다.")

    desc = desc_div.get_text("\n", strip=True)
    input_desc = input_div.get_text("\n", strip=True)
    output_desc = output_div.get_text("\n", strip=True)

    return title, desc, input_desc, output_desc

def sanitize_filename(name):
    """파일 이름에 사용할 수 없는 문자 제거"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip().replace(" ", "_")

def write_template_files(problem_id, title, description, input_fmt, output_fmt):
    """Python과 Java 템플릿 파일 생성"""
    safe_title = sanitize_filename(title)
    base_filename = f"{problem_id}_{safe_title}"

    python_code = f"""\"\"\"
Problem {problem_id}: {title}

{description}

[Input]
{input_fmt}

[Output]
{output_fmt}
\"\"\"

def main():
    # TODO: Implement solution
    pass

if __name__ == "__main__":
    main()
"""

    classname = f"Problem{problem_id}"
    java_code = f"""/*
Problem {problem_id}: {title}

{description}

[Input]
{input_fmt}

[Output]
{output_fmt}
*/

import java.util.*;

public class {classname} {{
    public static void main(String[] args) {{
        Scanner sc = new Scanner(System.in);
        // TODO: Implement solution
        sc.close();
    }}
}}
"""

    py_path = f"{base_filename}.py"
    java_path = f"{base_filename}.java"

    with open(py_path, "w", encoding="utf-8") as f:
        f.write(python_code)

    with open(java_path, "w", encoding="utf-8") as f:
        f.write(java_code)

    return py_path, java_path

def main(desired_difficulty="bronze-silver"):
    """메인 함수: 원하는 난이도(티어 1~10, 브론즈~실버)로 문제 선택"""
    # 난이도 범위 설정 (Solved.ac 티어 기준)
    if desired_difficulty == "bronze":
        min_level, max_level = 1, 5  # 브론즈 V ~ 브론즈 I
    elif desired_difficulty == "silver":
        min_level, max_level = 6, 10  # 실버 V ~ 실버 I
    elif desired_difficulty == "bronze-silver":
        min_level, max_level = 1, 10  # 브론즈 V ~ 실버 I
    else:
        min_level, max_level = 1, 10  # 기본값: 브론즈~실버

    tries = 0
    max_tries = 10
    while tries < max_tries:
        problem_id = get_random_problem_id()
        print(f"▶ 시도 중: 문제 ID {problem_id}")
        try:
            # 난이도 확인
            level = get_problem_difficulty(problem_id)
            if level is None or level < min_level or level > max_level:
                print(f"난이도 부적합 (티어 {level}): {problem_id}")
                tries += 1
                time.sleep(random.uniform(1, 3))
                continue

            soup = fetch_problem_page(problem_id)
            if not soup:
                raise RuntimeError("페이지 가져오기 실패")
            title, desc, input_fmt, output_fmt = extract_problem_details(soup)
            py_file, java_file = write_template_files(problem_id, title, desc, input_fmt, output_fmt)
            print(f"✅ 파일 생성 완료: {py_file}, {java_file} (티어: {level})")
            return
        except Exception as e:
            print(f"❌ 실패 ({problem_id}): {e}")
            tries += 1
            time.sleep(random.uniform(3, 7))  # 3~7초 랜덤 대기

    print("⚠️ 10회 시도에도 적합한 난이도의 문제를 찾지 못했습니다.")

if __name__ == "__main__":
    # 원하는 난이도 설정 (bronze, silver, bronze-silver)
    main(desired_difficulty="bronze-silver")