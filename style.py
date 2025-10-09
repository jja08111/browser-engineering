from typing import Literal, Type

DEFAULT_STYLE = "roman"

Style = Type[Literal[DEFAULT_STYLE] | Literal["italic"]]
