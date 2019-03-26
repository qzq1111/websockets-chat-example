import asyncio
import json
import logging

import websockets

connected = set()

users = dict()


def user_join(user):
    """
    用户加入消息
    :param user:
    :return:
    """
    return json.dumps({'type': 'user_join', 'name': user, 'total': len(users),})


def user_left(user):
    """
    用户离开消息
    :param user:
    :return:
    """
    return json.dumps({'type': 'user_left', 'name': user, 'total': len(users)})


def new_message(user, comment):
    """
    用户消息
    :param user:
    :param comment:
    :return:
    """
    return json.dumps({'type': 'message', 'name': user, **comment})


async def notify_users(message_builder_function, *args, **kwargs):
    """
    异步发布消息
    :param message_builder_function:
    :param args:
    :param kwargs:
    :return:
    """
    if users:
        message = message_builder_function(*args, **kwargs)
        await asyncio.wait([user.send(message) for user in users])


async def register(websocket):
    """
    用户websocket连接注册
    :param websocket:
    :return:
    """
    greeting = await websocket.recv()
    data = json.loads(greeting)
    if websocket in users:
        return users[websocket]
    else:
        users[websocket] = data["user"]

        await notify_users(user_join, data["user"])
        return data["user"]


async def unregister(websocket):
    """
     用户websocket断开
    :param websocket:
    :return:
    """
    user = users[websocket]
    del users[websocket]
    await notify_users(user_left, user, )


async def handler(websocket, path):
    # 只注册一次
    user = await register(websocket)
    try:
        async for msg in websocket:
            data = json.loads(msg)
            await notify_users(new_message, user, data)
    finally:
        await unregister(websocket)


if __name__ == "__main__":
    logger = logging.getLogger('websockets.server')
    logger.setLevel(logging.ERROR)
    logger.addHandler(logging.StreamHandler())

    asyncio.get_event_loop().run_until_complete(websockets.serve(handler, 'localhost', 6789))
    asyncio.get_event_loop().run_forever()
