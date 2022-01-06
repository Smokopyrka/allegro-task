import re
import pytest
from repolist.logic import API

test_repos = []
for i in range(3):
    test_repos.append(
        {
            'id': i,
            'name': f'test_user/repo{i}',
            'stars': i
        }
    )

test_data = {
    0: {
        'lang1': 1,
        'lang2': 2
    },
    1: {
        'lang2': 3,
        'lang3': 3
    },
    2: {
        'lang1': 3,
    }
}


class ClientResponseMock:

    def __init__(self, data):
        self.status = 200
        self._page = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return self._page


@pytest.mark.asyncio
async def test_get_user_lang_with_one_repo(mocker):
    async def mock_get_user_repos(*args, **kwargs):
        yield test_repos[0]

    async def mock_get(*args, **kwargs):
        return ClientResponseMock(test_data[0])

    mocker.patch(
        'repolist.logic.API.get_user_repos',
        mock_get_user_repos
    )

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    exptected = [
        {
            'language': 'lang2',
            'byte_count': 2
        },
        {
            'language': 'lang1',
            'byte_count': 1
        }
    ]

    api = API()

    actual = await api.get_users_language_list('test_user')
    assert actual == exptected


@pytest.mark.asyncio
async def test_get_user_lang_with_many_repos(mocker):
    async def mock_get_user_repos(*args, **kwargs):
        for repo in test_repos:
            yield repo

    async def mock_get(session, url, *args, **kwargs):
        print(url)
        repo_num = int(re.search(r'test_user/repo(\d+)', url).group(1))
        return ClientResponseMock(test_data[repo_num])

    mocker.patch(
        'repolist.logic.API.get_user_repos',
        mock_get_user_repos
    )

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    exptected = [
        {
            'language': 'lang2',
            'byte_count': 5
        },
        {
            'language': 'lang1',
            'byte_count': 4
        },
        {
            'language': 'lang3',
            'byte_count': 3
        }
    ]

    api = API()

    actual = await api.get_users_language_list('test_user')
    assert actual == exptected
