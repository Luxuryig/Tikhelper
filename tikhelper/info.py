import json
import random
import re
import time
from datetime import datetime, timezone

from curl_cffi import requests

from . import device as dev
from .countries import COUNTRIES

UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 "
    "Mobile/15E148 Safari/604.1"
)


def pause(a=0.3, b=0.8):
    time.sleep(random.uniform(a, b))


def clean_user(name):
    name = (name or "").strip()
    name = re.sub(r"^https?://(www\.)?tiktok\.com/@", "", name, flags=re.I)
    return name.split("?")[0].split("/")[0].lstrip("@").strip()


def country_name(code):
    if not code:
        return None
    code = str(code).upper()
    return COUNTRIES.get(code, code)


def get_html(url):
    s = requests.Session(impersonate="safari18_0_ios")
    r = s.get(
        url,
        headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
        timeout=25,
    )
    if r.status_code >= 400:
        return ""
    return r.text


_pages = {}


def embed_page(username):
    if username in _pages:
        return _pages[username]
    html = get_html(f"https://www.tiktok.com/embed/@{username}")
    if not html:
        _pages[username] = ({}, [])
        return _pages[username]
    m = re.search(r'<script id="__FRONTITY_CONNECT_STATE__"[^>]*>([^<]+)</script>', html)
    if not m:
        _pages[username] = ({}, [])
        return _pages[username]
    try:
        page = json.loads(m.group(1))["source"]["data"].get(f"/embed/@{username}", {})
    except Exception:
        _pages[username] = ({}, [])
        return _pages[username]
    got = (page.get("userInfo") or {}, page.get("videoList") or [])
    _pages[username] = got
    return got


def bigger_pic(url):
    if not url:
        return None
    return re.sub(r"cropcenter:\d+:\d+", "cropcenter:720:720", url)


def profile(username):
    username = clean_user(username)
    if not username:
        raise ValueError("need a username")
    info, _ = embed_page(username)
    if not info.get("uniqueId"):
        return None
    return {
        "username": info.get("uniqueId"),
        "nickname": info.get("nickname"),
        "bio": info.get("signature") or "",
        "avatar": bigger_pic(info.get("avatarThumbUrl")),
        "user_id": str(info.get("id") or "") or None,
        "followers": info.get("followerCount"),
        "following": info.get("followingCount"),
        "hearts": info.get("heartCount"),
        "verified": bool(info.get("verified")),
        "private": bool(info.get("privateAccount")),
    }


def exists(username):
    return profile(username) is not None


def avatar(username):
    p = profile(username)
    if not p:
        return None
    return p["avatar"]


def resolve(username):
    p = profile(username)
    if not p:
        return None
    return {"username": p["username"], "user_id": p["user_id"]}


def videos(username, n=10):
    username = clean_user(username)
    if not username:
        raise ValueError("need a username")
    info, raw = embed_page(username)
    user = info.get("uniqueId") or username
    out = []
    for v in raw:
        if not isinstance(v, dict) or not v.get("id"):
            continue
        vid = str(v["id"])
        out.append({
            "id": vid,
            "url": f"https://www.tiktok.com/@{user}/video/{vid}",
            "username": v.get("authorUniqueId") or user,
            "caption": v.get("desc") or "",
            "plays": v.get("playCount"),
            "cover": v.get("coverUrl") or v.get("originCoverUrl"),
            "width": v.get("width"),
            "height": v.get("height"),
            "private": bool(v.get("privateItem")),
        })
        if len(out) >= n:
            break
    return out


def split_video(url):
    url = (url or "").strip()
    m = re.search(r"@([\w.\-]+)/video/(\d+)", url)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"(\d{8,})", url)
    if m:
        return None, m.group(1)
    raise ValueError("need a video link")


def video_item(url):
    html = get_html(url)
    m = re.search(r'<script id="api-data"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(1).strip())
    except Exception:
        return None
    return ((data.get("videoDetail") or {}).get("itemInfo") or {}).get("itemStruct")


def video(url):
    user, vid = split_video(url)
    if user:
        page = f"https://www.tiktok.com/@{user}/video/{vid}"
    else:
        page = f"https://www.tiktok.com/embed/v2/{vid}"
    item = video_item(page)
    if not item and user:
        item = video_item(f"https://www.tiktok.com/embed/v2/{vid}")
    if not item:
        return None
    author = item.get("author") or {}
    stats = item.get("stats") or {}
    music = item.get("music") or {}
    media = item.get("video") or {}
    code = item.get("locationCreated")
    created = item.get("createTime")
    when = None
    if created:
        when = datetime.fromtimestamp(int(created), timezone.utc).strftime("%Y-%m-%d %H:%M")
    name = author.get("uniqueId") or user
    vid = str(item.get("id") or vid)
    return {
        "id": vid,
        "url": f"https://www.tiktok.com/@{name}/video/{vid}" if name else page,
        "username": name,
        "nickname": author.get("nickname"),
        "user_id": str(author.get("id") or "") or None,
        "caption": item.get("desc") or "",
        "likes": stats.get("diggCount"),
        "comments": stats.get("commentCount"),
        "shares": stats.get("shareCount"),
        "plays": stats.get("playCount"),
        "saves": stats.get("collectCount"),
        "sound": music.get("title"),
        "sound_author": music.get("authorName"),
        "created": created,
        "date": when,
        "region": code,
        "country": country_name(code),
        "cover": media.get("cover") or media.get("originCover"),
    }


def find_location(html):
    m = re.search(r'"locationCreated"\s*:\s*"([A-Z]{2})"', html)
    if m:
        return m.group(1)
    m = re.search(r'"ttSeller"\s*:\s*(?:true|false)\s*,\s*"region"\s*:\s*"([A-Z]{2})"', html)
    return m.group(1) if m else None


def base_info(username, info):
    return {
        "username": info.get("uniqueId") or username,
        "nickname": info.get("nickname"),
        "bio": info.get("signature") or "",
        "avatar": bigger_pic(info.get("avatarThumbUrl")),
        "user_id": str(info.get("id") or "") or None,
        "followers": info.get("followerCount"),
        "following": info.get("followingCount"),
        "hearts": info.get("heartCount"),
        "private": bool(info.get("privateAccount")),
        "verified": bool(info.get("verified")),
        "region": None,
        "country": None,
        "source": None,
    }


def from_videos(username, info, raw):
    out = base_info(username, info)
    ids = [str(v["id"]) for v in raw if isinstance(v, dict) and v.get("id")]
    for vid in ids[:3]:
        pause()
        html = get_html(f"https://www.tiktok.com/@{username}/video/{vid}")
        code = find_location(html)
        if code:
            out["region"] = code
            out["country"] = country_name(code)
            out["source"] = "video"
            return out
    return None


def from_mobile(s, device, username, user_id=None):
    try:
        dev.mobile_get(
            s, device, "/aweme/v1/feed/",
            {"count": "6", "type": "0", "max_cursor": "0", "min_cursor": "0", "pull_type": "1"},
        )
        pause(0.4, 0.7)
    except Exception:
        pass

    tries = []
    if user_id:
        tries.append({"user_id": user_id})
    tries.append({"unique_id": username})

    for extra in tries:
        pause(0.2, 0.5)
        try:
            r = dev.mobile_get(s, device, "/aweme/v1/user/profile/other/", extra)
        except Exception:
            continue
        if not r.content:
            continue
        user = (r.json().get("user") or {})
        region = user.get("region")
        if region and len(str(region)) == 2:
            code = str(region).upper()
            return {
                "username": user.get("unique_id") or username,
                "nickname": user.get("nickname"),
                "bio": user.get("signature") or "",
                "user_id": str(user.get("uid") or user.get("id") or user_id or "") or None,
                "followers": user.get("follower_count"),
                "following": user.get("following_count"),
                "hearts": user.get("total_favorited"),
                "private": bool(user.get("secret")),
                "verified": bool(user.get("custom_verify") or user.get("verified")),
                "region": code,
                "country": country_name(code),
                "source": "mobile",
            }
    return None


def findinfo(username, path=None, device=None):
    username = clean_user(username)
    if not username:
        raise ValueError("need a username")

    info, raw = embed_page(username)
    if raw:
        hit = from_videos(username, info, raw)
        if hit:
            return hit

    if device is None:
        device = dev.load(path)
    s = dev.session()
    hit = from_mobile(s, device, username, user_id=str(info.get("id") or "") or None)
    if hit:
        if hit.get("followers") is None:
            hit["followers"] = info.get("followerCount")
        if hit.get("following") is None:
            hit["following"] = info.get("followingCount")
        if hit.get("hearts") is None:
            hit["hearts"] = info.get("heartCount")
        if not hit.get("avatar"):
            hit["avatar"] = bigger_pic(info.get("avatarThumbUrl"))
        if not hit.get("bio"):
            hit["bio"] = info.get("signature") or ""
        return hit

    out = base_info(username, info)
    out["source"] = "none"
    out["videos"] = len([v for v in raw if isinstance(v, dict) and v.get("id")])
    return out


def region(username):
    info = findinfo(username)
    return {
        "username": info.get("username"),
        "region": info.get("region"),
        "country": info.get("country"),
    }
