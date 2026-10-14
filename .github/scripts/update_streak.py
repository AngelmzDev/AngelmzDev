"""Refresh both streak cards, keeping the previous images if a download fails."""

from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
COMMON = {
    "user": "AngelmzDev",
    "hide_border": "true",
    "disable_animations": "true",
    "background": "00000000",
}
THEMES = {
    "light": {
        "ring": "576F95", "fire": "576F95", "currStreakLabel": "576F95",
        "sideLabels": "57606A", "currStreakNum": "24292F",
        "sideNums": "24292F", "dates": "57606A", "stroke": "D0D7DE",
    },
    "dark": {
        "ring": "A6BCD9", "fire": "A6BCD9", "currStreakLabel": "A6BCD9",
        "sideLabels": "ADB8C5", "currStreakNum": "E6EDF3",
        "sideNums": "E6EDF3", "dates": "ADB8C5", "stroke": "30363D",
    },
}


def download_card(theme):
    url = "https://streak-stats.demolab.com/?" + urlencode(COMMON | theme)
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "AngelmzDev-profile"})
            with urlopen(request, timeout=45) as response:
                if response.headers.get_content_type() != "image/svg+xml":
                    raise ValueError("The service did not return an SVG image")
                content = response.read(200_001)
            if len(content) > 200_000:
                raise ValueError("Unexpected card size")
            root = ET.fromstring(content)
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                raise ValueError("Invalid SVG root")
            text = " ".join(root.itertext())
            for label in ("Total Contributions", "Current Streak", "Longest Streak"):
                if label not in text:
                    raise ValueError("The service returned an error or incomplete card")
            if any(node.tag.rsplit("}", 1)[-1] in {"script", "animate", "animateTransform"}
                   for node in root.iter()):
                raise ValueError("The card must be a static image")
            # Keep generated files stable and free of trailing whitespace.
            return ("\n".join(line.rstrip() for line in content.decode("utf-8").splitlines()) + "\n").encode("utf-8")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * (attempt + 1))


if __name__ == "__main__":
    # Validate both downloads before replacing either existing card.
    cards = {name: download_card(theme) for name, theme in THEMES.items()}
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for name, content in cards.items():
        destination = assets / f"streak-{name}.svg"
        destination.write_bytes(content)
        print(f"Updated {destination.name}")
