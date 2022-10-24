from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import scipy.ndimage


def pack(array: np.ndarray) -> bytes:
    """3次元配列をCIRCUSの内部表現に変換

    :return: _description_
    """
    assert array.ndim == 3
    return np.packbits(array, bitorder="big").tobytes()


def unpack(packed: bytes, shape: tuple[int, int, int]) -> np.ndarray:
    """CIRCUSの内部表現から3次元配列を復元

    :param packed: _description_
    :param shape: _description_
    :return: _description_
    """
    packed_array = np.frombuffer(packed, dtype=np.uint8)
    count = shape[0] * shape[1] * shape[2]
    return np.unpackbits(packed_array, bitorder="big", count=count).reshape(shape)


@dataclass
class CircusVoxelLabel(object):
    packed: bytes
    shape_zyx: tuple[int, int, int]
    origin_zyx: tuple[int, int, int]

    @classmethod
    def from_array(cls, array: np.ndarray) -> CircusVoxelLabel:
        array = array.astype(bool)

        # 端の0をトリミング
        crop_slices = scipy.ndimage.find_objects(array)[0] if array.any() else (slice(0, 0),) * 3
        array_cropped = array[crop_slices]

        return CircusVoxelLabel(
            packed=pack(array_cropped),
            shape_zyx=array_cropped.shape,
            origin_zyx=[s.start for s in crop_slices],  # type: ignore
        )

    def to_array(self, original_shape_zyx: tuple[int, int, int]) -> np.ndarray:
        array_cropped = unpack(self.packed, self.shape_zyx)

        # トリミングされている端の0を復元
        array = np.zeros(original_shape_zyx, dtype=bool)
        (d, h, w), (z, y, x) = self.shape_zyx, self.origin_zyx
        array[z : z + d, y : y + h, x : x + w] = array_cropped

        return array

    def sha1(self) -> str:
        return hashlib.sha1(self.packed).hexdigest()
