Nakao CIRCUS Utilities
===

# Installation
`pip install git+ssh://git@github.com/nakaotakahiro/nakaocircusutil.git`

# Executables
本パッケージをインストールすることで、下記のコマンドが実行可能になります。
- `update-voxels`: ボクセルラベル (.mhd) をCIRCUSサーバに送信
## update-voxels

ボクセルラベル (.mhd) をサーバに送信します。

症例画面から Export as MHD (Isolated)、または `circus-api-util case-dl` でダウンロードしたボクセルラベル (`vol***-label***.mhd`) をローカルで編集した後に、このコマンドで CIRCUS サーバに反映させることができます。

- 実行には [circus-api-util](https://github.com/smikitky/circus-api-util) のインストール、セットアップが別途必要です。
- いまのところ、既に存在するラベルを上書きすることしかできません (新規追加はできません)。

例:
```sh
$ update-voxels /path/to/vol000-label000.mhd  # 基本的にこれで OK、Case ID などはパスから推論
$ update-voxels /path/to/vol000-label000.mhd --force  # 確認プロンプトを出さずに実行したい場合
$ update-voxels /path/to/vol000-label000.mhd --description "some comments"  # revision のコメントを指定したい場合
```