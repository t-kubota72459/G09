# 269 KENTEI Web HMI v0.7 — STA版 / BCD 10～15で該当桁を消灯

v0.6の**教室Wi-Fi STA接続・DHCPアドレスのShell出力・学生向けMSB先頭API**を維持し、KENTEIくんで実機確認された「BCD=12で表示が消える」動作を追加しました。画面はv0.4のPCコンパクト表示／スマホ表示を継承しています。

**実機で確認された事実:** DPL1に8（1000）→12（1100）→4（0100）を入力すると「8 → 消灯 → 4」になる。v0.7は同じ動作を再現します。BCD 10～15の消灯は、10進表示器としての動作に合わせた設計です（実機で直接確認済みなのは12）。

## ESP32のファイル配置

```text
ESP32フラッシュ /
├── main.py          # STA接続・DSW×3デモ（v0.6から変更なし）
├── hmi.py           # v0.7：生BCDを保持して10～15で消灯
├── index.html       # v0.7：消灯＋ビット表示に対応
└── wifi_config.py   # wifi_config.example.pyをコピーして用意（Git管理外）
```

**v0.6からの更新なら、`hmi.py` と `index.html` の2ファイルをESP32のルートへ上書き**してください。`main.py` と `wifi_config.py` を上書きする必要はありません。Wi-FiパスワードはGitHubなどへ公開しないでください。

GitHubには `wifi_config.example.py`（ダミー値のみ）を登録します。ESP32へ配置する際には、ファイルを `wifi_config.py` にコピーし、各自でSSIDとパスワードを記入してください。実際の `wifi_config.py` は `.gitignore` でGit管理から除外します。

Wi-Fiの設定例（`wifi_config.py`）:

```python
WIFI_SSID = 'YOUR_CLASSROOM_SSID'
WIFI_PASSWORD = 'YOUR_CLASSROOM_PASSWORD'
```

ESP32起動時にDHCPで取得したIPとURLをThonnyのShellに表示します。教室APで端末間通信が許可されていれば、同じネットワークのPCやスマホからアクセスできます。

## 学生向けAPI（MSB先頭）

| メソッド | 動作 |
|---|---|
| `hmi.web_shori()` | HTTP要求が来ていたら最大1件処理 |
| `hmi.dsw_yomu()` | DSWの4ビットを `[8,4,2,1]` の順で返す |
| `hmi.dpl1_hyouji(bits)` | DPL1（一の位）にMSB先頭4ビットを出力 |
| `hmi.dpl2_hyouji(bits)` | DPL2（十の位）にMSB先頭4ビットを出力 |

```python
hmi.dpl1_hyouji([1, 0, 0, 0])  # DPL1: 8
hmi.dpl1_hyouji([1, 1, 0, 0])  # DPL1: 12 -> 消灯
hmi.dpl1_hyouji([0, 1, 0, 0])  # DPL1: 4 -> 再点灯
```

### 無効な値の扱い

**4ビットとして正常な入力（各ビット0/1、4要素）の場合:**

| 出力BCD | 表示 | 端子相当の4ビット | Shell |
|---|---|---|---|
| 0～9 | 数字を表示 | そのまま保持 | 警告なし |
| 10～15 | **その桁のみ消灯** | **そのまま保持** | 最初の1回だけ警告 |
| 10～15 → 0～9 | 数字を再表示 | 新しい値 | 警告状態をリセット |

警告の例:

```text
[KENTEI HMI] WARNING: DPL1 BCD=1100 (12) -> 10進表示範囲外のため消灯
```

同じ桁に10～15を繰り返し書いてもShellを埋めません。正常な値に戻した後の新たな異常では、再度警告します。学生プログラムへの例外は出しません。

**Pythonの呼び出し自体が不正な場合**（リストが4要素でない、`2`や文字列を含むなど）は、4ビットの信号を表現できないので、**前の出力を維持し警告**します。これも例外による制御ループ停止は避けます。

### Web画面（index.html）の変更

- 10～15の桁は、発光している7セグメントがすべてOFFになり、**暗いセグメントの輪郭だけ**残ります。
- 画面下のDPL1/DPL2ビット表示には、消灯時も実際に指定した `1100` などの値が表示されます。
- `/api/state` の `dpl1_bcd` と `dpl2_bcd` は生の4ビット値（0～15）です。いずれかの桁が消灯なら、合成十進数 `dpl` はJSONの `null` になります。追加の `dpl1_blank` / `dpl2_blank` は消灯状態を示します。
- **ブラウザ単体のデモ**には「BCD=12 消灯テスト」ボタンを追加しました。ESP32実機に接続しているときには、このテスト用ボタンは表示されません。
- 既存のPC向けコンパクトレイアウトとスマホ向けレイアウトは維持しています。

## テスト用の自動実行例

`examples/main_blank_test.py` は **3秒ずつ、8 → 消灯(12) → 4** を繰り返す確認用プログラムです。ESP32の動作版 `main.py` をバックアップした後、必要な場合に限りサンプル内容を `/main.py` にして実行してください。コンベヤのGPIOは操作しません。

`main.py` は従来の `DSW × 3` のデモのままなので、通常はBCD 10～15になりません。消灯を試す場合は上記のサンプルを使ってください。

## 既存APIとの互換性

以下はこれまでどおり使えます。

```python
hmi.read_dsw()       # 0～9の整数
hmi.dpl_hyouji(42)   # 00～99の整数
```

`read_dsw_bits()`、`read_dpl_bits()`、`write_dpl_bcd()` の旧APIは端子番号順（LSB先頭）のままです。`read_dpl_bits()` は、消灯時にも10～15の生の4ビットを読めるよう拡張しました。`encode_bcd()` / `decode_bcd()` および `write_dpl_bcd()` は引き続き10進BCDのみを受け付け、従来の厳密なエラー処理を維持しています。学生にはMSB先頭の新APIを使わせてください。

## 検証状況

PCで `python -m unittest discover -s tests -v` を実行して **22件合格**。ブラウザでの模擬表示についても、8 → 消灯(12) → 4、ビット表示維持、PC画面とスマホ幅のレイアウトを確認しています。

**実機確認（2026-11-17）:** 教室Wi-FiへのSTA接続、DHCPのIP/URLのThonny Shell出力、PCブラウザでの8→消灯(BCD=12)→4の動作を確認済みです。KENTEIくん単体でもBCD=12で表示が消えることを確認済みです（両機器を直接結線した試験ではありません）。元のv0.4/v0.6のSTA接続・HTTP処理は変更していません。Web通信は`web_shori()`の中で一時的にブロックする場合があるため、安全に関わる実機停止制御には使用しないでください。

## Git管理用の配置

このディレクトリを `G09/269_KENTEI_Web_HMI/` に配置してください。

```bash
git add 269_KENTEI_Web_HMI/
git commit -m "Add KENTEI Web HMI v0.7 STA BCD emulator"
git push origin main
```

`wifi_config.py`（実際のSSID・パスワード）はコミットしないでください。
