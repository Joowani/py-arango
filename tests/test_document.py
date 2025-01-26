import pytest
from packaging import version

from arango.exceptions import (
    DocumentCountError,
    DocumentDeleteError,
    DocumentGetError,
    DocumentIDsError,
    DocumentInError,
    DocumentInsertError,
    DocumentKeysError,
    DocumentParseError,
    DocumentReplaceError,
    DocumentRevisionError,
    DocumentUpdateError,
    IndexGetError,
    IndexMissingError,
)
from tests.helpers import (
    assert_raises,
    clean_doc,
    empty_collection,
    extract,
    generate_col_name,
    generate_doc_key,
)


def test_document_insert(col, docs):
    # Test insert document with no key
    result = col.insert({})
    assert result["_key"] in col
    assert len(col) == 1
    empty_collection(col)

    # Test insert document with ID
    doc_id = col.name + "/" + "foo"
    col.insert({"_id": doc_id})
    assert "foo" in col
    assert doc_id in col
    assert len(col) == 1
    empty_collection(col)

    with assert_raises(DocumentParseError) as err:
        col.insert({"_id": generate_col_name() + "/" + "foo"})
    assert "bad collection name" in err.value.message

    # Test insert with default options
    for doc in docs:
        result = col.insert(doc)
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert col[doc["_key"]]["val"] == doc["val"]
    assert len(col) == len(docs)
    empty_collection(col)

    # Test insert with sync set to True
    doc = docs[0]
    result = col.insert(doc, sync=True)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert with sync set to False
    doc = docs[1]
    result = col.insert(doc, sync=False)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert with return_new set to True
    doc = docs[2]
    result = col.insert(doc, return_new=True)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert result["new"]["_id"] == result["_id"]
    assert result["new"]["_key"] == result["_key"]
    assert result["new"]["_rev"] == result["_rev"]
    assert result["new"]["val"] == doc["val"]
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert with return_new set to False
    doc = docs[3]
    result = col.insert(doc, return_new=False)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert "new" not in result
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert with silent set to True
    doc = docs[4]
    assert col.insert(doc, silent=True) is True
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert duplicate document
    with assert_raises(DocumentInsertError) as err:
        col.insert(doc)
    assert err.value.error_code == 1210

    # Test insert replace
    doc = {"_key": doc["_key"], "foo": {"bar": 1}, "baz": None}
    result = col.insert(document=doc, overwrite=True, return_old=True, return_new=True)
    assert result["new"]["foo"] == {"bar": 1}
    assert result["new"]["baz"] is None
    assert "val" in result["old"]
    assert "val" not in result["new"]

    # Test insert ignore
    doc = {"_key": doc["_key"], "foo": {"qux": 2}}
    result = col.insert(
        document=doc,
        return_old=True,
        return_new=True,
        overwrite=True,
        overwrite_mode="ignore",
        keep_none=False,
        merge=True,
    )
    assert "old" not in result
    assert "new" not in result
    assert col[doc["_key"]]["foo"] == {"bar": 1}

    # Test insert conflict
    with assert_raises(DocumentInsertError) as err:
        col.insert(
            document=doc,
            return_old=True,
            return_new=True,
            overwrite=True,
            overwrite_mode="conflict",
            keep_none=False,
            merge=True,
        )
    assert err.value.error_code == 1210

    # Test insert with cache refilling
    empty_collection(col)
    doc = docs[0]
    assert col.insert(doc, refill_index_caches=True)
    assert col[doc["_key"]]["_key"] == doc["_key"]
    assert col[doc["_key"]]["val"] == doc["val"]


def test_document_insert_many(col, bad_col, docs):
    # Test insert_many with default options
    results = col.insert_many(docs)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert col[doc["_key"]]["val"] == doc["val"]
    assert len(col) == len(docs)
    empty_collection(col)

    # Test insert_many with document IDs
    docs_with_id = [{"_id": col.name + "/" + doc["_key"]} for doc in docs]
    results = col.insert_many(docs_with_id)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
    assert len(col) == len(docs)
    empty_collection(col)

    # Test insert_many with sync set to True
    results = col.insert_many(docs, sync=True)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]
    empty_collection(col)

    # Test insert_many with sync set to False
    results = col.insert_many(docs, sync=False)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]
    empty_collection(col)

    # Test insert_many with return_new set to True
    results = col.insert_many(docs, return_new=True)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert result["new"]["_id"] == result["_id"]
        assert result["new"]["_key"] == result["_key"]
        assert result["new"]["_rev"] == result["_rev"]
        assert result["new"]["val"] == doc["val"]
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]
    empty_collection(col)

    # Test insert_many with return_new set to False
    results = col.insert_many(docs, return_new=False)
    for result, doc in zip(results, docs):
        assert result["_id"] == f"{col.name}/{doc['_key']}"
        assert result["_key"] == doc["_key"]
        assert isinstance(result["_rev"], str)
        assert "new" not in result
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]
    empty_collection(col)

    # Test insert_many with silent set to True
    assert col.insert_many(docs, silent=True) is True
    for doc in docs:
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]

    # Test insert_many duplicate documents
    results = col.insert_many(docs, return_new=False)
    for error, doc in zip(results, docs):
        assert isinstance(error, DocumentInsertError)
        assert error.error_code in {1210}
        assert "unique constraint violated" in error.error_message
        assert error.http_code == 202
        assert "[HTTP 202][ERR 1210]" in error.message

    # Test insert_many with overwrite and return_old set to True
    results = col.insert_many(docs, overwrite=True, return_old=True)
    for result, doc in zip(results, docs):
        assert not isinstance(result, DocumentInsertError)
        assert isinstance(result["old"], dict)
        assert isinstance(result["_old_rev"], str)

    # Test get with bad database
    with assert_raises(DocumentInsertError) as err:
        bad_col.insert_many(docs)
    assert err.value.error_code in {11, 1228}

    # test overwrite_mode: replace
    extra_docs = [
        {"_key": docs[0]["_key"], "foo": {"qux": 2}},
        {"_key": "20", "foo": "t"},
    ]
    results = col.insert_many(
        documents=extra_docs,
        return_old=True,
        return_new=True,
        overwrite_mode="replace",
        keep_none=False,
        merge=True,
    )

    assert "old" in results[0]
    assert "new" in results[0]
    assert "old" not in results[1]
    assert "new" in results[1]

    # test overwrite_mode: update
    extra_docs = [
        {"_key": docs[0]["_key"], "foo": {"t": 1}},
        {"_key": "20", "foo": None},
    ]
    results = col.insert_many(
        documents=extra_docs,
        return_old=True,
        return_new=True,
        overwrite_mode="update",
        keep_none=False,
        merge=True,
    )
    assert "old" in results[0]
    assert "new" in results[0]
    assert results[0]["new"]["foo"] == {"qux": 2, "t": 1}
    assert "old" in results[1]
    assert "new" in results[1]
    assert "foo" not in results[1]["new"]

    extra_docs = [
        {"_key": docs[0]["_key"], "foo": {"t": 1}},
        {"_key": "21", "foo": None},
    ]

    # Test insert conflict
    results = col.insert_many(
        documents=extra_docs,
        return_old=True,
        return_new=True,
        overwrite_mode="conflict",
        keep_none=True,
        merge=True,
    )
    assert isinstance(results[0], DocumentInsertError)
    assert results[0].error_code == 1210
    assert "new" in results[1]

    # Test insert with cache refilling
    empty_collection(col)
    assert col.insert_many(docs, refill_index_caches=True)
    for doc in docs:
        assert col[doc["_key"]]["_key"] == doc["_key"]
        assert col[doc["_key"]]["val"] == doc["val"]


def test_document_update(col, docs):
    doc = docs[0]
    col.insert(doc)

    # Test update with default options
    doc["val"] = {"foo": 1}
    doc = col.update(doc)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert col[doc["_key"]]["val"] == {"foo": 1}
    old_rev = doc["_rev"]

    # Test update with merge set to True
    doc["val"] = {"bar": 2}
    doc = col.update(doc, merge=True)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] == {"foo": 1, "bar": 2}
    old_rev = doc["_rev"]

    # Test update with merge set to False
    doc["val"] = {"baz": 3}
    doc = col.update(doc, merge=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] == {"baz": 3}
    old_rev = doc["_rev"]

    # Test update with keep_none set to True
    doc["val"] = None
    doc = col.update(doc, keep_none=True)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] is None
    old_rev = doc["_rev"]

    # Test update with keep_none set to False
    doc["val"] = None
    doc = col.update(doc, keep_none=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert "val" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test update with return_new and return_old set to True
    doc["val"] = 3
    doc = col.update(doc, return_new=True, return_old=True)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert doc["new"]["_key"] == doc["_key"]
    assert doc["new"]["val"] == 3
    assert doc["old"]["_key"] == doc["_key"]
    assert "val" not in doc["old"]
    assert col[doc["_key"]]["val"] == 3
    old_rev = doc["_rev"]

    # Test update with return_new and return_old set to False
    doc["val"] = 4
    doc = col.update(doc, return_new=False, return_old=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert "new" not in doc
    assert "old" not in doc
    assert col[doc["_key"]]["val"] == 4
    old_rev = doc["_rev"]

    # Test update with check_rev set to True
    doc["val"] = 5
    doc["_rev"] = old_rev + "0"
    with assert_raises(DocumentRevisionError) as err:
        col.update(doc, check_rev=True)
    assert err.value.error_code == 1200
    assert col[doc["_key"]]["val"] == 4

    # Test update with check_rev set to False
    doc = col.update(doc, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] == 5
    old_rev = doc["_rev"]

    # Test update with sync set to True
    doc["val"] = 6
    doc = col.update(doc, sync=True, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] == 6
    old_rev = doc["_rev"]

    # Test update with sync set to False
    doc["val"] = 7
    doc = col.update(doc, sync=False, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["val"] == 7
    old_rev = doc["_rev"]

    # Test update missing document
    missing_doc = docs[1]
    with assert_raises(DocumentUpdateError) as err:
        col.update(missing_doc)
    assert err.value.error_code == 1202
    assert missing_doc["_key"] not in col
    assert col[doc["_key"]]["val"] == 7
    assert col[doc["_key"]]["_rev"] == old_rev

    # Test update with silent set to True
    doc["val"] = 8
    assert col.update(doc, silent=True) is True
    assert col[doc["_key"]]["val"] == 8

    # Test update with cache refilling
    doc["val"] = 9
    assert col.update(doc, refill_index_caches=True, check_rev=False)
    assert col[doc["_key"]]["val"] == 9


def test_document_update_many(col, bad_col, docs):
    col.insert_many(docs)

    old_revs = {}
    doc_keys = [d["_key"] for d in docs]

    # Test update_many with default options
    for doc in docs:
        doc["val"] = {"foo": 0}
    results = col.update_many(docs)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert col[doc_key]["val"] == {"foo": 0}
        old_revs[doc_key] = result["_rev"]

    # Test update_many with IDs
    docs_with_ids = [
        {"_id": col.name + "/" + d["_key"], "val": {"foo": 1}} for d in docs
    ]
    results = col.update_many(docs_with_ids)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert col[doc_key]["val"] == {"foo": 1}
        old_revs[doc_key] = result["_rev"]

    # Test update_many with merge set to True
    for doc in docs:
        doc["val"] = {"bar": 2}
    results = col.update_many(docs, merge=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] == {"foo": 1, "bar": 2}
        old_revs[doc_key] = result["_rev"]

    # Test update_many with merge set to False
    for doc in docs:
        doc["val"] = {"baz": 3}
    results = col.update_many(docs, merge=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] == {"baz": 3}
        old_revs[doc_key] = result["_rev"]

    # Test update_many with keep_none set to True
    for doc in docs:
        doc["val"] = None
    results = col.update_many(docs, keep_none=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] is None
        old_revs[doc_key] = result["_rev"]

    # Test update_many with keep_none set to False
    for doc in docs:
        doc["val"] = None
    results = col.update_many(docs, keep_none=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert "val" not in col[doc_key]
        old_revs[doc_key] = result["_rev"]

    # Test update_many with return_new and return_old set to True
    for doc in docs:
        doc["val"] = 3
    results = col.update_many(docs, return_new=True, return_old=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert result["new"]["_key"] == doc_key
        assert result["new"]["val"] == 3
        assert result["old"]["_key"] == doc_key
        assert "val" not in result["old"]
        assert col[doc_key]["val"] == 3
        old_revs[doc_key] = result["_rev"]

    # Test update_many with return_new and return_old set to False
    for doc in docs:
        doc["val"] = 4
    results = col.update_many(docs, return_new=False, return_old=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert "new" not in result
        assert "old" not in result
        assert col[doc_key]["val"] == 4
        old_revs[doc_key] = result["_rev"]

    # Test update_many with check_rev set to True
    for doc in docs:
        doc["val"] = 5
        doc["_rev"] = old_revs[doc["_key"]] + "0"
    results = col.update_many(docs, check_rev=True)
    for error, doc_key in zip(results, doc_keys):
        assert isinstance(error, DocumentRevisionError)
        assert error.error_code in {1200}
        assert "conflict" in error.error_message
        assert error.http_code == 202
        assert "[HTTP 202][ERR 1200]" in error.message

    for doc in col:
        assert doc["val"] == 4

    # Test update_many with check_rev set to False
    results = col.update_many(docs, check_rev=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] == 5
        old_revs[doc_key] = result["_rev"]

    # Test update_many with sync set to True
    for doc in docs:
        doc["val"] = 6
    results = col.update_many(docs, sync=True, check_rev=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] == 6
        old_revs[doc_key] = result["_rev"]

    # Test update_many with sync set to False
    for doc in docs:
        doc["val"] = 7
    results = col.update_many(docs, sync=False, check_rev=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["val"] == 7
        old_revs[doc_key] = result["_rev"]

    # Test update_many with bad database
    with assert_raises(DocumentUpdateError) as err:
        bad_col.update_many(docs)
    assert err.value.error_code in {11, 1228}

    # Test update_many with silent set to True
    for doc in docs:
        doc["val"] = 8
    assert col.update_many(docs, silent=True, check_rev=False) is True
    for doc in docs:
        assert col[doc["_key"]]["val"] == 8

    # Test update_many with cache refilling
    for doc in docs:
        doc["val"] = 9
    assert col.update_many(docs, refill_index_caches=True, check_rev=False)
    for doc in docs:
        assert col[doc["_key"]]["val"] == 9

    # Test update_many with bad documents
    with assert_raises(DocumentParseError) as err:
        bad_col.update_many([{}])
    assert str(err.value) == 'field "_key" or "_id" required'

    # Test update_many with raise on document error (revision)
    with assert_raises(DocumentRevisionError) as err:
        # Raises: [HTTP 202][ERR 1200] conflict, _rev values do not match
        col.update_many(docs, raise_on_document_error=True)

    # Test update_many with raise on document error (update)
    with assert_raises(DocumentUpdateError) as err:
        # Raises: [HTTP 202][ERR 1202] document not found
        bad_docs = [{"_key": "unknown_doc", "foo": "bar"}]
        col.update_many(bad_docs, raise_on_document_error=True)


def test_document_update_match(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test update single matching document
    assert col.update_match({"val": 2}, {"val": 1}) == 1
    assert col["2"]["val"] == 1

    # Test update multiple matching documents
    assert col.update_match({"val": 1}, {"foo": 1}) == 2
    for doc_key in ["1", "2"]:
        assert col[doc_key]["val"] == 1
        assert col[doc_key]["foo"] == 1

    # Test update multiple matching documents with limit set to 1
    assert col.update_match({"val": 1}, {"foo": 2}, limit=1) == 1
    assert [doc.get("foo") for doc in col].count(2) == 1

    # Test update matching documents with sync and keep_none set to True
    assert col.update_match({"val": 3}, {"val": None}, sync=True, keep_none=True) == 1
    assert col["3"]["val"] is None

    # Test update matching documents with sync and keep_none set to False
    assert col.update_match({"val": 1}, {"val": None}, sync=False, keep_none=False) == 2
    assert "val" not in col["1"]
    assert "val" not in col["2"]

    # Test update matching documents with bad database
    with assert_raises(DocumentUpdateError) as err:
        bad_col.update_match({"val": 1}, {"foo": 1})
    assert err.value.error_code in {11, 1228}


def test_document_replace(col, docs):
    doc = docs[0]
    col.insert(doc)

    # Test replace with default options
    doc["foo"] = 2
    doc.pop("val")
    doc = col.replace(doc)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert col[doc["_key"]]["foo"] == 2
    assert "val" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test update with return_new and return_old set to True
    doc["bar"] = 3
    doc = col.replace(doc, return_new=True, return_old=True)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert doc["new"]["_key"] == doc["_key"]
    assert doc["new"]["bar"] == 3
    assert "foo" not in doc["new"]
    assert doc["old"]["_key"] == doc["_key"]
    assert doc["old"]["foo"] == 2
    assert "bar" not in doc["old"]
    assert col[doc["_key"]]["bar"] == 3
    assert "foo" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test update with return_new and return_old set to False
    doc["baz"] = 4
    doc = col.replace(doc, return_new=False, return_old=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert "new" not in doc
    assert "old" not in doc
    assert col[doc["_key"]]["baz"] == 4
    assert "bar" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test replace with check_rev set to True
    doc["foo"] = 5
    doc["_rev"] = old_rev + "0"
    with assert_raises(DocumentRevisionError):
        col.replace(doc, check_rev=True)
    assert "foo" not in col[doc["_key"]]
    assert col[doc["_key"]]["baz"] == 4

    # Test replace with check_rev set to False
    doc = col.replace(doc, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["foo"] == 5
    old_rev = doc["_rev"]

    # Test replace with sync set to True
    doc["foo"] = 6
    doc = col.replace(doc, sync=True, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["foo"] == 6
    assert "baz" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test replace with sync set to False
    doc["bar"] = 7
    doc = col.replace(doc, sync=False, check_rev=False)
    assert doc["_id"] == f"{col.name}/1"
    assert doc["_key"] == doc["_key"]
    assert isinstance(doc["_rev"], str)
    assert doc["_old_rev"] == old_rev
    assert col[doc["_key"]]["bar"] == 7
    assert "foo" not in col[doc["_key"]]
    old_rev = doc["_rev"]

    # Test replace missing document
    with assert_raises(DocumentReplaceError):
        col.replace(docs[1])
    assert col[doc["_key"]]["bar"] == 7
    assert col[doc["_key"]]["_rev"] == old_rev

    # Test replace with silent set to True
    doc["val"] = 8
    assert col.replace(doc, silent=True) is True
    assert col[doc["_key"]]["val"] == 8

    # Test replace with cache refilling
    doc["val"] = 9
    assert col.replace(doc, refill_index_caches=True, check_rev=False)
    assert col[doc["_key"]]["val"] == 9


def test_document_replace_many(col, bad_col, docs):
    col.insert_many(docs)

    old_revs = {}
    doc_keys = list(d["_key"] for d in docs)

    # Test replace_many with default options
    for doc in docs:
        doc["foo"] = 1
        doc.pop("val")
    results = col.replace_many(docs)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert col[doc_key]["foo"] == 1
        assert "val" not in col[doc_key]
        old_revs[doc_key] = result["_rev"]

    # Test replace_many with IDs
    docs_with_ids = [{"_id": col.name + "/" + d["_key"], "foo": 2} for d in docs]
    results = col.replace_many(docs_with_ids)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert col[doc_key]["foo"] == 2
        old_revs[doc_key] = result["_rev"]

    # Test update with return_new and return_old set to True
    for doc in docs:
        doc["bar"] = 3
        doc.pop("foo")
    results = col.replace_many(docs, return_new=True, return_old=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert result["new"]["_key"] == doc_key
        assert result["new"]["bar"] == 3
        assert "foo" not in result["new"]
        assert result["old"]["_key"] == doc_key
        assert result["old"]["foo"] == 2
        assert "bar" not in result["old"]
        assert col[doc_key]["bar"] == 3
        old_revs[doc_key] = result["_rev"]

    # Test update with return_new and return_old set to False
    for doc in docs:
        doc["baz"] = 4
        doc.pop("bar")
    results = col.replace_many(docs, return_new=False, return_old=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert "new" not in result
        assert "old" not in result
        assert col[doc_key]["baz"] == 4
        assert "bar" not in col[doc_key]
        old_revs[doc_key] = result["_rev"]

    # Test replace_many with check_rev set to True
    for doc in docs:
        doc["foo"] = 5
        doc.pop("baz")
        doc["_rev"] = old_revs[doc["_key"]] + "0"
    results = col.replace_many(docs, check_rev=True)
    for error, doc_key in zip(results, doc_keys):
        assert isinstance(error, DocumentRevisionError)
        assert error.error_code in {1200}
        assert "conflict" in error.error_message
        assert error.http_code == 202
        assert "[HTTP 202][ERR 1200]" in error.message
    for doc in col:
        assert "foo" not in doc
        assert doc["baz"] == 4

    # Test replace_many with check_rev set to False and cache refilling
    results = col.replace_many(docs, check_rev=False, refill_index_caches=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["foo"] == 5
        assert "baz" not in col[doc_key]
        old_revs[doc_key] = result["_rev"]

    # Test replace_many with sync set to True
    for doc in docs:
        doc["foo"] = 6
    results = col.replace_many(docs, sync=True, check_rev=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["foo"] == 6
        old_revs[doc_key] = result["_rev"]

    # Test replace_many with sync set to False
    for doc in docs:
        doc["bar"] = 7
        doc.pop("foo")
    results = col.replace_many(docs, sync=False, check_rev=False)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["_old_rev"] == old_revs[doc_key]
        assert col[doc_key]["bar"] == 7
        assert "foo" not in col[doc_key]
        old_revs[doc_key] = result["_rev"]

    # Test replace_many with bad database
    with assert_raises(DocumentReplaceError) as err:
        bad_col.replace_many(docs)
    assert err.value.error_code in {11, 1228}

    # Test replace_many with silent set to True
    for doc in docs:
        doc["foo"] = 8
        doc.pop("bar")
    assert col.replace_many(docs, silent=True, check_rev=False) is True
    for doc in docs:
        doc_key = doc["_key"]
        assert col[doc_key]["foo"] == 8
        assert "bar" not in col[doc_key]

    # Test replace_many with bad documents
    with assert_raises(DocumentParseError) as err:
        bad_col.replace_many([{}])
    assert str(err.value) == 'field "_key" or "_id" required'


def test_document_replace_match(col, bad_col, docs):
    col.import_bulk(docs)

    # Test replace single matching document
    assert col.replace_match({"val": 2}, {"val": 1, "foo": 1}) == 1
    assert col["2"]["val"] == 1
    assert col["2"]["foo"] == 1

    # Test replace multiple matching documents
    assert col.replace_match({"val": 1}, {"foo": 1}) == 2
    for doc_key in ["1", "2"]:
        assert "val" not in col[doc_key]
        assert col[doc_key]["foo"] == 1

    # Test replace multiple matching documents with limit and sync
    assert col.replace_match({"foo": 1}, {"bar": 2}, limit=1, sync=True) == 1
    assert [doc.get("bar") for doc in col].count(2) == 1

    # Test replace matching documents with bad database
    with assert_raises(DocumentReplaceError) as err:
        bad_col.replace_match({"val": 1}, {"foo": 1})
    assert err.value.error_code in {11, 1228}


def test_document_delete(col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test delete (document) with default options
    doc = docs[0]
    result = col.delete(doc)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert "old" not in result
    assert doc["_key"] not in col
    assert len(col) == 5

    # Test delete (document ID) with return_old set to True
    doc = docs[1]
    doc_id = f"{col.name}/{doc['_key']}"
    result = col.delete(doc_id, return_old=True)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert result["old"]["_key"] == doc["_key"]
    assert result["old"]["val"] == doc["val"]
    assert doc["_key"] not in col
    assert len(col) == 4

    # Test delete (document doc_key) with sync set to True
    doc = docs[2]
    result = col.delete(doc, sync=True)
    assert result["_id"] == f"{col.name}/{doc['_key']}"
    assert result["_key"] == doc["_key"]
    assert isinstance(result["_rev"], str)
    assert doc["_key"] not in col
    assert len(col) == 3

    # Test delete (document) with check_rev set to True
    doc = docs[3]
    bad_rev = col[doc["_key"]]["_rev"] + "0"
    bad_doc = doc.copy()
    bad_doc.update({"_rev": bad_rev})
    with assert_raises(DocumentRevisionError):
        col.delete(bad_doc, check_rev=True)
    assert bad_doc["_key"] in col
    assert len(col) == 3

    # Test delete (document) with check_rev set to False
    doc = docs[4]
    bad_rev = col[doc["_key"]]["_rev"] + "0"
    bad_doc = doc.copy()
    bad_doc.update({"_rev": bad_rev})
    col.delete(bad_doc, check_rev=False)
    assert doc["_key"] not in col
    assert len(col) == 2

    # Test delete missing document
    bad_key = generate_doc_key()
    with assert_raises(DocumentDeleteError) as err:
        col.delete(bad_key, ignore_missing=False)
    assert err.value.error_code == 1202
    assert len(col) == 2
    if col.context != "transaction":
        assert col.delete(bad_key, ignore_missing=True) is False

    # Test delete (document) with silent set to True and cache refilling
    doc = docs[5]
    assert col.delete(doc, silent=True, refill_index_caches=True) is True
    assert doc["_key"] not in col
    assert len(col) == 1


def test_document_delete_many(col, bad_col, docs):
    # Set up test documents
    old_revs = {}
    doc_keys = [d["_key"] for d in docs]
    doc_ids = [col.name + "/" + d["_key"] for d in docs]

    # Test delete_many (documents) with default options
    col.import_bulk(docs)
    results = col.delete_many(docs)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert "old" not in result
        assert doc_key not in col
        old_revs[doc_key] = result["_rev"]
    assert len(col) == 0

    # Test delete_many (documents) with IDs
    col.import_bulk(docs)
    results = col.delete_many(doc_ids)
    for result, doc_key in zip(results, doc_keys):
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert "old" not in result
        assert doc_key not in col
        old_revs[doc_key] = result["_rev"]
    assert len(col) == 0

    # Test delete_many (documents) with return_old set to True
    col.import_bulk(docs)
    results = col.delete_many(docs, return_old=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert result["old"]["_key"] == doc_key
        assert result["old"]["val"] == doc["val"]
        assert doc_key not in col
        old_revs[doc_key] = result["_rev"]
    assert len(col) == 0

    # Test delete_many (document doc_keys) with sync set to True
    col.import_bulk(docs)
    results = col.delete_many(docs, sync=True)
    for result, doc in zip(results, docs):
        doc_key = doc["_key"]
        assert result["_id"] == f"{col.name}/{doc_key}"
        assert result["_key"] == doc_key
        assert isinstance(result["_rev"], str)
        assert "old" not in result
        assert doc_key not in col
        old_revs[doc_key] = result["_rev"]
    assert len(col) == 0

    # Test delete_many with silent set to True and cache refilling
    col.import_bulk(docs)
    assert col.delete_many(docs, silent=True, refill_index_caches=True) is True
    assert len(col) == 0

    # Test delete_many (documents) with check_rev set to True
    col.import_bulk(docs)
    for doc in docs:
        doc["_rev"] = old_revs[doc["_key"]] + "0"
    results = col.delete_many(docs, check_rev=True)
    for error, doc in zip(results, docs):
        assert isinstance(error, DocumentRevisionError)
        assert error.error_code in {1200}
        assert "conflict" in error.error_message
        assert error.http_code == 202
        assert "[HTTP 202][ERR 1200]" in error.message
    assert len(col) == 6

    # Test delete_many (documents) with missing documents
    empty_collection(col)
    results = col.delete_many(
        [
            {"_key": generate_doc_key()},
            {"_key": generate_doc_key()},
            {"_key": generate_doc_key()},
        ]
    )
    for error, doc in zip(results, docs):
        assert isinstance(error, DocumentDeleteError)
        assert error.error_code in {1202}
        assert "document not found" in error.error_message
        assert error.http_code == 202
        assert "[HTTP 202][ERR 1202]" in error.message
    assert len(col) == 0

    # Test delete_many with bad database
    with assert_raises(DocumentDeleteError) as err:
        bad_col.delete_many(docs)
    assert err.value.error_code in {11, 1228}


def test_document_delete_match(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test delete matching documents with default options
    doc = docs[0]
    assert doc in col
    assert col.delete_match(doc) == 1
    assert doc not in col

    # Test delete matching documents with sync
    doc = docs[1]
    assert doc in col
    assert col.delete_match(doc, sync=True) == 1
    assert doc not in col

    # Test delete matching documents with limit of 2
    assert col.delete_match({"text": "bar"}, limit=2) == 2
    assert [d["text"] for d in col].count("bar") == 1

    # Test delete matching documents with bad database
    with assert_raises(DocumentDeleteError) as err:
        bad_col.delete_match(doc)
    assert err.value.error_code in {11, 1228}


def test_document_count(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    assert len(col) == len(docs)
    assert col.count() == len(docs)

    with assert_raises(DocumentCountError):
        len(bad_col)

    with assert_raises(DocumentCountError):
        bad_col.count()


def test_document_find(col, bad_col, docs):
    # Check preconditions
    assert len(col) == 0

    # Set up test documents
    col.import_bulk(docs)

    # Test find with sort expression (single field)
    found = list(col.find({}, sort=[{"sort_by": "text", "sort_order": "ASC"}]))
    assert len(found) == 6
    assert found[0]["text"] == "bar"
    assert found[-1]["text"] == "foo"

    # Test find with sort expression (multiple fields)
    found = list(
        col.find(
            {},
            sort=[
                {"sort_by": "text", "sort_order": "ASC"},
                {"sort_by": "val", "sort_order": "DESC"},
            ],
        )
    )
    assert len(found) == 6
    assert found[0]["val"] == 6
    assert found[-1]["val"] == 1

    # Test find (single match) with default options
    found = list(col.find({"val": 2}))
    assert len(found) == 1
    assert found[0]["_key"] == "2"

    # Test find with text value
    found = list(col.find({"text": "foo"}))
    assert len(found) == 3

    # Test find with list value
    found = list(col.find({"loc": [1, 1]}))
    assert len(found) == 1
    assert found[0]["_key"] == "1"

    # Test find with dict value with None
    data = {"dict": {"foo": "bar", "foo_2": None}}
    col.insert(data)
    found = list(col.find(data))
    assert len(found) == 1

    # Test find with multiple conditions
    found = list(col.find({"val": 2, "text": "foo"}))
    assert len(found) == 1
    assert found[0]["_key"] == "2"

    # Test find (multiple matches) with default options
    col.update_match({"val": 2}, {"val": 1})
    found = list(col.find({"val": 1}))
    assert len(found) == 2
    for doc in map(dict, found):
        assert doc["_key"] in {"1", "2"}
        assert doc["_key"] in col

    # Test find with offset
    with assert_raises(AssertionError) as err:
        col.find({"val": 1}, skip=-1)
    assert "skip must be a non-negative int" == str(err.value)

    found = list(col.find({"val": 1}, skip=100))
    assert len(found) == 0

    found = list(col.find({"val": 1}, skip=0))
    assert len(found) == 2

    found = list(col.find({"val": 1}, skip=1))
    assert len(found) == 1
    for doc in map(dict, found):
        assert doc["_key"] in {"1", "2", "3"}
        assert doc["_key"] in col

    # Test find with limit
    with assert_raises(AssertionError) as err:
        col.find({}, limit=-1)
    assert "limit must be a non-negative int" == str(err.value)

    for limit in [3, 4, 5]:
        found = list(col.find({}, limit=limit))
        assert len(found) == limit
        for doc in map(dict, found):
            assert doc["_key"] in extract("_key", docs)
            assert doc["_key"] in col

    # Test find in empty collection
    empty_collection(col)
    assert list(col.find({})) == []
    assert list(col.find({"val": 1})) == []
    assert list(col.find({"val": 2})) == []
    assert list(col.find({"val": 3})) == []
    assert list(col.find({"val": 4})) == []

    # Test find with bad database
    with assert_raises(DocumentGetError) as err:
        bad_col.find({"val": 1})
    assert err.value.error_code in {11, 1228}

    # Test find by attribute with a space
    col.insert({"foo bar": "baz"})
    assert len(list(col.find({"foo bar": "baz"}))) == 1

    # Test find by nested attribute
    col.insert({"foo": {"bar": "baz"}})
    assert len(list(col.find({"foo.bar": "baz"}))) == 1


def test_document_find_near(col, bad_col, docs):
    col.import_bulk(docs)

    # Test find_near with default options
    result = col.find_near(latitude=1, longitude=1)
    assert extract("_key", result) == ["1", "2", "3", "4", "5", "6"]

    # Test find_near with limit of -1
    with assert_raises(AssertionError) as err:
        col.find_near(latitude=1, longitude=1, limit=-1)
    assert "limit must be a non-negative int" == str(err.value)

    # Test find_near with limit of 0
    result = col.find_near(latitude=1, longitude=1, limit=0)
    assert extract("_key", result) == []

    # Test find_near with limit of 1
    result = col.find_near(latitude=1, longitude=1, limit=1)
    assert extract("_key", result) == ["1"]

    # Test find_near with limit of 3
    result = col.find_near(latitude=1, longitude=1, limit=3)
    assert extract("_key", result) == ["1", "2", "3"]

    # Test find_near with limit of 3 (another set of coordinates)
    result = col.find_near(latitude=5, longitude=5, limit=3)
    assert extract("_key", result) == ["4", "5", "6"]

    # Test random with bad collection
    with assert_raises(DocumentGetError):
        bad_col.find_near(latitude=1, longitude=1, limit=1)

    # Test find_near in an empty collection
    empty_collection(col)
    result = col.find_near(latitude=1, longitude=1, limit=1)
    assert list(result) == []
    result = col.find_near(latitude=5, longitude=5, limit=4)
    assert list(result) == []

    # Test find near with bad collection
    with assert_raises(DocumentGetError) as err:
        bad_col.find_near(latitude=1, longitude=1, limit=1)
    assert err.value.error_code in {11, 1228}


def test_document_find_in_range(col, bad_col, docs):
    col.import_bulk(docs)

    # Test find_in_range with default options
    result = col.find_in_range("val", lower=1, upper=2)
    assert extract("_key", result) == ["1"]

    # Test find_in_range with limit of -1
    with assert_raises(AssertionError) as err:
        col.find_in_range("val", lower=1, upper=2, limit=-1)
    assert "limit must be a non-negative int" == str(err.value)

    # Test find_in_range with limit of 0
    result = col.find_in_range("val", lower=1, upper=2, limit=0)
    assert extract("_key", result) == []

    # Test find_in_range with limit of 3
    result = col.find_in_range("val", lower=1, upper=5, limit=3)
    assert extract("_key", result) == ["1", "2", "3"]

    # Test find_in_range with skip set to -1
    with assert_raises(AssertionError) as err:
        col.find_in_range("val", lower=1, upper=2, skip=-1)
    assert "skip must be a non-negative int" == str(err.value)

    # Test find_in_range with skip set to 0
    result = col.find_in_range("val", lower=1, upper=5, skip=0)
    assert extract("_key", result) == ["1", "2", "3", "4"]

    # Test find_in_range with skip set to 3
    result = col.find_in_range("val", lower=1, upper=5, skip=2)
    assert extract("_key", result) == ["3", "4"]

    # Test find_in_range with bad collection
    with assert_raises(DocumentGetError) as err:
        bad_col.find_in_range(field="val", lower=1, upper=2, skip=2)
    assert err.value.error_code in {11, 1228}


def test_document_find_in_radius(col, bad_col):
    doc1 = {"_key": "1", "loc": [1, 1]}
    doc2 = {"_key": "2", "loc": [1, 4]}
    doc3 = {"_key": "3", "loc": [4, 1]}
    doc4 = {"_key": "4", "loc": [4, 4]}

    col.import_bulk([doc1, doc2, doc3, doc4])

    # Test find_in_radius without distance field
    result = list(
        col.find_in_radius(
            latitude=1,
            longitude=4,
            radius=6,
        )
    )
    assert len(result) == 1
    assert clean_doc(result[0]) == {"_key": "2", "loc": [1, 4]}

    # Test find_in_radius with distance field
    result = list(
        col.find_in_radius(latitude=1, longitude=1, radius=6, distance_field="dist")
    )
    assert len(result) == 1
    assert clean_doc(result[0]) == {"_key": "1", "loc": [1, 1], "dist": 0}

    # Test find_in_radius with bad collection
    with assert_raises(DocumentGetError) as err:
        bad_col.find_in_radius(3, 3, 10)
    assert err.value.error_code in {11, 1228}


def test_document_find_in_box(db, col, bad_col, geo, cluster):
    if cluster:
        pytest.skip("Not tested in a cluster setup")

    doc1 = {"_key": "1", "loc": [1, 1]}
    doc2 = {"_key": "2", "loc": [1, 5]}
    doc3 = {"_key": "3", "loc": [5, 1]}
    doc4 = {"_key": "4", "loc": [5, 5]}

    col.import_bulk([doc1, doc2, doc3, doc4])

    # Test find_in_box with default options
    result = col.find_in_box(
        latitude1=0, longitude1=0, latitude2=6, longitude2=3, index=geo["id"]
    )
    assert clean_doc(result) == [doc1, doc3]

    # Test find_in_box with no index provided
    result = col.find_in_box(latitude1=0, longitude1=0, latitude2=6, longitude2=3)
    assert clean_doc(result) == [doc1, doc3]

    # Test find_in_box with limit of -1
    with assert_raises(AssertionError) as err:
        col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
            limit=-1,
            index=geo["id"],
        )
    assert "limit must be a non-negative int" == str(err.value)

    # Test find_in_box with limit of 0
    result = col.find_in_box(
        latitude1=0, longitude1=0, latitude2=6, longitude2=3, limit=0, index=geo["id"]
    )
    assert clean_doc(result) == []

    # Test find_in_box with limit of 1
    result = col.find_in_box(
        latitude1=2,
        longitude1=0,
        latitude2=6,
        longitude2=3,
        limit=1,
        index=geo["id"],
    )
    assert clean_doc(result) == [doc3]

    # Test find_in_box with limit of 4
    result = col.find_in_box(
        latitude1=0, longitude1=0, latitude2=10, longitude2=10, limit=4, index=geo["id"]
    )
    assert clean_doc(result) == [doc1, doc2, doc3, doc4]

    # Test find_in_box with limit of -1
    with assert_raises(AssertionError) as err:
        col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
            skip=-1,
            index=geo["id"],
        )
    assert "skip must be a non-negative int" == str(err.value)

    # Test find_in_box with skip 1
    result = col.find_in_box(
        latitude1=0,
        longitude1=0,
        latitude2=6,
        longitude2=3,
        skip=1,
        index=geo["id"],
    )
    assert clean_doc(result) in [[doc1], [doc3]]

    # Test find_in_box with skip 3
    result = col.find_in_box(
        latitude1=0, longitude1=0, latitude2=10, longitude2=10, skip=3, index=geo["id"]
    )
    assert clean_doc(result) in [[doc1], [doc2], [doc3], [doc4]]

    # Test find_in_box with missing index in collection
    empty_col = db.create_collection(generate_col_name())
    with assert_raises(IndexMissingError) as err:
        empty_col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
        )

    # Test find_in_box with non-existing index
    with assert_raises(IndexGetError) as err:
        col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
            index="abc",
        )

    # Test find_in_box with non-geo index
    persistent_index = {"type": "persistent", "fields": ["loc"]}
    non_geo = col.add_index(persistent_index)
    with assert_raises(ValueError) as err:
        col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
            index=non_geo["id"],
        )

    # Test find_in_box with bad collection
    with assert_raises(IndexGetError) as err:
        bad_col.find_in_box(
            latitude1=0,
            longitude1=0,
            latitude2=6,
            longitude2=3,
            index=geo["id"],
        )
    assert err.value.error_code in {11, 1228}


def test_document_find_by_text(col, docs):
    col.import_bulk(docs)

    # Test find_by_text with default options
    result = col.find_by_text(field="text", query="foo,|bar")
    assert clean_doc(result) == docs

    # Test find_by_text with limit
    with assert_raises(AssertionError) as err:
        col.find_by_text(field="text", query="foo", limit=-1)
    assert "limit must be a non-negative int" == str(err.value)

    result = col.find_by_text(field="text", query="foo", limit=0)
    assert len(list(result)) == 0

    result = col.find_by_text(field="text", query="foo", limit=1)
    assert len(list(result)) == 1

    result = col.find_by_text(field="text", query="foo", limit=2)
    assert len(list(result)) == 2

    result = col.find_by_text(field="text", query="foo", limit=3)
    assert len(list(result)) == 3

    # Test find_by_text with invalid queries
    with assert_raises(DocumentGetError):
        col.find_by_text(field="text", query="+")
    with assert_raises(DocumentGetError):
        col.find_by_text(field="text", query="|")

    # Test find_by_text with missing column
    with assert_raises(DocumentGetError) as err:
        col.find_by_text(field="missing", query="foo")
    assert err.value.error_code == 1571


def test_document_has(col, bad_col, docs):
    # Set up test document
    result = col.insert(docs[0])
    rev = result["_rev"]
    bad_rev = rev + "0"

    doc_key = docs[0]["_key"]
    doc_id = col.name + "/" + doc_key
    missing_doc_key = docs[1]["_key"]
    missing_doc_id = col.name + "/" + missing_doc_key

    # Test existing documents without revision or with good revision
    for doc_input in [
        doc_key,
        doc_id,
        {"_key": doc_key},
        {"_id": doc_id},
        {"_id": doc_id, "_key": doc_key},
        {"_key": doc_key, "_rev": rev},
        {"_id": doc_id, "_rev": rev},
        {"_id": doc_id, "_key": doc_key, "_rev": rev},
    ]:
        assert doc_input in col
        assert col.has(doc_input) is True
        assert col.has(doc_input, rev=rev) is True
        assert col.has(doc_input, rev=rev, check_rev=True) is True
        assert col.has(doc_input, rev=rev, check_rev=False) is True
        assert col.has(doc_input, rev=bad_rev, check_rev=False) is True

        with assert_raises(DocumentRevisionError) as err:
            col.has(doc_input, rev=bad_rev, check_rev=True)
        assert err.value.error_code == 412

    # Test existing documents with bad revision
    for doc_input in [
        {"_key": doc_key, "_rev": bad_rev},
        {"_id": doc_id, "_rev": bad_rev},
        {"_id": doc_id, "_key": doc_key, "_rev": bad_rev},
    ]:
        with assert_raises(DocumentRevisionError) as err:
            col.has(doc_input)
        assert err.value.error_code == 412

        with assert_raises(DocumentRevisionError) as err:
            col.has(doc_input, rev=bad_rev)
        assert err.value.error_code == 412

        with assert_raises(DocumentRevisionError) as err:
            col.has(doc_input, rev=bad_rev, check_rev=True)
        assert err.value.error_code == 412

        assert doc_input in col
        assert col.has(doc_input, rev=rev, check_rev=True) is True
        assert col.has(doc_input, rev=rev, check_rev=False) is True
        assert col.has(doc_input, rev=bad_rev, check_rev=False) is True

    # Test missing documents
    for doc_input in [
        missing_doc_key,
        missing_doc_id,
        {"_key": missing_doc_key},
        {"_id": missing_doc_id},
        {"_id": missing_doc_id, "_key": missing_doc_key},
        {"_key": missing_doc_key, "_rev": rev},
        {"_id": missing_doc_id, "_rev": rev},
        {"_id": missing_doc_id, "_key": missing_doc_key, "_rev": rev},
    ]:
        assert doc_input not in col
        assert col.has(doc_input) is False
        assert col.has(doc_input, rev=rev) is False
        assert col.has(doc_input, rev=rev, check_rev=True) is False
        assert col.has(doc_input, rev=rev, check_rev=False) is False

    # Test documents with IDs with wrong collection name
    expected_error_msg = "bad collection name"
    bad_id = generate_col_name() + "/" + doc_key
    for doc_input in [
        bad_id,
        {"_id": bad_id},
        {"_id": bad_id, "_rev": rev},
        {"_id": bad_id, "_rev": bad_rev},
        {"_id": bad_id, "_key": doc_key},
        {"_id": bad_id, "_key": doc_key, "_rev": rev},
        {"_id": bad_id, "_key": doc_key, "_rev": bad_rev},
    ]:
        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, check_rev=True)
        assert expected_error_msg in str(err.value)

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, check_rev=False)
        assert expected_error_msg in str(err.value)

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, rev=rev, check_rev=True)
        assert expected_error_msg in str(err.value)

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, rev=rev, check_rev=False)
        assert expected_error_msg in str(err.value)

    # Test documents with missing "_id" and "_key" fields
    expected_error_msg = 'field "_key" or "_id" required'
    for doc_input in [
        {},
        {"foo": "bar"},
        {"foo": "bar", "_rev": rev},
        {"foo": "bar", "_rev": bad_rev},
    ]:
        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, check_rev=True)
        assert str(err.value) == expected_error_msg

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, check_rev=False)
        assert str(err.value) == expected_error_msg

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, rev=rev, check_rev=True)
        assert str(err.value) == expected_error_msg

        with assert_raises(DocumentParseError) as err:
            col.has(doc_input, rev=rev, check_rev=False)
        assert str(err.value) == expected_error_msg

    # Test get with bad database
    with assert_raises(DocumentInError) as err:
        bad_col.has(doc_key)
    assert err.value.error_code == 401

    # Test contains with bad database
    with assert_raises(DocumentInError) as err:
        assert doc_key in bad_col
    assert err.value.error_code == 401


def test_document_get(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)
    doc = docs[0]
    doc_val = doc["val"]
    doc_key = doc["_key"]
    doc_id = f"{col.name}/{doc_key}"

    # Test get existing document by body
    result = col.get(doc)
    assert result["_key"] == doc_key
    assert result["val"] == doc_val

    # Test get existing document by ID
    result = col.get(doc_id)
    assert result["_key"] == doc_key
    assert result["val"] == doc_val

    # Test get existing document by key
    result = col.get(doc_key)
    assert result["_key"] == doc_key
    assert result["val"] == doc_val

    # Test get missing document
    assert col.get(generate_doc_key()) is None

    # Test get with correct revision
    good_rev = col[doc_key]["_rev"]
    result = col.get(doc, rev=good_rev)
    assert result["_key"] == doc_key
    assert result["val"] == doc_val

    # Test get with invalid revision
    bad_rev = col[doc_key]["_rev"] + "0"
    with assert_raises(DocumentRevisionError) as err:
        col.get(doc_key, rev=bad_rev, check_rev=True)
    assert err.value.error_code == 1200

    # Test get with correct revision and check_rev turned off
    result = col.get(doc, rev=bad_rev, check_rev=False)
    assert result["_key"] == doc_key
    assert result["_rev"] != bad_rev
    assert result["val"] == doc_val

    # Test get with bad database
    with assert_raises(DocumentGetError) as err:
        bad_col.get(doc["_key"])
    assert err.value.error_code in {11, 1228}

    # Test get with bad database
    with assert_raises(DocumentGetError) as err:
        assert bad_col[doc["_key"]]
    assert err.value.error_code in {11, 1228}


def test_document_get_many(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test get_many missing documents
    assert col.get_many([generate_doc_key()]) == []

    # Test get_many existing documents
    result = col.get_many(docs[:1])
    result = clean_doc(result)
    assert result == docs[:1]

    result = col.get_many(docs)
    assert clean_doc(result) == docs

    # Test get_many in empty collection
    empty_collection(col)

    # sending an empty list returns internal error
    # assert col.get_many([]) == []

    assert col.get_many(docs[:1]) == []
    assert col.get_many(docs[:3]) == []

    with assert_raises(DocumentGetError) as err:
        bad_col.get_many(docs)
    assert err.value.error_code in {11, 1228}


def test_document_all(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test all with default options
    cursor = col.all()
    result = list(cursor)
    assert clean_doc(result) == docs

    # Test all with skip of -1
    with assert_raises(AssertionError) as err:
        col.all(skip=-1)
    assert "skip must be a non-negative int" == str(err.value)

    # Test all with a skip of 0
    cursor = col.all(skip=0)
    result = list(cursor)
    assert cursor.count() == len(docs)
    assert clean_doc(result) == docs

    # Test all with a skip of 1
    cursor = col.all(skip=1)
    result = list(cursor)
    assert cursor.count() == len(result) == 5
    assert all([clean_doc(d) in docs for d in result])

    # Test all with a skip of 3
    cursor = col.all(skip=3)
    result = list(cursor)
    assert cursor.count() == len(result) == 3
    assert all([clean_doc(d) in docs for d in result])

    # Test all with skip of -1
    with assert_raises(AssertionError) as err:
        col.all(limit=-1)
    assert "limit must be a non-negative int" == str(err.value)

    # Test all with a limit of 0
    cursor = col.all(limit=0)
    result = list(cursor)
    assert cursor.count() == len(result) == 0

    # Test all with a limit of 1
    cursor = col.all(limit=1)
    result = list(cursor)
    assert cursor.count() == len(result) == 1
    assert all([clean_doc(d) in docs for d in result])

    # Test all with a limit of 3
    cursor = col.all(limit=3)
    result = list(cursor)
    assert cursor.count() == len(result) == 3
    assert all([clean_doc(d) in docs for d in result])

    # Test all with skip and limit
    cursor = col.all(skip=5, limit=2)
    result = list(cursor)
    assert cursor.count() == len(result) == 1
    assert all([clean_doc(d) in docs for d in result])

    # Test export with bad database
    with assert_raises(DocumentGetError) as err:
        bad_col.all()
    assert err.value.error_code in {11, 1228}


def test_document_ids(col, bad_col, docs):
    cursor = col.ids()
    result = list(cursor)
    assert result == []

    col.import_bulk(docs)
    cursor = col.ids()
    result = list(cursor)
    ids = set(f'{col.name}/{d["_key"]}' for d in docs)
    assert set(result) == ids

    # Test ids with bad database
    with assert_raises(DocumentIDsError) as err:
        bad_col.ids()
    assert err.value.error_code in {11, 1228}


def test_document_keys(col, bad_col, docs):
    cursor = col.keys()
    result = list(cursor)
    assert result == []

    col.import_bulk(docs)
    cursor = col.keys()
    result = list(cursor)
    assert len(result) == len(docs)
    assert sorted(result) == extract("_key", docs)

    # Test keys with bad database
    with assert_raises(DocumentKeysError) as err:
        bad_col.keys()
    assert err.value.error_code in {11, 1228}


def test_document_random(col, bad_col, docs):
    # Set up test documents
    col.import_bulk(docs)

    # Test random in non-empty collection
    for attempt in range(10):
        random_doc = col.random()
        assert clean_doc(random_doc) in docs

    # Test random in empty collection
    empty_collection(col)
    for attempt in range(10):
        random_doc = col.random()
        assert random_doc is None

    # Test random with bad database
    with assert_raises(DocumentGetError) as err:
        bad_col.random()
    assert err.value.error_code in {11, 1228}


def test_document_import_bulk(col, bad_col, docs):
    # Test import_bulk with default options
    result = col.import_bulk(docs)
    assert result["created"] == len(docs)
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 0
    assert "details" in result
    for doc in docs:
        doc_key = doc["_key"]
        assert doc_key in col
        assert col[doc_key]["_key"] == doc_key
        assert col[doc_key]["val"] == doc["val"]
        assert col[doc_key]["loc"] == doc["loc"]
    empty_collection(col)

    # Test import bulk without details and with sync
    result = col.import_bulk(docs, details=False, sync=True)
    assert result["created"] == len(docs)
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 0
    assert "details" not in result
    for doc in docs:
        doc_key = doc["_key"]
        assert doc_key in col
        assert col[doc_key]["_key"] == doc_key
        assert col[doc_key]["val"] == doc["val"]
        assert col[doc_key]["loc"] == doc["loc"]

    # Test import_bulk duplicates with halt_on_error
    with assert_raises(DocumentInsertError):
        col.import_bulk(docs, halt_on_error=True)

    # Test import bulk duplicates without halt_on_error
    result = col.import_bulk(docs, halt_on_error=False)
    assert result["created"] == 0
    assert result["errors"] == len(docs)
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 0
    empty_collection(col)

    # Test import bulk with bad database
    with assert_raises(DocumentInsertError):
        bad_col.import_bulk(docs, halt_on_error=True)
    assert len(col) == 0

    # Test import bulk with overwrite
    result = col.import_bulk(docs, overwrite=True)
    assert result["created"] == len(docs)
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 0
    for doc in docs:
        doc_key = doc["_key"]
        assert doc_key in col
        assert col[doc_key]["_key"] == doc_key
        assert col[doc_key]["val"] == doc["val"]
        assert col[doc_key]["loc"] == doc["loc"]
    empty_collection(col)

    # Test import bulk with batch_size
    results = col.import_bulk(docs, batch_size=len(docs) // 2)
    assert type(results) is list
    assert len(results) == 2
    empty_collection(col)

    result = col.import_bulk(docs, batch_size=len(docs) * 2)
    assert type(result) is list
    assert len(result) == 1
    empty_collection(col)

    # Test import bulk with overwrite and batch_size
    with pytest.raises(ValueError):
        col.import_bulk(docs, overwrite=True, batch_size=1)

    # Test import bulk on_duplicate actions
    doc = docs[0]
    doc_key = doc["_key"]
    old_doc = {"_key": doc_key, "foo": "2"}
    new_doc = {"_key": doc_key, "bar": "3"}

    col.insert(old_doc)
    result = col.import_bulk([new_doc], on_duplicate="error", halt_on_error=False)
    assert len(col) == 1
    assert result["created"] == 0
    assert result["errors"] == 1
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 0
    assert col[doc["_key"]]["foo"] == "2"
    assert "bar" not in col[doc["_key"]]

    result = col.import_bulk([new_doc], on_duplicate="ignore", halt_on_error=False)
    assert len(col) == 1
    assert result["created"] == 0
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 0
    assert result["ignored"] == 1
    assert col[doc["_key"]]["foo"] == "2"
    assert "bar" not in col[doc["_key"]]

    result = col.import_bulk([new_doc], on_duplicate="update", halt_on_error=False)
    assert len(col) == 1
    assert result["created"] == 0
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 1
    assert result["ignored"] == 0
    assert col[doc["_key"]]["foo"] == "2"
    assert col[doc["_key"]]["bar"] == "3"

    empty_collection(col)
    col.insert(old_doc)
    result = col.import_bulk([new_doc], on_duplicate="replace", halt_on_error=False)
    assert len(col) == 1
    assert result["created"] == 0
    assert result["errors"] == 0
    assert result["empty"] == 0
    assert result["updated"] == 1
    assert result["ignored"] == 0
    assert "foo" not in col[doc["_key"]]
    assert col[doc["_key"]]["bar"] == "3"


def test_document_management_via_db(db, col):
    doc1_id = col.name + "/foo"
    doc2_id = col.name + "/bar"
    doc1 = {"_key": "foo"}
    doc2 = {"_id": doc2_id}

    # Test document insert with empty body
    result = db.insert_document(col.name, {})
    assert len(col) == 1
    assert db.has_document(result["_id"]) is True
    assert db.has_document(result["_id"], rev=result["_rev"]) is True

    # Test document insert with key
    assert db.has_document(doc1_id) is False
    result = db.insert_document(col.name, doc1)
    assert result["_key"] == "foo"
    assert result["_id"] == doc1_id
    assert len(col) == 2
    assert db.has_document(doc1_id) is True
    assert db.has_document(doc1_id, rev=result["_rev"]) is True

    # Test document insert with ID
    assert db.has_document(doc2_id) is False
    result = db.insert_document(col.name, doc2)
    assert result["_key"] == "bar"
    assert result["_id"] == doc2_id
    assert len(col) == 3
    assert db.has_document(doc2_id) is True
    assert db.has_document(doc2_id, rev=result["_rev"]) is True

    # Test document get with bad input
    with assert_raises(DocumentParseError) as err:
        db.document(doc1)
    assert str(err.value) == 'field "_id" required'

    # Test document get
    for doc_id in [doc1_id, doc2_id]:
        result = db.document(doc_id)
        assert "_rev" in result
        assert "_key" in result
        assert result["_id"] == doc_id

    # Test document update with bad input
    with assert_raises(DocumentParseError) as err:
        db.update_document(doc1)
    assert str(err.value) == 'field "_id" required'

    # Test document update
    result = db.update_document({"_id": doc1_id, "val": 100})
    assert result["_id"] == doc1_id
    assert col[doc1_id]["val"] == 100
    assert len(col) == 3

    # Test document replace with bad input
    with assert_raises(DocumentParseError) as err:
        db.replace_document(doc1)
    assert str(err.value) == 'field "_id" required'

    # Test document replace
    result = db.replace_document({"_id": doc1_id, "num": 300})
    assert result["_id"] == doc1_id
    assert "val" not in col[doc1_id]
    assert col[doc1_id]["num"] == 300
    assert len(col) == 3

    # Test document delete with bad input
    with assert_raises(DocumentParseError) as err:
        db.delete_document(doc1)
    assert str(err.value) == 'field "_id" required'

    # Test document delete
    result = db.delete_document({"_id": doc1_id})
    assert result["_id"] == doc1_id
    assert doc1_id not in col
    assert len(col) == 2


def test_version_attributes_update_many(col, db_version):
    if db_version < version.parse("3.12.0"):
        pytest.skip("Version attributes is tested in 3.12.0+")

    col.insert_many(
        [
            {"_key": "test1", "version": 0},
            {"_key": "test2", "version": 0},
            {"_key": "test3", "version": 0},
        ]
    )

    docs = [
        {"_key": "test1", "version": 2},
        {"_key": "test1", "version": 3},
        {"_key": "test1", "version": 1},
        {"_key": "test2", "version": 1},
        {"_key": "test2", "version": 9},
        {"_key": "test2", "version": 42},
        {"_key": "test2", "version": 0},
        {"_key": "test3"},
        {"_key": "test3", "version": 5},
        {"_key": "test3", "version": 4},
        {"_key": "test3", "value": 2},
    ]

    col.update_many(docs, version_attribute="version")
    assert col["test1"]["version"] == 3
    assert col["test2"]["version"] == 42
    assert col["test3"]["version"] == 5

    docs = [
        {"_key": "test1", "version": 2},
        {"_key": "test1", "version": 3},
        {"_key": "test1", "version": 5},
        {"_key": "test2", "version": 1},
        {"_key": "test2", "version": 9},
        {"_key": "test2", "version": 42},
        {"_key": "test2", "version": 0},
        {"_key": "test3", "version": 5},
        {"_key": "test3", "version": 6},
    ]

    col.replace_many(docs, version_attribute="version")
    assert col["test1"]["version"] == 5
    assert col["test2"]["version"] == 42
    assert col["test3"]["version"] == 6

    docs = [
        {"_key": "test1", "version": 0},
        {"_key": "test2", "version": 0},
        {"_key": "test3", "version": 0},
    ]

    col.insert_many(docs, overwrite_mode="update", version_attribute="version")
    assert col["test1"]["version"] == 5
    assert col["test2"]["version"] == 42
    assert col["test3"]["version"] == 6

    docs = [
        {"_key": "test1", "version": 43},
        {"_key": "test2", "version": 41},
        {"_key": "test3", "version": 43},
    ]

    col.insert_many(docs, overwrite_mode="replace", version_attribute="version")
    assert col["test1"]["version"] == 43
    assert col["test2"]["version"] == 42
    assert col["test3"]["version"] == 43
