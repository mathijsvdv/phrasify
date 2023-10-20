# SPDX-FileCopyrightText: 2023-present Mathijs van der Vlies <mathijsvdvlies@solcon.nl>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from .addition_filter import init_addition_filter
from .card_count_view import init_card_count_view
from .field_filter import init_field_filter


def init_addon():
    init_card_count_view()
    init_field_filter()
    init_addition_filter()


init_addon()
