"""circus-api-util case-addrev -e に渡すためだけのスクリプト"""

import json

import fire


def make_revision(label_meta_json: str, series_no: int, label_no: int):
    revision = json.loads(input())
    revision["series"][series_no]["labels"][label_no] = json.load(open(label_meta_json, "r"))
    print(json.dumps(revision))


if __name__ == "__main__":
    fire.Fire(make_revision)
