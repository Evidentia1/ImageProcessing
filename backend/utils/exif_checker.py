# ✅ utils/exif_checker.py

from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

def extract_exif_data(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        extracted = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            extracted[tag] = value
        return extracted
    except Exception:
        return None

def get_datetime_original(exif):
    try:
        return datetime.strptime(exif.get("DateTimeOriginal", ""), "%Y:%m:%d %H:%M:%S")
    except:
        return None

def has_gps_data(exif):
    return 'GPSInfo' in exif if exif else False

def validate_exif_logic(file_path, policy_data):
    exif = extract_exif_data(file_path)
    exif_date = get_datetime_original(exif) if exif else None

    result = {
        'exif': exif,
        'exif_date': str(exif_date) if exif_date else None,
        'gps_available': has_gps_data(exif),
        'exif_vs_policy': "unknown",
        'exif_vs_dol': "unknown"
    }

    def to_date(val):
        if isinstance(val, datetime): return val.date()
        if hasattr(val, "date"): return val.date()
        if isinstance(val, str):
            try:
                val = val.split("T")[0]
                return datetime.strptime(val, "%Y-%m-%d").date()
            except:
                return None
        return None

    policy_start = to_date(policy_data.get("policy_date"))
    dol = to_date(policy_data.get("dol"))
    threshold = int(policy_data.get("threshold", 0))
    exif_dt = to_date(exif_date)

    if exif_dt and policy_start:
        result["exif_vs_policy"] = "valid" if exif_dt >= policy_start else "invalid"

    if exif_dt and dol:
        diff = abs((dol - exif_dt).days)
        result["exif_vs_dol"] = "approve" if diff <= threshold else "too_far"

    return result
