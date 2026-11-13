# Copyright (c) 2026 Devansh Lodha
# SPDX-License-Identifier: MIT

"""Independent runs spread across all cores."""

import os
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def parallel_map[T, R](task: Callable[[T], R], items: list[T]) -> list[R]:
    """The task applied to each item, in order, spread across all cores."""
    # About four chunks per core balance the load against the cost of sending work.
    chunk = max(1, len(items) // (4 * (os.process_cpu_count() or 1)))
    with ProcessPoolExecutor() as pool:
        return list(pool.map(task, items, chunksize=chunk))
