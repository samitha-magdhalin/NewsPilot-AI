from PIL import Image
import pytest
from src.graphic_generator import _font, make_graphic, STYLES

@pytest.mark.parametrize('style', STYLES)
@pytest.mark.parametrize('size', [(1080, 1350), (1080, 1080), (1200, 675), (1080, 1920)])
def test_graphic_styles_and_sizes(tmp_path, style, size):
    path = tmp_path / 'graphic.png'
    result = make_graphic(
        'A long editorial headline about a developing news story',
        'A short supporting description based on available source metadata.',
        'Example Publisher', '2026-10-27', 'https://example.org/news',
        'SINGLE_SOURCE', str(path), size, style,
    )
    assert result.exists()
    with Image.open(result) as image:
        assert image.format == 'PNG'
        assert image.size == size


def test_graphic_rejects_extreme_canvas(tmp_path):
    with pytest.raises(ValueError):
        make_graphic('Headline', 'Summary', output_path=str(tmp_path / 'bad.png'), size=(10, 10))


def test_graphic_font_uses_requested_size():
    font = _font(48, bold=True)
    assert font.getbbox('Headline')[3] - font.getbbox('Headline')[1] >= 24
