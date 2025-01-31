import pytest

from arango.exceptions import (
    CursorCloseError,
    CursorCountError,
    CursorEmptyError,
    CursorNextError,
    CursorStateError,
)
from tests.helpers import clean_doc


@pytest.fixture(autouse=True)
def setup_collection(col, docs):
    col.import_bulk(docs)


def test_cursor_from_execute_query(db, col, docs):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=2,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=2,
    )
    cursor_id = cursor.id
    assert "Cursor" in repr(cursor)
    assert cursor.type == "cursor"
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 6
    assert clean_doc(cursor.batch()) == docs[:2]

    statistics = cursor.statistics()
    assert statistics["modified"] == 0
    assert statistics["filtered"] == 0
    assert statistics["ignored"] == 0
    assert statistics["execution_time"] > 0
    assert "http_requests" in statistics
    assert "scanned_full" in statistics
    assert "scanned_index" in statistics
    assert "nodes" in statistics

    assert cursor.warnings() == []

    profile = cursor.profile()
    assert profile["initializing"] > 0
    assert profile["parsing"] > 0

    plan = cursor.plan()
    expected_keys = {
        "nodes",
        "rules",
        "collections",
        "variables",
        "estimatedCost",
        "estimatedNrItems",
        "isModificationQuery",
    }
    for key in expected_keys:
        assert key in plan

    assert clean_doc(cursor.next()) == docs[0]
    assert cursor.id == cursor_id
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 6
    assert clean_doc(cursor.batch()) == [docs[1]]

    assert clean_doc(cursor.next()) == docs[1]
    assert cursor.id == cursor_id
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 6
    assert clean_doc(cursor.batch()) == []

    assert clean_doc(cursor.next()) == docs[2]
    assert cursor.id == cursor_id
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 6
    assert clean_doc(cursor.batch()) == [docs[3]]

    assert clean_doc(cursor.next()) == docs[3]
    assert clean_doc(cursor.next()) == docs[4]
    assert clean_doc(cursor.next()) == docs[5]
    assert cursor.id == cursor_id
    assert cursor.has_more() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 6
    assert clean_doc(cursor.batch()) == []
    with pytest.raises(StopIteration):
        cursor.next()
    assert cursor.close(ignore_missing=True) is False


def test_cursor_write_query(db, col, docs):
    cursor = db.aql.execute(
        """
        FOR d IN {col} FILTER d._key == @first OR d._key == @second
        UPDATE {{_key: d._key, _val: @val }} IN {col}
        RETURN NEW
        """.format(
            col=col.name
        ),
        bind_vars={"first": "1", "second": "2", "val": 42},
        count=True,
        batch_size=1,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=1,
        max_runtime=0.0,
    )
    cursor_id = cursor.id
    assert "Cursor" in repr(cursor)
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 2
    assert clean_doc(cursor.batch()) == [docs[0]]

    statistics = cursor.statistics()
    assert statistics["modified"] == 2
    assert statistics["filtered"] == 0
    assert statistics["ignored"] == 0
    assert statistics["execution_time"] > 0
    assert "http_requests" in statistics
    assert "scanned_full" in statistics
    assert "scanned_index" in statistics
    assert cursor.warnings() == []

    profile = cursor.profile()
    assert profile["initializing"] > 0
    assert profile["parsing"] > 0

    assert clean_doc(cursor.next()) == docs[0]
    assert cursor.id == cursor_id
    assert cursor.has_more() is True
    assert cursor.cached() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 2
    assert clean_doc(cursor.batch()) == []

    assert clean_doc(cursor.next()) == docs[1]
    assert cursor.id == cursor_id
    assert cursor.has_more() is False
    assert cursor.cached() is False
    assert cursor.statistics() == statistics
    assert cursor.profile() == profile
    assert cursor.warnings() == []
    assert cursor.count() == len(cursor) == 2
    assert clean_doc(cursor.batch()) == []

    with pytest.raises(CursorCloseError) as err:
        cursor.close(ignore_missing=False)
    assert err.value.error_code == 1600
    assert cursor.close(ignore_missing=True) is False


def test_cursor_invalid_id(db, col):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=2,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
    )
    # Set the cursor ID to "invalid" and assert errors
    setattr(cursor, "_id", "invalid")

    with pytest.raises(CursorNextError) as err:
        list(cursor)
    assert err.value.error_code == 1600

    with pytest.raises(CursorCloseError) as err:
        cursor.close(ignore_missing=False)
    assert err.value.error_code == 1600
    assert cursor.close(ignore_missing=True) is False

    # Set the cursor ID to None and assert errors
    setattr(cursor, "_id", None)

    with pytest.raises(CursorStateError) as err:
        cursor.next()
    assert err.value.message == "cursor ID not set"

    with pytest.raises(CursorStateError) as err:
        cursor.fetch()
    assert err.value.message == "cursor ID not set"

    assert cursor.close() is None


def test_cursor_premature_close(db, col, docs):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=2,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
    )
    assert clean_doc(cursor.batch()) == docs[:2]
    assert cursor.close() is True
    with pytest.raises(CursorCloseError) as err:
        cursor.close(ignore_missing=False)
    assert err.value.error_code == 1600
    assert cursor.close(ignore_missing=True) is False


def test_cursor_context_manager(db, col, docs):
    with db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=2,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
    ) as cursor:
        assert clean_doc(cursor.next()) == docs[0]

    with pytest.raises(CursorCloseError) as err:
        cursor.close(ignore_missing=False)
    assert err.value.error_code == 1600
    assert cursor.close(ignore_missing=True) is False


def test_cursor_manual_fetch_and_pop(db, col, docs):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=1,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
    )
    for size in range(2, 6):
        result = cursor.fetch()
        assert result["id"] == cursor.id
        assert result["count"] == len(docs)
        assert result["cached"] == cursor.cached()
        assert result["has_more"] == cursor.has_more()
        assert result["profile"] == cursor.profile()
        assert result["warnings"] == cursor.warnings()
        assert result["statistics"] == cursor.statistics()
        assert len(result["batch"]) > 0
        assert cursor.count() == len(docs)
        assert cursor.has_more()
        assert len(cursor.batch()) == size

    cursor.fetch()
    assert len(cursor.batch()) == 6
    assert not cursor.has_more()

    while not cursor.empty():
        cursor.pop()
    assert len(cursor.batch()) == 0

    with pytest.raises(CursorEmptyError) as err:
        cursor.pop()
    assert err.value.message == "current batch is empty"


def test_cursor_retry_disabled(db, col, docs):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=1,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
        allow_retry=False,
    )
    result = cursor.fetch()
    assert result["id"] == cursor.id

    while not cursor.empty():
        cursor.pop()

    # The next batch ID should have no effect
    cursor._next_batch_id = "2"
    result = cursor.fetch()
    assert result["next_batch_id"] == "4"
    doc = cursor.pop()
    assert clean_doc(doc) == docs[2]

    assert cursor.close(ignore_missing=True)


def test_cursor_retry(db, col, docs, db_version):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=True,
        batch_size=1,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
        allow_retry=True,
    )

    assert cursor.count() == len(docs)
    doc = cursor.pop()
    assert clean_doc(doc) == docs[0]
    assert cursor.has_more()

    result = cursor.fetch()
    assert result["id"] == cursor.id
    assert result["next_batch_id"] == "3"
    doc = cursor.pop()
    assert clean_doc(doc) == docs[1]
    assert cursor.empty()

    # Decrease the next batch ID as if the previous fetch failed
    cursor._next_batch_id = "2"
    result = cursor.fetch()
    assert result["id"] == cursor.id
    assert result["next_batch_id"] == "3"
    doc = cursor.pop()
    assert clean_doc(doc) == docs[1]
    assert cursor.empty()

    # Fetch the next batches normally
    for batch in range(2, 5):
        result = cursor.fetch()
        assert result["id"] == cursor.id
        assert result["next_batch_id"] == str(batch + 2)
        doc = cursor.pop()
        assert clean_doc(doc) == docs[batch]

    result = cursor.fetch()
    assert not cursor.has_more()
    assert "id" not in result
    assert "next_batch_id" not in result
    doc = cursor.pop()
    assert clean_doc(doc) == docs[-1]

    # We should be able to fetch the last batch again
    cursor.fetch()
    doc = cursor.pop()
    assert clean_doc(doc) == docs[-1]

    assert cursor.close()


def test_cursor_no_count(db, col):
    cursor = db.aql.execute(
        f"FOR d IN {col.name} SORT d._key RETURN d",
        count=False,
        batch_size=2,
        ttl=1000,
        optimizer_rules=["+all"],
        profile=True,
    )
    with pytest.raises(CursorCountError) as err:
        _ = len(cursor)
    assert err.value.message == "cursor count not enabled"

    with pytest.raises(CursorCountError) as err:
        _ = bool(cursor)
    assert err.value.message == "cursor count not enabled"

    while cursor.has_more():
        assert cursor.count() is None

        with pytest.raises(CursorCountError) as err:
            _ = len(cursor)
        assert err.value.message == "cursor count not enabled"

        with pytest.raises(CursorCountError) as err:
            _ = bool(cursor)
        assert err.value.message == "cursor count not enabled"
        assert cursor.fetch()
