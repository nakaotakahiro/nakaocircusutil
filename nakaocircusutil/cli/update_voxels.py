from __future__ import annotations

import json
import re
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory

import fire
from nakaocircusutil import circus_api
from nakaocircusutil.imread import imread
from nakaocircusutil.voxel_label import CircusVoxelLabel


def main():
    fire.Fire(update_voxels)  # setup.cfgで晒す


def update_voxels(
    label_mhd: str,
    case_id: str = None,
    series_no: int = None,
    label_no: int = None,
    description: str = None,
    force: bool = False,
):
    """CIRCUSのボクセルラベル (.mhd) をCIRCUSに送信する。

    症例画面から Export as MHD (Isolated)、または circus-api-util case-dl でダウンロードした
    ボクセルラベル (vol***-label***.mhd) を手元で編集し、
    このコマンドで CIRCUS サーバに反映させることができます。
    いまのところ、既に存在するラベルを上書きすることしかできません (新規追加はできません)。
    実行には circus-api-util のインストールが必要です。

    例:
    $ update-voxels /path/to/vol000-label000.mhd  # 基本的にはこれでOK
    $ update-voxels /path/to/vol000-label000.mhd --force  # 確認プロンプトを出さずに実行したい場合
    $ update-voxels /path/to/vol000-label000.mhd --description "some comments"  # revision のコメントを指定したい場合

    :param label_mhd: ラベルのパス (.mhd)
    :param case_id: Case ID (省略時はファイルパスから推論)
    :param series_no: 何番目のシリーズか (0オリジン、省略時はファイルパスから推論)
    :param label_no: 何番目のラベルか (0オリジン、省略時はファイルパスから推論)
    :param description: revisionのdescription (省略時は自動生成)
    :param force: 確認のプロンプトを出さずに送信
    """
    label_path = Path(label_mhd)

    # mhdのパスからcase_id, series_no, label_noを自動で読み取り
    m = re.fullmatch(r"vol(\d+)\-label(\d+).mhd", label_path.name)
    if m:
        series_no = int(m[1]) if series_no is None else series_no
        label_no = int(m[2]) if label_no is None else label_no
        case_id = label_path.parent.name if case_id is None else case_id
    assert case_id is not None, "failed to infer CASE_ID"
    assert series_no is not None, "failed to infer SERIES_NO"
    assert label_no is not None, "failed to infer LABEL_NO"

    # 諸々読み込み
    label_local = CircusVoxelLabel.from_array(imread(label_path))
    case = circus_api.get_case(case_id)
    label_meta = case["revisions"][-1]["series"][series_no]["labels"][label_no]

    # 確認のため、更新されるラベルのメタデータを出力
    print(f"The following label ('{label_meta['name']}') will be updated:")
    pprint(label_meta)
    print("")
    if not force:  # --force がついていない場合、確認用プロンプトを表示
        if label_meta["data"]["voxels"] == label_local.sha1():
            print("No change has been made to the latest revision. Proceed anyway (y/[n])?")
        else:
            print("Proceed (y/[n])?")
        if input() != "y":
            return

    # ラベルの実データを送信
    circus_api.blob_post(label_local.packed)

    # ラベルのメタデータを更新
    label_meta["data"]["voxels"] = label_local.sha1()
    label_meta["data"]["origin"] = label_local.origin_zyx[::-1]
    label_meta["data"]["size"] = label_local.shape_zyx[::-1]
    with TemporaryDirectory() as temp_dir:
        label_meta_json = Path(temp_dir) / "label_meta.json"
        json.dump(label_meta, open(label_meta_json, "w"))
        circus_api.case_addrev(
            case_id,
            [
                "--force",
                "-d",
                description or f"update {label_meta['name']} (series[{series_no}].label[{label_no}])",
                "-e",
                f"python -m nakaocircusutil.cli.make_voxel_revision {label_meta_json} {series_no} {label_no}",
            ],
        )


if __name__ == "__main__":
    main()
