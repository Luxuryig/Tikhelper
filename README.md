# tikhelper

Public TikTok profiles and videos.

## Install

One line, straight from GitHub:

```bash
pip install git+https://github.com/Luxuryig/Tikhelper.git
```

Or clone it yourself:

```bash
git clone https://github.com/Luxuryig/Tikhelper.git
cd Tikhelper
pip install .
```



## Use

```python
import tikhelper

tikhelper.profile("mrbeast")
tikhelper.exists("mrbeast")
tikhelper.avatar("mrbeast")
tikhelper.resolve("mrbeast")
tikhelper.videos("mrbeast")
tikhelper.video("https://www.tiktok.com/@mrbeast/video/7707741942771191054")
tikhelper.region("mrbeast")
tikhelper.findinfo("mrbeast")
```

## Features

| Function | Returns |
| --- | --- |
| **profile** | name, bio, avatar, followers, following, hearts, verified, private, user id |
| **exists** | `True` or `False` |
| **avatar** | picture url |
| **resolve** | username and user id |
| **videos** | recent posts, caption, plays, cover, link |
| **video** | one post: likes, comments, shares, plays, sound, date, country |
| **region** | country only |
| **findinfo** | profile plus country |

Country only shows up when the account has a **public video**. Empty accounts come back with `region` set to `null`.

## Examples

**profile**

```python
tikhelper.profile("mrbeast")
```

```json
{
  "username": "mrbeast",
  "nickname": "MrBeast",
  "followers": 147000000,
  "user_id": "6614519312189947909",
  "verified": true
}
```

**video**

```python
tikhelper.video("https://www.tiktok.com/@mrbeast/video/7707741942771191054")
```

```json
{
  "caption": "Will the odds be in my favor?",
  "plays": 6900000,
  "likes": 656500,
  "comments": 16000,
  "date": "2026-11-13 19:35",
  "region": "US",
  "country": "United States"
}
```

**region**

```python
tikhelper.region("mrbeast")
```

```json
{
  "username": "mrbeast",
  "region": "US",
  "country": "United States"
}
```

