import time
import random
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpyxl import load_workbook

##
# Date        Description   Authur
# 2026-01-11  최초생성      created by 양창일
##

SECONDS_IN_DAY = 86400

# Session + Retry
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://store.steampowered.com/",
})

def safe_get(url, params=None, timeout=30, max_retries=8):

    base_backoff = 1.5
    for attempt in range(1, max_retries + 1):
        try:
            r = session.get(url, params=params, timeout=timeout)

            # 429: 레이트리밋
            if r.status_code == 429:
                retry_after = r.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 10
                wait += random.uniform(0, 1.0)
                print(f"[429] wait {wait:.1f}s (attempt {attempt}/{max_retries})")
                time.sleep(wait)
                continue

            # 5xx: 서버 불안정(502 포함)
            if 500 <= r.status_code < 600:
                wait = min(60, base_backoff * (2 ** (attempt - 1))) + random.uniform(0, 0.7)
                print(f"[{r.status_code}] wait {wait:.1f}s (attempt {attempt}/{max_retries})")
                time.sleep(wait)
                continue

            r.raise_for_status()
            return r

        except requests.RequestException as e:
            wait = min(60, base_backoff * (2 ** (attempt - 1))) + random.uniform(0, 0.7)
            print(f"[EXC] {type(e).__name__}: {e} -> wait {wait:.1f}s (attempt {attempt}/{max_retries})")
            time.sleep(wait)

    raise RuntimeError(f"safe_get failed after {max_retries} retries: {url}")

# 리뷰 수집 함수
def fetch_reviews_last_n_days(
    appid: int,
    days: int = 1,
    filter: str = "recent",
    language: str = "all",
    review_type: str = "all",
    purchase_type: str = "all",
    num_per_page: int = 100,
    filter_offtopic_activity: int = 1,
    sleep_sec: float = 0.35,     # 병렬이면 너무 낮추지 말기
):
    url = f"https://store.steampowered.com/appreviews/{appid}"
    cursor = "*"
    rows = []
    page = 0

    now_ts = int(time.time())
    cutoff_ts = now_ts - days * SECONDS_IN_DAY

    while True:
        params = {
            "json": 1,
            "filter": filter,
            "language": language,
            "review_type": review_type,
            "purchase_type": purchase_type,
            "num_per_page": num_per_page,
            "cursor": cursor,
            "filter_offtopic_activity": filter_offtopic_activity,
        }

        r = safe_get(url, params=params, timeout=30, max_retries=8)
        data = r.json()

        if data.get("success") != 1:
            raise RuntimeError(f"API success != 1: {data}")

        reviews = data.get("reviews", [])
        if not reviews:
            break

        stop = False
        for rev in reviews:
            ts_created = rev.get("timestamp_created")

            # 기간 컷
            if ts_created is not None and ts_created < cutoff_ts:
                stop = True
                break

            author = rev.get("author", {})
            rows.append({
                "appid": str(appid),
                "recommendationid": rev.get("recommendationid"),
                "steamid": author.get("steamid"),
                "num_games_owned": author.get("num_games_owned"),
                "num_reviews_author": author.get("num_reviews"),
                "playtime_forever": author.get("playtime_forever"),
                "playtime_last_two_weeks": author.get("playtime_last_two_weeks"),
                "playtime_at_review": author.get("playtime_at_review"),
                "deck_playtime_at_review": author.get("deck_playtime_at_review"),
                "last_played": author.get("last_played"),
                "language": rev.get("language"),
                "review": rev.get("review"),
                "timestamp_created": ts_created,
                "timestamp_updated": rev.get("timestamp_updated"),
                "voted_up": rev.get("voted_up"),
                "votes_up": rev.get("votes_up"),
                "votes_funny": rev.get("votes_funny"),
                "weighted_vote_score": rev.get("weighted_vote_score"),
                "comment_count": rev.get("comment_count"),
                "steam_purchase": rev.get("steam_purchase"),
                "received_for_free": rev.get("received_for_free"),
                "written_during_early_access": rev.get("written_during_early_access"),
                "developer_response": rev.get("developer_response"),
                "timestamp_dev_responded": rev.get("timestamp_dev_responded"),
                "primarily_steam_deck": rev.get("primarily_steam_deck"),
            })

        page += 1
        print(f"appid={appid}, page={page}, fetched={len(reviews)}, kept_total={len(rows)}")

        if stop:
            break

        cursor = data.get("cursor")
        time.sleep(sleep_sec)

    return pd.DataFrame(rows)

def fetch_reviews_last_n(
    appid: int,
    filter: str = "recent",
    language: str = "all",
    review_type: str = "all",
    purchase_type: str = "all",
    num_per_page: int = 100,
    filter_offtopic_activity: int = 1,
    sleep_sec: float = 0.35,     # 병렬이면 너무 낮추지 말기
):
    url = f"https://store.steampowered.com/appreviews/{appid}"
    cursor = "*"
    rows = []
    page = 0

    now_ts = int(time.time())

    while True:
        params = {
            "json": 1,
            "filter": filter,
            "language": language,
            "review_type": review_type,
            "purchase_type": purchase_type,
            "num_per_page": num_per_page,
            "cursor": cursor,
            "filter_offtopic_activity": filter_offtopic_activity,
        }

        r = safe_get(url, params=params, timeout=30, max_retries=8)
        data = r.json()

        if data.get("success") != 1:
            raise RuntimeError(f"API success != 1: {data}")

        reviews = data.get("reviews", [])
        if not reviews:
            break

        stop = False
        for rev in range(5):
            ts_created = rev.get("timestamp_created")
            author = reviews[rev].get("author", {})
            rows.append({
                "appid": str(appid),
                "recommendationid": rev.get("recommendationid"),
                "steamid": author.get("steamid"),
                "num_games_owned": author.get("num_games_owned"),
                "num_reviews_author": author.get("num_reviews"),
                "playtime_forever": author.get("playtime_forever"),
                "playtime_last_two_weeks": author.get("playtime_last_two_weeks"),
                "playtime_at_review": author.get("playtime_at_review"),
                "deck_playtime_at_review": author.get("deck_playtime_at_review"),
                "last_played": author.get("last_played"),
                "language": rev.get("language"),
                "review": rev.get("review"),
                "timestamp_created": ts_created,
                "timestamp_updated": rev.get("timestamp_updated"),
                "voted_up": rev.get("voted_up"),
                "votes_up": rev.get("votes_up"),
                "votes_funny": rev.get("votes_funny"),
                "weighted_vote_score": rev.get("weighted_vote_score"),
                "comment_count": rev.get("comment_count"),
                "steam_purchase": rev.get("steam_purchase"),
                "received_for_free": rev.get("received_for_free"),
                "written_during_early_access": rev.get("written_during_early_access"),
                "developer_response": rev.get("developer_response"),
                "timestamp_dev_responded": rev.get("timestamp_dev_responded"),
                "primarily_steam_deck": rev.get("primarily_steam_deck"),
            })

        page += 1
        print(f"appid={appid}, page={page}, fetched={len(reviews)}, kept_total={len(rows)}")

        if stop:
            break

        cursor = data.get("cursor")
        time.sleep(sleep_sec)

    return pd.DataFrame(rows)



def run_batch(appids, days=1, max_workers=4, sleep_range=(0.2, 0.6)):
    results = []

    def job(appid):
        df = fetch_reviews_last_n_days(int(appid), days=days)
        return str(appid), df

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(job, appid): appid for appid in appids}

        for fut in as_completed(futures):
            appid = futures[fut]
            try:
                appid_done, df = fut.result()

                # df가 비어도 성공 처리 (원하면 여기서 필터링 가능)
                results.append((appid_done, df))
                print(f"done {appid_done}: {df.shape}")

                # 병렬이니까 너무 공격적으로 추가요청 안 하게 약간 랜덤 쉬기
                lo, hi = sleep_range
                if lo or hi:
                    time.sleep(random.uniform(lo, hi))

            except Exception as e:
                # 실패한 건 반환하지 않고 로그만 찍고 스킵
                print(f"fail {appid}: {e}")
                continue

    return results

def run_batch_id(appids, streamid, max_workers=4, sleep_range=(0.2, 0.6)):

    results = []

    def job(appid):
        df = fetch_reviews_last_n(int(appid),streamid, days=0)
        return str(appid), df

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(job, appid): appid for appid in appids}

        for fut in as_completed(futures):
            appid = futures[fut]
            try:
                appid_done, df = fut.result()

                # df가 비어도 성공 처리 (원하면 여기서 필터링 가능)
                results.append((appid_done, df))
                print(f"done {appid_done}: {df.shape}")

                # 병렬이니까 너무 공격적으로 추가요청 안 하게 약간 랜덤 쉬기
                lo, hi = sleep_range
                if lo or hi:
                    time.sleep(random.uniform(lo, hi))

            except Exception as e:
                # 실패한 건 반환하지 않고 로그만 찍고 스킵
                print(f"fail {appid}: {e}")
                continue

    return results



