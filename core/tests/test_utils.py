from core.services.utils import chunk_list


def test_chunk_list_with_one_chunk():
    lst = [10, 5, 100]
    chunk_size = 100
    res = list(chunk_list(lst, chunk_size))

    assert len(res) == 1
    assert res[0] == lst


def test_chunk_list_with_multiple_same_chunks():
    lst = [10, 5, 100]
    chunk_size = 1
    res = list(chunk_list(lst, chunk_size))

    assert len(res) == len(lst)
    assert res == [[10], [5], [100]]


def test_chunk_list_with_empty_list():
    lst = []
    chunk_size = 5
    res = list(chunk_list(lst, chunk_size))

    assert len(res) == 0


def test_chunk_list_with_multiple_different_chunks():
    lst = [1, 2, 3, 4, 5]
    chunk_size = 2
    res = list(chunk_list(lst, chunk_size))

    assert len(res) == 3
    assert res[0] == [1, 2]
    assert res[-1] == [5]
