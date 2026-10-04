# マイコン実習 第19回
## Web AGV④ ― 完成と「プロトコルでつながる」

**実施日：2026年10月5日**  
**授業時間：200分**

---

# 今日の目標

今日は Web AGV の最終回です。

これまで、

```text
センサ入力
   ↓
判断
   ↓
モータ制御
```

から、

```text
Web入力
   ↓
HTTP request
   ↓
判断
   ↓
モータ制御
```

へ発展させてきました。

今日は進み具合によって、2つのMISSIONに分かれます。

| MISSION | 対象 | 今日のゴール |
|---|---|---|
| A | Web AGVがまだ未完成 | LEFT / RIGHT を追加し、全方向操作を完成する |
| B | Web AGVが完成済み | Raspberry Pi 4 からHTTPでWeb AGVを操作する |

どちらのMISSIONでも、

> **すでに動く部分は作り直さず、必要な部分だけ変更して実機で確認する。**

---

# 0. 最初に確認する

自分の Web AGV を起動し、現在できていることを確認してください。

- [ ] Webページが表示できる
- [ ] FORWARD が動作する
- [ ] BACK が動作する
- [ ] STOP が動作する
- [ ] SPEED UP / SPEED DOWN が動作する
- [ ] LEFT が動作する
- [ ] RIGHT が動作する

LEFT / RIGHT がまだ動かない場合は **MISSION A**、全方向と速度変更まで動く場合は **MISSION B** へ進みます。

> 15分程度で前回の状態へ戻せない場合は、そこで止まり続けず先生へ相談してください。

---

# MISSION A
## Web AGVを完成させる ― LEFT / RIGHT を追加する

### MISSION A のゴール

> **Webから FORWARD / BACK / LEFT / RIGHT / STOP を操作できる。**

速度変更まで動けば、Web AGV完成です。

---

## A-1　復旧用基準版を使う場合

前回のプログラムが大きく崩れている場合は、

```text
191_web_agv_restore.py
```

から再開しても構いません。

このプログラムには、

```text
FORWARD
BACK
STOP
SPEED UP
SPEED DOWN
```

まで入っています。

ただし、

```text
LEFT
RIGHT
```

は入っていません。

> **LEFT / RIGHT は、自分で追加してください。**

---

## A-2　既存の旋回処理を探す

以前のプログラムから、左旋回・右旋回に使えるモータ制御を探します。

新しくモータ制御を全部作り直す必要はありません。

```text
LEFT で使う関数：______________________________

RIGHTで使う関数：______________________________
```

- [ ] 左旋回の処理を見つけた
- [ ] 右旋回の処理を見つけた
- [ ] 関数だけを呼び出して、実機の向きを確認した

---

## A-3　Webページへ LEFT / RIGHT を追加する

FORWARD / BACK のボタンを参考に、

```text
/left
/right
```

へアクセスするボタンを追加します。

まだ車体の電池電源はOFFのままです。

ThonnyのShellで、

```text
GET /left HTTP/1.1
GET /right HTTP/1.1
```

が表示されることを確認します。

> Shellに表示されているGETは、Shellから入力したものではありません。  
> Picoがネットワークから**受け取ったHTTP request**の先頭行を `print()` して確認しています。

---

## A-4　request と旋回処理をつなぐ

FORWARD / BACK の処理を参考に、

```text
GET /left
   ↓
左旋回

GET /right
   ↓
右旋回
```

となるようにします。

---

## A-5　車体を動かして確認する

ここから車体の電源を入れます。

最初は車輪を浮かせるなど、すぐに停止できる状態で確認します。

- [ ] FORWARD → STOP
- [ ] BACK → STOP
- [ ] LEFT → STOP
- [ ] RIGHT → STOP
- [ ] SPEED UP / SPEED DOWN → もう一度走行
- [ ] 最後にSTOP

### ✅ MISSION A CLEAR

> **FORWARD / BACK / LEFT / RIGHT / STOP と速度変更をWebから操作できた。**

---

## A-6　うまく動かないとき

全体を書き直さず、どこまで正常かを確認します。

```text
Web画面
  ↓
HTTP request
  ↓
if / elif
  ↓
モータ制御関数
  ↓
GPIO / PWM
  ↓
モータドライバ
  ↓
モータ・ギヤボックス
```

```text
正常だったところ：


おかしいところ：


次に確認するところ：

```

<div style="break-before: page; page-break-before: always;"></div>

# MISSION B
## Raspberry Pi 4 から Web AGV を操作する

### MISSION B のゴール

これまでは、スマホやPCの**ブラウザ**から Pico へHTTP requestを送っていました。

今日は送信する側を変えます。

```text
スマホ・PCのブラウザ
        │
        │ HTTP
        ▼
       Pico
```

から、

```text
Raspberry Pi 4 のPython
        │
        │ HTTP
        ▼
       Pico
```

へ変更します。

ここで確認したいことは、

> **送信する機械やプログラムが変わっても、同じプロトコルに従えば通信できる。**

ということです。

---

# B-1　Raspberry Pi 4 を Pico のWi-Fiへ接続する

Raspberry Pi 4 の有線LANは、そのまま接続しておきます。

Wi-Fiだけを、自分のPicoへ接続します。

```text
Ethernet → 学内LAN
Wi-Fi    → PICO_AGV_<出席番号>
```

GUIからWi-Fiを選び、自分のPicoへ接続してください。

その後、Raspberry Pi 4 のChromiumで、

```text
http://192.168.4.1/
```

を開きます。

- [ ] Web AGVの画面が表示された
- [ ] ブラウザからFORWARD / STOPなどを操作できた

---

# B-2　ブラウザが送ったHTTP requestを見る

この確認では、

```text
Pico      ：USB接続
車体電源  ：OFF
```

としておきます。

Raspberry Pi 4 のブラウザからFORWARDを押します。

Pico側のThonny Shellに、

```text
GET /forward HTTP/1.1
```

が表示されることを確認します。

このGETは、

> **Picoがネットワークから受け取ったHTTP request**

です。

---

# B-3　Pythonから同じHTTP requestを送る

配布された、

```text
192_raspi_http_test.py
```

をRaspberry Pi 4で開きます。

このプログラムでは、ブラウザを使わずに、PythonからHTTP requestを送ります。

特に、次の文字列を確認してください。

```text
GET /forward HTTP/1.1
Host: 192.168.4.1
Connection: close
```

これは、ブラウザが送っていたHTTP requestと同じ形式です。

プログラムを実行し、Pico側のThonny Shellを確認します。

- [ ] Pythonを実行した
- [ ] PicoのShellに `GET /forward HTTP/1.1` が表示された
- [ ] 続いて `GET /stop HTTP/1.1` が表示された

## 比べる

ブラウザから操作したとき：

```text
GET /forward HTTP/1.1
```

Pythonから操作したとき：

```text
GET /forward HTTP/1.1
```

送信したプログラムは違います。

しかし、Picoから見ると同じ形式のrequestです。

### 確認問題

なぜ、ブラウザでもPythonでも同じWeb AGVを操作できるのでしょうか。

```text


```

---

# HTTPで決まっているもの / 自分たちで決めたもの

HTTPでは、

```text
GET /xxxx HTTP/1.1
```

のようなrequestの形式や、request / response のやり取り方法が決められています。

一方、

```text
/forward
/back
/left
/right
/stop
```

という名前は、HTTPで決められているわけではありません。

これは、

> **今回のWeb AGVで自分たちが決めた命令の名前**

です。

```text
HTTPの共通ルール
        ＋
Web AGVで決めたURL
        ↓
異なるプログラムから同じPicoを操作できる
```

---

# B-4　PythonからWeb AGVを走行させる

通信だけの確認ができたら、次は車体を動かします。

```text
Pico      ：最終プログラムを保存
USB       ：外す
車体電源  ：ON
RasPi Wi-Fi：自分のPicoへ接続
```

`192_raspi_http_test.py` を実行します。

- [ ] PythonからFORWARDできた
- [ ] PythonからSTOPできた

### ✅ MISSION B CLEAR 1

> **ブラウザ以外のPythonプログラムから、HTTPを使ってWeb AGVを操作できた。**

---

# B-5　課題：命令を順番に送る

これまでは、人が1つずつ命令を送っていました。

ここでは、Pythonに複数の命令を順番に実行させます。

## 課題

Web AGVを次の順番で動かしてください。

```text
2秒前進
  ↓
STOP
  ↓
右へ約90°旋回
  ↓
STOP
```

この動作を **4回繰り返し**、

> **四角形を描くように走行して、出発地点付近へ戻ってくる**

ようにしてください。

前進時間は **2秒** とします。

右旋回の時間は、自分の車体に合わせて調整してください。

- [ ] 2秒前進した
- [ ] 前進後にSTOPした
- [ ] 右へ約90°旋回した
- [ ] 旋回後にSTOPした
- [ ] この動作を4回繰り返した
- [ ] 出発地点付近へ戻ってきた

## 調整

最初から正確に戻る必要はありません。

実際に走らせ、

```text
曲がりすぎた
        ↓
右旋回の時間を短くする

曲がり足りない
        ↓
右旋回の時間を長くする
```

のように、プログラムを変更して再確認します。

### ✅ MISSION B CLEAR 2

> **PythonからHTTP requestを決められた順番で送り、Web AGVを一連の手順で動かすことができた。**

この「決められた順番で動かす」という考え方は、次に扱う**シーケンス制御**につながります。

---

# B-6　FlaskからAUTO運転を開始する

B-5で作った、

```text
2秒前進
  ↓
STOP
  ↓
右へ約90°旋回
  ↓
STOP
```

を4回繰り返して出発地点付近へ戻る動作を、ここでは **AUTO運転** とします。

配布された、

```text
193_raspi_flask_controller.py
```

を使います。

このプログラムのWebページには、

```text
AUTO START
```

だけがあります。

Raspberry Pi 4でFlaskを起動し、Chromiumで、

```text
http://127.0.0.1:5000/
```

を開きます。

AUTO STARTを押すと、B-5と同じ動作が始まります。

```text
Raspberry Pi上のブラウザ
        │
        │ HTTP
        ▼
Raspberry Pi上のFlask
        │
        │ HTTP
        ▼
Pico Web AGV
        │
        ▼
モータ
```

右旋回の時間 `TURN_TIME` は、B-5で調整した値へ変更してください。

- [ ] Flaskを起動した
- [ ] `AUTO START` のページを表示した
- [ ] AUTO STARTを押した
- [ ] B-5と同じ動作が始まった
- [ ] 出発地点付近へ戻ってきた
- [ ] 最後に停止した

### ✅ MISSION B CLEAR 3

> **ブラウザからFlaskへHTTP requestを送り、FlaskからPicoへHTTP requestを送ってAUTO運転を開始できた。**

---

# 早く終わった人
## 左回りのAUTO運転を追加する

MISSION B CLEAR 3 まで終わった人は、右回りのAUTO運転をもとに、**左回り版**を作ります。

## 発展1　左回りで出発地点付近へ戻る

次の動作を作ってください。

```text
2秒前進
  ↓
STOP
  ↓
左へ約90°旋回
  ↓
STOP
```

これを **4回繰り返し**、

> **左回りで四角形を描くように走行して、出発地点付近へ戻ってくる**

ようにします。

右回りで作ったプログラムを全部作り直すのではなく、どこを変更すればよいか考えてください。

- [ ] 左旋回のHTTP requestへ変更した
- [ ] 左旋回の時間を調整した
- [ ] 4回繰り返して走行した
- [ ] 出発地点付近へ戻ってきた
- [ ] 最後にSTOPした

---

## 発展2　左回りを `AUTO2` として呼び出す

左回りの動作が確認できたら、Flaskのページから呼び出せるようにします。

Webページに、

```text
AUTO START
AUTO2
```

の2つを表示します。

```text
AUTO START
   ↓
右回りで出発地点付近へ戻る

AUTO2
   ↓
左回りで出発地点付近へ戻る
```

`193_raspi_flask_controller.py` を読み、`/auto` の処理を参考にして、

```text
/auto2
```

へアクセスしたときに左回りのAUTO運転が始まるようにしてください。

- [ ] Webページに `AUTO2` を追加した
- [ ] `/auto2` の処理を追加した
- [ ] `AUTO START` では右回りした
- [ ] `AUTO2` では左回りした
- [ ] どちらも最後にSTOPした

### ✅ 発展CLEAR

> **既存の右回りAUTO運転を参考にして、左回りへ仕様変更し、別のWeb入力から呼び出せるようにした。**

---

# Web AGV 最終まとめ

今回のWeb AGVでは、入力するものを変えてきました。

```text
センサ
  ↓
文字入力
  ↓
Webブラウザ
  ↓
Raspberry PiのPython
```

MISSION Bでは、さらに、

```text
ブラウザ → Flask → Pico
```

というように、別々のプログラムをつなぎました。

それができる理由の一つが、

> **HTTPという共通のプロトコル（通信の約束）**

です。

異なる機器・OS・プログラムでも、共通の約束に従えば情報をやり取りできます。

---

# 今日の記録

自分が取り組んだMISSION：

```text
A / B
```

今日できたこと：

```text


```

今日うまくいかなかったこと：

```text


```

どこまで確認したか：

```text


```

MISSION Bの人は、ブラウザとPythonからPicoへ届いたrequestを比較して、気づいたことを書いてください。

```text


```

---

# 保存・記録・片付け

最後の20分は、新しい作業を始めません。

- [ ] Pico側の最終プログラムを保存した
- [ ] PC側にも最終プログラムを保存した
- [ ] Raspberry Piで作ったプログラムを保存した
- [ ] 車体の電源をOFFにした
- [ ] PicoのUSBケーブルを外した
- [ ] Raspberry Piを通常の状態へ戻した
- [ ] 工具・部品を片付けた
- [ ] 机の上を整理した

> 保存場所やファイルの整理方法は、次回あらためて扱います。
