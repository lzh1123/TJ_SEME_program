from ppt_backend.services.rag.milvus_client import MilvusStore

store = MilvusStore.__new__(MilvusStore)

# Test _escape_filter_string
# Normal string: no change
assert store._escape_filter_string("hello.pdf") == "hello.pdf"

# String with double quotes: quotes should be escaped
result = store._escape_filter_string('name".pdf')
assert result == 'name\\".pdf', f"Got: {result!r}"
print(f"Double-quote escape OK: {result!r}")

# String with backslashes
result = store._escape_filter_string("a\b")
assert result == "a\\b", f"Got: {result!r}"
print(f"Backslash escape OK: {result!r}")

# String with both
result = store._escape_filter_string('a\b"c')
assert result == 'a\\b\\"c', f"Got: {result!r}"
print(f"Combined escape OK: {result!r}")

# Test _parse_delete_count
assert store._parse_delete_count({"delete_count": 5, "cost": 100}, 10) == 5
assert store._parse_delete_count({"delete_count": 0}, 10) == 0
assert store._parse_delete_count(None, 10) == 10
assert store._parse_delete_count({}, 10) == 10
assert store._parse_delete_count({"delete_count": "not int"}, 10) == 10
print("_parse_delete_count tests OK!")

print("All unit tests passed!")
