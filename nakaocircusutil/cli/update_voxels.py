from __future__ import annotations

import re
from pathlib import Path
from pprint import pprint
from typing import Optional

import fire
from nakaocircusutil import circus_api
from nakaocircusutil.imread import imread
from nakaocircusutil.voxel_label import CircusVoxelLabel


def main():
    fire.Fire(update_voxels)  # setup.cfgで晒す


def update_voxels(
    label_mhd: str,
    mode: str = "infer",
    case_id: str = None,
    series_no: int = None,
    label_no: int = None,
    description: str = None,
    force: bool = False,
):
    """CIRCUSのボクセルラベル (.mhd) をCIRCUSに送信する。

    症例画面から Export as MHD、または circus-api-util case-dl でダウンロードした
    ボクセルラベル (vol***-label***.mhd) を手元で編集し、
    このコマンドで CIRCUS サーバに反映させることができます。
    いまのところ、既に存在するラベルを上書きすることしかできません (新規追加はできません)。
    実行には circus-api-util のインストールが必要です。

    例:
    $ update-voxels /path/to/vol000-label000.mhd  # isolatedなラベルの場合、そのラベルのみが更新されます
    $ update-voxels /path/to/vol000-label.mhd  # combinedなラベルの場合、すべてのラベルが更新されます
    $ update-voxels /path/to/vol000-label000.mhd --force  # 確認プロンプトを出さずに実行したい場合
    $ update-voxels /path/to/vol000-label000.mhd --description "some comments"  # revision のコメントを指定したい場合

    :param label_mhd: ラベルのパス (.mhd)
    :param mode: {"infer", "isolated", "combined"}
    :param case_id: Case ID (inferモード時はパスから推論)
    :param series_no: 何番目のシリーズか (0オリジン、inferモード時はパスから推論)
    :param label_no: 何番目のラベルか (0オリジン、inferモード時はパスから推論)
    :param description: revisionのdescription (省略時は自動生成)
    :param force: 確認のプロンプトを出さずに送信
    """
    modes = ["infer", "isolated", "combined"]
    if mode not in modes:
        raise ValueError(f"--mode must be one of {modes}")

    label_path = Path(label_mhd)
    if mode == "infer":
        # mhdのパスからcase_id, series_no, label_no, modeを自動で読み取り
        m = re.fullmatch(r"vol(\d+)\-label(|\d+).mhd", label_path.name)
        if not m:
            raise ValueError("failed to infer case id, series no (and label no)")

        series_no = int(m[1])
        label_no = int(m[2]) if m[2] else None
        case_id = label_path.parent.name
        mode = "isolated" if m[2] else "combined"

    assert case_id is not None
    assert series_no is not None
    if mode == "isolated":
        assert label_no is not None
        _update_voxels_isolated(label_path, case_id, series_no, label_no, description, force)
    elif mode == "combined":
        _update_voxels_combined(label_path, case_id, series_no, description, force)


def _update_voxels_isolated(
    label_path: Path,
    case_id: str,
    series_no: int,
    label_no: int,
    description: Optional[str],
    force: bool,
):
    # 諸々読み込み
    label_local = CircusVoxelLabel.from_array(imread(label_path))
    case = circus_api.get_case(case_id)
    revision = case["revisions"][-1]
    label_meta = revision["series"][series_no]["labels"][label_no]

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
    label_meta["data"].update(label_local.get_meta_dict())
    revision["description"] = description or f"update {label_meta['name']} (series[{series_no}].label[{label_no}])"
    circus_api.case_addrev_dict(case_id, revision, ["--force", "-D"])


def _update_voxels_combined(
    label_path: Path,
    case_id: str,
    series_no: int,
    description: Optional[str],
    force: bool,
):
    # 諸々読み込み
    labels_local = CircusVoxelLabel.from_combined(imread(label_path))
    case = circus_api.get_case(case_id)
    revision = case["revisions"][-1]
    labels_meta = revision["series"][series_no]["labels"]

    # 確認のため、更新されるラベルのメタデータを出力
    indices_changed = []
    labels_meta_changed = []
    for i, (label_meta, label_local) in enumerate(zip(labels_meta, labels_local)):
        if label_local.sha1() != label_meta["data"]["voxels"]:
            indices_changed.append(i)
            labels_meta_changed.append(label_meta)
    names_changed = ", ".join([label_meta_changed["name"] for label_meta_changed in labels_meta_changed])
    print(f"The following label(s) ('{names_changed}') will be updated:")
    pprint(labels_meta_changed)
    print("")
    if not force:  # --force がついていない場合、確認用プロンプトを表示
        if labels_meta_changed:
            print("Proceed (y/[n])?")
        else:
            print("No change has been made to the latest revision. Proceed anyway (y/[n])?")
        if input() != "y":
            return

    # ラベルの実データを送信
    for i in indices_changed:
        circus_api.blob_post(labels_local[i].packed)

    # ラベルのメタデータを更新
    for i in indices_changed:
        labels_meta[i]["data"].update(labels_local[i].get_meta_dict())
    indices_changed_str = ",".join(map(str, indices_changed))
    description_default = f"update {names_changed} (series[{series_no}].label[{indices_changed_str}])"
    revision["description"] = description or description_default
    circus_api.case_addrev_dict(case_id, revision, ["--force", "-D"])


if __name__ == "__main__":
    main()
