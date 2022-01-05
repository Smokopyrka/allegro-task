import pytest
from repolist.logic import API, UserQuotaExceededError, InvalidUserError

test_data = []
for i in range(7):
    test_data.append(
        {
            'id': i,
            'full_name': f'test_user/repo{i}',
            'stargazers_count': i
        }
    )

expected = []
for item in test_data:
    expected.append(
        {
            'id': item['id'],
            'name': item['full_name'],
            'stars': item['stargazers_count']
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


class ClientErrorResponseMock:

    def __init__(self, status):
        self.status = status


@pytest.mark.asyncio
async def test_get_user_repo_multiple_page(mocker):
    mock_resps = [
        ClientResponseMock(test_data[:2], 1, last_page=4),
        ClientResponseMock(test_data[2:4], 2, last_page=4),
        ClientResponseMock(test_data[4:6], 3, last_page=4),
        ClientResponseMock(test_data[6:], 4, last_page=4)
    ]

    async def mock_get(*args, params, **kwargs):
        if (page := params.get('page')) is None:
            page = 1
        return mock_resps[page - 1]

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    api = API()

    ret = [repo async for repo in api.get_user_repos('test')]
    ret = sorted(ret, key=lambda item: item['id'])
    assert len(ret) == len(test_data)
    for act, exp in zip(ret, expected):
        assert act['id'] == exp['id']
        assert act['name'] == exp['name']
        assert act['stars'] == exp['stars']
        assert len(act.keys()) == len(exp.keys())


@pytest.mark.asyncio
async def test_get_user_repo_single_page(mocker):
    async def mock_get(*args, **kwargs):
        return ClientResponseMock(test_data, 1, last_page=1)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get
    )

    api = API()

    ret = [repo async for repo in api.get_user_repos('test')]
    ret = sorted(ret, key=lambda item: item['id'])
    assert len(ret) == len(test_data)
    for act, exp in zip(ret, expected):
        assert act['id'] == exp['id']
        assert act['name'] == exp['name']
        assert act['stars'] == exp['stars']
        assert len(act.keys()) == len(exp.keys())


@pytest.mark.asyncio
async def test_get_user_repo_invalid_user(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(404)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    api = API()

    with pytest.raises(InvalidUserError):
        ret = [repo async for repo in api.get_user_repos('test')]


@pytest.mark.asyncio
async def test_get_user_repo_with_exceeded_quota(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(403)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    api = API()

    with pytest.raises(UserQuotaExceededError):
        ret = [repo async for repo in api.get_user_repos('test')]
