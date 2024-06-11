from enum import Enum
from typing import Dict

from pydantic import BaseModel

class CellType(str, Enum):
    primitive = 'primitive'
    formula = 'formula'

class Cell(BaseModel):
    value: str
    type: CellType

class Sheet(BaseModel):
    cells: Dict[str, Cell]

def test():
    sheet = Sheet(
        cells={
            'a1': Cell(value='1', type=CellType.primitive),
            'a2': Cell(value='2', type=CellType.primitive),
            'b1': Cell(value='3', type=CellType.primitive),
            'b2': Cell(value='=SUM(a1, a2)', type=CellType.formula)
        }
    )

if __name__ == "__main__":
    test()