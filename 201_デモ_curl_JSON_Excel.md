# 第20回　教員デモ
## `curl` / JSON / Python / Excel

このデモでは、

```text
Web API
   ↓ GET
JSON
   ↓
Python で複数回取得
   ↓
1つの JSON ファイルにまとめる
   ↓
Excel で表として利用する
```

という流れを見せる。

学生にコマンドやプログラムを暗記させることが目的ではない。

> **データをまず汎用的なテキストとして集めておき、必要になったときに Excel などで利用する**

という考え方を示す。

---

# 0. `curl` / `nkf` コマンドの紹介

## 阿部寛さんのホームページを GET する

まず、`curl` で HTML を取得する。

```bash
curl -s "https://abehiroshi.la.coocan.jp/"
```

Web ページも、元をたどれば HTML というテキストであることを確認する。

ただし、テキストには **文字コード** という約束がある。

日本語部分が正しく表示されない場合は、`nkf` で UTF-8 に変換する。

```bash
curl -s "https://abehiroshi.la.coocan.jp/" | nkf -w
```

ここで、

```text
curl
 ↓
Web からデータを取得

|
 ↓
左側の出力を右側へ渡す

nkf -w
 ↓
UTF-8 に変換
```

という流れだけ見せる。

必要ならファイルへ保存する。

```bash
curl -s "https://abehiroshi.la.coocan.jp/" | nkf -w > abe.html
```

## ここで伝えること

> **HTML もテキスト。  
> ただし、文字コードという約束が合わないと正しく読めない。**

ここでは文字コードやパイプを詳しく教え込まない。

---

# 1. `curl` で郵便番号に対応する住所を取得する

次は Web ページではなく、**データそのもの**を取得する。

zipcloud の郵便番号検索 API を使う。

例：

```bash
curl -s "https://zipcloud.ibsnet.co.jp/api/search?zipcode=7300011"
```

この API は、`zipcode` に指定した郵便番号を完全一致で検索し、結果を JSON で返す。

返ってくるデータのイメージ：

```json
{
  "message": null,
  "results": [
    {
      "address1": "広島県",
      "address2": "広島市中区",
      "address3": "基町",
      "prefcode": "34",
      "zipcode": "7300011"
    }
  ],
  "status": 200
}
```

JSON も中身はテキストである。

必要ならファイルへ保存する。

```bash
curl -s "https://zipcloud.ibsnet.co.jp/api/search?zipcode=7300011" -o address.json
```

確認：

```bash
cat address.json
```

## ここで伝えること

```text
ブラウザで見る Web ページ
        ↓
      HTML

プログラムから使うデータ
        ↓
      JSON
```

どちらも Web から HTTP で取得でき、どちらもテキストとして扱える。

---

# 2. Python で GET 要求を繰り返し、JSON データを集める

1件だけなら `curl` でよい。

しかし、複数の郵便番号について住所を集めたい場合は、Python で同じ GET 要求を繰り返せる。

今回は、あらかじめ調べたい郵便番号をリストにしておく。

```python
postcodes = [
    "7300011",
    "7300031",
    "7300035",
    "7320822",
    "7390046",
]
```

このリストの郵便番号について、1件ずつ Web API へ GET 要求を送り、結果を集める。

## プログラム例

```python
import json
import time
import urllib.parse
import urllib.request

API_URL = "https://zipcloud.ibsnet.co.jp/api/search"

postcodes = [
    "7300011",
    "7300031",
    "7300035",
    "7320822",
    "7390046",
]

records = []

for zipcode in postcodes:
    params = urllib.parse.urlencode({
        "zipcode": zipcode
    })

    url = API_URL + "?" + params

    print("GET", url)

    with urllib.request.urlopen(url) as response:
        data = json.load(response)

    if data["status"] != 200:
        print("ERROR:", zipcode, data["message"])
        continue

    if data["results"] is None:
        print("NOT FOUND:", zipcode)
        continue

    for result in data["results"]:
        records.append({
            "zipcode": result["zipcode"],
            "prefecture": result["address1"],
            "city": result["address2"],
            "town": result["address3"]
        })

    # 短時間に大量の要求を送らないよう、少し待つ
    time.sleep(0.2)

with open(
    "hiroshima_addresses.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        records,
        f,
        ensure_ascii=False,
        indent=2
    )

print("件数:", len(records))
print("hiroshima_addresses.json に保存しました")
```

例えば、

```text
get_addresses.py
```

として保存して実行する。

```bash
python3 get_addresses.py
```

実行中は、

```text
GET https://zipcloud.ibsnet.co.jp/api/search?zipcode=7300011
GET https://zipcloud.ibsnet.co.jp/api/search?zipcode=7300031
GET https://zipcloud.ibsnet.co.jp/api/search?zipcode=7300035
...
```

のように表示される。

> **同じ API へ、郵便番号を変えながら GET 要求を繰り返している**

ことを見せる。

---

# 3. 集めた JSON ファイルを確認する

生成された、

```text
hiroshima_addresses.json
```

を開く。

形式は次のような **JSON のリスト** になる。

```json
[
  {
    "zipcode": "7300011",
    "prefecture": "広島県",
    "city": "広島市中区",
    "town": "基町"
  },
  {
    "zipcode": "...",
    "prefecture": "広島県",
    "city": "...",
    "town": "..."
  }
]
```

ここで重要なのは、

> **1件ずつ返ってきた JSON を、Python で1つの JSON ファイルにまとめた**

という点。

```text
GET 1回目 → JSON
GET 2回目 → JSON
GET 3回目 → JSON
GET 4回目 → JSON
GET 5回目 → JSON
              ↓
         Python で集約
              ↓
hiroshima_addresses.json
```

CSV をダウンロードしているわけではない。

---

# 4. JSON を Excel で表形式にする

生成した、

```text
hiroshima_addresses.json
```

を Windows PC へコピーする。

Excel から JSON を読み込む。

```text
データ
 ↓
データの取得
 ↓
ファイルから
 ↓
JSON から
```

`hiroshima_addresses.json` を選択する。

Power Query で JSON の内容が表示される。

一番外側はリストなので、

```text
List
 ↓
テーブルへの変換
 ↓
Record の列を展開
```

と操作する。

展開する項目：

```text
zipcode
prefecture
city
town
```

最終的に、

| zipcode | prefecture | city | town |
|---|---|---|---|
| 7300011 | 広島県 | 広島市中区 | 基町 |
| … | … | … | … |

のような表になる。

最後に、

```text
閉じて読み込む
```

で Excel のシートへ読み込む。

---

# デモ全体のまとめ

```text
0. HTML を GET
   ↓
curl / nkf
   ↓
テキストと文字コード

1. 郵便番号を1件 GET
   ↓
JSON が返る

2. Python で郵便番号を変えながら
   GET を繰り返す
   ↓
返ってきた JSON を集める
   ↓
1つの JSON ファイルとして保存

3. JSON
   ↓
Excel / Power Query
   ↓
表形式で閲覧・集計
```

このデモで見せたいのは、

> **Excel ファイルを直接生成しなくてもよい**

ということ。

```text
データを取得する
      ↓
JSON として保存する
      ↓
必要なときに Excel で読む
```

と分けることができる。

元データが JSON のようなテキストなら、

```text
JSON
 ├─ Excel で読む
 ├─ Python で読む
 ├─ 別のプログラムへ渡す
 ├─ Web で送る
 └─ AI へ渡す
```

と、あとから利用方法を選びやすい。

## 今日の一言

> **まずデータを汎用的なテキストとして集める。  
> Excel は必要になったときに利用する。**
