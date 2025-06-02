import random
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def get_random_problem_id(min_id=1000, max_id=2000):
    """1000~2000 사이의 랜덤 문제 ID 생성"""
    return random.randint(min_id, max_id)

def fetch_problem_page(problem_id):
    """Selenium으로 문제 페이지 가져오기"""
    url = f"https://www.acmicpc.net/problem/{problem_id}"
    options = Options()
    options.add_argument("--headless")  # 헤드리스 모드
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
    options.add_argument("accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    
    # ChromeDriver 경로 지정 (본인 환경에 맞게 수정)
    # 예: service = Service('/path/to/chromedriver')
    # service = Service('/path/to/chromedriver')  # 필요 시 활성화
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

def main():
    """메인 함수: 랜덤 문제 ID로 템플릿 생성 시도"""
    tries = 0
    max_tries = 10
    while tries < max_tries:
        problem_id = get_random_problem_id()
        print(f"▶ 시도 중: 문제 ID {problem_id}")
        try:
            soup = fetch_problem_page(problem_id)
            if not soup:
                raise RuntimeError("페이지 가져오기 실패")
            title, desc, input_fmt, output_fmt = extract_problem_details(soup)
            py_file, java_file = write_template_files(problem_id, title, desc, input_fmt, output_fmt)
            print(f"✅ 파일 생성 완료: {py_file}, {java_file}")
            return
        except Exception as e:
            print(f"❌ 실패 ({problem_id}): {e}")
            tries += 1
            time.sleep(random.uniform(3, 7))  # 3~7초 랜덤 대기

    print("⚠️ 10회 시도에도 문제를 찾지 못했습니다.")

if __name__ == "__main__":
    main()