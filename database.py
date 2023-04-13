import sqlite3
from datetime import date

class database:
    def __init__(self) -> None:
        self.create_tables_if_not_exists()

    def search_items(self, query) -> list:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute("SELECT item.*, item_fts.rank FROM item JOIN item_fts ON item.id = item_fts.id WHERE item_fts.name MATCH ? ORDER BY item_fts.rank", (query,))
        results = cursor.fetchall()

        print(f"Search results for '{query}':")
        for result in results:
            print(f"ID: {result[0]}, Name: {result[1]}, Row: {result[3]}, Col: {result[4]} Relevance Score: {result[-1]}")

        conn.close()

        return results

    def add_or_update_item(self, item_name, additional_quantity) -> None:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        # Check if the item already exists
        cursor.execute("SELECT * FROM item WHERE name = ?", (item_name,))
        item = cursor.fetchone()

        if item:
            # Item exists, update its quantity
            new_quantity = item[2] + additional_quantity
            cursor.execute("UPDATE item SET quantity = ?, date_updated = ? WHERE name = ?",
                        (new_quantity, date.today(), item_name))
        else:
            # Item does not exist, find the next available row and column
            # Query all rows and columns in the item table
            cursor.execute("SELECT row, col FROM item")
            occupied_positions = cursor.fetchall()

            # Determine the minimum available row and column
            occupied_positions_set = set(occupied_positions)
            if len(occupied_positions_set) > 0:
                max_row = max([pos[0] for pos in occupied_positions])
                max_col = max([pos[1] for pos in occupied_positions])
            else:
                max_row, max_col = 0, 0

            next_row, next_column = None, None
            for row in range(1, min(max_row + 2, 8)):
                for col in range(1, min(max_col + 2, 16)):
                    if (row, col) not in occupied_positions_set:
                        next_row, next_column = row, col
                        break
                if next_row is not None:
                    break

            if next_row == None or next_column == None:
                raise Exception("There is no remaining space in the organizer!")
            
            print(f"Inserting item '{item_name}' at [{next_row}, {next_column}]")

            # Insert the new item with the given quantity at the next available row and column
            cursor.execute("""
                INSERT INTO item (name, quantity, row, col, date_created, date_updated)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (item_name, additional_quantity, next_row, next_column, date.today(), date.today()))
            
            cursor.execute("""
                INSERT INTO item_fts (id, name)
                VALUES (?, ?)
                """, (cursor.lastrowid, item_name))

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

    def delete_items(items) -> None:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        for item in items:
            cursor.execute(f"DELETE FROM item WHERE name=?", (item,))

            if cursor.rowcount > 0:
                print(f"'{item}' deleted from the item table.")
            else:
                print(f"'{item}' not found in the item table.")

            cursor.execute(f"DELETE FROM item_fts WHERE name=?", (item,))
            
            if cursor.rowcount > 0:
                print(f"'{item}' deleted from the item_fts table.")
            else:
                print(f"'{item}' not found in the item_fts table.")

        conn.commit()
        conn.close()

    def print_tables(self) -> None:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM item")
        items = cursor.fetchall()

        print("Item table:")
        print(f"{'ID':<4} | {'Name':<15} | {'Quantity':<8} | {'Row':<4} | {'Col':<6} | {'Date Created':<12} | {'Date Updated':<16}")
        print("-----------------------------------------------------------------------------")

        for item in items:
            print(f"{item[0]:<4} | {item[1]:<15} | {item[2]:<8} | {item[3]:<4} | {item[4]:<6} | {item[5]:<12} | {item[6]:<16}")

        print()
        print("Item FTS table:")
        cursor.execute("SELECT * FROM item_fts")
        rows = cursor.fetchall()

        if not rows:
            print("The item_fts table is empty.")
        else:
            print(f"{'ID':<4} {'Name':<30}")
            print("-" * 40)
            for row in rows:
                print(f"{row[0]:<4} {row[1]:<30}")

        conn.close()

    def create_tables_if_not_exists(self) -> None:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                row INTEGER NOT NULL,
                col INTEGER NOT NULL,
                date_created DATE NOT NULL,
                date_updated DATE NOT NULL
            )
        """)

        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS item_fts USING fts5(id, name, tokenize='porter');
        """)

        conn.commit()
        conn.close()

    def delete_tables(self) -> None:
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS item")
        cursor.execute("DROP TABLE IF EXISTS item_fts")

        conn.commit()
        conn.close()