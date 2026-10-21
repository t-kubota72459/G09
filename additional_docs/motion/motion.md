# Raspberry Piカメラを使ったウェブカメラサーバーの作り方

Raspberry Piを使ったセキュリティカメラプロジェクトを試してみよう。
まずは基本を学ぶ必要がある。このドキュメントでは、USB カメラを使ってウェブカメラサーバーを作成する方法を学ぶ。

## ウェブカメラサーバー

ウェブカメラサーバーとは、IP カメラの出力を表示するウェブページである。
IP カメラは IP ネットワークを介して通信するデバイスである。
つまり、ルーターによって構築されたネットワークを使用して制御データを受信し、画像データを送信する。
ウェブカメラサーバーは、ローカルネットワークに接続されたデバイスからアクセスすることも、ポート転送を介してインターネットに展開されたデバイスからアクセスすることもできる。
このチュートリアルでは、この両方を取り上げる。

## motion のインストール

次のコマンドを入力して、最新バージョンの OS を使用していることを確認する。

```sh
$ sudo apt-get update
$ sudo apt-get upgrade
```

motionは、様々な種類のカメラからのビデオ信号を監視できる、高度に設定可能なプログラムである。
Raspberry Piカメラモジュールも利用可能だが、今回は USB カメラを使ってみよう。
写真や動画の作成、カメラのライブストリーミング、さらにはモーション検知機能を使ってカメラで捉えたアクティビティのログ記録も可能である。
motion をインストールするには以下のようにする：

```sh
$ sudo mkdir /var/log/motion
$ sudo touch /var/log/motion/motion.log
$ sudo chmod a+rw /var/log/motion/motion.log
$ sudo apt install motion
```

## motion の設定

システムに motion が組み込まれたので、Raspberry Pi で動作するようにデフォルト設定を変更する。

次のコマンドを使用して、motion.conf ファイルを開く:

```sh
$ sudo vi /etc/motion/motion.conf
```

次の行を検索し、それぞれ変更した内容に置き換える：

- `daemon` off
- `stream_localhost` off
- `picture_output` off
- `movie_output` off


これらの設定により motion は不要な機能を無効にして動作する。

```sh
$ sudo systemctl enable motion # 起動時に有効化
```

再起動してみよう。

```sh
$ sudo reboot
```

## motion 動作確認

Raspberry Pi が立ち上がったら、他の PC の Web ブラウザから、以下のアドレスにアクセスしてみよう

http://自分のRasPi:8080/

お互いのアドレスにもアクセスしてみよう。

### うまくいかないとき

motion がうまく動かないときは、以下を試してみよう：

```sh
$ sudo systemctl status motion  # 動作を確認する
$ sudo systemctl restart motion # motion を再起動する
```
