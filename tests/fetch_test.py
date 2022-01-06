import pytest
import aiohttp
from repolist.logic import API, InvalidUserError, UserQuotaExceededError

class ClientErrorResponseMock:

    def __init__(self, status):
        self.status = status

@pytest.mark.asyncio
async def test_fetch(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(200)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    api = API('dummy.com')

    async with aiohttp.ClientSession() as session:
        await api._fetch(session, None)

@pytest.mark.asyncio
async def test_get_user_repo_invalid_user(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(404)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    api = API('dummy.com')

    with pytest.raises(InvalidUserError):
        async with aiohttp.ClientSession() as session:
            await api._fetch(session, None)


@pytest.mark.asyncio
async def test_get_user_repo_quota_exceeded(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(403)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    api = API('dummy.com')

    with pytest.raises(UserQuotaExceededError):
        async with aiohttp.ClientSession() as session:
            await api._fetch(session, None)
