from src.validators import validate_citations, safe_filename


def test_citation_ids_allow_only_registry():
    assert validate_citations(['src1', 'invented', 'src2'], {'src1': 'url', 'src2': 'url2'}) == ['src1', 'src2']


def test_safe_filename():
    assert safe_filename('../../unsafe name') == 'unsafe_name'
