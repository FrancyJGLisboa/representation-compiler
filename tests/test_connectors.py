from representation_compiler.connectors import local_file


def test_reads_plain_text_source(tmp_path):
    path = tmp_path / "roadmap.md"
    path.write_text("Project Alpha is blocked.")
    source = local_file(path)
    assert source.origin == "file"
    assert source.text == "Project Alpha is blocked."


def test_reads_email_source_with_headers(tmp_path):
    path = tmp_path / "launch.eml"
    path.write_text("From: maya@example.com\nTo: team@example.com\nSubject: Launch\n\nAPI v2 is delayed.")
    source = local_file(path)
    assert source.origin == "email"
    assert "Subject: Launch" in source.text
    assert "API v2 is delayed." in source.text
