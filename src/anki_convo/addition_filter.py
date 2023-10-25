import random
import re
from functools import lru_cache

from anki import hooks
from anki.template import TemplateRenderContext

# Possible hooks and filters to use
# from anki.hooks import card_did_render, field_filter

# The filter in the question can be put like {{add-x:1-10}}
# In the answer we can put {{add-x:1-10-answer}} to generate the answer


@lru_cache(maxsize=None)
def cached_randrange(
    start: int,
    stop: int,
    context_id: int,  # noqa: ARG001 context_id is needed because we only want to cache within one card render
) -> int:
    return random.randrange(start, stop)


def addition_filter(
    field_text: str,
    field_name: str,
    filter_name: str,
    context: TemplateRenderContext,
) -> str:
    # add-1-10:5
    # add-1-10-q:5
    # add-1-10-a:5

    # gen-sentence-q:de nada
    # gen-sentence-a:de nada

    if not filter_name.startswith("add-"):
        # not our filter, return string unchanged
        return field_text

    match = re.match(r"add-(?P<start>[0-9]+)-(?P<stop>[0-9]+)(-(?P<qa>[qa]))?", filter_name)

    if match:
        start = int(match.group("start"))
        stop = int(match.group("stop"))
        qa = match.group("qa")
    else:
        return invalid_name(filter_name)

    to_add = cached_randrange(start, stop, context_id=id(context))

    if qa == "q":
        return get_question(field_text, to_add)
    elif qa == "a":
        return get_answer(field_text, to_add, field_name=field_name)

    if context.question_side:
        return get_question(field_text, to_add)
    else:
        return get_answer(field_text, to_add, field_name=field_name)


def invalid_name(filter_name: str) -> str:
    return f"invalid filter name: {filter_name}"


def get_question(field_text, to_add):
    return f"{field_text} + {to_add}"


def get_answer(field_text, to_add, field_name=None):
    if field_text == f"({field_name})":
        # It's just the example text for the field, make a placeholder
        return f"<answer to '{get_question(field_text, to_add)}'>"

    return str(int(field_text) + to_add)


def init_addition_filter():
    # register our function to be called when the hook fires
    hooks.field_filter.append(addition_filter)
