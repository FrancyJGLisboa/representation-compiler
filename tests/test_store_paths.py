from representation_compiler.store import SQLiteStore


def test_store_creates_missing_parent_directory(tmp_path):
    path = tmp_path / "new" / "nested" / "history.db"
    store = SQLiteStore(path)
    store.close()
    assert path.exists()
