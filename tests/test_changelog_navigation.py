from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_changelog_heeft_geen_eigen_legacy_linkernavigatie():
    html = (ROOT / "changelog.html").read_text(encoding="utf-8")

    assert 'id="topnav"' in html
    assert 'class="doc-sidebar"' not in html
    assert 'class="doc-shell"' not in html
    assert "width:220px" not in html


def test_changelog_blijft_via_de_wiki_bereikbaar():
    wiki = (ROOT / "wiki.html").read_text(encoding="utf-8")

    assert 'href="#changelog" data-page="changelog.html"' in wiki
