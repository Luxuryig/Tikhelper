import json
import sys

from . import avatar, exists, findinfo, profile, region, register, resolve, video, videos


def show(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("tikhelper register")
        print("tikhelper profile name")
        print("tikhelper videos name")
        print("tikhelper video <link>")
        print("tikhelper region name")
        print("tikhelper name")
        return 0

    cmd = args[0]
    if cmd == "register":
        d = register()
        print(d["device_id"])
        return 0

    if cmd == "profile":
        p = profile(args[1])
        show(p)
        return 0 if p else 2

    if cmd == "videos":
        show(videos(args[1]))
        return 0

    if cmd == "video":
        v = video(args[1])
        show(v)
        return 0 if v else 2

    if cmd == "region":
        show(region(args[1]))
        return 0

    if cmd == "avatar":
        print(avatar(args[1]))
        return 0

    if cmd == "exists":
        print(exists(args[1]))
        return 0

    if cmd == "resolve":
        show(resolve(args[1]))
        return 0

    info = findinfo(cmd)
    if "--json" in args:
        show(info)
    else:
        print("@" + str(info.get("username")))
        if info.get("nickname"):
            print("name:   ", info["nickname"])
        if info.get("region"):
            print("country:", info.get("country"), "(" + info["region"] + ")")
        else:
            print("country: unknown")
    return 0 if info.get("region") else 2


if __name__ == "__main__":
    raise SystemExit(main())
