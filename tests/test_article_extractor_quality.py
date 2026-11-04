from src.article_extractor import _is_boilerplate, _usable_article_text


def test_rejects_sitemap_and_navigation_content():
    junk = (
        'Advanced Search Subscribe Newsletter Sitemap Magazine. '
        'Read the latest edition of AIR and MEIR as an Interactive e-book. '
        'Read the latest edition of AIR and MEIR as an Interactive e-book. '
        'Home About Contact Us Privacy Policy.'
    )
    assert _is_boilerplate(junk)
    assert not _usable_article_text(junk)


def test_accepts_multi_sentence_article_prose():
    article = (
        'Australian insurers are reviewing their cyber risk models as attacks become more frequent. '
        'Industry specialists say businesses need stronger incident response plans and clearer recovery procedures. '
        'The report describes how insurers are assessing the changing threat landscape and the costs of disruption. '
        'It also discusses the role of security investment and communication between companies and insurers.'
    )
    assert _usable_article_text(article)
