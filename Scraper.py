import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate


def show_data(data, headers):
    print(tabulate(data, headers=headers, tablefmt="pretty"))


def show_gui(data, headers):
    root = tk.Tk()
    root.title("Scraped Data Table")

    tree = ttk.Treeview(root)
    tree["columns"] = headers

    for col in tree["columns"]:
        tree.column(col, anchor=tk.W, width=100)
        tree.heading(col, text=col, anchor=tk.W)

    for row in data:
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()


def _find_tables_with_name(soup, tables_name):
    tgju_widgets = soup.find_all('div', class_='tgju-widget')

    for widget in tgju_widgets:

        if tables_name == "عملکرد دلار":
            title_div = widget.find('div', class_='tgju-widget-title')
            title = title_div.find('h2') if title_div else None
            if title:
                table = widget.find('table', class_='table')
                a = title.text.strip()
                b = tables_name in title.text.strip()
                if table and tables_name in title.text.strip():
                    return table
        else:
            title = widget.find('h2')

            if title:
                table = widget.find('table', class_='table')
                if table and tables_name in title.text.strip():
                    return table


class Scraper:
    def __init__(self):

        self.user_agent = "User-Agent String"
        self.headers = {"User-Agent": self.user_agent}
        self.data_dpa = []
        self.data_dp = []
        self.data_dt = []
        self.data_dpag = []
        self.last_update = None
        self.force_reload = False

        self.p2e_table_names_map = {
            "عملکرد دلار": "Dollar Performance",
            "دلار در یک نگاه": "Dollar at a Glance",
            "تاریخچه دلار": "Dollar Price Archive",
            "دلار در روز جاری": "Dollar Today",
        }
        self.urls = {
            "Dollar at a Glance": "https://www.tgju.org/profile/price_dollar_rl",
            "Dollar Price Archive": "https://www.tgju.org/profile/price_dollar_rl/history",
            "Dollar Today": "https://www.tgju.org/profile/price_dollar_rl/today",
            "Dollar Performance": "https://www.tgju.org/profile/price_dollar_rl/performance",
        }
        self.p2e_dpa_col_names_map = {
            "بازگشایی": "Opening",
            "کمترین": "Minimum",
            "بیشترین": "Maximum",
            "پایانی": "Closing",
            "میزان تغییر": "Change Amount",
            "درصد تغییر": "Percentage Change",
            "تاریخ / میلادی": "Date Miladi",
            "تاریخ / شمسی": "Date Shamsi",
        }
        self.p2e_dp_col_names_map = {
            "نام": "Name",
            "روز": "Day",
            "یک هفته": "One Week",
            "یک ماه": "One Month",
            "شش ماه": "Six Months",
            "یک سال": "One Year",
            "سه سال": "Three Years",
        }
        self.p2e_dt_col_names_map = {
            "قیمت": "Price",
            "زمان": "Time",
            "مقدار تغییر نسبت به نرخ قبلی": "Change Amount Relative to Previous Rate",
            "درصد تغییر نسبت به نرخ قبلی": "Percentage Change Relative to Previous Rate",
            "مقدار تغییر نسبت به نرخ روز گذشته": "Change Amount Relative to Previous Day Rate",
            "درصد تغییر نسبت نرخ روز گذشته": "Percentage Change Relative to Previous Day Rate",
            "مقدار تغییر نسبت به نرخ بازگشایی": "Change Amount Relative to Opening Rate",
            "درصد تغییر نسبت نرخ بازگشایی": "Percentage Change Relative to Opening Rate",
            "مقدار تغییر نسبت به بالاترین نرخ هفته": "Change Amount Relative to Highest Weekly Rate",
            "مقدار تغییر نسبت به میانگین نرخ هفته": "Change Amount Relative to Weekly Average Rate",
        }
        self.p2e_dpag_col_names_map = {
            # "خصیصه": "Attribute",
            "نرخ فعلی": "Current Rate",
            "بالاترین قیمت روز": "Highest Daily Price",
            "پایین ترین قیمت روز": "Lowest Daily Price",
            "بیشترین مقدار نوسان روز": "Maximum Daily Fluctuation",
            "درصد بیشترین نوسان روز": "Percentage of Maximum Daily Fluctuation",
            "نرخ بازگشایی بازار": "Market Opening Rate",
            "زمان ثبت آخرین نرخ": "Last Rate Registration Time",
            "نرخ روز گذشته": "Previous Day Rate",
            "درصد تغییر نسبت به روز گذشته": "Percentage Change Compared to Previous Day",
            "میزان تغییر نسبت به روز گذشته": "Amount of Change Compared to Previous Day",
        }
        self.persian_to_english_digit_map = {
            '۰': '0',
            '۱': '1',
            '۲': '2',
            '۳': '3',
            '۴': '4',
            '۵': '5',
            '۶': '6',
            '۷': '7',
            '۸': '8',
            '۹': '9'
        }

    def set_force_reload(self, value):
        self.force_reload = value
    def scrape(self):
        english_to_persian_map = {value: key for key, value in self.p2e_table_names_map.items()}
        for tables_name in self.p2e_table_names_map.values():

            url = self.urls[tables_name]
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                soup = BeautifulSoup(response.content, 'html.parser')

                table = _find_tables_with_name(soup, english_to_persian_map[tables_name])

                # Extracting data from the table
                if table and tables_name == "Dollar Price Archive":

                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    for row in rows:
                        cols = row.find_all('td')
                        cols = [ele.text.strip() for ele in cols]

                        # Extracting values with their signs
                        change_span_pos = row.find('span', {'class': 'high'})
                        if change_span_pos:
                            change = change_span_pos.text.strip()
                            cols[4] = '+' + str(change)
                            change_span_pos.decompose()

                        percent_span_pos = row.find('span', {'class': 'high'})
                        if percent_span_pos:
                            percent = percent_span_pos.text.strip()
                            cols[5] = '+' + str(percent)

                        change_span_neg = row.find('span', {'class': 'low'})
                        if change_span_neg:
                            change = change_span_neg.text.strip()
                            cols[4] = '-' + str(change)
                            change_span_neg.decompose()

                        percent_span_neg = row.find('span', {'class': 'low'})
                        if percent_span_neg:
                            percent = percent_span_neg.text.strip()
                            cols[5] = '-' + str(percent)

                        self.data_dpa.append(cols)
                    self._save_to_database(self.data_dpa, "dpa")


                elif table and tables_name == "Dollar at a Glance":

                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    values = []
                    for row in rows:
                        cols = row.find_all('td')
                        cols_values = [ele.text.strip() for ele in cols]
                        cols_values[1] = cols_values[1]

                        text_left = row.find('td', {'class': 'text-left'})
                        pos_sign = text_left.find('span', {'class': 'high'})
                        if pos_sign:
                            cols_values[1] = '+' + str(cols_values[1])
                        neg_sign = text_left.find('span', {'class': 'low'})
                        if neg_sign:
                            cols_values[1] = '-' + str(cols_values[1])
                        # Convert string numbers to double
                        values.append(cols_values[1])

                    values[6] = ''.join(
                        self.persian_to_english_digit_map.get(char, char) for char in values[6])
                    # Add the date to the Time column
                    values[6] = f"{datetime.now().strftime('%Y-%m-%d')}"
                    self.data_dpag.append(values)
                    self._save_to_database(self.data_dpag, "dpag")


                elif table and tables_name == "Dollar Today":

                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    for row in rows:
                        cols = row.find_all('td')
                        for col in cols:
                            col_value = col.text.strip()
                            pos_sign = col.find('span', {'class': 'high'})
                            neg_sign = col.find('span', {'class': 'low'})
                            if pos_sign:
                                col_value = '+' + str(col_value)
                            if neg_sign:
                                col_value = '-' + str(col_value)
                            cols[cols.index(col)] = col_value

                        # Add the date to the Time column
                        cols[1] = f"{datetime.now().strftime('%Y-%m-%d')}_{cols[1]}"

                        self.data_dt.append(cols)
                    self._save_to_database(self.data_dt, "dt")

                elif table and tables_name == "Dollar Performance":

                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    for row in rows:
                        cols = row.find_all('td')
                        cols_values = [ele.text.strip() for ele in cols]

                        # Convert string numbers to double
                        for i in [1, 2, 3, 4, 5, 6]:

                            pos_sign = cols[i].find('span', {'class': 'high'})
                            if pos_sign:
                                cols_values[i] = '+' + str(cols_values[i])
                            neg_sign = cols[i].find('span', {'class': 'low'})
                            if neg_sign:
                                cols_values[i] = '-' + str(cols_values[i])

                        # Add the date to the Time column
                        cols_values[0] = f"{datetime.now().strftime('%Y-%m-%d')}_{cols_values[0]}"
                        self.data_dp.append(cols_values)
                    self._save_to_database(self.data_dp, "dp")

            else:
                print(f"Error: {response.status_code}")
        self.p2e_dpa_col_names_map['inserted_time'] = 'Inserted Time'
        self.p2e_dp_col_names_map['inserted_time'] = 'Inserted Time'
        self.p2e_dt_col_names_map['inserted_time'] = 'Inserted Time'
        self.p2e_dpag_col_names_map['inserted_time'] = 'Inserted Time'

    def _save_to_database(self, data, table_name):
        conn = sqlite3.connect('scraper_data.db')
        cursor = conn.cursor()

        # Get the column names based on the table_name
        col_names_map = getattr(self, f"p2e_{table_name.lower()}_col_names_map", None)
        if not col_names_map:
            print(f"Error: Column names map not found for {table_name}.")
            return

        col_names_with_underscores = [col.replace(' ', '_') for col in col_names_map.values()]
        col_names_with_underscores.append('time_inserted')

        # Create a table if it doesn't exist
        col_definitions = ', '.join([f"{col.replace(' ', '_')} TEXT" for col in col_names_map.values()])
        col_definitions += ', time_inserted TEXT'
        primary_key = None

        if table_name == "dt":
            primary_key = "Time"
        elif table_name == "dp":
            primary_key = "Name"
        elif table_name == "dpa":
            primary_key = "Date_Shamsi"
        elif table_name == "dpag":
            primary_key = "Last_Rate_Registration_Time"

        if primary_key:

            cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {col_definitions},
                        PRIMARY KEY ({primary_key})
                    )
                ''')
        else:
            cursor.execute(f'''
                                CREATE TABLE IF NOT EXISTS {table_name} (
                                    {col_definitions},
                                    PRIMARY KEY (time_inserted)
                                )
                            ''')

        # Insert new data into the table or update existing data
        for row in data:

            # Add the time_inserted column
            row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Check if the row already exists based on the primary key
            if primary_key:
                primary_key_values = primary_key.split(',')
                if len(primary_key_values) == 1:
                    primary_key_values = (primary_key_values[0],)  # Convert to a tuple for consistency
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE {primary_key.replace(' ', '_')} LIKE ?",
                    (f'%{row[col_names_with_underscores.index(primary_key_values[0])]}%',)
                )
            else:
                cursor.execute(f'SELECT * FROM {table_name} WHERE time_inserted = ?', (row[-1],))

            existing_row = cursor.fetchone()
            if existing_row:
                # Update existing row if it's a duplicate
                set_columns = ', '.join([f"{col.replace(' ', '_')} = ?" for col in col_names_map.values()])
                cursor.execute(f'''
                    UPDATE {table_name}
                    SET {set_columns}, time_inserted = ?
                    WHERE {primary_key.replace(" ", "_")} = ?
                ''', (*row[:-1], row[-1], row[col_names_with_underscores.index(primary_key_values[0])]))
            else:
                # Insert new row if it's not a duplicate
                if primary_key:
                    placeholders = ", ".join(["?" for _ in row])
                    cursor.execute(f'INSERT INTO {table_name} VALUES ({placeholders})', row)
                else:
                    cursor.execute(f'INSERT INTO {table_name} VALUES ({", ".join(["?" for _ in row])})', row)

        conn.commit()
        conn.close()
        print(f"Data saved to database for {table_name}.")

    def load_from_database(self):
        self.data_dpa = self._load_table_from_database("dpa")
        self.data_dp = self._load_table_from_database("dp")
        self.data_dt = self._load_table_from_database("dt")
        self.data_dpag = self._load_table_from_database("dpag")

        self.data_dpa = sorted(self.data_dpa, key=lambda row: row[7], reverse=True)
        self.data_dp = [self.data_dp[-1]]
        self.data_dt = sorted(self.data_dt, key=lambda row: row[1])
        self.data_dpag = [self.data_dpag[-1]]

        print(f"{len(self.data_dpa)} rows loaded from database for dpa.")
        print(f"{len(self.data_dp)} rows loaded from database for dp.")
        print(f"{len(self.data_dt)} rows loaded from database for dt.")
        print(f"{len(self.data_dpag)} rows loaded from database for dpag.")

    def _load_table_from_database(self, table_name):
        conn = sqlite3.connect('scraper_data.db')
        cursor = conn.cursor()

        col_names_map = getattr(self, f"p2e_{table_name.lower()}_col_names_map", None)
        if not col_names_map:
            print(f"Error: Column names map not found for {table_name}.")
            return []

        col_names_with_underscores = [col.replace(' ', '_') for col in col_names_map.values()]

        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append([*row])

        conn.close()
        return data

    def show_data(self):

        show_data(self.data_dpa, self.p2e_dpa_col_names_map.values())

        reversed_map = {value: key for key, value in self.p2e_dp_col_names_map.items()}
        show_data(self.data_dp, reversed_map.values())
        show_data(self.data_dt, self.p2e_dt_col_names_map.values())
        show_data(self.data_dpag, self.p2e_dpag_col_names_map.values())
