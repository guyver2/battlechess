import asyncio
import time
from datetime import timedelta

import pytest

from battlechess.server import crud


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


@pytest.mark.skip(reason="slow test")
@pytest.mark.anyio
async def test__getTurn__long_polling_async(asyncclient, classicSetup):
    firstgame_uuid, john_token = classicSetup

    start = time.time()

    response = await asyncclient.get(
        f"/games/{firstgame_uuid}/turn",
        headers={
            "Authorization": "Bearer " + john_token,
            "Content-Type": "application/json",
        },
        params={"long_polling": True},
    )
    assert response.status_code == 200

    elapsed = time.time() - start
    assert elapsed > 5


@pytest.mark.anyio
async def test__getTurn__long_polling_move(asyncclient, classicSetup):
    firstgame_uuid, john_token = classicSetup
    jane_token = getToken("janedoe")

    background_tasks = set()

    hard_turn_timeout = 10

    start = time.time()

    # Check that's it's not john'd turn
    long_polling = False
    response = await asyncclient.get(
        f"/games/{firstgame_uuid}/turn/me",
        headers={
            "Authorization": "Bearer " + john_token,
            "Content-Type": "application/json",
        },
        params={"long_polling": long_polling},
    )
    short_polling_elapsed = time.time() - start
    assert response.status_code == 200
    assert response.json() is False
    # ensure that non-long-polling get is non blocking
    assert short_polling_elapsed < 1

    start = time.time()
    # ask turn again but with long polling
    long_polling = True
    premature_turn_ask_task = asyncio.create_task(
        asyncclient.get(
            f"/games/{firstgame_uuid}/turn/me",
            headers={
                "Authorization": "Bearer " + john_token,
                "Content-Type": "application/json",
            },
            params={"long_polling": long_polling},
        )
    )

    create_task_elapsed = time.time() - start
    # ensure that create_task get is non blocking
    assert create_task_elapsed < 1

    background_tasks.add(premature_turn_ask_task)
    premature_turn_ask_task.add_done_callback(background_tasks.discard)
    await asyncio.sleep(1)  # only blocks current task
    # time.sleep(1) # blocks everything
    if premature_turn_ask_task.done():
        print("turn returned too early!", premature_turn_ask_task.result().json())
    assert not premature_turn_ask_task.done()

    # Jane (black) moves
    move_response = await asyncclient.post(
        f"/games/{firstgame_uuid}/move",
        headers={
            "Authorization": "Bearer " + jane_token,
            "Content-Type": "application/json",
        },
        json={
            "move": "d7d5",
        },
    )

    assert move_response.status_code == 200
    # gather turn and assert it didn't timeout
    await premature_turn_ask_task
    elapsed = time.time() - start
    assert elapsed < hard_turn_timeout / 2
    response = premature_turn_ask_task.result()
    print(f"task result {response.json()}")
    assert response.json() is True
    assert response.status_code == 200
