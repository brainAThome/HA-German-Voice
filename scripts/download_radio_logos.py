#!/usr/bin/env python3
"""Download missing radio logos for all built-in stations via Radio Browser API."""
import json
import os
import ssl
import urllib.request
import urllib.parse
import time

LOGO_DIR = "/config/www/radio_logos"
os.makedirs(LOGO_DIR, exist_ok=True)

# SSL context for downloads
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

RADIO_BROWSER = "https://de1.api.radio-browser.info"

# All built-in station keys → search terms for Radio Browser API
STATIONS = {
    "SWR3": "SWR3",
    "SWR1": "SWR1 Baden-Württemberg",
    "SWR2": "SWR Kultur",
    "WDR2": "WDR 2",
    "1LIVE": "1LIVE",
    "WDR5": "WDR 5",
    "Bayern3": "Bayern 3",
    "Bayern1": "Bayern 1",
    "NDR2": "NDR 2",
    "HR3": "HR3",
    "AntenneBayern": "Antenne Bayern",
    "RadioBob": "Radio BOB",
    "RockAntenne": "Rock Antenne",
    "SunshineLive": "Sunshine Live",
    "Fritz": "Fritz",
    "DLF": "Deutschlandfunk",
    "DLFKultur": "Deutschlandfunk Kultur",
    "Energy": "Energy Berlin",
    "BigFM": "bigFM",
    "KlassikRadio": "Klassik Radio",
    "Radio7": "Radio 7",
    "OE3": "Hitradio Ö3",
    "FIP": "FIP",
    "SwissJazz": "Radio Swiss Jazz",
    "LoungeFM": "Lounge FM",
    "AbsolutRelax": "Absolut Relax",
    "PlanetRadio": "Planet Radio",
    "RadioHamburg": "Radio Hamburg",
    "FFN": "radio ffn",
    "NDR1": "NDR 1 Niedersachsen",
    "NJOY": "N-JOY",
    "RadioBremen": "Bremen Eins",
    "DeltaRadio": "delta radio",
    "RSH": "R.SH",
    "Ostseewelle": "Ostseewelle",
    "AlsterRadio": "Alster Radio",
    "MDRJump": "MDR JUMP",
    "MDRSputnik": "MDR SPUTNIK",
    "RadioPSR": "Radio PSR",
    "Radio21": "Radio 21",
    "HitRadioFFH": "HIT RADIO FFH",
    "RPR1": "RPR1",
    "RadioRegenbogen": "Radio Regenbogen",
    "DieNeue1077": "die neue 107.7",
    "FluxFM": "FluxFM",
    "RadioPaloma": "Radio Paloma",
    "RTLRadio": "RTL Radio",
    "JamFM": "JAM FM",
    "StarFM": "Star FM",
    "RadioEins": "radioeins",
    "Cosmo": "COSMO",
    "YouFM": "YOU FM",
    # SomaFM channels
    "SomaFM": "SomaFM Groove Salad",
    "SomaGrooveSalad": "SomaFM Groove Salad",
    "SomaDroneZone": "SomaFM Drone Zone",
    "SomaSpaceStation": "SomaFM Space Station",
    "SomaIndiePop": "SomaFM Indie Pop Rocks",
    "SomaDefcon": "SomaFM DEF CON",
}


def is_valid_png(filepath):
    """Check if file exists and is a valid image (not SVG/too small)."""
    if not os.path.exists(filepath):
        return False
    size = os.path.getsize(filepath)
    if size < 500:  # SVGs renamed to .png or broken files
        return False
    # Check PNG magic bytes
    with open(filepath, "rb") as f:
        header = f.read(8)
    if header[:4] == b'\x89PNG':
        return True
    if header[:3] == b'\xff\xd8\xff':  # JPEG
        return True
    return False


def search_favicon(query):
    """Search Radio Browser API for a station and return its favicon URL."""
    url = f"{RADIO_BROWSER}/json/stations/byname/{urllib.parse.quote(query)}?limit=5&order=votes&reverse=true&hidebroken=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ha-radio-logos/1.0"})
        resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=10)
        stations = json.loads(resp.read())
        for s in stations:
            favicon = s.get("favicon", "")
            if favicon and len(favicon) > 10:
                return favicon
    except Exception as e:
        print(f"  Search failed for '{query}': {e}")
    return None


def download_image(url, filepath):
    """Download an image from URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ha-radio/1.0)"})
        data = urllib.request.urlopen(req, context=ssl_ctx, timeout=15).read()
        if len(data) < 100:
            return False
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"  OK: {len(data)} bytes")
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False


def main():
    downloaded = 0
    skipped = 0
    failed = 0

    for key, search_term in STATIONS.items():
        filepath = os.path.join(LOGO_DIR, f"{key}.png")

        if is_valid_png(filepath):
            print(f"[SKIP] {key} — already exists")
            skipped += 1
            continue

        print(f"[DOWNLOAD] {key} — searching '{search_term}'...")
        favicon_url = search_favicon(search_term)

        if not favicon_url:
            print(f"  FAIL: No favicon found")
            failed += 1
            continue

        print(f"  Favicon: {favicon_url[:80]}...")
        if download_image(favicon_url, filepath):
            # Verify it's valid
            if is_valid_png(filepath):
                downloaded += 1
            else:
                print(f"  WARN: Downloaded file is not a valid image, removing")
                os.remove(filepath)
                failed += 1
        else:
            failed += 1

        time.sleep(0.3)  # Be nice to the API

    print(f"\n=== DONE: {downloaded} downloaded, {skipped} skipped, {failed} failed ===")

    # Final check
    print(f"\nTotal files in {LOGO_DIR}:")
    files = [f for f in os.listdir(LOGO_DIR) if f.endswith(".png")]
    print(f"  {len(files)} PNG files")

    # Show still missing
    missing = []
    for key in STATIONS:
        fp = os.path.join(LOGO_DIR, f"{key}.png")
        if not is_valid_png(fp):
            missing.append(key)
    if missing:
        print(f"\nStill missing ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
