from __future__ import annotations

import json
import subprocess
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Optional, Sequence, Union


def call(
    args: Sequence[str],
    stdin: Union[str, bytes] = "",
) -> Any:
    logger = getLogger(__name__)
    logger.info(["circus-api-util", *args])

    stdin_bytes = stdin.encode("utf-8") if type(stdin) is str else stdin
    try:
        cp = subprocess.run(["circus-api-util", *args], capture_output=True, check=True, input=stdin_bytes)
    except subprocess.CalledProcessError as e:
        logger.error(e.stderr.decode("utf-8"))
        raise e

    stderr = cp.stderr.decode("utf-8")
    if stderr != "":
        logger.error(stderr)
        raise AssertionError(stderr)

    stdout = cp.stdout.decode("utf-8")
    try:
        return json.loads(stdout)
    except json.decoder.JSONDecodeError:
        return stdout


def get(
    resource: str,
    filter: Optional[dict] = None,
    sort: Optional[dict] = None,
    limit: Optional[int] = None,
    page: Optional[int] = None,
) -> Any:
    args = ["get", resource]
    if filter:
        args.extend(["-q", f"filter={json.dumps(filter)}"])
    if sort:
        args.extend(["-q", f"sort={json.dumps(sort)}"])
    if limit:
        args.extend(["-q", f"limit={limit}"])
    if page:
        args.extend(["-q", f"page={page}"])
    return call(args)


def get_one(
    resource: str,
    filter: Optional[dict] = None,
    sort: Optional[dict] = None,
) -> Any:
    logger = getLogger(__name__)

    ret = get(resource, filter=filter, sort=sort, limit=1)
    if ret["totalItems"] != 1:
        logger.error(ret)
        logger.error("number of item(s) != 1")
        raise AssertionError("number of item(s) != 1")
    return ret["items"][0]


def get_case(case_id: str) -> dict[str, Any]:
    return get(f"cases/{case_id}")


def blob_post(blob: bytes):
    call(["blob-post"], stdin=blob)


def case_addrev(case_id: str, args: Sequence[str]):
    call(["case-addrev", *args, case_id])


def case_addrev_dict(case_id: str, revision: dict, args: Sequence[str]):
    """引数revisionの内容でrevisionを作成"""
    with TemporaryDirectory() as temp_dir:
        revision_json = Path(temp_dir) / "revision.json"
        json.dump(revision, open(revision_json, "w"))
        cat = f"python -c \"print(open('{revision_json}').read())\""
        case_addrev(case_id, ["-e", cat, *args])
