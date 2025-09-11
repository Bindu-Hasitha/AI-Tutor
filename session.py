import uuid
import os

def get_session():
    new_uuid = uuid.uuid4()
    session_id = str(new_uuid)
    return session_id


def get_request_id():
    random_bytes = os.urandom(24)
    request_id = random_bytes.hex()
    return request_id


if __name__ == "__main__":
    sid = get_request_id()
    print(sid)