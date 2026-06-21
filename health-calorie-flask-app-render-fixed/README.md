# 健康熱量記錄器

這是一個使用 Python Flask 製作的 RWD 網頁小程式，可以記錄使用者身體組成、每日飲食、運動消耗與剩餘熱量。資料會保存到 `data/user_data.json`，重新整理或重新開啟網站後仍會保留。

## 功能

- 輸入性別、年齡、身高、體重、活動量
- 自動計算 BMR 與 TDEE
- 新增每日食物與熱量
- 新增運動項目與分鐘數，依照體重與 METs 計算消耗
- 顯示今日攝取進度、運動消耗與剩餘熱量
- 可部署成公開網站，手機瀏覽器可加入主畫面

## 本機執行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

打開瀏覽器進入：

```text
http://127.0.0.1:5000
```

## 部署到 Render

1. 到 GitHub 建立一個新的 Repository。
2. 將本專案所有檔案上傳到 GitHub。
3. 到 Render 建立 New Web Service。
4. 連接你的 GitHub Repository。
5. Build Command 填：

```bash
pip install -r requirements.txt
```

6. Start Command 填：

```bash
gunicorn app:app
```

7. 部署完成後 Render 會給你一個公開網址，例如 `https://你的專案.onrender.com`。

## 已刪除項目

原本企劃中的政府 API 運動中心人流查詢已移除，避免 API 斷線、資料格式異動或跨縣市資料不一致造成展示失敗。本版本專注於健康紀錄與熱量管理。
