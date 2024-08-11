import contextlib
import json
from io import StringIO


@contextlib.contextmanager
def uncloseable(fd):
    """Context manager which turns the fd's close operation to no-op
    for the duration of the context"""
    close = fd.close
    fd.close = lambda: None
    yield fd
    fd.close = close

    # Go back to the beginning of the buffer so that we can read from the start again
    fd.seek(0)


myfile = StringIO()

with uncloseable(myfile) as f:
    json.dump({"asdf": 1}, f)

with uncloseable(myfile) as f:
    obj = json.load(f)
    print(obj)

# myfile.write("asdf2")
# print(myfile.read())
