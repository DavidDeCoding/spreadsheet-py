import tkinter as tk
import tk_tools
import random

from render import Renderer
from engine import Sheet, Cell, CellType


class UI:

    def __init__(self, root: tk.Tk):
        self.root = root

        self.cols = 3
        self.rows = 3

        cells = {}
        for row in range(self.rows):
            for col in range(self.cols):
                cells[f"{chr(ord('a') + row)}{col + 1}"] = Cell(value='', type=CellType.primitive)

        self.sheet = Sheet(cells=cells)
        self.renderer = Renderer()

    def render(self):
        self.entry_grid = tk_tools.EntryGrid(self.root, self.cols)
        for _ in range(self.rows):
            self.entry_grid.add_row()
        self.entry_grid.grid(row=0, column=0, sticky='ew')

        self.add_row_btn = tk.Button(self.root, text='Calculate', command=self.re_render)
        self.add_row_btn.grid(row=1, column=0, columnspan=2, sticky='ew')

    def _parse_cell_type(self, cell_data) -> CellType:
        cell_type = CellType.primitive
        for ch in cell_data:
            if ch == ' ':
                continue
            
            if ch != '=':
                break
            else:
                cell_type = CellType.formula
                break
        
        return cell_type

    def re_render(self):
        data = self.entry_grid.read(as_dicts=False)

        for col in range(len(data)):
            for row in range(len(data[0])):
                cell_type = self._parse_cell_type(data[row][col])
                self.sheet.cells[f"{chr(ord('a') + col)}{row + 1}"] = Cell(value=data[row][col], type=cell_type)

        grid = self.renderer.render(self.sheet)

        new_data = [['' for _ in range(len(data[0]))] for _ in range(len(data))]
        for row in range(len(data)):
            for col in range(len(data[0])):
                new_data[row][col] = grid[row][col].displayValue.output
        
        self.entry_grid.clear()
        
        self.entry_grid = tk_tools.EntryGrid(self.root, len(new_data[0]))
        for row in range(len(new_data)):
            self.entry_grid.add_row(new_data[row])
        self.entry_grid.grid(row=0, column=0, sticky='ew')

if __name__ == '__main__':

    root = tk.Tk()

    # read_btn = tk.Button(root, text='Read', command=read)
    # read_btn.grid(row=3, column=0, columnspan=2, sticky='ew')

    # entry_grid = tk_tools.EntryGrid(root, 3)
    # entry_grid.add_row()
    # entry_grid.add_row()
    ui = UI(root)
    ui.render()

    root.mainloop()