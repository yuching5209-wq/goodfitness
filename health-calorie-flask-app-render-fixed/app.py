from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = Path(os.environ.get("DATA_FILE", BASE_DIR / "data" / "user_data.json"))
FALLBACK_DATA_FILE = Path("/tmp/user_data.json")

ACTIVITY_FACTORS = {
    "sedentary": ("久坐/少運動", 1.2),
    "light": ("輕度活動", 1.375),
    "moderate": ("中度活動", 1.55),
    "active": ("高度活動", 1.725),
}

EXERCISE_METS = {
    "快走": 4.3,
    "慢跑": 7.0,
    "跑步": 9.8,
    "自行車": 6.8,
    "游泳": 8.0,
    "重量訓練": 5.0,
    "瑜伽": 3.0,
    "籃球": 6.5,
    "跳繩": 12.3,
}


def today_key() -> str:
    return date.today().isoformat()


def default_data() -> dict:
    return {
        "profile": None,
        "records": {},
    }


def load_data() -> dict:
    ensure_data_file()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        data = default_data()
        save_data(data)

    data.setdefault("profile", None)
    data.setdefault("records", {})
    return data


def save_data(data: dict) -> None:
    global DATA_FILE
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except OSError:
        DATA_FILE = FALLBACK_DATA_FILE
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)


def ensure_data_file() -> None:
    if not DATA_FILE.exists():
        save_data(default_data())


def get_today_record(data: dict) -> dict:
    records = data.setdefault("records", {})
    return records.setdefault(today_key(), {"foods": [], "exercises": []})


def as_float(value: str, minimum: float = 0) -> float:
    number = float(value)
    if number < minimum:
        raise ValueError("number below minimum")
    return number


def calculate_bmr(profile: dict | None) -> int:
    if not profile:
        return 0

    weight = profile["weight"]
    height = profile["height"]
    age = profile["age"]
    if profile["gender"] == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    return round(bmr)


def calculate_tdee(profile: dict | None) -> int:
    if not profile:
        return 0
    bmr = calculate_bmr(profile)
    factor = ACTIVITY_FACTORS.get(profile.get("activity"), ACTIVITY_FACTORS["sedentary"])[1]
    return round(bmr * factor)


def summarize(data: dict) -> dict:
    profile = data.get("profile")
    record = get_today_record(data)
    bmr = calculate_bmr(profile)
    tdee = calculate_tdee(profile)
    total_food = round(sum(item["calories"] for item in record["foods"]))
    total_exercise = round(sum(item["calories"] for item in record["exercises"]))
    allowance = max(tdee + total_exercise, 0)
    remaining = allowance - total_food
    progress = 0 if allowance == 0 else min(round(total_food / allowance * 100), 100)

    return {
        "date": today_key(),
        "bmr": bmr,
        "tdee": tdee,
        "total_food": total_food,
        "total_exercise": total_exercise,
        "allowance": allowance,
        "remaining": remaining,
        "progress": progress,
        "record": record,
    }


@app.route("/")
def index():
    data = load_data()
    profile = data.get("profile")
    activity_label = None
    if profile:
        activity_label = ACTIVITY_FACTORS.get(profile["activity"], ACTIVITY_FACTORS["sedentary"])[0]

    return render_template(
        "index.html",
        profile=profile,
        activity_label=activity_label,
        summary=summarize(data),
        activity_factors=ACTIVITY_FACTORS,
        exercise_mets=EXERCISE_METS,
    )


@app.post("/profile")
def update_profile():
    data = load_data()
    try:
        data["profile"] = {
            "gender": request.form["gender"],
            "age": round(as_float(request.form["age"], 1)),
            "height": as_float(request.form["height"], 1),
            "weight": as_float(request.form["weight"], 1),
            "activity": request.form["activity"],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        save_data(data)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.post("/food")
def add_food():
    data = load_data()
    try:
        food_name = request.form["food_name"].strip()
        calories = as_float(request.form["food_calories"], 0)
        if food_name:
            record = get_today_record(data)
            record["foods"].append(
                {
                    "name": food_name,
                    "calories": round(calories),
                    "time": datetime.now().strftime("%H:%M"),
                }
            )
            save_data(data)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.post("/exercise")
def add_exercise():
    data = load_data()
    profile = data.get("profile")
    try:
        exercise_name = request.form["exercise_name"]
        minutes = as_float(request.form["minutes"], 1)
        met = EXERCISE_METS[exercise_name]
        weight = profile["weight"] if profile else 60
        calories = met * 3.5 * weight / 200 * minutes
        record = get_today_record(data)
        record["exercises"].append(
            {
                "name": exercise_name,
                "minutes": round(minutes),
                "calories": round(calories),
                "time": datetime.now().strftime("%H:%M"),
            }
        )
        save_data(data)
    except (KeyError, ValueError):
        pass
    return redirect(url_for("index"))


@app.post("/reset-today")
def reset_today():
    data = load_data()
    data.setdefault("records", {})[today_key()] = {"foods": [], "exercises": []}
    save_data(data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
