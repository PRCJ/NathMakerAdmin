from core.excel_import import parse_csv_bytes, parse_spreadsheet, name_from_image_ref


def test_csv_details_without_image():
    raw = (
        "productName,price,description,material\n"
        "Pearl Nath,4500,Classic pearl drop,Silver\n"
    ).encode()
    rows = parse_csv_bytes(raw)
    assert len(rows) == 1
    assert rows[0]["productName"] == "Pearl Nath"
    assert rows[0]["price"] == 4500
    assert rows[0]["imageRefs"] == []
    assert rows[0]["isAvailable"] is False


def test_csv_image_only_uses_filename_as_name():
    raw = "image\nhttps://cdn.example.com/photos/bridal-nath.jpg\n".encode()
    rows = parse_csv_bytes(raw)
    assert len(rows) == 1
    assert rows[0]["productName"] == "bridal nath"
    assert rows[0]["imageRefs"] == ["https://cdn.example.com/photos/bridal-nath.jpg"]


def test_csv_image_filename_is_kept_for_matching():
    raw = "productName,image\nRing,gold-ring.png\n".encode()
    rows = parse_csv_bytes(raw)
    assert rows[0]["imageRefs"] == ["gold-ring.png"]


def test_name_from_image_ref():
    assert name_from_image_ref("folder/gold_hoop.jpg") == "gold hoop"


def test_unknown_extension_rejected():
    try:
        parse_spreadsheet("stock.pdf", b"%PDF")
    except ValueError as exc:
        assert "xlsx" in str(exc)
    else:
        raise AssertionError("expected ValueError")
