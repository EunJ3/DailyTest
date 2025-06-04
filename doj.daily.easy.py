import random
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def get_random_problem_id(min_id=1000, max_id=3000):
    """1000~3000 사이의 랜덤 문제 ID 생성"""
    return random.randint(min_id, max_id)

def get_problem_difficulty(problem_id, retries=3):
    """Solved.ac API로 문제 난이도 확인 (티어 1~3)"""
    url = f"https://solved.ac/api/v3/problem/lookup?problemIds={problem_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                level = data[0].get("level", 0)
                print(f"문제 {problem_id} 티어: {level}")
                return level
            return None
        except Exception as e:
            print(f"Solved.ac API 오류 (시도 {attempt+1}/{retries}): {str(e)}")
            time.sleep(random.uniform(1, 2))
    return None

def get_random_bronze_problem():
    """백준 문제 목록에서 브론즈 V~III 문제 ID 가져오기 (폴백)"""
    url = "https://www.acmicpc.net/problemset?sort=rank-desc&tier=1,2,3"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        problem_rows = soup.select("table#problemset tbody tr")
        problem_ids = []
        for row in problem_rows:
            problem_id = row.select_one("td:nth-child(1)").get_text(strip=True)
            tier_tag = row.select_one("td:nth-child(2) img")
            if tier_tag and "bronze" in tier_tag['src'].lower():
                problem_ids.append(problem_id)
        
        if not problem_ids:
            raise RuntimeError("브론즈 문제를 찾을 수 없습니다.")
        
        return random.choice(problem_ids)
    except Exception as e:
        print(f"백준 문제 목록 크롤링 실패: {str(e)}")
        return None
    finally:
        driver.quit()

def fetch_problem_page(problem_id):
    """Selenium으로 문제 페이지 가져오기"""
    url = f"https://www.acmicpc.net/problem/{problem_id}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))
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
    """메인 함수: 브론즈 V~III (티어 1~3) 문제로 템플릿 생성 시도"""
    min_level, max_level = 1, 3  # 브론즈 V(1) ~ 브론즈 III(3)
    tries = 0
    max_tries = 10
    while tries < max_tries:
        # 먼저 solved.ac API로 시도
        problem_id = get_random_problem_id()
        print(f"▶ 시도 중: 문제 ID {problem_id}")
        try:
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
            time.sleep(random.uniform(3, 7))

        # API로 실패 시 백준 문제 목록에서 폴백
        if tries == max_tries // 2:
            print("⚠️ solved.ac API로 적합한 문제를 못 찾음. 백준 목록에서 시도...")
            problem_id = get_random_bronze_problem()
            if not problem_id:
                print("❌ 백준 목록에서도 문제를 찾지 못함.")
                tries += 1
                continue
            print(f"▶ 폴백 시도: 문제 ID {problem_id}")
            try:
                soup = fetch_problem_page(problem_id)
                if not soup:
                    raise RuntimeError("페이지 가져오기 실패")
                title, desc, input_fmt, output_fmt = extract_problem_details(soup)
                py_file, java_file = write_template_files(problem_id, title, desc, input_fmt, output_fmt)
                print(f"✅ 파일 생성 완료 (폴백): {py_file}, {java_file}")
                return
            except Exception as e:
                print(f"❌ 폴백 실패 ({problem_id}): {e}")
                tries += 1
                time.sleep(random.uniform(3, 7))

    print("⚠️ 10회 시도에도 브론즈 V~III 문제를 찾지 못했습니다.")

if __name__ == "__main__":
    main()