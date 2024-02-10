import asyncio
import time
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from battlechess.server import crud, models
from battlechess.server.btchApi import app, get_db


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    return "asyncio"


def getToken(username):
    return crud.create_access_token(
        data={"sub": username}, expires_delta=timedelta(minutes=3000)
    )


@pytest.mark.anyio
async def test__getTurn__long_polling_async(asyncclient, classicSetup):
    firstgame_uuid, john_token = classicSetup
    token = getToken("janedoe")

    start = time.time()

    response = await asyncclient.get(
        f"/games/{firstgame_uuid}/turn",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        params={"long_polling": True},
    )
    assert response.status_code == 200

    elapsed = time.time() - start
    assert elapsed > 5
