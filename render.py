from typing import List, Callable, Dict, Tuple
from pydantic import BaseModel

import re
import functools
from collections import defaultdict, deque

from engine import Sheet, Cell, CellType

class DerivedCellValue(BaseModel):
    output: str
    input: List[str] = None

class UICell(BaseModel):
    value: str
    row: int
    col: str
    displayValue: DerivedCellValue = None

class Dimension(BaseModel):
    rows: int
    cols: int

class Renderer:

    def _deriveValue(self, sheet: Sheet, cell: Cell, res: Dict[Tuple[int, int], UICell]) -> str:
        matcher = re.compile(r'=(SUM|MUL|AVG)\((.*)\)')
        op, args = matcher.match(cell.value).groups()

        cells = []
        for arg in args.split(','):
            cell_index = arg.strip()
            row, col = self._parse_dependencies([cell_index])[0]

            cells.append(int(res[(row, col)].displayValue.output))


        if op == 'SUM':
            return str(functools.reduce(lambda a, b: a+b, cells))
        elif op == 'MUL':
            return str(functools.reduce(lambda a, b: a*b, cells))
        elif op == 'AVG':
            values = list(cells)
            
            summation = sum(values)
            length = len(values)
            
            return "{:.2f}".format(summation/length)
        else:
            raise Exception("Unknown Formula Provided")

    def _displayValueFactory(self, sheet: Sheet, cell: Cell = None) -> DerivedCellValue:
        if not cell:
            return DerivedCellValue(output='')

        if cell.type == CellType.primitive:
            return DerivedCellValue(output=cell.value)

        if cell.type == CellType.formula:
            return DerivedCellValue(output=self._deriveValue(sheet, cell))

    def _calculate_dimension(self, sheet: Sheet) -> Dimension:
        rows = []
        cols = []
        
        matcher = re.compile(r'(\w.*?)(\d.*)')
        for key in sheet.cells.keys():
            
            col, row = matcher.match(key).groups()
            rows.append(int(row))
            cols.append(col)

        return Dimension(
            rows=max(rows),
            cols=ord(sorted(cols)[-1]) - ord('a') + 1
        )

    def _parse_dependencies(self, cell_indexes: List[str]) -> List[Tuple[int, int]]:
        res = []

        matcher = re.compile(r'(\w.*?)(\d.*)')
        for cell_index in cell_indexes:
            cell_index = cell_index.strip()
            col, row = matcher.match(cell_index).groups()
            row, col = int(row) - 1, ord(col) - ord('a')

            res.append((row, col))
        
        return res

    def _topological_sort(self, sheet: Sheet, rows: int, cols: int) -> Dict[Tuple[int, int], UICell]:
        graph = defaultdict(lambda: [])

        in_degrees = defaultdict(lambda: 0)
        q = deque()
        for r in range(rows):
            for c in range(cols):
                letter = chr(c + 97)
                index = f"{letter}{r + 1}"
                cell = sheet.cells[index]

                if cell.type == CellType.primitive:
                    q.append((r, c))
                else:
                    matcher = re.compile(r'=(SUM|MUL|AVG)\((.*)\)')
                    op, args = matcher.match(cell.value).groups()

                    deps = self._parse_dependencies(args.split(','))
                    for dep in deps:
                        dep_r, dep_c = dep
                        
                        graph[(dep_r, dep_c)].append((r, c))
                        in_degrees[(r, c)] += 1
        
        res = {}

        while q:
            r, c = q.popleft()

            letter = chr(c + 97)
            index = f"{letter}{r + 1}"
            cell = sheet.cells[index]
            
            output = cell.value
            if cell.type == CellType.formula:
                output = self._deriveValue(sheet, cell, res)
            
            res[(r, c)] = UICell(
                value=cell.value,
                row=r + 1,
                col=letter,
                displayValue=DerivedCellValue(output=output)
            )

            for dep in graph[(r, c)]:
                dep_r, dep_c = dep

                in_degrees[(dep_r, dep_c)] -= 1
                if in_degrees[(dep_r, dep_c)] == 0:
                    q.append((dep_r, dep_c))
                    del in_degrees[(dep_r, dep_c)]
        
        if len(in_degrees):
            raise Exception("There is a cycle")
        
        return res
            
    def render(self, sheet: Sheet) -> List[List[UICell]]:
        dimension = self._calculate_dimension(sheet)
        rows, cols = dimension.rows, dimension.cols

        cells_to_ui_cells = self._topological_sort(sheet, rows, cols)

        rendered = []
        for r in range(rows):
            row = []
            for c in range(cols):
                row.append(cells_to_ui_cells[(r, c)])
            rendered.append(row)
        
        return rendered

def test():

    # Setup
    sheet = Sheet(
        cells={
            'a1': Cell(value='1', type=CellType.primitive),
            'a2': Cell(value='2', type=CellType.primitive),
            'b1': Cell(value='3', type=CellType.primitive),
            'b2': Cell(value='=AVG(a1, a2)', type=CellType.formula)
        }
    )

    renderer = Renderer()
    
    # Test 1: Testing Dimension Calculation

    expected_dimension = Dimension(
        cols=2,
        rows=2
    )
    actual_dimension = renderer._calculate_dimension(sheet)


    assert expected_dimension == actual_dimension

    # Test 2: Testing Renderer

    expected_uicells = [
        [UICell(value='1', row=1, col='a', displayValue=DerivedCellValue(output='1')), UICell(value='3', row=1, col='b', displayValue=DerivedCellValue(output='3'))],
        [UICell(value='2', row=2, col='a', displayValue=DerivedCellValue(output='2')), UICell(value='=AVG(a1, a2)', row=2, col='b', displayValue=DerivedCellValue(output='1.50'))]
    ]
    actual_uicells = renderer.render(sheet)
    assert expected_uicells == actual_uicells


if __name__ == '__main__':
    test()