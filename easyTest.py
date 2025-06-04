import random
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def get_random_level0_problem(retries=3):
    """프로그래머스 레벨 0, 파이썬3 문제 목록에서 랜덤 문제 URL 가져오기"""
    url = "https://school.programmers.co.kr/learn/challenges?levels=0&order=recent&page=1&languages=python3"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
    ]
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    options.add_argument("accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
    options.add_argument("accept-language=ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
    
    for attempt in range(retries):
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(30)
            driver.get(url)
            time.sleep(random.uniform(5, 8))
            with open("problem_list_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            problem_links = soup.select("div.challenge-content a[href*='/learn/courses/30/lessons/']")
            if not problem_links:
                problem_links = soup.find_all("a", href=re.compile(r"/learn/courses/30/lessons/"))
            if not problem_links:
                raise RuntimeError(f"레벨 0 파이썬3 문제 목록을 찾을 수 없습니다 (시도 {attempt+1}/{retries})")
            
            random_problem = random.choice(problem_links)
            problem_url = "https://school.programmers.co.kr" + random_problem['href']
            problem_id = problem_url.split('/')[-1]
            print(f"선택된 문제: ID {problem_id}, URL {problem_url}")
            return problem_id, problem_url
        except Exception as e:
            print(f"문제 목록 가져오기 실패 (시도 {attempt+1}/{retries}): {str(e)}")
            time.sleep(random.uniform(1, 2))
        finally:
            driver.quit()
    return None, None

def fetch_problem_page(problem_url, retries=3):
    """Selenium으로 문제 페이지 가져오기"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
    ]
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    for attempt in range(retries):
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(30)
            driver.get(problem_url)
            time.sleep(random.uniform(5, 8))
            with open("problem_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            print(f"Selenium 실패 (시도 {attempt+1}/{retries}): {str(e)}")
            time.sleep(random.uniform(1, 2))
        finally:
            driver.quit()
    return None

def extract_problem_details(soup):
    """문제 제목, 설명, 입력, 출력 추출"""
    title_tag = soup.select_one("h1")
    if not title_tag:
        title_tag = soup.select_one("h2")  # 대체 셀렉터
    if not title_tag:
        raise RuntimeError("문제 제목을 찾을 수 없습니다.")
    title = title_tag.get_text(strip=True)
    
    desc_div = soup.select_one("div.challenge-description")
    if not desc_div:
        desc_div = soup.select_one("div.markdown")  # 대체 셀렉터
    if not desc_div:
        raise RuntimeError("문제 설명을 찾을 수 없습니다.")
    desc = desc_div.get_text("\n", strip=True)
    
    input_desc = "입출력 예시는 문제 페이지에서 확인하세요."
    output_desc = "입출력 예시는 문제 페이지에서 확인하세요."
    
    return title, desc, input_desc, output_desc

def sanitize_filename(name):
    """파일 이름에 사용할 수 없는 문자 제거"""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip().replace(" ", "_")

def write_template_file(problem_id, title, description, input_fmt, output_fmt):
    """파이썬 템플릿 파일 생성"""
    safe_title = sanitize_filename(title)
    base_filename = f"{problem_id}_{safe_title}"

    python_code = f"""\"\"\"
Programmers Problem {problem_id}: {title}

{description}

[Input]
{input_fmt}

[Output]
{output_fmt}
\"\"\"

def solution():
    # TODO: Implement solution
    pass
"""

    py_path = f"{base_filename}.py"

    with open(py_path, "w", encoding="utf-8-sig") as f:
        f.write(python_code)

    return py_path

def main():
    """메인 함수: 프로그래머스 레벨 0, 파이썬3 문제로 템플릿 생성"""
    tries = 0
    max_tries = 10
    while tries < max_tries:
        problem_id, problem_url = get_random_level0_problem()
        if not problem_id:
            print(f"❌ 레벨 0 파이썬3 문제 목록을 가져오지 못했습니다 (시도 {tries+1}/{max_tries}).")
            tries += 1
            time.sleep(random.uniform(5, 8))
            continue
        
        print(f"▶ 시도 중: 문제 ID {problem_id}")
        try:
            soup = fetch_problem_page(problem_url)
            if not soup:
                raise RuntimeError("페이지 가져오기 실패")
            title, desc, input_fmt, output_fmt = extract_problem_details(soup)
            py_file = write_template_file(problem_id, title, desc, input_fmt, output_fmt)
            print(f"✅ 파일 생성 완료: {py_file}")
            return
        except Exception as e:
            print(f"❌ 실패 (ID {problem_id}): {str(e)}")
            tries += 1
            time.sleep(random.uniform(5, 8))

    print("⚠️ 10회 시도에도 레벨 0 파이썬3 문제를 찾지 못했습니다. problem_list_source.html 또는 problem_page_source.html 확인하세요.")

if __name__ == "__main__":
    main()