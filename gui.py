import pandas as pd
import tkinter as tk
from tkinter import ttk

class DataFrameGUI(tk.Tk):
    def __init__(self, dataframe):
        super().__init__()

        self.title("DataFrame GUI")

        # Create a Treeview widget to display the DataFrame
        self.tree = ttk.Treeview(self)
        self.tree["columns"] = list(dataframe.columns)
        self.tree["show"] = "headings"

        # Add column headers
        for column in dataframe.columns:
            self.tree.heading(column, text=column, command=lambda c=column: self.sort_column(c, dataframe))

        # Add data to the Treeview with centered alignment
        for index, row in dataframe.iterrows():
            values = list(row)
            self.tree.insert("", "end", values=values, tags="centered")

        # Configure the Treeview columns for centered alignment
        for column in dataframe.columns:
            self.tree.column(column, anchor="center")

        # Pack the Treeview
        self.tree.pack(expand=tk.YES, fill=tk.BOTH)

    def sort_column(self, column, dataframe):
        """Sort the DataFrame based on the clicked column."""
        data = dataframe.sort_values(by=column)
        self.tree.delete(*self.tree.get_children())

        for index, row in data.iterrows():
            values = list(row)
            self.tree.insert("", "end", values=values, tags="centered")

if __name__ == "__main__":
    # Example DataFrame
    data = {'Name': ['Alice', 'Bob', 'Charlie', 'David'],
            'Age': [25, 30, 22, 35],
            'Salary': [50000, 60000, 45000, 70000]}

    df = pd.DataFrame(data)

    # Create and run the GUI
    app = DataFrameGUI(df)
    app.mainloop()