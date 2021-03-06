import aiohttp
import pytest
from repolist.logic import API, InvalidUserError, UserQuotaExceededError

api = API('dummy.com')


class ClientErrorResponseMock:

    def __init__(self, status):
        self.status = status


@pytest.mark.asyncio
async def test_with_200_success(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(200)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    async with aiohttp.ClientSession() as session:
        await api._fetch(session, None)


@pytest.mark.asyncio
async def test_with_404_error(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(404)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    with pytest.raises(InvalidUserError):
        async with aiohttp.ClientSession() as session:
            await api._fetch(session, None)


@pytest.mark.asyncio
async def test_with_403_error(mocker):
    async def mock_get_error(*args, **kwargs):
        return ClientErrorResponseMock(403)

    mocker.patch(
        'aiohttp.ClientSession.get',
        mock_get_error
    )

    with pytest.raises(UserQuotaExceededError):
        async with aiohttp.ClientSession() as session:
            await api._fetch(session, None)
