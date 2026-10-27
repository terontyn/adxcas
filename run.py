"""One-shot generation or an explicit timezone-aware daily schedule."""
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time

def next_run(now, clock):
    hour, minute = map(int, clock.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return target if target > now else target + timedelta(days=1)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="synthetic prices; no supplier requests")
    parser.add_argument("--daily", help="HH:MM; explicit recurring execution")
    parser.add_argument("--timezone", default="UTC", help="IANA timezone; default UTC")
    args = parser.parse_args()
    zone = ZoneInfo(args.timezone)
    if args.daily:
        next_run(datetime.now(zone), args.daily)
    def job():
        if args.demo:
            from demo.generate import generate
            generate()
        else:
            import main as app
            app.main()
    job()
    while args.daily:
        target = next_run(datetime.now(zone), args.daily)
        while datetime.now(zone) < target:
            time.sleep(min(30, max(0, (target - datetime.now(zone)).total_seconds())))
        job()

if __name__ == "__main__":
    main()
