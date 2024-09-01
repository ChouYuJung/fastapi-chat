from numbers import Number
from typing import Dict, List, Text, TypeVar, Union

T = TypeVar("T", bound="JSONSerializable")


JSONSerializable = Union[Dict[Text, T], List[T], Text, Number, bool, None]
