import json
import random
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

from curl_cffi import requests
from tiktokforge import AppDefaults, DeviceProfile, TikTokSigner, version_code_for

VERSION = "47.5.3"
VERSION_CODE = str(version_code_for(VERSION))
AID = 1233
HOST = "https://api16-normal-useast5.tiktokv.us"
LOG_HOST = "https://log-va.tiktokv.com"


def device_path(path=None):
    if path:
        return Path(path)
    return Path.cwd() / "device.json"


def hex_id(n):
    return "".join(random.choice("0123456789abcdef") for _ in range(n))


def new_persona():
    return {
        "openudid": hex_id(16),
        "cdid": str(uuid.uuid4()),
        "device_type": "Pixel 7",
        "device_brand": "google",
        "os_version": "14",
        "os_api": "34",
        "resolution": "1080*2400",
        "dpi": "420",
        "channel": "googleplay",
        "language": "en",
        "region": "US",
        "timezone_name": "America/New_York",
        "timezone_offset": "-18000",
        "carrier_region": "US",
    }


def app_profile(persona, device_id, install_id):
    return AppDefaults(
        aid=AID,
        version_name=VERSION,
        device=DeviceProfile(
            device_id=str(device_id),
            install_id=str(install_id),
            device_type=persona["device_type"],
            device_brand=persona["device_brand"],
            os_version=persona["os_version"],
            os_api=int(persona["os_api"]),
            language=persona["language"],
            region=persona["region"],
            channel=persona["channel"],
        ),
    )


def query(persona, device_id, install_id, extra=None):
    now = int(time.time())
    p = {
        "ac": "wifi",
        "channel": persona["channel"],
        "aid": str(AID),
        "app_name": "musical_ly",
        "version_code": VERSION_CODE,
        "version_name": VERSION,
        "device_platform": "android",
        "ab_version": VERSION,
        "ssmix": "a",
        "device_type": persona["device_type"],
        "device_brand": persona["device_brand"],
        "language": persona["language"],
        "os_api": persona["os_api"],
        "os_version": persona["os_version"],
        "openudid": persona["openudid"],
        "manifest_version_code": VERSION_CODE,
        "resolution": persona["resolution"],
        "dpi": persona["dpi"],
        "update_version_code": VERSION_CODE,
        "ac2": "wifi",
        "sys_region": persona["region"],
        "region": persona["region"],
        "carrier_region": persona["carrier_region"],
        "app_language": persona["language"],
        "op_region": persona["region"],
        "timezone_name": persona["timezone_name"],
        "timezone_offset": persona["timezone_offset"],
        "build_number": VERSION,
        "host_abi": "arm64-v8a",
        "locale": "en",
        "ts": str(now),
        "_rticket": str(now * 1000),
        "app_type": "normal",
        "cdid": persona["cdid"],
        "device_id": str(device_id),
        "iid": str(install_id),
    }
    if extra:
        p.update(extra)
    return p


def signed_headers(q, prof, data=None, cookie=None):
    sig = TikTokSigner.generate_headers(
        params=q,
        data=data,
        profile=prof,
        cookie=cookie,
        aid=AID,
        version_name=VERSION,
        version_code=VERSION_CODE,
        device_id=prof.device.device_id,
    )
    h = {
        "User-Agent": prof.user_agent(),
        "Accept-Encoding": "gzip",
        "sdk-version": "2",
        "x-tt-store-region": "us",
        "x-tt-store-region-src": "did",
        **sig,
    }
    if cookie:
        h["Cookie"] = cookie
    if data is not None:
        h["Content-Type"] = "application/octet-stream;tt-data=a"
    return h


def session():
    return requests.Session(impersonate="chrome131")


def register(path=None):
    path = device_path(path)
    s = session()
    persona = new_persona()
    q = urlencode(query(persona, "0", "0"))
    prof = app_profile(persona, "0", "0")

    body = {
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": "TikTok",
            "update_version_code": int(VERSION_CODE),
            "manifest_version_code": int(VERSION_CODE),
            "aid": AID,
            "channel": persona["channel"],
            "package": "com.zhiliaoapp.musically",
            "app_version": VERSION,
            "version_code": int(VERSION_CODE),
            "sdk_version": "2.12.1-rc.27-live-android",
            "os": "Android",
            "os_version": persona["os_version"],
            "os_api": int(persona["os_api"]),
            "device_model": persona["device_type"],
            "device_brand": persona["device_brand"],
            "device_manufacturer": persona["device_brand"],
            "cpu_abi": "arm64-v8a",
            "density_dpi": int(persona["dpi"]),
            "resolution": persona["resolution"].replace("*", "x"),
            "language": persona["language"],
            "timezone": -5,
            "access": "wifi",
            "cdid": persona["cdid"],
            "openudid": persona["openudid"],
            "clientudid": str(uuid.uuid4()),
            "region": persona["region"],
            "tz_name": persona["timezone_name"],
            "tz_offset": int(persona["timezone_offset"]),
            "sim_region": "us",
        },
        "_gen_time": int(time.time() * 1000),
    }
    blob = TikTokSigner.encrypt(body)
    if isinstance(blob, str):
        blob = blob.encode("latin-1")

    r = s.post(
        f"{LOG_HOST}/service/2/device_register/?{q}",
        headers=signed_headers(q, prof, data=blob),
        data=blob,
        timeout=30,
    )
    data = r.json()
    device_id = str(data.get("device_id_str") or data.get("device_id") or "")
    install_id = str(data.get("install_id_str") or data.get("install_id") or "")
    if not device_id or device_id == "0":
        raise RuntimeError("device register failed")

    cookie = "; ".join(f"{c.name}={c.value}" for c in s.cookies.jar)
    device = {
        "persona": persona,
        "device_id": device_id,
        "install_id": install_id or device_id,
        "cookie": cookie,
    }
    path.write_text(json.dumps(device, indent=2), encoding="utf-8")
    return device


def load(path=None, create=True):
    path = device_path(path)
    if path.exists():
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            if d.get("device_id") and d.get("persona"):
                return d
        except Exception:
            pass
    if not create:
        return None
    return register(path)


def mobile_get(s, device, path, extra=None):
    persona = device["persona"]
    prof = app_profile(persona, device["device_id"], device["install_id"])
    q = urlencode(query(persona, device["device_id"], device["install_id"], extra))
    return s.get(
        f"{HOST}{path}?{q}",
        headers=signed_headers(q, prof, cookie=device.get("cookie")),
        timeout=30,
    )
