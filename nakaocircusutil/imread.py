from pathlib import Path
from typing import Union

import numpy as np
import SimpleITK as sitk


def imread(path: Union[str, Path]) -> np.ndarray:
    return sitk.GetArrayFromImage(sitk.ReadImage(str(path)))
