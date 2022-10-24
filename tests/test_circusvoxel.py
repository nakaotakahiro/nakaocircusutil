from pathlib import Path

import numpy as np
from nakaocircusutil.imread import imread
from nakaocircusutil.voxel_label import CircusVoxelLabel, pack, unpack
from numpy.testing import assert_array_equal

resource_dir = resource_dir = Path(__file__).parent / "resources"


def test_pack():
    volume = imread(resource_dir / "label.nii.gz")
    packed = open(resource_dir / "label.bin", "rb").read()
    assert pack(volume) == packed
    assert_array_equal(volume, unpack(packed, volume.shape))


def test_circusvoxel():
    # ランダムなarrayに対して、from_array().to_array() が元に戻るかを確認
    for i in range(1000):
        label_size = np.random.randint(low=1, high=10, size=3)
        p = np.random.random()
        random_label = np.random.random(label_size) < p

        origin = np.random.randint(low=0, high=10, size=3)
        volume_size = label_size + origin + np.random.randint(low=0, high=10, size=3)

        volume = np.zeros(volume_size, dtype=bool)
        (d, h, w), (z, y, x) = label_size, origin
        volume[z : z + d, y : y + h, x : x + w] = random_label

        assert_array_equal(volume, CircusVoxelLabel.from_array(volume).to_array(tuple(volume_size)))
