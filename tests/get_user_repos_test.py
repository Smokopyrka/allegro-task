import pytest
from repolist.logic import API

api = API('dummy.com')

test_repos = []
for i in range(7):
    test_repos.append(
        {
            'id': i,
            'full_name': f'test_user/repo{i}',
            'stargazers_count': i
        }
    )


expected = []
for item in test_repos:
    expected.append(
        {
            'id': item['id'],
            'name': item['full_name'],
            'star_count': item['stargazers_count']
        }
    )


class ClientResponseMock:

    def __init__(self, page, page_num, *, last_page):
        self.status = 200
        self._page = page
        if page_num == last_page:
            self.headers = {}
        else:
            self.headers = {
                'Link': f'<t.io/users/test/repos?page={last_page}>; rel="last"'
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        print(f'getting page {self._page}')
        return self._page


@pytest.mark.asyncio
async def test_with_multiple_pages(mocker):
    mock_resps = [
        ClientResponseMock(test_repos[:2], 1, last_page=4),
        ClientResponseMock(test_repos[2:4], 2, last_page=4),
        ClientResponseMock(test_repos[4:6], 3, last_page=4),
        ClientResponseMock(test_repos[6:], 4, last_page=4)
    ]

    async def mock_get(*args, params, **kwargs):
        if (page := params.get('page')) is None:
            page = 1
        return mock_resps[page - 1]

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    ret = [repo async for repo in api.get_user_repos('test')]
    actual = sorted(ret, key=lambda item: item['id'])
    assert actual == expected


@pytest.mark.asyncio
async def test_with_single_page(mocker):
    async def mock_get(*args, **kwargs):
        return ClientResponseMock(test_repos, 1, last_page=1)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    ret = [repo async for repo in api.get_user_repos('test')]
    actual = sorted(ret, key=lambda item: item['id'])
    assert actual == expected


@pytest.mark.asyncio
async def test_with_no_repos(mocker):
    async def mock_get(*args, **kwargs):
        return ClientResponseMock([], 1, last_page=1)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    ret = [repo async for repo in api.get_user_repos('test')]
    assert not ret
