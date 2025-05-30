import requests
import random
import json

def get_random_easy_problem():
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        raise Exception("문제 불러오기 실패")

    # 쉬운 문제 (800~1200점)만 필터링
    easy_problems = [
        p for p in data["result"]["problems"]
        if "rating" in p and 800 <= p["rating"] <= 1200
    ]

    problem = random.choice(easy_problems)
    contest_id = problem["contestId"]
    index = problem["index"]
    name = problem["name"]
    rating = problem["rating"]

    problem_url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

    return {
        "name": name,
        "contestId": contest_id,
        "index": index,
        "rating": rating,
        "url": problem_url
    }

# 예시 실행
if __name__ == "__main__":
    problem = get_random_easy_problem()
    print(f"[{problem['rating']}] {problem['name']}")
    print(f"👉 {problem['url']}")


import os

def save_problem_to_file(problem):
    filename = f"{problem['rating']}_{problem['name'].replace(' ', '_')}.py"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 문제 이름: {problem['name']}\n")
        f.write(f"# 문제 링크: {problem['url']}\n\n")
        f.write("# 여기에 코드를 작성하세요\n")
    return filepath


if __name__ == "__main__":
    problem = get_random_easy_problem()
    print(f"[{problem['rating']}] {problem['name']}")
    print(f"👉 {problem['url']}")

    path = save_problem_to_file(problem)
    print(f"✅ 저장 완료: {path}")
