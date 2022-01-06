import pytest
from repolist.logic import API

api = API('dummy.com')

test_data = []
for i in range(7):
    test_data.append(
        {
            'id': i,
            'name': f'test_user/repo{i}',
            'star_count': i
        }
    )


@pytest.mark.asyncio
async def test_with_one_repo(mocker):
    async def mock_get_user_repos(*args, **kwargs):
        yield test_data[0]

    mocker.patch(
        'repolist.logic.API.get_user_repos',
        mock_get_user_repos
    )

    assert test_data[0]['star_count'] == await api.get_user_star_total('test')


@pytest.mark.asyncio
async def test_with_multiple_repo(mocker):
    async def mock_get_user_repos(*args, **kwargs):
        for data in test_data:
            yield data

    mocker.patch(
        'repolist.logic.API.get_user_repos',
        mock_get_user_repos
    )

    expected = sum([data['star_count'] for data in test_data])
    assert expected == await api.get_user_star_total('test')


@pytest.mark.asyncio
async def test_with_no_repos(mocker):
    async def mock_get_user_repos(*args, **kwargs):
        repos = []
        for repo in repos:
            yield repo

    mocker.patch(
        'repolist.logic.API.get_user_repos',
        mock_get_user_repos
    )

    expected = 0
    assert expected == await api.get_user_star_total('test')
