from representation_compiler.protocol import DISCOVERY_HARNESS, learning_invocation, material_reference


def test_learning_invocation_requires_discovery_not_just_a_diagram(tmp_path):
    transcript = tmp_path / "video.txt"
    transcript.write_text("A transcript")

    packet = learning_invocation("Understand crop stress", material_reference(str(transcript)))

    assert "Treat the existing representation as arbitrary" in packet
    assert "Run a tournament" in packet
    assert "falsifiable experiment" in packet
    assert f"Local file: {transcript}" in packet
    assert "quotient representations" in DISCOVERY_HARNESS
