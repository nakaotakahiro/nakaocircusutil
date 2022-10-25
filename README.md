Nakao CIRCUS Utilities
===

# Installation
`pip install git+ssh://git@github.com/nakaotakahiro/nakaocircusutil.git`

# Executables
本パッケージをインストールすることで、下記のコマンドが実行可能になります。
- `update-voxels`: ボクセルラベル (.mhd) をCIRCUSサーバに送信 (上書き)
## update-voxels

既存のボクセルラベルを、ローカルにある .mhd ファイルの内容で上書きします。

症例画面から Export as MHD (Isolated)、または `circus-api-util case-dl` でダウンロードしたボクセルラベル (`vol***-label***.mhd`) をローカルで編集した後に、このコマンドで CIRCUS サーバに反映させることができます。

- 実行には [circus-api-util](https://github.com/smikitky/circus-api-util) のインストール、セットアップが別途必要です。
- いまのところ、**ラベルの新規追加はできません** (既存ラベルの上書きしかできません)。
  - 新規追加をしたい場合は、`circus-api-util case-addrev` などで空のラベルを別途作成してから `update-voxels` で上書きしてください。

例:
```sh
$ update-voxels /path/to/vol000-label000.mhd  # 基本的にこれで OK、Case ID などはパスから推論
$ update-voxels /path/to/vol000-label000.mhd --force  # 確認プロンプトを出さずに実行したい場合
$ update-voxels /path/to/vol000-label000.mhd --description "some comments"  # revision のコメントを指定したい場合
$ 
$ # どの症例のどのシリーズのどのラベルを上書きするか指定
$ # --series-no, --label-no は「上から何番目か (0オリジン)」
$ update-voxels /path/to/label.mhd \
    --case-id CASE_ID \
    --series-no 0 \
    --label-no 2
```