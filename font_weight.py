from typing import Literal, Type

DEFAULT_WEIGHT = "normal"

Weight = Type[Literal[DEFAULT_WEIGHT] | Literal["bold"]]
