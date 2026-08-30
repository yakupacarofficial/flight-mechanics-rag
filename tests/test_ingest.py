"""ingest.split_into_chunks: markdown'i ## basliklarindan chunk'lara boler."""
from ingest import split_into_chunks

DOC = """# Airfoils

Bu bir giris paragrafi, hicbir chunk'a girmemeli.

## Airfoil Geometry

Chord line, camber, thickness.

### Alt baslik

Alt baslik ayni chunk'ta kalmali.

## Angle of Attack

AoA tanimi ve stall.
"""


def test_chunk_count_and_sections():
    chunks = split_into_chunks(DOC, "02-airfoils.md")
    assert [c["section"] for c in chunks] == ["Airfoil Geometry", "Angle of Attack"]


def test_source_is_filename():
    chunks = split_into_chunks(DOC, "02-airfoils.md")
    assert all(c["source"] == "02-airfoils.md" for c in chunks)


def test_intro_and_title_excluded():
    text = " ".join(c["text"] for c in split_into_chunks(DOC, "x.md"))
    assert "giris paragrafi" not in text
    assert "# Airfoils" not in text


def test_chunk_text_keeps_heading_and_subsection():
    first = split_into_chunks(DOC, "x.md")[0]
    assert first["text"].startswith("## Airfoil Geometry")
    # ### alt baslik parent chunk icinde kalir, yeni chunk acmaz
    assert "Alt baslik ayni chunk'ta kalmali." in first["text"]


def test_no_headings_returns_empty():
    assert split_into_chunks("Sadece duz metin, baslik yok.", "x.md") == []
