"""`tesserae.widgets`'s Media & Graphics category: `image`'s missing-file
error. `image`, `video`, `node_graph` and `graph_node` are Tesserae's
since M42 (`tests/test_media.py`), and `icon` since M41
(`tests/test_composed_widgets.py`).
"""

from pathlib import Path

import pytest
from tre import Window

from tesserae.widgets import image

PIXEL_PNG = str(Path(__file__).parent / "fixtures" / "pixel.png")


def test_image_raises_oserror_on_missing_file_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(OSError):
        image(window, "does/not/exist.png", 40, 40)
