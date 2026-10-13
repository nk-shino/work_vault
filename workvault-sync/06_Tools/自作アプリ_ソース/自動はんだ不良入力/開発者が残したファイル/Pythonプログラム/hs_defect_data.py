#!/usr/bin/env python3.8
# coding: utf_8

# Hand Soldering Defect Data Aggregating_System(HSDS)
# =============================================================================
# 2021/04/01 ver 1.0.0  Release
#                       実装支援課 ものづくり係    N.Okano
# 2021/04/01 ver 1.1.1  Update(データ区分変更など)
#                       実装支援課 ものづくり係    N.Okano)
# 2022/03/01 ver 0.0.1 新規作成 実装支援課 ものづくり係
#                       Parts Picking System(special screen)
# =============================================================================


# ----- import settings -----
import datetime
from datetime import date
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import mysql.connector
import mojimoji
from decimal import Decimal, ROUND_HALF_UP
import csv
import my_font
import os

# ----- setting -----
now = datetime.datetime.now()
today = datetime.date.today()
g_year = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030,
          2031, 2032, 2033, 2034, 2035]
g_month = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
g_day = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
         11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
         21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
         31]
g_rate = ["", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
g_input_order_number = "000000000"
g_preprocessing_p_date = ""
g_input_employee_name = ""
g_ordernumber_information_result = ["000000000", "UR-0000", "0"]  # [orderNumber, typeID, orderQty]
g_duplicate_result = ""
g_d_duplicate_check = ""
g_d_process = ""
g_d_solder = ""
g_d_insertion_point = 0
g_d_multiple = 0

# ----- database1 setting -----
g_db1_u = 'no13792'
g_db1_pw = 'no13792'
g_db1_host = 'nksv560.ad.nkc.co.jp'
g_db1_db = 'test'


# ----- SQL(existence check) -----
def existence_check(table, count_column, parameter):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        if parameter == "no":
            # ----- existence check(no data is return 0) -----
            query = "SELECT count("
            cur.execute(query + count_column + ") FROM " + table)
            res_query = cur.fetchall()
            return res_query[0][0]
        else:
            # ----- existence check(no data is return 0) -----
            query = "SELECT count("
            cur.execute(query + count_column + ") FROM " + table + " WHERE " + parameter)
            res_query = cur.fetchall()
            return res_query[0][0]

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# ----- SQL(existence check) -----
def existence_check_sasizu_data(sasizu):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        query = "SELECT orderNumber,typeID,process,solder,orderQty,sheet_number,insertion_point FROM T_HSDS_data WHERE orderNumber = '"
        cur.execute(query + sasizu + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# ----- SQL(count check) -----
def sum_result(table, count_column, parameter):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        if parameter == "no":
            # ----- existence check(no data is return 0) -----
            query = "SELECT SUM("
            cur.execute(query + count_column + ") FROM " + table)
            res_query = cur.fetchall()
            return res_query[0][0]
        else:
            # ----- existence check(no data is return 0) -----
            query = "SELECT SUM("
            cur.execute(query + count_column + ") FROM " + table + " WHERE " + parameter)
            res_query = cur.fetchall()
            return res_query[0][0]

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# ----- SQL(data delete) -----
def data_delete(table, parameter):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        query = "DELETE FROM "
        cur.execute(query + table + " WHERE " + parameter)

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# ----- SQL(data delete) -----
def data_select(table, column):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        query = "SELECT "
        cur.execute(query + column + " FROM " + table)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# ----- SQL(data delete) -----
def data_select_where(table, column, parameter):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u, password=g_db1_pw, host=g_db1_host, database=g_db1_db, autocommit=True)
        cur = conn.cursor()

        # ----- parameter check -----
        query = "SELECT "
        cur.execute(query + column + " FROM " + table + " WHERE " + parameter)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "MySQL connector error!")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -employee name-
def get_employee_name():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT employee_name FROM T_HSDS_operator WHERE employee_enrolled = '1'"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -employee number and name-
def get_employee_number_name():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT employee_number,employee_name FROM T_HSDS_operator"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -process-
def get_process():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT process From T_HSDS_process"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -solder-
def get_solder():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT solder FROM T_HSDS_solder"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -symptom-
def get_symptom():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT id,defect_symptom FROM T_HSDS_defect_symptom"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -defect symptom-
def get_defect_symptom():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT id,symptom FROM T_HSDS_symptom"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -symbol-
def get_symbol(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT symbol FROM T_HSDS_symbol WHERE typeID = '"
        cur.execute(query + typeid + "'" + "ORDER BY symbol")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -remark-
def get_remark():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT remark FROM T_HSDS_remark"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -parts_number-
def get_parts_number():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT part_number FROM T_HSDS_symbol ORDER BY part_number"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# combobox -typeid-
def get_combo_typeid():
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT typeID FROM T_HSDS_symbol ORDER BY typeID DESC"
        cur.execute(query)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# change to employee number by employee name
def get_employee_number(employee_name):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT employee_number FROM T_HSDS_operator WHERE employee_name ="
        cur.execute(query + "'" + employee_name + "'")
        res_query = cur.fetchone()
        return res_query[0]

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "社員番号が見つかりませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# Duplicate check -orderNumber-
def get_duplicate_check(order_number):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT f_date FROM T_HSDS_data WHERE orderNumber = '"
        cur.execute(query + order_number + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "初登録日を取得出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# get p_date(duplicate)
def get_d_preprocessing_p_date(order_number):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT f_date FROM T_HSDS_data WHERE orderNumber ='"
        cur.execute(query + order_number + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "初登録日を取得出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# get orderNumber information
def get_ordernumber_information(table_name, order_number):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT orderNumber,typeID,orderQty FROM "
        cur.execute(query + table_name + " WHERE orderNumber = '" + order_number + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error:
        return

    finally:
        cur.close()
        conn.close()


# get process data
def get_d_process(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT process FROM T_HSDS_typeID WHERE typeID = "
        cur.execute(query + "'" + typeid + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "工程情報を取得出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# get solder data
def get_d_solder(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT solder FROM T_HSDS_typeID where typeID ="
        cur.execute(query + "'"  + typeid + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# get insertion point data
def get_d_insertion_point(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT SnS1_surface FROM T_HSDS_typeID WHERE typeID ="
        cur.execute(query + "'" + typeid  + "'")
        res_query = cur.fetchone()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()


# get multiple(sheet) data
def get_d_multiple(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT multiple FROM T_HSDS_typeID WHERE typeID ="
        cur.execute(query + "'" + typeid + "'")
        res_query = cur.fetchone()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# part number search
def d_part_number_check(typeid, symbol):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT part_number FROM test.T_HSDS_symbol WHERE typeID = '"
        cur.execute(query
                    + typeid + "' and symbol = '"
                    + symbol + "'")
        res_query = cur.fetchone()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# write defect data to database(no defect)
def no_defect_data_registration(p_date, f_date, order_number, typeid, orderqty, employee_number, process, solder,
                                point, sheet_number, danger_alarm):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "INSERT INTO T_HSDS_data (" \
                "p_date," \
                "f_date," \
                "orderNumber," \
                "typeID," \
                "orderQty," \
                "employee_number," \
                "process," \
                "solder," \
                "defect_symptom," \
                "defect_symbol," \
                "defect_number," \
                "defect_remark," \
                "no_defect," \
                "insertion_point," \
                "sheet_number," \
                "danger_alarm)" \
                "values ("
        cur.execute(query + "'"
                    + p_date + "','"
                    + f_date + "','"
                    + order_number + "','"
                    + typeid + "','"
                    + orderqty + "','"
                    + employee_number + "','"
                    + process + "','"
                    + solder + "', '', '', '0', '', 'no defects','"
                    + str(point) + "','"
                    + str(sheet_number) + "','"
                    + str(danger_alarm) + "')")
        conn.commit()

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# write defect data to database(a defect)
def defect_data_registration(p_date, f_date, order_number, typeid, orderqty, employee_number, process, solder,
                             symptom, symbol, defect_number, remark, point, sheet_number, danger_alarm, d_part_number):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "INSERT INTO T_HSDS_data (" \
                "p_date," \
                "f_date," \
                "orderNumber," \
                "typeID," \
                "orderQty," \
                "employee_number," \
                "process," \
                "solder," \
                "defect_symptom," \
                "defect_symbol," \
                "defect_number," \
                "defect_remark," \
                "insertion_point," \
                "sheet_number," \
                "danger_alarm," \
                "defect_part_number)" \
                " values ("
        print(query + "'"
                    + p_date + "','"
                    + f_date + "','"
                    + order_number + "','"
                    + typeid + "','"
                    + orderqty + "','"
                    + employee_number + "','"
                    + process + "','"
                    + solder + "','"
                    + symptom + "','"
                    + symbol + "','"
                    + defect_number + "','"
                    + remark + "','"
                    + str(point) + "','"
                    + str(sheet_number) + "','"
                    + str(danger_alarm) + "','"
                    + str(d_part_number) + "')")
        cur.execute(query + "'"
                    + p_date + "','"
                    + f_date + "','"
                    + order_number + "','"
                    + typeid + "','"
                    + orderqty + "','"
                    + employee_number + "','"
                    + process + "','"
                    + solder + "','"
                    + symptom + "','"
                    + symbol + "','"
                    + defect_number + "','"
                    + remark + "','"
                    + str(point) + "','"
                    + str(sheet_number) + "','"
                    + str(danger_alarm) + "','"
                    + str(d_part_number) + "')")
        conn.commit()

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_worst_list_csv(search_day, start_day, end_day, process, process2, symptom, solder):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT f_date,orderNumber,typeID,orderQty,T_HSDS_operator.employee_name,process,solder,T_HSDS_defect_symptom.defect_symptom,defect_symbol,defect_part_number,SUM(defect_number),defect_remark FROM T_HSDS_data LEFT OUTER JOIN T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id LEFT OUTER JOIN T_HSDS_operator ON T_HSDS_data.employee_number = T_HSDS_operator.employee_number WHERE "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "'AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + symptom + " "
                    + solder
                    + " GROUP BY f_date,orderNumber,typeID,orderQty,T_HSDS_data.employee_number,process,solder,defect_symptom,defect_symbol,defect_part_number,defect_remark ORDER BY SUM(defect_number) DESC")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_worst_list(search_day, start_day, end_day, process, process2, symptom, solder):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT typeID,process,T_HSDS_defect_symptom.defect_symptom,defect_symbol,defect_part_number,SUM(defect_number),defect_remark FROM T_HSDS_data LEFT OUTER JOIN T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id WHERE defect_number > 0 AND "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "' AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + symptom + " "
                    + solder
                    + " GROUP BY typeID,process,defect_symptom,defect_symbol,defect_part_number,defect_remark ORDER BY SUM(defect_number) DESC")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_sasizu_worst_list_csv(sasizu):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT p_date,typeID,T_HSDS_operator.employee_name,defect_symbol,T_HSDS_defect_symptom.defect_symptom,defect_number,defect_remark FROM T_HSDS_data LEFT OUTER JOIN T_HSDS_operator ON T_HSDS_data.employee_number = T_HSDS_operator.employee_number LEFT OUTER JOIN T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id WHERE orderNumber = '"
        cur.execute(query + sasizu + "' ORDER BY defect_symbol")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_sasizu_worst_list(sasizu):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT p_date,typeID,T_HSDS_operator.employee_name,defect_symbol,T_HSDS_defect_symptom.defect_symptom,defect_number,defect_remark FROM T_HSDS_data LEFT OUTER JOIN T_HSDS_operator ON T_HSDS_data.employee_number = T_HSDS_operator.employee_number LEFT OUTER JOIN T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id WHERE orderNumber = '"
        cur.execute(query + sasizu + "' ORDER BY defect_symbol")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_typeid_worst_list_csv(start_day, end_day, typeid, symptom, symbol, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT typeID,T_HSDS_operator.employee_name,process,T_HSDS_defect_symptom.defect_symptom,defect_symbol,defect_part_number,SUM(defect_number),defect_remark FROM test.T_HSDS_data LEFT OUTER JOIN test.T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id LEFT OUTER JOIN test.T_HSDS_operator ON T_HSDS_data.employee_number = T_HSDS_operator.employee_number WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + symptom
                    + symbol
                    + employee
                    + " GROUP BY typeID,T_HSDS_operator.employee_name,process,defect_symptom,defect_symbol,defect_part_number,defect_remark ORDER BY SUM(defect_number) DESC")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# worst list
def get_defect_typeid_worst_list(start_day, end_day, typeid, symptom, symbol, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT typeID,T_HSDS_operator.employee_name,process,T_HSDS_defect_symptom.defect_symptom,defect_symbol,defect_part_number,SUM(defect_number),defect_remark FROM test.T_HSDS_data LEFT OUTER JOIN test.T_HSDS_defect_symptom ON T_HSDS_data.defect_symptom = T_HSDS_defect_symptom.id LEFT OUTER JOIN test.T_HSDS_operator ON T_HSDS_data.employee_number = T_HSDS_operator.employee_number WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + symptom
                    + symbol
                    + employee
                    + " GROUP BY typeID,T_HSDS_operator.employee_name,process,defect_symptom,defect_symbol,defect_part_number,defect_remark ORDER BY SUM(defect_number) DESC")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# production volume
def get_production_volume(search_day, start_day, end_day, process, process2, solder):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,orderQty FROM T_HSDS_data WHERE "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "' AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + solder)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# production volume
def get_typeid_production_volume(start_day, end_day, typeid, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,orderQty FROM T_HSDS_data WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + employee)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# production sheet volume
def get_production_sheet_volume(search_day, start_day, end_day, process, process2, solder):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,IFNULL(sheet_number, 0) FROM T_HSDS_data WHERE "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "' AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + solder)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# production sheet volume
def get_typeid_production_sheet_volume(start_day, end_day, typeid, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,IFNULL(sheet_number, 0) FROM T_HSDS_data WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + employee)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# insertion point volume
def get_insertion_point_volume(search_day, start_day, end_day, process, process2, solder):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,insertion_point FROM T_HSDS_data WHERE "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "' AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + solder)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# insertion point volume
def get_typeid_insertion_point_volume(start_day, end_day, typeid, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT DISTINCT orderNumber,insertion_point FROM T_HSDS_data WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + employee)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# defect volume
def get_defect_volume(search_day, start_day, end_day, process, process2, solder, symptom):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT defect_number FROM T_HSDS_data WHERE "
        cur.execute(query + search_day + " between '"
                    + start_day
                    + "' and '"
                    + end_day
                    + "' AND process IN("
                    + process + ", '"
                    + process2 + "')"
                    + symptom + " "
                    + solder)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


# defect volume
def get_pre_typeid_defect_volume(start_day, end_day, typeid, symptom, symbol, employee):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT defect_number FROM T_HSDS_data WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' and '"
                    + end_day + "'"
                    + typeid
                    + symptom
                    + symbol
                    + employee)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def get_parts_number_defect_number_all(start_day, end_day):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT defect_part_number,SUM(defect_number),COUNT(defect_number) FROM T_HSDS_data WHERE f_date between '"
        cur.execute(query
                    + start_day
                    + "' AND '"
                    + end_day
                    + "' AND defect_part_number NOT IN ('*') GROUP BY defect_part_number ORDER BY SUM(defect_number) DESC")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def get_parts_number_defect_number_symbol(start_day, end_day, symbol, order):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT defect_part_number,orderNumber,typeID,defect_symbol,SUM(defect_number),SUM(defect_number) / insertion_point * 100 FROM T_HSDS_data WHERE f_date between "
        cur.execute(query + "'"
                    + start_day
                    + "' AND '"
                    + end_day
                    + "' AND defect_part_number ='"
                    + symbol
                    + "' GROUP BY defect_part_number,orderNumber,typeID,defect_symbol,insertion_point "
                    + order)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def get_parts_number_defect_number_symbol_search(start_day, end_day, symbol, order):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT orderNumber,typeID,defect_symbol,SUM(defect_number),insertion_point FROM T_HSDS_data WHERE f_date between "
        cur.execute(query + "'"
                    + start_day
                    + "' AND '"
                    + end_day
                    + "' AND defect_part_number ='"
                    + symbol
                    + "' GROUP BY orderNumber,typeID,defect_symbol,insertion_point "
                    + order)
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def insert_typeid_data(typeid, process, solder, sn, s1, s1sn, multiple, remark):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "INSERT INTO T_HSDS_typeID VALUES ('"
        cur.execute(query
                    + typeid + "','"
                    + process + "','"
                    + solder + "','"
                    + sn + "','"
                    + s1 + "','"
                    + s1sn + "','"
                    + multiple + "','"
                    + remark + "')")
        conn.commit()
        messagebox.showinfo("情報", "登録致しました。")

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def get_search_typeid(typeid):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "SELECT typeID,process,solder,S1_surface,Sn_surface,SnS1_surface,multiple,remark FROM T_HSDS_typeID WHERE typeID ='"
        cur.execute(query + typeid + "'")
        res_query = cur.fetchall()
        return res_query

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()


def update_typeid_data(process, solder, sn, s1, s1sn, multiple, remark, typeid2):
    try:
        # ----- database1 setting -----
        conn = mysql.connector.connect(user=g_db1_u,
                                       password=g_db1_pw,
                                       host=g_db1_host,
                                       database=g_db1_db)
        cur = conn.cursor(buffered=True)

        # ----- query -----
        query = "UPDATE T_HSDS_typeID SET process = '"
        cur.execute(query + process
                    + "', solder ='" + solder
                    + "', Sn_surface ='" + sn
                    + "', S1_surface ='" + s1
                    + "', SnS1_surface ='" + s1sn
                    + "', multiple ='" + multiple
                    + "', remark ='" + remark
                    + "' WHERE typeID ='" + typeid2
                    + "'")
        conn.commit()
        messagebox.showinfo("情報", "情報を更新しました。")

    except mysql.connector.Error as err:
        messagebox.showerror("エラー", "データを追加出来ませんでした。")
        messagebox.showerror("エラー詳細", str(err))

    finally:
        cur.close()
        conn.close()




class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # -------------------- frame setting --------------------
        self.typeid_input_frame_remark_input_box = None
        self.typeid_input_frame_multiple_input_box = None
        self.typeid_input_frame_s1sn_input_box = None
        self.typeid_input_frame_sn_input_box = None
        self.typeid_input_frame_s1_input_box = None
        self.typeid_input_frame_solder_input_box = None
        self.typeid_input_frame_process_input_box = None
        self.typeid_input_frame_typeid2_input_box = None
        self.master.geometry("1280x1000")
        self.master.title("自動はんだ不良入力")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        # Default settings -frame construction-
        # database setting & query(後で削除)
        import mysql.connector
        conn = mysql.connector.connect(user='no13792',
                                       password='no13792',
                                       host='nksv560.ad.nkc.co.jp',
                                       database='test')
        cur = conn.cursor(buffered=True)

        # -----------------------------menu frame(home page)-----------------------------
        # ----- page open -----
        def goto_menu_frame():
            self.menu_frame.tkraise()

        # ----- frame setting -----
        self.menu_frame = tk.Frame()
        self.menu_frame.grid(row=0, column=0, sticky="nsew")

        # ----- frame structure -----
        self.menu_Label = tk.Label(self.menu_frame,
                                   text="メインメニュー　-Menu Page-",
                                   font=my_font.myfont(30))
        self.menu_Label.place(x=10, y=10)
        self.menu_Label = tk.Label(self.menu_frame,
                                   text="データ収集開始日：2021/4/1～",
                                   font=my_font.myfont(15))
        self.menu_Label.place(x=900, y=10)
        self.menu_Label = tk.Label(self.menu_frame,
                                   text="Version：1.1.2021.12.15",
                                   font=my_font.myfont(15))
        self.menu_Label.place(x=900, y=40)

        # ----- button setting -----
        # change page button -go to sasizu_input_frame-
        self.change_page_sasizu_Button = tk.Button(self.menu_frame,
                                                   text="不良入力",
                                                   font=my_font.myfont(20),
                                                   height=5,
                                                   width=20,
                                                   command=lambda: goto_sasizu_input_frame())
        self.change_page_sasizu_Button.place(x=50, y=150)

        # change page button -go to defect_period_frame-
        self.change_page_period_Button = tk.Button(self.menu_frame,
                                                   text="不良速報",
                                                   font=my_font.myfont(20),
                                                   height=5,
                                                   width=20,
                                                   command=lambda: goto_defect_period_frame_button_click())
        self.change_page_period_Button.place(x=450, y=150)

        def goto_defect_period_frame_button_click():
            self.defect_period_frame_process_box.focus_set()
            self.defect_period_frame.tkraise()

        # change page button -go to defect_data_frame-
        self.change_page_defect_data_Button = tk.Button(self.menu_frame,
                                                        text="不良集計",
                                                        font=my_font.myfont(20),
                                                        height=5,
                                                        width=20,
                                                        command=lambda: goto_defect_data_frame_button_click())
        self.change_page_defect_data_Button.place(x=850, y=150)

        def goto_defect_data_frame_button_click():
            self.defect_data_frame_process_box.focus_set()
            self.defect_data_frame.tkraise()

        # change page button -go to defect_sasizu_frame-
        self.change_page_defect_sasizu_Button = tk.Button(self.menu_frame,
                                                          text="指図別不良集計",
                                                          font=my_font.myfont(20),
                                                          height=5,
                                                          width=20,
                                                          command=lambda: goto_defect_sasizu_frame_button_click())
        self.change_page_defect_sasizu_Button.place(x=50, y=400)

        def goto_defect_sasizu_frame_button_click():
            self.defect_sasizu_frame_sasizu_input_box.focus_set()
            self.defect_sasizu_frame.tkraise()

        # change page button -go to defect_typeid_frame-
        self.change_page_defect_typeid_Button = tk.Button(self.menu_frame,
                                                          text="品目別不良集計",
                                                          font=my_font.myfont(20),
                                                          height=5,
                                                          width=20,
                                                          command=lambda: goto_defect_typeid_frame_button_click())
        self.change_page_defect_typeid_Button.place(x=450, y=400)

        def goto_defect_typeid_frame_button_click():
            self.defect_typeid_frame_typeid_box.focus_set()
            self.defect_typeid_frame.tkraise()

        # change page button -go to defect_part_number_frame-
        self.change_page_part_number_Button = tk.Button(self.menu_frame,
                                                        text="部品番号別不良集計",
                                                        font=my_font.myfont(20),
                                                        height=5,
                                                        width=20,
                                                        command=lambda: goto_defect_part_number_frame_button_click())
        self.change_page_part_number_Button.place(x=850, y=400)

        def goto_defect_part_number_frame_button_click():
            self.defect_part_number_frame_part_number_box.focus_set()
            self.defect_part_number_frame.tkraise()

        # change page button -go to hs_admin_frame-
        self.change_page_hs_admin_Button = tk.Button(self.menu_frame,
                                                     text="管理画面",
                                                     font=my_font.myfont(20),
                                                     height=5,
                                                     width=20,
                                                     command=lambda: goto_hs_admin_frame_button_click())
        self.change_page_hs_admin_Button.place(x=50, y=650)

        def goto_hs_admin_frame_button_click():
            self.hs_admin_frame.tkraise()

        # -----------------------------sasizu_input_frame-----------------------------
        # ----- page open -----
        def goto_sasizu_input_frame():
            self.sasizu_input_frame_sasizu_input_box.delete(0, tk.END)
            self.sasizu_input_frame_date_year_box.delete(0, tk.END)
            self.sasizu_input_frame_date_year_box.insert(tk.END, str(now.year))
            self.sasizu_input_frame_date_month_box.delete(0, tk.END)
            self.sasizu_input_frame_date_month_box.insert(tk.END, str(now.month))
            self.sasizu_input_frame_date_day_box.delete(0, tk.END)
            self.sasizu_input_frame_date_day_box.insert(tk.END, str(now.day))
            self.sasizu_input_frame_name_box.delete(0, tk.END)
            self.sasizu_input_frame_sasizu_input_box.focus_set()
            self.sasizu_input_frame.tkraise()

        # ----- page open -----
        def goto_sasizu_input_frame_keep():
            self.sasizu_input_frame_sasizu_input_box.focus_set()
            self.sasizu_input_frame.tkraise()

        # ----- frame setting -----
        self.sasizu_input_frame = tk.Frame()
        self.sasizu_input_frame.grid(row=0, column=0, sticky="nsew")

        # ----- frame structure -----
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="指図入力",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=10, y=10)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="指図：",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=50, y=150)
        self.sasizu_input_frame_sasizu_input_box = tk.Entry(self.sasizu_input_frame,
                                                            width=20,
                                                            font=my_font.myfont(30))
        self.sasizu_input_frame_sasizu_input_box.place(x=200, y=150)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="日付:",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=50, y=250)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="年",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=350, y=250)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="月",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=500, y=250)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="日",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=650, y=250)
        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                 text="作業者:",
                                                 font=my_font.myfont(30))
        self.sasizu_input_frame_label.place(x=50, y=350)

        # ----- button setting -----
        # execution button -go to defect_input_frame-
        self.smt_defect_input_button = tk.Button(self.sasizu_input_frame,
                                                 text="実行",
                                                 font=my_font.myfont(20),
                                                 height=1,
                                                 width=10,
                                                 command=lambda: goto_defect_input_button_click())
        self.smt_defect_input_button.place(x=200, y=450)
        # return bind
        self.smt_defect_input_button.bind("<Return>", lambda event: goto_defect_input_button_click())
        # reset button
        self.smt_defect_reset_button = tk.Button(self.sasizu_input_frame,
                                                 text="リセット",
                                                 font=my_font.myfont(20),
                                                 height=1,
                                                 width=10,
                                                 command=lambda: goto_sasizu_input_frame())
        self.smt_defect_reset_button.place(x=520, y=450)
        # back button -go to menu_frame-
        self.back_button = tk.Button(self.sasizu_input_frame,
                                     text="戻る",
                                     font=my_font.myfont(20),
                                     height=1,
                                     width=10,
                                     command=lambda: goto_menu_frame())
        self.back_button.place(x=520, y=10)

        # ----- input box -----
        # combo box -date year-
        self.sasizu_input_frame_date_year_box = ttk.Combobox(self.sasizu_input_frame,
                                                             values=g_year,
                                                             width=5,
                                                             font=my_font.myfont(30))
        self.sasizu_input_frame_date_year_box.place(x=200, y=250)
        self.sasizu_input_frame_date_year_box.insert(tk.END, str(now.year))
        # combobox -date month-
        self.sasizu_input_frame_date_month_box = ttk.Combobox(self.sasizu_input_frame,
                                                              values=g_month,
                                                              width=3,
                                                              font=my_font.myfont(30))
        self.sasizu_input_frame_date_month_box.place(x=400, y=250)
        self.sasizu_input_frame_date_month_box.insert(tk.END, str(now.month))
        # combobox -date day-
        self.sasizu_input_frame_date_day_box = ttk.Combobox(self.sasizu_input_frame,
                                                            values=g_day,
                                                            width=3,
                                                            font=my_font.myfont(30))
        self.sasizu_input_frame_date_day_box.place(x=550, y=250)
        self.sasizu_input_frame_date_day_box.insert(tk.END, str(now.day))
        # combobox -employee name-
        self.sasizu_input_frame_name_box = ttk.Combobox(self.sasizu_input_frame,
                                                        values=get_employee_name(),
                                                        width=19,
                                                        font=my_font.myfont(30))
        self.sasizu_input_frame_name_box.place(x=200, y=350)

        # ----- other setting -----
        # focus set & tab order
        self.sasizu_input_frame_sasizu_input_box.focus_set()
        new_order = (self.sasizu_input_frame_sasizu_input_box,
                     self.smt_defect_input_button,
                     self.sasizu_input_frame_date_year_box,
                     self.sasizu_input_frame_date_month_box,
                     self.sasizu_input_frame_date_day_box,
                     self.sasizu_input_frame_name_box
                     )
        for widget in new_order:
            widget.lift()

        def goto_defect_input_button_click():
            # input check
            get_input_order_number = mojimoji.zen_to_han(self.sasizu_input_frame_sasizu_input_box.get()).replace('\n', '')
            get_preprocessing_p_date = (self.sasizu_input_frame_date_year_box.get()
                                        + "-" + self.sasizu_input_frame_date_month_box.get()
                                        + "-" + self.sasizu_input_frame_date_day_box.get())
            get_input_employee_name = self.sasizu_input_frame_name_box.get()

            if not get_input_order_number:
                messagebox.showerror("エラー", "指図が入力されていません。")
                self.sasizu_input_frame_sasizu_input_box.focus_set()
            elif not get_input_employee_name:
                messagebox.showerror("エラー", "作業者が入力されていません。")
                self.sasizu_input_frame_name_box.focus_set()
            else:
                # duplicate check -orderNumber-
                get_d_duplicate_check = get_duplicate_check(get_input_order_number)
                if get_d_duplicate_check:  # data available
                    continue_check = messagebox.askyesno("警告", "入力実績がある指図です。入力しますか？")
                    get_duplicate_result = "yes"
                    if continue_check is False:
                        self.sasizu_input_frame_sasizu_input_box.delete(0, tk.END)
                        self.sasizu_input_frame_name_box.delete(0, tk.END)
                        self.sasizu_input_frame_sasizu_input_box.focus_set()
                        messagebox.showinfo("確認", "登録しませんでした。")
                        return
                else:
                    get_duplicate_result = "no"

                # get orderNumber information -table liveOrder_1year-
                d_sasizu_data = get_ordernumber_information("liveOrder_1year", get_input_order_number)
                # check of the orderNumber information
                if not d_sasizu_data:  # data not available
                    # get orderNumber information -table orderInformation_1year-
                    d_sasizu_data = get_ordernumber_information("orderInformation_1year", get_input_order_number)
                    if not d_sasizu_data:  # data not available
                        self.sasizu_input_frame_sasizu_input_box.delete(0, tk.END)
                        self.sasizu_input_frame_sasizu_input_box.focus_set()
                        return
                for column in d_sasizu_data:
                    get_ordernumber_information_result = column
                self.sasizu_input_frame_sasizu_input_box.delete(0, tk.END)
                self.sasizu_input_frame_sasizu_input_box.focus_set()
                goto_defect_input_frame(get_ordernumber_information_result[0],
                                        get_ordernumber_information_result[1],
                                        get_ordernumber_information_result[2],
                                        get_input_employee_name,
                                        get_duplicate_result,
                                        get_preprocessing_p_date)

        # -----------------------------defect_input_frame-----------------------------
        # ----- page open -----
        def goto_defect_input_frame(order_number, typeid, orderqty, employee_name, duplicate_result, p_date):
            self.defect_input_frame.tkraise()
            self.defect_input_sasizu_input_box.delete(0, tk.END)
            self.defect_input_sasizu_input_box.insert(tk.END, order_number)
            self.defect_input_typeid_input_box.delete(0, tk.END)
            self.defect_input_typeid_input_box.insert(tk.END, typeid)
            self.defect_input_orderqty_input_box.delete(0, tk.END)
            self.defect_input_orderqty_input_box.insert(tk.END, str(int(float(orderqty))))
            self.defect_input_employee_name_input_box.delete(0, tk.END)
            self.defect_input_employee_name_input_box.insert(tk.END, employee_name)
            self.defect_input_f_date_input_box.delete(0, tk.END)
            if duplicate_result == "yes":
                self.defect_input_f_date_input_box.insert(tk.END, get_d_preprocessing_p_date(order_number))
            else:
                self.defect_input_f_date_input_box.insert(tk.END, p_date)
            self.defect_input_p_date_input_box.delete(0, tk.END)
            self.defect_input_p_date_input_box.insert(tk.END, p_date)
            self.defect_input_process_input_box.delete(0, tk.END)
            self.defect_input_process_input_box.insert(tk.END, get_d_process(typeid))
            self.defect_input_solder_input_box.delete(0, tk.END)
            self.defect_input_solder_input_box.insert(tk.END, get_d_solder(typeid))
            self.defect_input_point_input_box.delete(0, tk.END)
            self.defect_input_point_input_box.insert(tk.END, get_d_insertion_point(typeid)[0])
            self.defect_input_multiple_input_box.delete(0, tk.END)
            self.defect_input_multiple_input_box.insert(tk.END, str(int(int(float(orderqty)) / get_d_multiple(typeid)[0])))

        # ----- frame setting -----
        self.defect_input_frame = tk.Frame()
        self.defect_input_frame.grid(row=0, column=0, sticky="nsew")

        # ----- frame structure -----
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="不良入力",
                                                 font=my_font.myfont(30))
        self.defect_input_frame_label.place(x=10, y=10)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="指図：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=50, y=90)
        self.defect_input_sasizu_input_box = tk.Entry(self.defect_input_frame,
                                                      width=12,
                                                      font=my_font.myfont(18))
        self.defect_input_sasizu_input_box.place(x=150, y=90)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="品目：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=400, y=90)
        self.defect_input_typeid_input_box = tk.Entry(self.defect_input_frame,
                                                      width=12,
                                                      font=my_font.myfont(18))
        self.defect_input_typeid_input_box.place(x=500, y=90)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="台数：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=750, y=90)
        self.defect_input_orderqty_input_box = tk.Entry(self.defect_input_frame,
                                                        width=6,
                                                        font=my_font.myfont(18))
        self.defect_input_orderqty_input_box.place(x=850, y=90)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="作業：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=50, y=130)
        self.defect_input_employee_name_input_box = tk.Entry(self.defect_input_frame,
                                                             width=12,
                                                             font=my_font.myfont(18))
        self.defect_input_employee_name_input_box.place(x=150, y=130)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="初登録日：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=50, y=170)
        self.defect_input_f_date_input_box = tk.Entry(self.defect_input_frame,
                                                      width=10,
                                                      font=my_font.myfont(18))
        self.defect_input_f_date_input_box.place(x=180, y=170)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="更新日：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=400, y=170)
        self.defect_input_p_date_input_box = tk.Entry(self.defect_input_frame,
                                                      width=10,
                                                      font=my_font.myfont(18))
        self.defect_input_p_date_input_box.place(x=530, y=170)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="工程：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=400, y=130)
        self.defect_input_process_input_box = ttk.Combobox(self.defect_input_frame,
                                                           values=get_process(),
                                                           width=11,
                                                           font=my_font.myfont(18))
        self.defect_input_process_input_box.place(x=500, y=130)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="はんだ：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=750, y=130)
        self.defect_input_solder_input_box = ttk.Combobox(self.defect_input_frame,
                                                          values=get_solder(),
                                                          width=11,
                                                          font=my_font.myfont(18))
        self.defect_input_solder_input_box.place(x=850, y=130)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="総点数：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=750, y=170)
        self.defect_input_point_input_box = tk.Entry(self.defect_input_frame,
                                                     width=12,
                                                     font=my_font.myfont(18))
        self.defect_input_point_input_box.place(x=850, y=170)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text="シート数：",
                                                 font=my_font.myfont(18))
        self.defect_input_frame_label.place(x=980, y=90)
        self.defect_input_multiple_input_box = tk.Entry(self.defect_input_frame,
                                                        width=6,
                                                        font=my_font.myfont(18))
        self.defect_input_multiple_input_box.place(x=1100, y=90)

        # Title field
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                 font=my_font.myfont(10))
        self.defect_input_frame_label.place(x=50, y=210)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='不良項目：1:ブリッジ、2:熱不足(はんだ過多,芋はんだ,コールドジョイント,はんだ上り不足,つの)、3:ピンホール(ブローホール)、4:浮き,傾き、5:未はんだ、6:その他',
                                                 font=my_font.myfont(12))
        self.defect_input_frame_label.place(x=50, y=230)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='シンボル',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=100, y=310)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='不良項目',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=300, y=310)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='割合',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=500, y=310)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='目視数(割合時のみ入力)：',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=180, y=265)
        self.defect_input_frame_rate_box = tk.Entry(self.defect_input_frame,
                                                    width=8,
                                                    justify="right",
                                                    font=my_font.myfont(20))
        self.defect_input_frame_rate_box.place(x=500, y=265)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='数量',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=655, y=310)
        self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                 text='備考',
                                                 font=my_font.myfont(20))
        self.defect_input_frame_label.place(x=800, y=310)

        # input field -loop version-
        # initial value
        number = 0
        count_y = 300

        for count in range(12):
            # count up
            number += 1
            count_y += 50

            # number
            self.defect_input_frame_label = tk.Label(self.defect_input_frame,
                                                     text=number,
                                                     font=my_font.myfont(18))
            self.defect_input_frame_label.place(x=50, y=count_y)

        # input field -case1-
        # symbol
        self.defect_input_frame_defect_symbol_case1_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case1_input_box.place(x=100, y=350)
        # symptom
        self.defect_input_frame_defect_symptom_case1_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case1_input_box.place(x=300, y=350)
        # rate
        self.defect_input_frame_defect_rate_case1_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case1_input_box.place(x=500, y=350)
        # number
        self.defect_input_frame_defect_number_case1_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case1_input_box.place(x=655, y=350)
        self.defect_input_frame_defect_number_case1_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case1_button_click())
        self.defect_input_countup_button.place(x=730, y=346)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case1_button_click())
        self.defect_input_countdw_button.place(x=730, y=367)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case1_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case1_input_box.place(x=800, y=350)

        def goto_defect_input_countup_case1_button_click():
            d_number = self.defect_input_frame_defect_number_case1_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case1_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case1_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case1_button_click():
            d_number = self.defect_input_frame_defect_number_case1_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case1_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case1_input_box.insert(0, str(countdw))

        # input field -case2-
        # symbol
        self.defect_input_frame_defect_symbol_case2_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case2_input_box.place(x=100, y=400)
        # symptom
        self.defect_input_frame_defect_symptom_case2_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case2_input_box.place(x=300, y=400)
        # rate
        self.defect_input_frame_defect_rate_case2_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case2_input_box.place(x=500, y=400)
        # number
        self.defect_input_frame_defect_number_case2_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case2_input_box.place(x=655, y=400)
        self.defect_input_frame_defect_number_case2_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case2_button_click())
        self.defect_input_countup_button.place(x=730, y=396)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case2_button_click())
        self.defect_input_countdw_button.place(x=730, y=417)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case2_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case2_input_box.place(x=800, y=400)

        def goto_defect_input_countup_case2_button_click():
            d_number = self.defect_input_frame_defect_number_case2_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case2_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case2_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case2_button_click():
            d_number = self.defect_input_frame_defect_number_case2_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case2_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case2_input_box.insert(0, str(countdw))

        # input field -case3-
        # symbol
        self.defect_input_frame_defect_symbol_case3_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case3_input_box.place(x=100, y=450)
        # symptom
        self.defect_input_frame_defect_symptom_case3_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case3_input_box.place(x=300, y=450)
        # rate
        self.defect_input_frame_defect_rate_case3_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case3_input_box.place(x=500, y=450)
        # number
        self.defect_input_frame_defect_number_case3_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case3_input_box.place(x=655, y=450)
        self.defect_input_frame_defect_number_case3_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case3_button_click())
        self.defect_input_countup_button.place(x=730, y=446)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case3_button_click())
        self.defect_input_countdw_button.place(x=730, y=467)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case3_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case3_input_box.place(x=800, y=450)

        def goto_defect_input_countup_case3_button_click():
            d_number = self.defect_input_frame_defect_number_case3_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case3_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case3_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case3_button_click():
            d_number = self.defect_input_frame_defect_number_case3_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case3_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case3_input_box.insert(0, str(countdw))

        # input field -case4-
        # symbol
        self.defect_input_frame_defect_symbol_case4_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case4_input_box.place(x=100, y=500)
        # symptom
        self.defect_input_frame_defect_symptom_case4_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case4_input_box.place(x=300, y=500)
        # rate
        self.defect_input_frame_defect_rate_case4_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case4_input_box.place(x=500, y=500)
        # number
        self.defect_input_frame_defect_number_case4_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case4_input_box.place(x=655, y=500)
        self.defect_input_frame_defect_number_case4_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case4_button_click())
        self.defect_input_countup_button.place(x=730, y=496)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case4_button_click())
        self.defect_input_countdw_button.place(x=730, y=517)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case4_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case4_input_box.place(x=800, y=500)

        def goto_defect_input_countup_case4_button_click():
            d_number = self.defect_input_frame_defect_number_case4_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case4_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case4_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case4_button_click():
            d_number = self.defect_input_frame_defect_number_case4_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case4_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case4_input_box.insert(0, str(countdw))

        # input field -case5-
        # symbol
        self.defect_input_frame_defect_symbol_case5_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case5_input_box.place(x=100, y=550)
        # symptom
        self.defect_input_frame_defect_symptom_case5_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case5_input_box.place(x=300, y=550)
        # rate
        self.defect_input_frame_defect_rate_case5_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case5_input_box.place(x=500, y=550)
        # number
        self.defect_input_frame_defect_number_case5_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case5_input_box.place(x=655, y=550)
        self.defect_input_frame_defect_number_case5_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case5_button_click())
        self.defect_input_countup_button.place(x=730, y=546)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case5_button_click())
        self.defect_input_countdw_button.place(x=730, y=567)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case5_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case5_input_box.place(x=800, y=550)

        def goto_defect_input_countup_case5_button_click():
            d_number = self.defect_input_frame_defect_number_case5_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case5_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case5_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case5_button_click():
            d_number = self.defect_input_frame_defect_number_case5_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case5_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case5_input_box.insert(0, str(countdw))

        # input field -case6-
        # symbol
        self.defect_input_frame_defect_symbol_case6_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case6_input_box.place(x=100, y=600)
        # symptom
        self.defect_input_frame_defect_symptom_case6_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case6_input_box.place(x=300, y=600)
        # rate
        self.defect_input_frame_defect_rate_case6_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case6_input_box.place(x=500, y=600)
        # number
        self.defect_input_frame_defect_number_case6_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case6_input_box.place(x=655, y=600)
        self.defect_input_frame_defect_number_case6_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case6_button_click())
        self.defect_input_countup_button.place(x=730, y=596)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case6_button_click())
        self.defect_input_countdw_button.place(x=730, y=617)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case6_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case6_input_box.place(x=800, y=600)

        def goto_defect_input_countup_case6_button_click():
            d_number = self.defect_input_frame_defect_number_case6_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case6_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case6_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case6_button_click():
            d_number = self.defect_input_frame_defect_number_case6_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case6_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case6_input_box.insert(0, str(countdw))

        # input field -case7-
        # symbol
        self.defect_input_frame_defect_symbol_case7_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case7_input_box.place(x=100, y=650)
        # symptom
        self.defect_input_frame_defect_symptom_case7_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case7_input_box.place(x=300, y=650)
        # rate
        self.defect_input_frame_defect_rate_case7_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case7_input_box.place(x=500, y=650)
        # number
        self.defect_input_frame_defect_number_case7_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case7_input_box.place(x=655, y=650)
        self.defect_input_frame_defect_number_case7_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case7_button_click())
        self.defect_input_countup_button.place(x=730, y=646)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case7_button_click())
        self.defect_input_countdw_button.place(x=730, y=667)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case7_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case7_input_box.place(x=800, y=650)

        def goto_defect_input_countup_case7_button_click():
            d_number = self.defect_input_frame_defect_number_case7_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case7_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case7_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case7_button_click():
            d_number = self.defect_input_frame_defect_number_case7_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case7_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case7_input_box.insert(0, str(countdw))

        # input field -case8-
        # symbol
        self.defect_input_frame_defect_symbol_case8_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case8_input_box.place(x=100, y=700)
        # symptom
        self.defect_input_frame_defect_symptom_case8_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case8_input_box.place(x=300, y=700)
        # rate
        self.defect_input_frame_defect_rate_case8_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case8_input_box.place(x=500, y=700)
        # number
        self.defect_input_frame_defect_number_case8_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case8_input_box.place(x=655, y=700)
        self.defect_input_frame_defect_number_case8_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case8_button_click())
        self.defect_input_countup_button.place(x=730, y=696)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case8_button_click())
        self.defect_input_countdw_button.place(x=730, y=717)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case8_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case8_input_box.place(x=800, y=700)

        def goto_defect_input_countup_case8_button_click():
            d_number = self.defect_input_frame_defect_number_case8_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case8_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case8_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case8_button_click():
            d_number = self.defect_input_frame_defect_number_case8_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case8_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case8_input_box.insert(0, str(countdw))

        # input field -case9-
        # symbol
        self.defect_input_frame_defect_symbol_case9_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=12,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case9_input_box.place(x=100, y=750)
        # symptom
        self.defect_input_frame_defect_symptom_case9_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_symptom(),
                                                                              width=11,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case9_input_box.place(x=300, y=750)
        # rate
        self.defect_input_frame_defect_rate_case9_input_box = ttk.Combobox(self.defect_input_frame,
                                                                           values=g_rate,
                                                                           width=8,
                                                                           font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case9_input_box.place(x=500, y=750)
        # number
        self.defect_input_frame_defect_number_case9_input_box = tk.Entry(self.defect_input_frame,
                                                                         width=4,
                                                                         font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case9_input_box.place(x=655, y=750)
        self.defect_input_frame_defect_number_case9_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case9_button_click())
        self.defect_input_countup_button.place(x=730, y=746)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case9_button_click())
        self.defect_input_countdw_button.place(x=730, y=767)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case9_input_box = ttk.Combobox(self.defect_input_frame,
                                                                             values=get_remark(),
                                                                             width=25,
                                                                             font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case9_input_box.place(x=800, y=750)

        def goto_defect_input_countup_case9_button_click():
            d_number = self.defect_input_frame_defect_number_case9_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case9_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case9_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case9_button_click():
            d_number = self.defect_input_frame_defect_number_case9_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case9_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case9_input_box.insert(0, str(countdw))

        # input field -case10-
        # symbol
        self.defect_input_frame_defect_symbol_case10_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=12,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case10_input_box.place(x=100, y=800)
        # symptom
        self.defect_input_frame_defect_symptom_case10_input_box = ttk.Combobox(self.defect_input_frame,
                                                                               values=get_symptom(),
                                                                               width=11,
                                                                               font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case10_input_box.place(x=300, y=800)
        # rate
        self.defect_input_frame_defect_rate_case10_input_box = ttk.Combobox(self.defect_input_frame,
                                                                            values=g_rate,
                                                                            width=8,
                                                                            font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case10_input_box.place(x=500, y=800)
        # number
        self.defect_input_frame_defect_number_case10_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=4,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case10_input_box.place(x=655, y=800)
        self.defect_input_frame_defect_number_case10_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case10_button_click())
        self.defect_input_countup_button.place(x=730, y=796)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case10_button_click())
        self.defect_input_countdw_button.place(x=730, y=817)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case10_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_remark(),
                                                                              width=25,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case10_input_box.place(x=800, y=800)

        def goto_defect_input_countup_case10_button_click():
            d_number = self.defect_input_frame_defect_number_case10_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case10_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case10_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case10_button_click():
            d_number = self.defect_input_frame_defect_number_case10_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case10_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case10_input_box.insert(0, str(countdw))

        # input field -case11-
        # symbol
        self.defect_input_frame_defect_symbol_case11_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=12,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case11_input_box.place(x=100, y=850)
        # symptom
        self.defect_input_frame_defect_symptom_case11_input_box = ttk.Combobox(self.defect_input_frame,
                                                                               values=get_symptom(),
                                                                               width=11,
                                                                               font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case11_input_box.place(x=300, y=850)
        # rate
        self.defect_input_frame_defect_rate_case11_input_box = ttk.Combobox(self.defect_input_frame,
                                                                            values=g_rate,
                                                                            width=8,
                                                                            font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case11_input_box.place(x=500, y=850)
        # number
        self.defect_input_frame_defect_number_case11_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=4,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case11_input_box.place(x=655, y=850)
        self.defect_input_frame_defect_number_case11_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case11_button_click())
        self.defect_input_countup_button.place(x=730, y=846)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case11_button_click())
        self.defect_input_countdw_button.place(x=730, y=867)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case11_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_remark(),
                                                                              width=25,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case11_input_box.place(x=800, y=850)

        def goto_defect_input_countup_case11_button_click():
            d_number = self.defect_input_frame_defect_number_case11_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case11_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case11_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case11_button_click():
            d_number = self.defect_input_frame_defect_number_case11_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case11_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case11_input_box.insert(0, str(countdw))

        # input field -case12-
        # symbol
        self.defect_input_frame_defect_symbol_case12_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=12,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_symbol_case12_input_box.place(x=100, y=900)
        # symptom
        self.defect_input_frame_defect_symptom_case12_input_box = ttk.Combobox(self.defect_input_frame,
                                                                               values=get_symptom(),
                                                                               width=11,
                                                                               font=my_font.myfont(18))
        self.defect_input_frame_defect_symptom_case12_input_box.place(x=300, y=900)
        # rate
        self.defect_input_frame_defect_rate_case12_input_box = ttk.Combobox(self.defect_input_frame,
                                                                            values=g_rate,
                                                                            width=8,
                                                                            font=my_font.myfont(18))
        self.defect_input_frame_defect_rate_case12_input_box.place(x=500, y=900)
        # number
        self.defect_input_frame_defect_number_case12_input_box = tk.Entry(self.defect_input_frame,
                                                                          width=4,
                                                                          font=my_font.myfont(18))
        self.defect_input_frame_defect_number_case12_input_box.place(x=655, y=900)
        self.defect_input_frame_defect_number_case12_input_box.insert(0, "0")
        # number countup
        self.defect_input_countup_button = tk.Button(self.defect_input_frame,
                                                     text="+",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_countup_case12_button_click())
        self.defect_input_countup_button.place(x=730, y=896)
        # number countdw
        self.defect_input_countdw_button = tk.Button(self.defect_input_frame,
                                                     text="-",
                                                     font=my_font.myfont(7),
                                                     height=1,
                                                     width=3,
                                                     command=lambda: goto_defect_input_count_dw_case12_button_click())
        self.defect_input_countdw_button.place(x=730, y=917)
        # combo box -remark-
        self.defect_input_frame_defect_remark_case12_input_box = ttk.Combobox(self.defect_input_frame,
                                                                              values=get_remark(),
                                                                              width=25,
                                                                              font=my_font.myfont(18))
        self.defect_input_frame_defect_remark_case12_input_box.place(x=800, y=900)

        def goto_defect_input_countup_case12_button_click():
            d_number = self.defect_input_frame_defect_number_case12_input_box.get()
            countup = int(d_number) + 1
            self.defect_input_frame_defect_number_case12_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case12_input_box.insert(0, str(countup))

        def goto_defect_input_count_dw_case12_button_click():
            d_number = self.defect_input_frame_defect_number_case12_input_box.get()
            countdw = int(d_number) - 1
            self.defect_input_frame_defect_number_case12_input_box.delete(0, tk.END)
            self.defect_input_frame_defect_number_case12_input_box.insert(0, str(countdw))

        # ----- button setting -----
        # back button -go to sasizu_input_frame-
        self.back_button = tk.Button(self.defect_input_frame,
                                     text="戻る",
                                     font=my_font.myfont(20),
                                     height=1,
                                     width=10,
                                     command=lambda: goto_sasizu_input_frame_keep())
        self.back_button.place(x=900, y=10)

        # database_registration button -go to defect_database_registration_button-
        self.defect_input_continue_button = tk.Button(self.defect_input_frame,
                                                      text="登録",
                                                      font=my_font.myfont(20),
                                                      height=1,
                                                      width=15,
                                                      command=lambda: goto_defect_data_database_registration_button_click())
        self.defect_input_continue_button.place(x=950, y=275)
        # return bind
        self.defect_input_continue_button.bind("<Return>",
                                               lambda event: goto_defect_data_database_registration_button_click())

        # focus set & tab order
        self.defect_input_frame_rate_box.focus_set()
        defect_input_order = (self.defect_input_frame_rate_box,
                              self.defect_input_frame_defect_symbol_case1_input_box,
                              self.defect_input_frame_defect_symptom_case1_input_box,
                              self.defect_input_frame_defect_rate_case1_input_box,
                              self.defect_input_frame_defect_number_case1_input_box,
                              self.defect_input_frame_defect_symbol_case2_input_box,
                              self.defect_input_frame_defect_symptom_case2_input_box,
                              self.defect_input_frame_defect_rate_case2_input_box,
                              self.defect_input_frame_defect_number_case2_input_box,
                              self.defect_input_frame_defect_symbol_case3_input_box,
                              self.defect_input_frame_defect_symptom_case3_input_box,
                              self.defect_input_frame_defect_rate_case3_input_box,
                              self.defect_input_frame_defect_number_case3_input_box,
                              self.defect_input_frame_defect_symbol_case4_input_box,
                              self.defect_input_frame_defect_symptom_case4_input_box,
                              self.defect_input_frame_defect_rate_case4_input_box,
                              self.defect_input_frame_defect_number_case4_input_box,
                              self.defect_input_frame_defect_symbol_case5_input_box,
                              self.defect_input_frame_defect_symptom_case5_input_box,
                              self.defect_input_frame_defect_rate_case5_input_box,
                              self.defect_input_frame_defect_number_case5_input_box,
                              self.defect_input_frame_defect_symbol_case6_input_box,
                              self.defect_input_frame_defect_symptom_case6_input_box,
                              self.defect_input_frame_defect_rate_case6_input_box,
                              self.defect_input_frame_defect_number_case6_input_box,
                              self.defect_input_frame_defect_symbol_case7_input_box,
                              self.defect_input_frame_defect_symptom_case7_input_box,
                              self.defect_input_frame_defect_rate_case7_input_box,
                              self.defect_input_frame_defect_number_case7_input_box,
                              self.defect_input_frame_defect_symbol_case8_input_box,
                              self.defect_input_frame_defect_symptom_case8_input_box,
                              self.defect_input_frame_defect_rate_case8_input_box,
                              self.defect_input_frame_defect_number_case8_input_box,
                              self.defect_input_frame_defect_symbol_case9_input_box,
                              self.defect_input_frame_defect_symptom_case9_input_box,
                              self.defect_input_frame_defect_rate_case9_input_box,
                              self.defect_input_frame_defect_number_case9_input_box,
                              self.defect_input_frame_defect_symbol_case10_input_box,
                              self.defect_input_frame_defect_symptom_case10_input_box,
                              self.defect_input_frame_defect_rate_case10_input_box,
                              self.defect_input_frame_defect_number_case10_input_box,
                              self.defect_input_frame_defect_symbol_case11_input_box,
                              self.defect_input_frame_defect_symptom_case11_input_box,
                              self.defect_input_frame_defect_rate_case11_input_box,
                              self.defect_input_frame_defect_number_case11_input_box,
                              self.defect_input_frame_defect_symbol_case12_input_box,
                              self.defect_input_frame_defect_symptom_case12_input_box,
                              self.defect_input_frame_defect_rate_case12_input_box,
                              self.defect_input_frame_defect_number_case12_input_box)
        for widget in defect_input_order:
            widget.lift()

        def goto_defect_data_database_registration_button_click():
            # sort out the databox
            input_order_number = self.defect_input_sasizu_input_box.get()
            input_p_date = self.defect_input_p_date_input_box.get()
            input_f_date = self.defect_input_f_date_input_box.get()
            input_typeid = self.defect_input_typeid_input_box.get()
            input_orderqty = self.defect_input_orderqty_input_box.get()
            input_multiple = self.defect_input_multiple_input_box.get()
            input_process = self.defect_input_process_input_box.get()
            input_solder = self.defect_input_solder_input_box.get()
            input_employee_name = self.defect_input_employee_name_input_box.get()
            input_employee_number = str(get_employee_number(input_employee_name))
            input_point = self.defect_input_point_input_box.get()

            # input check
            if input_order_number == "":
                messagebox.showerror("NG", "指図が入力されていません。")
                self.defect_input_sasizu_input_box.focus_set()
                return
            if input_typeid == "":
                messagebox.showerror("NG", "品目が入力されていません。")
                self.defect_input_typeid_input_box.focus_set()
                return
            if input_orderqty == "":
                messagebox.showerror("NG", "台数が入力されていません。")
                self.defect_input_orderqty_input_box.focus_set()
                return
            if input_multiple == "":
                messagebox.showerror("NG", "シート数が入力されていません。")
                self.defect_input_multiple_input_box.focus_set()
                return
            if input_process == "":
                messagebox.showerror("NG", "工程が入力されていません。")
                self.defect_input_process_input_box.focus_set()
                return
            if input_solder == "":
                messagebox.showerror("NG", "はんだが入力されていません。")
                self.defect_input_solder_input_box.focus_set()
                return
            if input_employee_name == "":
                messagebox.showerror("NG", "作業者が入力されていません。")
                self.defect_input_employee_name_input_box.focus_set()
                return
            if input_f_date == "":
                messagebox.showerror("NG", "初期登録日が入力されていません。")
                self.defect_input_f_date_input_box.focus_set()
                return
            if input_p_date == "":
                messagebox.showerror("NG", "登録日が入力されていません。")
                self.defect_input_p_date_input_box.focus_set()
                return
            if input_point == "":
                messagebox.showerror("NG", "総点数が入力されていません。")
                self.defect_input_point_input_box.focus_set()
                return

            # sort out the data
            input_point_case = int(self.defect_input_point_input_box.get()) * int(self.defect_input_orderqty_input_box.get())

            input_sheet_number_case = int(self.defect_input_multiple_input_box.get())
            input_symptom_case1 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case1_input_box.get())
            input_symbol_case1 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case1_input_box.get())).replace('\n', '')
            input_number_case1 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case1_input_box.get())
            input_remark_case1 = self.defect_input_frame_defect_remark_case1_input_box.get()
            input_danger_alarm_case1 = (int(input_number_case1) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case2 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case2_input_box.get())
            input_symbol_case2 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case2_input_box.get())).replace('\n', '')
            input_number_case2 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case2_input_box.get())
            input_remark_case2 = self.defect_input_frame_defect_remark_case2_input_box.get()
            input_danger_alarm_case2 = (int(input_number_case2) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case3 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case3_input_box.get())
            input_symbol_case3 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case3_input_box.get())).replace('\n', '')
            input_number_case3 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case3_input_box.get())
            input_remark_case3 = self.defect_input_frame_defect_remark_case3_input_box.get()
            input_danger_alarm_case3 = (int(input_number_case3) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case4 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case4_input_box.get())
            input_symbol_case4 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case4_input_box.get())).replace('\n', '')
            input_number_case4 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case4_input_box.get())
            input_remark_case4 = self.defect_input_frame_defect_remark_case4_input_box.get()
            input_danger_alarm_case4 = (int(input_number_case4) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case5 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case5_input_box.get())
            input_symbol_case5 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case5_input_box.get())).replace('\n', '')
            input_number_case5 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case5_input_box.get())
            input_remark_case5 = self.defect_input_frame_defect_remark_case5_input_box.get()
            input_danger_alarm_case5 = (int(input_number_case5) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case6 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case6_input_box.get())
            input_symbol_case6 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case6_input_box.get())).replace('\n', '')
            input_number_case6 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case6_input_box.get())
            input_remark_case6 = self.defect_input_frame_defect_remark_case6_input_box.get()
            input_danger_alarm_case6 = (int(input_number_case6) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case7 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case7_input_box.get())
            input_symbol_case7 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case7_input_box.get())).replace('\n', '')
            input_number_case7 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case7_input_box.get())
            input_remark_case7 = self.defect_input_frame_defect_remark_case7_input_box.get()
            input_danger_alarm_case7 = (int(input_number_case7) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case8 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case8_input_box.get())
            input_symbol_case8 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case8_input_box.get())).replace('\n', '')
            input_number_case8 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case8_input_box.get())
            input_remark_case8 = self.defect_input_frame_defect_remark_case8_input_box.get()
            input_danger_alarm_case8 = (int(input_number_case8) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case9 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case9_input_box.get())
            input_symbol_case9 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case9_input_box.get())).replace('\n', '')
            input_number_case9 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case9_input_box.get())
            input_remark_case9 = self.defect_input_frame_defect_remark_case9_input_box.get()
            input_danger_alarm_case9 = (int(input_number_case9) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case10 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case10_input_box.get())
            input_symbol_case10 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case10_input_box.get())).replace('\n', '')
            input_number_case10 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case10_input_box.get())
            input_remark_case10 = self.defect_input_frame_defect_remark_case10_input_box.get()
            input_danger_alarm_case10 = (int(input_number_case10) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case11 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case11_input_box.get())
            input_symbol_case11 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case11_input_box.get())).replace('\n', '')
            input_number_case11 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case11_input_box.get())
            input_remark_case11 = self.defect_input_frame_defect_remark_case11_input_box.get()
            input_danger_alarm_case11 = (int(input_number_case11) / int(self.defect_input_orderqty_input_box.get())) * 100
            input_symptom_case12 = mojimoji.zen_to_han(self.defect_input_frame_defect_symptom_case12_input_box.get())
            input_symbol_case12 = mojimoji.zen_to_han(str.upper(self.defect_input_frame_defect_symbol_case12_input_box.get())).replace('\n', '')
            input_number_case12 = mojimoji.zen_to_han(self.defect_input_frame_defect_number_case12_input_box.get())
            input_remark_case12 = self.defect_input_frame_defect_remark_case12_input_box.get()
            input_danger_alarm_case12 = (int(input_number_case12) / int(self.defect_input_orderqty_input_box.get())) * 100

            # case: symptom & symbol in the case of input is null
            if not input_symptom_case1 and not input_symbol_case1 and \
                    not input_symptom_case2 and not input_symbol_case2 and \
                    not input_symptom_case3 and not input_symbol_case3 and \
                    not input_symptom_case4 and not input_symbol_case4 and \
                    not input_symptom_case5 and not input_symbol_case5 and \
                    not input_symptom_case6 and not input_symbol_case6 and \
                    not input_symptom_case7 and not input_symbol_case7 and \
                    not input_symptom_case8 and not input_symbol_case8 and \
                    not input_symptom_case9 and not input_symbol_case9 and \
                    not input_symptom_case10 and not input_symbol_case10 and \
                    not input_symptom_case11 and not input_symbol_case11 and \
                    not input_symptom_case12 and not input_symbol_case12:
                request = messagebox.askokcancel("確認", "症状とシンボルが入力されていないので不良無しで登録します。")

                if request is False:  # database registration cancellation
                    messagebox.showinfo("情報", "登録しませんでした。")
                    self.defect_input_frame_defect_symptom_case1_input_box.focus_set()
                    return
                else:  # database registration
                    # write data to database
                    no_defect_data_registration(input_p_date, input_p_date, input_order_number, input_typeid,
                                                input_orderqty, input_employee_number, input_process, input_solder,
                                                input_point_case, input_sheet_number_case, "")

                # input contents reset
                self.defect_input_frame_defect_symptom_case1_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case1_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case1_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case1_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case1_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case2_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case2_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case2_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case2_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case2_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case3_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case3_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case3_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case3_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case3_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case4_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case4_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case4_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case4_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case4_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case5_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case5_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case5_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case5_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case5_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case6_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case6_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case6_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case6_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case6_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case7_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case7_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case7_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case7_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case7_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case8_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case8_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case8_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case8_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case8_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case9_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case9_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case9_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case9_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case9_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case10_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case10_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case10_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case10_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case10_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case11_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case11_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case11_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case11_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case11_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symptom_case12_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_symbol_case12_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case12_input_box.delete(0, tk.END)
                self.defect_input_frame_defect_number_case12_input_box.insert(0, "0")
                self.defect_input_frame_defect_remark_case12_input_box.delete(0, tk.END)

            # case: symptom & symbol in the case of input is available
            else:
                input_rate = mojimoji.zen_to_han(self.defect_input_frame_rate_box.get())
                if bool(input_rate) is False:
                    rate_check = messagebox.askyesno("警告", "割合が入力されていないので数量入力します。宜しいですか？")
                    if rate_check is False:
                        self.defect_input_frame_rate_box.focus_set()
                        return
                else:
                    input_rate_integer_check = mojimoji.zen_to_han(self.defect_input_frame_rate_box.get()).isdigit()
                    if input_rate_integer_check is False:
                        messagebox.showerror("NG", "目視数に整数以外が入っています。入力し直して下さい。")
                        self.defect_input_frame_rate_box.focus_set()
                        return

                    # rate change
                    # case1
                    input_rate_case1 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case1_input_box.get())
                    if bool(input_rate_case1) is True:
                        input_rate_case1_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case1_input_box.get()).isdigit()
                        if input_rate_case1_integer_check is False:
                            messagebox.showerror("NG", "1 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case1_input_box.focus_set()
                            return
                        input_rate_case1_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case1_input_box.get()))
                        if 0 < input_rate_case1_range_check <= 10:
                            rate_c1 = (int(input_rate_case1) * int(input_rate)) / 10
                            rate_case1 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case1 == 0:
                                rate_case1 = 1
                            self.defect_input_frame_defect_rate_case1_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case1_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case1_input_box.insert(0, str(rate_case1))
                            input_number_case1 = self.defect_input_frame_defect_number_case1_input_box.get()
                        else:
                            messagebox.showerror("NG", "1 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case1_input_box.focus_set()
                            return

                    # case2
                    input_rate_case2 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case2_input_box.get())
                    if bool(input_rate_case2) is True:
                        input_rate_case2_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case2_input_box.get()).isdigit()
                        if input_rate_case2_integer_check is False:
                            messagebox.showerror("NG", "2 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case2_input_box.focus_set()
                            return
                        input_rate_case2_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case2_input_box.get()))
                        if 0 < input_rate_case2_range_check <= 10:
                            rate_c1 = (int(input_rate_case2) * int(input_rate)) / 10
                            rate_case2 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case2 == 0:
                                rate_case2 = 1
                            self.defect_input_frame_defect_rate_case2_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case2_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case2_input_box.insert(0, str(rate_case2))
                            input_number_case2 = self.defect_input_frame_defect_number_case2_input_box.get()
                        else:
                            messagebox.showerror("NG", "2 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case2_input_box.focus_set()
                            return

                    # case3
                    input_rate_case3 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case3_input_box.get())
                    if bool(input_rate_case3) is True:
                        input_rate_case3_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case3_input_box.get()).isdigit()
                        if input_rate_case3_integer_check is False:
                            messagebox.showerror("NG", "3 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case3_input_box.focus_set()
                            return
                        input_rate_case3_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case3_input_box.get()))
                        if 0 < input_rate_case3_range_check <= 10:
                            rate_c1 = (int(input_rate_case3) * int(input_rate)) / 10
                            rate_case3 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case3 == 0:
                                rate_case3 = 1
                            self.defect_input_frame_defect_rate_case3_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case3_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case3_input_box.insert(0, str(rate_case3))
                            input_number_case3 = self.defect_input_frame_defect_number_case3_input_box.get()
                        else:
                            messagebox.showerror("NG", "3 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case3_input_box.focus_set()
                            return

                    # case4
                    input_rate_case4 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case4_input_box.get())
                    if bool(input_rate_case4) is True:
                        input_rate_case4_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case4_input_box.get()).isdigit()
                        if input_rate_case4_integer_check is False:
                            messagebox.showerror("NG", "4 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case4_input_box.focus_set()
                            return
                        input_rate_case4_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case4_input_box.get()))
                        if 0 < input_rate_case4_range_check <= 10:
                            rate_c1 = (int(input_rate_case4) * int(input_rate)) / 10
                            rate_case4 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case4 == 0:
                                rate_case4 = 1
                            self.defect_input_frame_defect_rate_case4_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case4_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case4_input_box.insert(0, str(rate_case4))
                            input_number_case4 = self.defect_input_frame_defect_number_case4_input_box.get()
                        else:
                            messagebox.showerror("NG", "4 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case4_input_box.focus_set()
                            return

                    # case5
                    input_rate_case5 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case5_input_box.get())
                    if bool(input_rate_case5) is True:
                        input_rate_case5_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case5_input_box.get()).isdigit()
                        if input_rate_case5_integer_check is False:
                            messagebox.showerror("NG", "5 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case5_input_box.focus_set()
                            return
                        input_rate_case5_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case5_input_box.get()))
                        if 0 < input_rate_case5_range_check <= 10:
                            rate_c1 = (int(input_rate_case5) * int(input_rate)) / 10
                            rate_case5 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case5 == 0:
                                rate_case5 = 1
                            self.defect_input_frame_defect_rate_case5_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case5_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case5_input_box.insert(0, str(rate_case5))
                            input_number_case5 = self.defect_input_frame_defect_number_case5_input_box.get()
                        else:
                            messagebox.showerror("NG", "5 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case5_input_box.focus_set()
                            return

                    # case6
                    input_rate_case6 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case6_input_box.get())
                    if bool(input_rate_case6) is True:
                        input_rate_case6_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case6_input_box.get()).isdigit()
                        if input_rate_case6_integer_check is False:
                            messagebox.showerror("NG", "6 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case6_input_box.focus_set()
                            return
                        input_rate_case6_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case6_input_box.get()))
                        if 0 < input_rate_case6_range_check <= 10:
                            rate_c1 = (int(input_rate_case6) * int(input_rate)) / 10
                            rate_case6 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case6 == 0:
                                rate_case6 = 1
                            self.defect_input_frame_defect_rate_case6_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case6_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case6_input_box.insert(0, str(rate_case6))
                            input_number_case6 = self.defect_input_frame_defect_number_case6_input_box.get()
                        else:
                            messagebox.showerror("NG", "6 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case6_input_box.focus_set()
                            return

                    # case7
                    input_rate_case7 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case7_input_box.get())
                    if bool(input_rate_case7) is True:
                        input_rate_case7_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case7_input_box.get()).isdigit()
                        if input_rate_case7_integer_check is False:
                            messagebox.showerror("NG", "7 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case7_input_box.focus_set()
                            return
                        input_rate_case7_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case7_input_box.get()))
                        if 0 < input_rate_case7_range_check <= 10:
                            rate_c1 = (int(input_rate_case7) * int(input_rate)) / 10
                            rate_case7 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case7 == 0:
                                rate_case7 = 1
                            self.defect_input_frame_defect_rate_case7_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case7_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case7_input_box.insert(0, str(rate_case7))
                            input_number_case7 = self.defect_input_frame_defect_number_case7_input_box.get()
                        else:
                            messagebox.showerror("NG", "7 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case7_input_box.focus_set()
                            return

                    # case8
                    input_rate_case8 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case8_input_box.get())
                    if bool(input_rate_case8) is True:
                        input_rate_case8_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case8_input_box.get()).isdigit()
                        if input_rate_case8_integer_check is False:
                            messagebox.showerror("NG", "8 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case8_input_box.focus_set()
                            return
                        input_rate_case8_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case8_input_box.get()))
                        if 0 < input_rate_case8_range_check <= 10:
                            rate_c1 = (int(input_rate_case8) * int(input_rate)) / 10
                            rate_case8 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case8 == 0:
                                rate_case8 = 1
                            self.defect_input_frame_defect_rate_case8_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case8_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case8_input_box.insert(0, str(rate_case8))
                            input_number_case8 = self.defect_input_frame_defect_number_case8_input_box.get()
                        else:
                            messagebox.showerror("NG", "8 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case8_input_box.focus_set()
                            return

                    # case9
                    input_rate_case9 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case9_input_box.get())
                    if bool(input_rate_case9) is True:
                        input_rate_case9_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case9_input_box.get()).isdigit()
                        if input_rate_case9_integer_check is False:
                            messagebox.showerror("NG", "9 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case9_input_box.focus_set()
                            return
                        input_rate_case9_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case9_input_box.get()))
                        if 0 < input_rate_case9_range_check <= 10:
                            rate_c1 = (int(input_rate_case9) * int(input_rate)) / 10
                            rate_case9 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case9 == 0:
                                rate_case9 = 1
                            self.defect_input_frame_defect_rate_case9_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case9_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case9_input_box.insert(0, str(rate_case9))
                            input_number_case9 = self.defect_input_frame_defect_number_case9_input_box.get()
                        else:
                            messagebox.showerror("NG", "9 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case9_input_box.focus_set()
                            return

                    # case10
                    input_rate_case10 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case10_input_box.get())
                    if bool(input_rate_case10) is True:
                        input_rate_case10_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case10_input_box.get()).isdigit()
                        if input_rate_case10_integer_check is False:
                            messagebox.showerror("NG", "10 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case10_input_box.focus_set()
                            return
                        input_rate_case10_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case10_input_box.get()))
                        if 0 < input_rate_case10_range_check <= 10:
                            rate_c1 = (int(input_rate_case10) * int(input_rate)) / 10
                            rate_case10 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case10 == 0:
                                rate_case10 = 1
                            self.defect_input_frame_defect_rate_case10_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case10_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case10_input_box.insert(0, str(rate_case10))
                            input_number_case10 = self.defect_input_frame_defect_number_case10_input_box.get()
                        else:
                            messagebox.showerror("NG", "10 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case10_input_box.focus_set()
                            return

                    # case11
                    input_rate_case11 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case11_input_box.get())
                    if bool(input_rate_case11) is True:
                        input_rate_case11_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case11_input_box.get()).isdigit()
                        if input_rate_case11_integer_check is False:
                            messagebox.showerror("NG", "11 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case11_input_box.focus_set()
                            return
                        input_rate_case11_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case11_input_box.get()))
                        if 0 < input_rate_case11_range_check <= 10:
                            rate_c1 = (int(input_rate_case11) * int(input_rate)) / 10
                            rate_case11 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case11 == 0:
                                rate_case11 = 1
                            self.defect_input_frame_defect_rate_case11_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case11_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case11_input_box.insert(0, str(rate_case11))
                            input_number_case11 = self.defect_input_frame_defect_number_case11_input_box.get()
                        else:
                            messagebox.showerror("NG", "11 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case11_input_box.focus_set()
                            return

                    # case12
                    input_rate_case12 = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case12_input_box.get())
                    if bool(input_rate_case12) is True:
                        input_rate_case12_integer_check = mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case12_input_box.get()).isdigit()
                        if input_rate_case12_integer_check is False:
                            messagebox.showerror("NG", "12 の割合に整数以外が入っています。入力し直して下さい。")
                            self.defect_input_frame_defect_rate_case12_input_box.focus_set()
                            return
                        input_rate_case12_range_check = int(mojimoji.zen_to_han(self.defect_input_frame_defect_rate_case12_input_box.get()))
                        if 0 < input_rate_case12_range_check <= 10:
                            rate_c1 = (int(input_rate_case12) * int(input_rate)) / 10
                            rate_case12 = Decimal(str(rate_c1)).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
                            if rate_case12 == 0:
                                rate_case12 = 1
                            self.defect_input_frame_defect_rate_case12_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case12_input_box.delete(0, tk.END)
                            self.defect_input_frame_defect_number_case12_input_box.insert(0, str(rate_case12))
                            input_number_case12 = self.defect_input_frame_defect_number_case12_input_box.get()
                        else:
                            messagebox.showerror("NG", "12 の割合は 1~10 の整数で入力して下さい")
                            self.defect_input_frame_defect_rate_case12_input_box.focus_set()
                            return

                # input check
                # case1
                if not input_symbol_case1 == "" or not input_symptom_case1 == "":
                    if input_symbol_case1 == "":
                        messagebox.showerror("警告", "1 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case1_input_box.focus_set()
                        return
                    if input_symptom_case1 == "":
                        messagebox.showerror("警告", "1 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case1_input_box.focus_set()
                        return
                    if input_number_case1 == "0":
                        messagebox.showerror("警告", "1 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case1_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case1 = d_part_number_check(input_typeid, input_symbol_case1)
                    if not d_part_number_case1:
                        d_part_number_case1 = "*"

                    # write data to database
                    print("test")
                    print(input_symptom_case1[0])
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case1[0], input_symbol_case1, input_number_case1,
                                             input_remark_case1, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case1, d_part_number_case1)

                    self.defect_input_frame_defect_symptom_case1_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case1_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case1_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case1_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case1_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case1_input_box.delete(0, tk.END)

                # case2
                if not input_symbol_case2 == "" or not input_symptom_case2 == "":
                    if input_symbol_case2 == "":
                        messagebox.showerror("警告", "2 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case2_input_box.focus_set()
                        return
                    if input_symptom_case2 == "":
                        messagebox.showerror("警告", "2 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case2_input_box.focus_set()
                        return
                    if input_number_case2 == "0":
                        messagebox.showerror("警告", "2 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case2_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case2 = d_part_number_check(input_typeid, input_symbol_case2)
                    if not d_part_number_case2:
                        d_part_number_case2 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case2[0], input_symbol_case2, input_number_case2,
                                             input_remark_case2, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case2, d_part_number_case2)
                    self.defect_input_frame_defect_symptom_case2_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case2_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case2_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case2_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case2_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case2_input_box.delete(0, tk.END)

                # case3
                if not input_symbol_case3 == "" or not input_symptom_case3 == "":
                    if input_symbol_case3 == "":
                        messagebox.showerror("警告", "3 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case3_input_box.focus_set()
                        return
                    if input_symptom_case3 == "":
                        messagebox.showerror("警告", "3 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case3_input_box.focus_set()
                        return
                    if input_number_case3 == "0":
                        messagebox.showerror("警告", "3 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case3_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case3 = d_part_number_check(input_typeid, input_symbol_case3)
                    if not d_part_number_case3:
                        d_part_number_case3 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case3[0], input_symbol_case3, input_number_case3,
                                             input_remark_case3, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case3, d_part_number_case3)
                    self.defect_input_frame_defect_symptom_case3_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case3_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case3_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case3_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case3_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case3_input_box.delete(0, tk.END)

                # case4
                if not input_symbol_case4 == "" or not input_symptom_case4 == "":
                    if input_symbol_case4 == "":
                        messagebox.showerror("警告", "4 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case4_input_box.focus_set()
                        return
                    if input_symptom_case4 == "":
                        messagebox.showerror("警告", "4 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case4_input_box.focus_set()
                        return
                    if input_number_case4 == "0":
                        messagebox.showerror("警告", "4 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case4_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case4 = d_part_number_check(input_typeid, input_symbol_case4)
                    if not d_part_number_case4:
                        d_part_number_case4 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case4[0], input_symbol_case4, input_number_case4,
                                             input_remark_case4, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case4, d_part_number_case4)
                    self.defect_input_frame_defect_symptom_case4_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case4_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case4_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case4_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case4_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case4_input_box.delete(0, tk.END)

                # case5
                if not input_symbol_case5 == "" or not input_symptom_case5 == "":
                    if input_symbol_case5 == "":
                        messagebox.showerror("警告", "5 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case5_input_box.focus_set()
                        return
                    if input_symptom_case5 == "":
                        messagebox.showerror("警告", "5 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case5_input_box.focus_set()
                        return
                    if input_number_case5 == "0":
                        messagebox.showerror("警告", "5 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case5_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case5 = d_part_number_check(input_typeid, input_symbol_case5)
                    if not d_part_number_case5:
                        d_part_number_case5 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case5[0], input_symbol_case5, input_number_case5,
                                             input_remark_case5, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case5, d_part_number_case5)
                    self.defect_input_frame_defect_symptom_case5_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case5_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case5_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case5_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case5_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case5_input_box.delete(0, tk.END)

                # case6
                if not input_symbol_case6 == "" or not input_symptom_case6 == "":
                    if input_symbol_case6 == "":
                        messagebox.showerror("警告", "6 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case6_input_box.focus_set()
                        return
                    if input_symptom_case6 == "":
                        messagebox.showerror("警告", "6 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case6_input_box.focus_set()
                        return
                    if input_number_case6 == "0":
                        messagebox.showerror("警告", "6 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case6_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case6 = d_part_number_check(input_typeid, input_symbol_case6)
                    if not d_part_number_case6:
                        d_part_number_case6 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case6[0], input_symbol_case6, input_number_case6,
                                             input_remark_case6, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case6, d_part_number_case6)
                    self.defect_input_frame_defect_symptom_case6_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case6_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case6_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case6_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case6_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case6_input_box.delete(0, tk.END)

                # case7
                if not input_symbol_case7 == "" or not input_symptom_case7 == "":
                    if input_symbol_case7 == "":
                        messagebox.showerror("警告", "7 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case7_input_box.focus_set()
                        return
                    if input_symptom_case7 == "":
                        messagebox.showerror("警告", "7 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case7_input_box.focus_set()
                        return
                    if input_number_case7 == "0":
                        messagebox.showerror("警告", "7 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case7_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case7 = d_part_number_check(input_typeid, input_symbol_case7)
                    if not d_part_number_case7:
                        d_part_number_case7 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case7[0], input_symbol_case7, input_number_case7,
                                             input_remark_case7, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case7, d_part_number_case7)
                    self.defect_input_frame_defect_symptom_case7_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case7_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case7_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case7_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case7_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case7_input_box.delete(0, tk.END)

                # case8
                if not input_symbol_case8 == "" or not input_symptom_case8 == "":
                    if input_symbol_case8 == "":
                        messagebox.showerror("警告", "8 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case8_input_box.focus_set()
                        return
                    if input_symptom_case8 == "":
                        messagebox.showerror("警告", "8 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case8_input_box.focus_set()
                        return
                    if input_number_case8 == "0":
                        messagebox.showerror("警告", "8 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case8_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case8 = d_part_number_check(input_typeid, input_symbol_case8)
                    if not d_part_number_case8:
                        d_part_number_case8 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case8[0], input_symbol_case8, input_number_case8,
                                             input_remark_case8, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case8, d_part_number_case8)
                    self.defect_input_frame_defect_symptom_case8_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case8_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case8_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case8_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case8_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case8_input_box.delete(0, tk.END)

                # case9
                if not input_symbol_case9 == "" or not input_symptom_case9 == "":
                    if input_symbol_case9 == "":
                        messagebox.showerror("警告", "9 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case9_input_box.focus_set()
                        return
                    if input_symptom_case9 == "":
                        messagebox.showerror("警告", "9 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case9_input_box.focus_set()
                        return
                    if input_number_case9 == "0":
                        messagebox.showerror("警告", "9 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case9_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case9 = d_part_number_check(input_typeid, input_symbol_case9)
                    if not d_part_number_case9:
                        d_part_number_case9 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case9[0], input_symbol_case9, input_number_case9,
                                             input_remark_case9, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case9, d_part_number_case9)
                    self.defect_input_frame_defect_symptom_case9_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case9_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case9_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case9_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case9_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case9_input_box.delete(0, tk.END)

                # case10
                if not input_symbol_case10 == "" or not input_symptom_case10 == "":
                    if input_symbol_case10 == "":
                        messagebox.showerror("警告", "10 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case10_input_box.focus_set()
                        return
                    if input_symptom_case10 == "":
                        messagebox.showerror("警告", "10 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case10_input_box.focus_set()
                        return
                    if input_number_case10 == "0":
                        messagebox.showerror("警告", "10 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case10_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case10 = d_part_number_check(input_typeid, input_symbol_case10)
                    if not d_part_number_case10:
                        d_part_number_case10 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case10[0], input_symbol_case10, input_number_case10,
                                             input_remark_case10, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case10, d_part_number_case10)
                    self.defect_input_frame_defect_symptom_case10_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case10_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case10_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case10_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case10_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case10_input_box.delete(0, tk.END)

                # case11
                if not input_symbol_case11 == "" or not input_symptom_case11 == "":
                    if input_symbol_case11 == "":
                        messagebox.showerror("警告", "11 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case11_input_box.focus_set()
                        return
                    if input_symptom_case11 == "":
                        messagebox.showerror("警告", "11 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case11_input_box.focus_set()
                        return
                    if input_number_case11 == "0":
                        messagebox.showerror("警告", "11 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case11_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case11 = d_part_number_check(input_typeid, input_symbol_case11)
                    if not d_part_number_case11:
                        d_part_number_case11 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case11[0], input_symbol_case11, input_number_case11,
                                             input_remark_case11, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case11, d_part_number_case11)
                    self.defect_input_frame_defect_symptom_case11_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case11_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case11_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case11_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case11_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case11_input_box.delete(0, tk.END)

                # case12
                if not input_symbol_case12 == "" or not input_symptom_case12 == "":
                    if input_symbol_case12 == "":
                        messagebox.showerror("警告", "12 のシンボルが入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symbol_case12_input_box.focus_set()
                        return
                    if input_symptom_case12 == "":
                        messagebox.showerror("警告", "12 の不良項目が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_symptom_case12_input_box.focus_set()
                        return
                    if input_number_case12 == "0":
                        messagebox.showerror("警告", "12 の数量が入力されていません。入力を確認して下さい。")
                        self.defect_input_frame_defect_number_case12_input_box.focus_set()
                        return

                    # part number search
                    d_part_number_case12 = d_part_number_check(input_typeid, input_symbol_case12)
                    if not d_part_number_case12:
                        d_part_number_case12 = "*"

                    # write data to database
                    defect_data_registration(input_p_date, input_f_date, input_order_number, input_typeid,
                                             input_orderqty, input_employee_number, input_process, input_solder,
                                             input_symptom_case12[0], input_symbol_case12, input_number_case12,
                                             input_remark_case12, input_point_case, input_sheet_number_case,
                                             input_danger_alarm_case12, d_part_number_case12)
                    self.defect_input_frame_defect_symptom_case12_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_symbol_case12_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case12_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_number_case12_input_box.insert(0, "0")
                    self.defect_input_frame_defect_rate_case12_input_box.delete(0, tk.END)
                    self.defect_input_frame_defect_remark_case12_input_box.delete(0, tk.END)

                messagebox.showinfo("メッセージ", "データベースに追加しました。")
                # focus set
                self.defect_input_frame_defect_symptom_case1_input_box.focus_set()

            self.sasizu_input_frame_sasizu_input_box.focus_set()
            self.sasizu_input_frame.tkraise()


        # -----------------------------defect_period_frame-----------------------------

        # define frame
        self.defect_period_frame = tk.Frame()
        self.defect_period_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text="不良速報",
                                                  font=my_font.myfont(30))
        self.defect_period_frame_label.place(x=10, y=10)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text="■検索条件■",
                                                  font=my_font.myfont(20))
        self.defect_period_frame_label.place(x=50, y=100)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='期間：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=50, y=150)
        self.defect_period_frame_start_day_input_box = tk.Entry(self.defect_period_frame,
                                                                width=11,
                                                                font=my_font.myfont(15))
        self.defect_period_frame_start_day_input_box.place(x=120, y=150)
        adjust_day = datetime.timedelta(weeks=1)
        self.defect_period_frame_start_day_input_box.insert(0, str(today - adjust_day))
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='~',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=265, y=150)
        self.defect_period_frame_end_day_input_box = tk.Entry(self.defect_period_frame,
                                                              width=11,
                                                              font=my_font.myfont(15))
        self.defect_period_frame_end_day_input_box.place(x=300, y=150)
        self.defect_period_frame_end_day_input_box.insert(0, str(today))
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='工程：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=50, y=190)

        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='or',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=290, y=190)

        # combo box -process-
        self.defect_period_frame_process_box = ttk.Combobox(self.defect_period_frame,
                                                            values=get_process(),
                                                            width=12,
                                                            font=my_font.myfont(15))
        self.defect_period_frame_process_box.place(x=120, y=190)
        self.defect_period_frame_process_box.insert(0, "*")
        # combo box -process2-
        self.defect_period_frame_process_box2 = ttk.Combobox(self.defect_period_frame,
                                                             values=get_process(),
                                                             width=12,
                                                             font=my_font.myfont(15))
        self.defect_period_frame_process_box2.place(x=320, y=190)
        self.defect_period_frame_process_box2.insert(0, "*")

        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='不良項目：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=510, y=190)
        # combo box symptom--
        self.defect_period_frame_symptom_box = ttk.Combobox(self.defect_period_frame,
                                                            values=get_defect_symptom(),
                                                            width=30,
                                                            font=my_font.myfont(15))
        self.defect_period_frame_symptom_box.place(x=620, y=190)
        self.defect_period_frame_symptom_box.insert(0, "*")

        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='はんだ：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=50, y=225)
        # combo box solder--
        self.defect_period_frame_solder_box = ttk.Combobox(self.defect_period_frame,
                                                           values=get_solder(),
                                                           width=12,
                                                           font=my_font.myfont(15))
        self.defect_period_frame_solder_box.place(x=120, y=225)
        self.defect_period_frame_solder_box.insert(0, "*")
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_period_frame_label.place(x=100, y=260)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text="■検索結果■",
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=100, y=280)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='生産台数：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=120, y=320)
        self.defect_period_frame_production_number_box = tk.Entry(self.defect_period_frame,
                                                                  width=12,
                                                                  justify="right",
                                                                  font=my_font.myfont(15))
        self.defect_period_frame_production_number_box.place(x=230, y=320)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='台',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=380, y=320)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='生産シート数：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=450, y=320)
        self.defect_period_frame_multiple_number_box = tk.Entry(self.defect_period_frame,
                                                                width=12,
                                                                justify="right",
                                                                font=my_font.myfont(15))
        self.defect_period_frame_multiple_number_box.place(x=670, y=320)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='シート',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=820, y=320)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='不良件数：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=120, y=360)
        self.defect_period_frame_defect_number_box = tk.Entry(self.defect_period_frame,
                                                              width=12,
                                                              justify="right",
                                                              font=my_font.myfont(15))
        self.defect_period_frame_defect_number_box.place(x=230, y=360)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='件',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=380, y=360)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='自動はんだ付け部品数：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=450, y=360)
        self.defect_period_frame_insertion_point_number_box = tk.Entry(self.defect_period_frame,
                                                                       width=12,
                                                                       justify="right",
                                                                       font=my_font.myfont(15))
        self.defect_period_frame_insertion_point_number_box.place(x=670, y=360)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='件',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=820, y=360)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='不良率：',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=120, y=400)
        self.defect_period_frame_defect_rate_box = tk.Entry(self.defect_period_frame,
                                                            width=12,
                                                            justify="right",
                                                            font=my_font.myfont(15))
        self.defect_period_frame_defect_rate_box.place(x=230, y=400)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='%',
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=380, y=400)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_period_frame_label.place(x=100, y=450)
        # worst title
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="■不良一覧 Worst10■",
                                                  font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=100, y=470)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="品目", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=120, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="工程", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=300, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="不良項目", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=450, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="シンボル", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=600, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="部品番号", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=750, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="件数", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=950, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="備考", font=my_font.myfont(15))
        self.defect_period_frame_label.place(x=1050, y=510)
        self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_period_frame_label.place(x=120, y=540)

        # ----- button setting -----
        # renew button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="リセット",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=10,
                                                    command=lambda: goto_defect_period_frame_renew_button_click())
        self.defect_period_renew_button.place(x=300, y=10)
        # yesterday button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="前日",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_yesterday_button_click())
        self.defect_period_renew_button.place(x=450, y=120)
        # two days before button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="2日前",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_two_days_before_button_click())
        self.defect_period_renew_button.place(x=550, y=120)
        # three days before button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="3日前",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_three_days_before_button_click())
        self.defect_period_renew_button.place(x=650, y=120)
        # week button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="週間",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_week_button_click())
        self.defect_period_renew_button.place(x=750, y=120)
        # month button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="今月",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_month_button_click())
        self.defect_period_renew_button.place(x=850, y=120)
        # previous button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="前月",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_period_frame_previous_button_click())
        self.defect_period_renew_button.place(x=950, y=120)
        # period button
        self.defect_period_renew_button = tk.Button(self.defect_period_frame,
                                                    text="指定期間",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=8,
                                                    command=lambda: goto_defect_period_frame_period_button_click())
        self.defect_period_renew_button.place(x=1050, y=120)
        # csv output button
        self.defect_period_csv_button = tk.Button(self.defect_period_frame,
                                                  text="CSV",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=8,
                                                  command=lambda: goto_defect_period_frame_csv_button_click())
        self.defect_period_csv_button.place(x=1050, y=200)
        # back button -go to menu_frame-
        self.defect_period_back_button = tk.Button(self.defect_period_frame,
                                                   text="戻る",
                                                   font=my_font.myfont(20),
                                                   height=1,
                                                   width=10,
                                                   command=lambda: goto_menu_from_defect_period_button_click())
        self.defect_period_back_button.place(x=520, y=10)

        def goto_defect_period_frame_csv_button_click():
            # --- get data ---
            c_start_day = self.defect_period_frame_start_day_input_box.get()
            c_end_day = self.defect_period_frame_end_day_input_box.get()
            c_process = self.defect_period_frame_process_box.get()
            c_process2 = self.defect_period_frame_process_box2.get()
            c_symptom = self.defect_period_frame_symptom_box.get()
            c_solder = self.defect_period_frame_solder_box.get()
            if c_process == "" or c_process == "*":
                process1 = "'新局所'"
                process2 = "'新局所-新局所'"
                process3 = "'旧局所'"
                process4 = "'旧局所-旧局所'"
                process5 = "'ウェーブ'"
                process6 = "'ウェーブ-ウェーブ'"
                process7 = "'ウェーブ-旧局所'"
                process8 = "'ウェーブ-ポイント'"
                process9 = "'ポイント'"
                process10 = "'ポイント-ポイント'"
                c_process = (process1 + ","
                             + process2 + ","
                             + process3 + ","
                             + process4 + ","
                             + process5 + ","
                             + process6 + ","
                             + process7 + ","
                             + process8 + ","
                             + process9 + ","
                             + process10)
            else:
                c_process = "'" + c_process + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = "AND T_HSDS_data.defect_symptom =" + c_symptom[0]

            if c_solder == "" or c_solder == "*":
                c_solder = ""
            else:
                c_solder = "AND solder ='" + c_solder + "'"

            # worst list
            d_worst_list = get_defect_worst_list_csv("p_date", c_start_day, c_end_day, c_process, c_process2, c_symptom, c_solder)
            texta = os.getcwd()
            messagebox.showinfo("ファイル保存場所", texta + '/不良速報データ.csv')
            with open(texta + '/不良速報データ.csv', 'w', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["日付", "指図", "品目", "台数", "作業者", "工程", "はんだ", "不良項目", "シンボル", "部品番号", "件数", "備考"])
                for column in d_worst_list:
                    writer.writerow(column)
            # open folder
            path = texta
            path = os.path.realpath(path)
            os.startfile(path)

        def period_search_results():
            # --- get data ---
            c_start_day = self.defect_period_frame_start_day_input_box.get()
            c_end_day = self.defect_period_frame_end_day_input_box.get()
            c_process = self.defect_period_frame_process_box.get()
            c_process2 = self.defect_period_frame_process_box2.get()
            c_symptom = self.defect_period_frame_symptom_box.get()
            c_solder = self.defect_period_frame_solder_box.get()
            if c_process == "" or c_process == "*":
                process1 = "'新局所'"
                process2 = "'新局所-新局所'"
                process3 = "'旧局所'"
                process4 = "'旧局所-旧局所'"
                process5 = "'ウェーブ'"
                process6 = "'ウェーブ-ウェーブ'"
                process7 = "'ウェーブ-旧局所'"
                process8 = "'ウェーブ-ポイント'"
                process9 = "'ポイント'"
                process10 = "'ポイント-ポイント'"
                c_process = (process1 + ","
                             + process2 + ","
                             + process3 + ","
                             + process4 + ","
                             + process5 + ","
                             + process6 + ","
                             + process7 + ","
                             + process8 + ","
                             + process9 + ","
                             + process10)
            else:
                c_process = "'" + c_process + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = "AND T_HSDS_data.defect_symptom =" + c_symptom[0]

            if c_solder == "" or c_solder == "*":
                c_solder = ""
            else:
                c_solder = "AND solder ='" + c_solder + "'"

            # production volume
            d_production_volume = get_production_volume("p_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for p_number in d_production_volume:
                list1.append(p_number[1])
            self.defect_period_frame_production_number_box.delete(0, tk.END)
            self.defect_period_frame_production_number_box.insert(0, sum(list1))

            # production sheet volume
            d_production_sheet_volume = get_production_sheet_volume("p_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for p_number in d_production_sheet_volume:
                list1.append(p_number[1])
            self.defect_period_frame_multiple_number_box.delete(0, tk.END)
            self.defect_period_frame_multiple_number_box.insert(0, sum(list1))

            # insertion point volume
            d_insertion_point_volume = get_insertion_point_volume("p_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for i_p_number in d_insertion_point_volume:
                list1.append(i_p_number[1])
            self.defect_period_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_period_frame_insertion_point_number_box.insert(0, sum(list1))

            # defect volume
            d_defect_volume = get_defect_volume("p_date", c_start_day, c_end_day, c_process, c_process2, c_solder, c_symptom)
            list1 = []
            for d_number in d_defect_volume:
                list1.append(d_number[0])
            self.defect_period_frame_defect_number_box.delete(0, tk.END)
            self.defect_period_frame_defect_number_box.insert(0, sum(list1))

            # defect rate
            denominator = self.defect_period_frame_insertion_point_number_box.get()
            numerator = self.defect_period_frame_defect_number_box.get()
            if int(denominator) == 0:
                self.defect_period_frame_defect_rate_box.delete(0, tk.END)
                self.defect_period_frame_defect_rate_box.insert(tk.END, "0")
            else:
                rate = int(numerator) / int(denominator) * 100
                self.defect_period_frame_defect_rate_box.delete(0, tk.END)
                self.defect_period_frame_defect_rate_box.insert(0, str(round(rate, 1)))

            # worst list
            d_worst_list = get_defect_worst_list("p_date", c_start_day, c_end_day, c_process, c_process2, c_solder, c_symptom)
            count_a = 0
            count_y1 = 520
            for column in d_worst_list:
                if count_a < 10:
                    count_a += 1
                    count_y1 += 40
                    if not column:
                        self.defect_period_frame_label = tk.Label(self.defect_period_frame, text="不良無し",
                                                                  font=my_font.myfont(15))
                        self.defect_period_frame_label.place(x=10, y=560)
                    else:
                        result_1 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[0],
                                                                             font=my_font.myfont(15))
                        result_1.place(x=120, y=count_y1)
                        result_2 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[1],
                                                                             font=my_font.myfont(15))
                        result_2.place(x=300, y=count_y1)
                        result_3 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[2],
                                                                             font=my_font.myfont(15))
                        result_3.place(x=450, y=count_y1)
                        result_4 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[3],
                                                                             font=my_font.myfont(15))
                        result_4.place(x=600, y=count_y1)
                        result_5 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[4],
                                                                             font=my_font.myfont(15))
                        result_5.place(x=750, y=count_y1)
                        result_6 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[5],
                                                                             font=my_font.myfont(15))
                        result_6.place(x=950, y=count_y1)
                        result_7 = self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                                             text=column[6],
                                                                             font=my_font.myfont(15))
                        result_7.place(x=1050, y=count_y1)

        def goto_defect_period_frame_yesterday_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_period_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            self.defect_period_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_two_days_before_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput two days before
            self.defect_period_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            self.defect_period_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_three_days_before_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput two days before
            self.defect_period_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            self.defect_period_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_week_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput week
            self.defect_period_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(weeks=1)))
            self.defect_period_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_month_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput month
            d_month = date.today()
            self.defect_period_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1)))
            self.defect_period_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month + 1, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_previous_button_click():
            # inputbox clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput previous
            d_month = date.today()
            self.defect_period_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month - 1, 1)))
            self.defect_period_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_period_button_click():
            # search result clear
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            # goto search results
            period_search_results()

        def goto_defect_period_frame_renew_button_click():
            # search result clear
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_start_day_input_box.insert(0, str(today))
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.insert(0, str(today))
            self.defect_period_frame_process_box.delete(0, tk.END)
            self.defect_period_frame_process_box.insert(0, "*")
            self.defect_period_frame_process_box2.delete(0, tk.END)
            self.defect_period_frame_process_box2.insert(0, "*")
            self.defect_period_frame_symptom_box.delete(0, tk.END)
            self.defect_period_frame_symptom_box.insert(0, "*")
            self.defect_period_frame_solder_box.delete(0, tk.END)
            self.defect_period_frame_solder_box.insert(0, "*")
            self.defect_period_frame_production_number_box.delete(0, tk.END)
            self.defect_period_frame_multiple_number_box.delete(0, tk.END)
            self.defect_period_frame_defect_number_box.delete(0, tk.END)
            self.defect_period_frame_defect_rate_box.delete(0, tk.END)
            self.defect_period_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)

        def goto_menu_from_defect_period_button_click():
            self.defect_period_frame_start_day_input_box.delete(0, tk.END)
            self.defect_period_frame_start_day_input_box.insert(0, str(today))
            self.defect_period_frame_end_day_input_box.delete(0, tk.END)
            self.defect_period_frame_end_day_input_box.insert(0, str(today))
            self.defect_period_frame_process_box.delete(0, tk.END)
            self.defect_period_frame_process_box.insert(0, "*")
            self.defect_period_frame_process_box2.delete(0, tk.END)
            self.defect_period_frame_process_box2.insert(0, "*")
            self.defect_period_frame_symptom_box.delete(0, tk.END)
            self.defect_period_frame_symptom_box.insert(0, "*")
            self.defect_period_frame_solder_box.delete(0, tk.END)
            self.defect_period_frame_solder_box.insert(0, "*")
            self.defect_period_frame_production_number_box.delete(0, tk.END)
            self.defect_period_frame_multiple_number_box.delete(0, tk.END)
            self.defect_period_frame_defect_number_box.delete(0, tk.END)
            self.defect_period_frame_defect_rate_box.delete(0, tk.END)
            self.defect_period_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_period_frame_label = tk.Label(self.defect_period_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_period_frame_label.place(x=120, y=560)
            self.menu_frame.tkraise()

        # -----------------------------defect_data_frame-----------------------------
        # define frame
        self.defect_data_frame = tk.Frame()
        self.defect_data_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text="不良集計",
                                                font=my_font.myfont(30))
        self.defect_data_frame_label.place(x=10, y=10)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text="■検索条件■",
                                                font=my_font.myfont(20))
        self.defect_data_frame_label.place(x=50, y=100)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='期間：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=50, y=150)
        self.defect_data_frame_start_day_input_box = tk.Entry(self.defect_data_frame,
                                                              width=11,
                                                              font=my_font.myfont(15))
        self.defect_data_frame_start_day_input_box.place(x=120, y=150)
        adjustday = datetime.timedelta(weeks=1)
        self.defect_data_frame_start_day_input_box.insert(0, str(today - adjustday))
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='~',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=265, y=150)
        self.defect_data_frame_end_day_input_box = tk.Entry(self.defect_data_frame,
                                                            width=11,
                                                            font=my_font.myfont(15))
        self.defect_data_frame_end_day_input_box.place(x=300, y=150)
        self.defect_data_frame_end_day_input_box.insert(0, str(today))
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='工程：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=50, y=190)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='or',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=290, y=190)

        # --- input box ---
        # combo box -process-
        self.defect_data_frame_process_box = ttk.Combobox(self.defect_data_frame,
                                                          values=get_process(),
                                                          width=12,
                                                          font=my_font.myfont(15))
        self.defect_data_frame_process_box.place(x=120, y=190)
        self.defect_data_frame_process_box.insert(0, "*")
        # combo box -process2-
        self.defect_data_frame_process_box2 = ttk.Combobox(self.defect_data_frame,
                                                           values=get_process(),
                                                           width=10,
                                                           font=my_font.myfont(15))
        self.defect_data_frame_process_box2.place(x=320, y=190)
        self.defect_data_frame_process_box2.insert(0, "*")
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='不良項目：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=510, y=190)
        # combo box symptom--
        self.defect_data_frame_symptom_box = ttk.Combobox(self.defect_data_frame,
                                                          values=get_defect_symptom(),
                                                          width=30,
                                                          font=my_font.myfont(15))
        self.defect_data_frame_symptom_box.place(x=620, y=190)
        self.defect_data_frame_symptom_box.insert(0, "*")

        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='はんだ：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=50, y=225)
        # combo box solder--
        self.defect_data_frame_solder_box = ttk.Combobox(self.defect_data_frame,
                                                         values=get_solder(),
                                                         width=10,
                                                         font=my_font.myfont(15))
        self.defect_data_frame_solder_box.place(x=120, y=225)
        self.defect_data_frame_solder_box.insert(0, "*")
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                font=my_font.myfont(10))
        self.defect_data_frame_label.place(x=100, y=260)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text="■検索結果■",
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=100, y=280)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='生産台数：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=120, y=320)
        self.defect_data_frame_production_number_box = tk.Entry(self.defect_data_frame,
                                                                width=12,
                                                                justify="right",
                                                                font=my_font.myfont(15))
        self.defect_data_frame_production_number_box.place(x=230, y=320)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='台',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=380, y=320)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='生産シート数：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=450, y=320)
        self.defect_data_frame_multiple_number_box = tk.Entry(self.defect_data_frame,
                                                              width=12,
                                                              justify="right",
                                                              font=my_font.myfont(15))
        self.defect_data_frame_multiple_number_box.place(x=670, y=320)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='シート',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=820, y=320)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='不良件数：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=120, y=360)
        self.defect_data_frame_defect_number_box = tk.Entry(self.defect_data_frame,
                                                            width=12,
                                                            justify="right",
                                                            font=my_font.myfont(15))
        self.defect_data_frame_defect_number_box.place(x=230, y=360)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='件',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=380, y=360)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='自動はんだ付け部品数：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=450, y=360)
        self.defect_data_frame_insertion_point_number_box = tk.Entry(self.defect_data_frame,
                                                                     width=12,
                                                                     justify="right",
                                                                     font=my_font.myfont(15))
        self.defect_data_frame_insertion_point_number_box.place(x=670, y=360)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='件',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=820, y=360)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='不良率：',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=120, y=400)
        self.defect_data_frame_defect_rate_box = tk.Entry(self.defect_data_frame,
                                                          width=12,
                                                          justify="right",
                                                          font=my_font.myfont(15))
        self.defect_data_frame_defect_rate_box.place(x=230, y=400)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='%',
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=380, y=400)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                font=my_font.myfont(10))
        self.defect_data_frame_label.place(x=100, y=450)

        # worst title
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="■不良一覧 Worst10■",
                                                font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=100, y=470)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="品目", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=120, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="工程", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=300, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="不良項目", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=450, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="シンボル", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=600, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="部品番号", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=750, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="件数", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=950, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="備考", font=my_font.myfont(15))
        self.defect_data_frame_label.place(x=1050, y=510)
        self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                font=my_font.myfont(10))
        self.defect_data_frame_label.place(x=120, y=540)

        # ----- button setting -----
        # renew button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="リセット",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=10,
                                                  command=lambda: goto_defect_data_frame_renew_button_click())
        self.defect_data_renew_button.place(x=300, y=10)

        # yesterday button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="前日",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_yesterday_button_click())
        self.defect_data_renew_button.place(x=450, y=120)

        # two days before button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="2日前",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_two_days_before_button_click())
        self.defect_data_renew_button.place(x=550, y=120)

        # three days before button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="3日前",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_three_days_before_button_click())
        self.defect_data_renew_button.place(x=650, y=120)

        # week button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="週間",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_week_button_click())
        self.defect_data_renew_button.place(x=750, y=120)

        # month button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="今月",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_month_button_click())
        self.defect_data_renew_button.place(x=850, y=120)

        # previous button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="前月",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=5,
                                                  command=lambda: goto_defect_data_frame_previous_button_click())
        self.defect_data_renew_button.place(x=950, y=120)

        # data button
        self.defect_data_renew_button = tk.Button(self.defect_data_frame,
                                                  text="指定期間",
                                                  font=my_font.myfont(20),
                                                  height=1,
                                                  width=8,
                                                  command=lambda: goto_defect_data_frame_period_button_click())
        self.defect_data_renew_button.place(x=1050, y=120)

        # back button -go to menu_frame-
        self.defect_data_back_button = tk.Button(self.defect_data_frame,
                                                 text="戻る",
                                                 font=my_font.myfont(20),
                                                 height=1,
                                                 width=10,
                                                 command=lambda: goto_menu_from_defect_data_button_click())
        self.defect_data_back_button.place(x=520, y=10)

        # csv output button
        self.defect_data_csv_button = tk.Button(self.defect_data_frame,
                                                text="CSV",
                                                font=my_font.myfont(20),
                                                height=1,
                                                width=8,
                                                command=lambda: goto_defect_data_frame_csv_button_click())
        self.defect_data_csv_button.place(x=1050, y=200)

        def goto_defect_data_frame_csv_button_click():
            c_start_day = self.defect_data_frame_start_day_input_box.get()
            c_end_day = self.defect_data_frame_end_day_input_box.get()
            c_process = self.defect_data_frame_process_box.get()
            c_process2 = self.defect_data_frame_process_box2.get()
            c_symptom = self.defect_data_frame_symptom_box.get()
            c_solder = self.defect_data_frame_solder_box.get()
            if c_process == "" or c_process == "*":
                process1 = "'新局所'"
                process2 = "'新局所-新局所'"
                process3 = "'旧局所'"
                process4 = "'旧局所-旧局所'"
                process5 = "'ウェーブ'"
                process6 = "'ウェーブ-ウェーブ'"
                process7 = "'ウェーブ-旧局所'"
                process8 = "'ウェーブ-ポイント'"
                process9 = "'ポイント'"
                process10 = "'ポイント-ポイント'"
                c_process = (process1 + ","
                             + process2 + ","
                             + process3 + ","
                             + process4 + ","
                             + process5 + ","
                             + process6 + ","
                             + process7 + ","
                             + process8 + ","
                             + process9 + ","
                             + process10)
            else:
                c_process = "'" + c_process + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = "AND T_HSDS_data.defect_symptom =" + c_symptom[0]

            if c_solder == "" or c_solder == "*":
                c_solder = ""
            else:
                c_solder = "AND solder ='" + c_solder + "'"

            # worst list
            d_worst_list = get_defect_worst_list_csv("f_date", c_start_day, c_end_day, c_process, c_process2, c_symptom, c_solder)
            texta = os.getcwd()
            messagebox.showinfo("ファイル保存場所", texta + '/不良集計データ.csv')
            with open(texta + '/不良集計データ.csv', 'w', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["日付", "指図", "品目", "台数", "作業者", "工程", "はんだ", "不良項目", "シンボル", "部品番号", "件数", "備考"])
                for column in d_worst_list:
                    writer.writerow(column)
            # open folder
            path = texta
            path = os.path.realpath(path)
            os.startfile(path)

        def data_search_results():
            c_start_day = self.defect_data_frame_start_day_input_box.get()
            c_end_day = self.defect_data_frame_end_day_input_box.get()
            c_process = self.defect_data_frame_process_box.get()
            c_process2 = self.defect_data_frame_process_box2.get()
            c_symptom = self.defect_data_frame_symptom_box.get()
            c_solder = self.defect_data_frame_solder_box.get()
            if c_process == "" or c_process == "*":
                process1 = "'新局所'"
                process2 = "'新局所-新局所'"
                process3 = "'旧局所'"
                process4 = "'旧局所-旧局所'"
                process5 = "'ウェーブ'"
                process6 = "'ウェーブ-ウェーブ'"
                process7 = "'ウェーブ-旧局所'"
                process8 = "'ウェーブ-ポイント'"
                process9 = "'ポイント'"
                process10 = "'ポイント-ポイント'"
                c_process = (process1 + ","
                             + process2 + ","
                             + process3 + ","
                             + process4 + ","
                             + process5 + ","
                             + process6 + ","
                             + process7 + ","
                             + process8 + ","
                             + process9 + ","
                             + process10)
            else:
                c_process = "'" + c_process + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = "AND T_HSDS_data.defect_symptom =" + c_symptom[0]

            if c_solder == "" or c_solder == "*":
                c_solder = ""
            else:
                c_solder = "AND solder ='" + c_solder + "'"

            # production volume
            d_production_volume = get_production_volume("f_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for p_number in d_production_volume:
                list1.append(p_number[1])
            self.defect_data_frame_production_number_box.delete(0, tk.END)
            self.defect_data_frame_production_number_box.insert(0, sum(list1))

            # production sheet volume
            d_production_sheet_volume = get_production_sheet_volume("f_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for p_number in d_production_sheet_volume:
                list1.append(p_number[1])
            self.defect_data_frame_multiple_number_box.delete(0, tk.END)
            self.defect_data_frame_multiple_number_box.insert(0, sum(list1))

            # insertion point volume
            d_insertion_point_volume = get_insertion_point_volume("f_date", c_start_day, c_end_day, c_process, c_process2, c_solder)
            list1 = []
            for i_p_number in d_insertion_point_volume:
                list1.append(i_p_number[1])
            self.defect_data_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_data_frame_insertion_point_number_box.insert(0, sum(list1))

            # defect volume
            d_defect_volume = get_defect_volume("f_date", c_start_day, c_end_day, c_process, c_process2, c_solder, c_symptom)
            list1 = []
            for d_number in d_defect_volume:
                list1.append(d_number[0])
            self.defect_data_frame_defect_number_box.delete(0, tk.END)
            self.defect_data_frame_defect_number_box.insert(0, sum(list1))

            # defect rate
            denominator = self.defect_data_frame_insertion_point_number_box.get()
            numerator = self.defect_data_frame_defect_number_box.get()
            if int(denominator) == 0:
                self.defect_data_frame_defect_rate_box.delete(0, tk.END)
                self.defect_data_frame_defect_rate_box.insert(tk.END, "0")
            else:
                rate = int(numerator) / int(denominator) * 100
                self.defect_data_frame_defect_rate_box.delete(0, tk.END)
                self.defect_data_frame_defect_rate_box.insert(0, str(round(rate, 1)))

            # worst list
            d_worst_list = get_defect_worst_list("f_date", c_start_day, c_end_day, c_process, c_process2, c_solder, c_symptom)
            count_a = 0
            count_y1 = 520
            for column in d_worst_list:
                if count_a < 10:
                    count_a += 1
                    count_y1 += 40
                    if not column:
                        self.defect_data_frame_label = tk.Label(self.defect_data_frame, text="不良無し",
                                                                font=my_font.myfont(15))
                        self.defect_data_frame_label.place(x=10, y=560)
                    else:
                        result_1 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[0],
                                                                           font=my_font.myfont(15))
                        result_1.place(x=120, y=count_y1)
                        result_2 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[1],
                                                                           font=my_font.myfont(15))
                        result_2.place(x=300, y=count_y1)
                        result_3 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[2],
                                                                           font=my_font.myfont(15))
                        result_3.place(x=450, y=count_y1)
                        result_4 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[3],
                                                                           font=my_font.myfont(15))
                        result_4.place(x=600, y=count_y1)
                        result_5 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[4],
                                                                           font=my_font.myfont(15))
                        result_5.place(x=750, y=count_y1)
                        result_6 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[5],
                                                                           font=my_font.myfont(15))
                        result_6.place(x=950, y=count_y1)
                        result_7 = self.defect_data_frame_label = tk.Label(self.defect_data_frame, text=column[6],
                                                                           font=my_font.myfont(15))
                        result_7.place(x=1050, y=count_y1)

        def goto_defect_data_frame_yesterday_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_data_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            self.defect_data_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_two_days_before_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_data_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            self.defect_data_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_three_days_before_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_data_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            self.defect_data_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_week_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_data_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(weeks=1)))
            self.defect_data_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_month_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput month
            d_month = date.today()
            self.defect_data_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1)))
            self.defect_data_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month + 1, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_previous_button_click():
            # inputbox clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput month
            d_month = date.today()
            self.defect_data_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month - 1, 1)))
            self.defect_data_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_period_button_click():
            # search result clear
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            # goto search results
            data_search_results()

        def goto_defect_data_frame_renew_button_click():
            # search result clear
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_start_day_input_box.insert(0, str(today))
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.insert(0, str(today))
            self.defect_data_frame_process_box.delete(0, tk.END)
            self.defect_data_frame_process_box.insert(0, "*")
            self.defect_data_frame_process_box2.delete(0, tk.END)
            self.defect_data_frame_process_box2.insert(0, "*")
            self.defect_data_frame_symptom_box.delete(0, tk.END)
            self.defect_data_frame_symptom_box.insert(0, "*")
            self.defect_data_frame_solder_box.delete(0, tk.END)
            self.defect_data_frame_solder_box.insert(0, "*")
            self.defect_data_frame_production_number_box.delete(0, tk.END)
            self.defect_data_frame_multiple_number_box.delete(0, tk.END)
            self.defect_data_frame_defect_number_box.delete(0, tk.END)
            self.defect_data_frame_defect_rate_box.delete(0, tk.END)
            self.defect_data_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)

        def goto_menu_from_defect_data_button_click():
            self.defect_data_frame_start_day_input_box.delete(0, tk.END)
            self.defect_data_frame_start_day_input_box.insert(0, str(today))
            self.defect_data_frame_end_day_input_box.delete(0, tk.END)
            self.defect_data_frame_end_day_input_box.insert(0, str(today))
            self.defect_data_frame_process_box.delete(0, tk.END)
            self.defect_data_frame_process_box.insert(0, "*")
            self.defect_data_frame_process_box2.delete(0, tk.END)
            self.defect_data_frame_process_box2.insert(0, "*")
            self.defect_data_frame_symptom_box.delete(0, tk.END)
            self.defect_data_frame_symptom_box.insert(0, "*")
            self.defect_data_frame_solder_box.delete(0, tk.END)
            self.defect_data_frame_solder_box.insert(0, "*")
            self.defect_data_frame_production_number_box.delete(0, tk.END)
            self.defect_data_frame_multiple_number_box.delete(0, tk.END)
            self.defect_data_frame_defect_number_box.delete(0, tk.END)
            self.defect_data_frame_defect_rate_box.delete(0, tk.END)
            self.defect_data_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_data_frame_label = tk.Label(self.defect_data_frame,
                                                    text='   ',
                                                    font=my_font.myfont(999))
            self.defect_data_frame_label.place(x=120, y=560)
            self.menu_frame.tkraise()

        # -----------------------------defect_sasizu_frame-----------------------------
        # define frame
        self.defect_sasizu_frame = tk.Frame()
        self.defect_sasizu_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text="指図別不良集計",
                                                  font=my_font.myfont(30))
        self.defect_sasizu_frame_label.place(x=10, y=10)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text="■検索条件■",
                                                  font=my_font.myfont(20))
        self.defect_sasizu_frame_label.place(x=50, y=100)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='指図：',
                                                  font=my_font.myfont(20))
        self.defect_sasizu_frame_label.place(x=50, y=150)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='登録データが消えるので注意↓',
                                                  font=my_font.myfont(20))
        self.defect_sasizu_frame_label.place(x=800, y=100)
        self.defect_sasizu_frame_sasizu_input_box = tk.Entry(self.defect_sasizu_frame,
                                                             width=15,
                                                             font=my_font.myfont(20))
        self.defect_sasizu_frame_sasizu_input_box.place(x=150, y=150)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_sasizu_frame_label.place(x=100, y=200)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text="■検索結果■",
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=100, y=220)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='指図：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=120, y=260)
        self.defect_sasizu_frame_sasizu_box = tk.Entry(self.defect_sasizu_frame,
                                                       width=12,
                                                       justify="left",
                                                       font=my_font.myfont(15))
        self.defect_sasizu_frame_sasizu_box.place(x=190, y=260)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='品目：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=400, y=260)
        self.defect_sasizu_frame_typeid_box = tk.Entry(self.defect_sasizu_frame,
                                                       width=12,
                                                       justify="left",
                                                       font=my_font.myfont(15))
        self.defect_sasizu_frame_typeid_box.place(x=470, y=260)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='工程：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=660, y=260)
        self.defect_sasizu_frame_process_box = tk.Entry(self.defect_sasizu_frame,
                                                        width=12,
                                                        justify="left",
                                                        font=my_font.myfont(15))
        self.defect_sasizu_frame_process_box.place(x=750, y=260)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='はんだ：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=920, y=260)
        self.defect_sasizu_frame_solder_box = tk.Entry(self.defect_sasizu_frame,
                                                       width=12,
                                                       justify="left",
                                                       font=my_font.myfont(15))
        self.defect_sasizu_frame_solder_box.place(x=1000, y=260)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='生産ロット：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=120, y=295)
        self.defect_sasizu_frame_production_number_box = tk.Entry(self.defect_sasizu_frame,
                                                                  width=12,
                                                                  justify="right",
                                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_production_number_box.place(x=230, y=295)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='台',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=380, y=295)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='シート数：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=450, y=295)
        self.defect_sasizu_frame_multiple_number_box = tk.Entry(self.defect_sasizu_frame,
                                                                width=12,
                                                                justify="right",
                                                                font=my_font.myfont(15))
        self.defect_sasizu_frame_multiple_number_box.place(x=545, y=295)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='自動はんだ付け部品数：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=780, y=295)
        self.defect_sasizu_frame_insertion_point_number_box = tk.Entry(self.defect_sasizu_frame,
                                                                       width=12,
                                                                       justify="right",
                                                                       font=my_font.myfont(15))
        self.defect_sasizu_frame_insertion_point_number_box.place(x=1000, y=295)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='点',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=1150, y=295)

        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='不良件数：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=120, y=330)
        self.defect_sasizu_frame_defect_number_box = tk.Entry(self.defect_sasizu_frame,
                                                              width=12,
                                                              justify="right",
                                                              font=my_font.myfont(15))
        self.defect_sasizu_frame_defect_number_box.place(x=230, y=330)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='件',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=380, y=330)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='不良率：',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=450, y=330)
        self.defect_sasizu_frame_defect_rate_box = tk.Entry(self.defect_sasizu_frame,
                                                            width=12,
                                                            justify="right",
                                                            font=my_font.myfont(15))
        self.defect_sasizu_frame_defect_rate_box.place(x=545, y=330)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='%',
                                                  font=my_font.myfont(15))
        self.defect_sasizu_frame_label.place(x=695, y=330)

        # worst title
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="日付", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=120, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="品目", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=280, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="作業者", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=440, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="シンボル", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=600, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="不良項目", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=760, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="件数", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=920, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame, text="備考", font=my_font.myfont(12))
        self.defect_sasizu_frame_label.place(x=1020, y=380)
        self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_sasizu_frame_label.place(x=120, y=405)

        # renew button
        self.defect_sasizu_frame_button = tk.Button(self.defect_sasizu_frame,
                                                    text="リセット",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=10,
                                                    command=lambda: goto_defect_sasizu_frame_renew_button_click())
        self.defect_sasizu_frame_button.place(x=320, y=10)

        # search button
        self.defect_sasizu_frame_search_button = tk.Button(self.defect_sasizu_frame,
                                                           text="検索",
                                                           font=my_font.myfont(20),
                                                           height=1,
                                                           width=5,
                                                           command=lambda: goto_defect_sasizu_frame_search_button_click())
        self.defect_sasizu_frame_search_button.place(x=430, y=140)

        # delete button
        self.defect_sasizu_frame_delete_button = tk.Button(self.defect_sasizu_frame,
                                                           text="指図削除",
                                                           font=my_font.myfont(20),
                                                           height=1,
                                                           width=8,
                                                           command=lambda: goto_defect_sasizu_frame_defect_button_click())
        self.defect_sasizu_frame_delete_button.place(x=1000, y=140)

        # csv output button
        self.defect_sasizu_frame_csv_button = tk.Button(self.defect_sasizu_frame,
                                                        text="CSV",
                                                        font=my_font.myfont(20),
                                                        height=1,
                                                        width=8,
                                                        command=lambda: goto_defect_sasizu_frame_csv_button_click())
        self.defect_sasizu_frame_csv_button.place(x=550, y=140)

        # back button -go to menu_frame-
        self.defect_sasizu_back_button = tk.Button(self.defect_sasizu_frame,
                                                   text="戻る",
                                                   font=my_font.myfont(20),
                                                   height=1,
                                                   width=10,
                                                   command=lambda: goto_menu_from_defect_sasizu_button_click())
        self.defect_sasizu_back_button.place(x=520, y=10)

        def goto_defect_sasizu_frame_csv_button_click():
            c_sasizu = self.defect_sasizu_frame_sasizu_box.get().replace('\n', '')
            # worst list
            d_worst_list = get_defect_sasizu_worst_list_csv(c_sasizu)
            texta = os.getcwd()
            messagebox.showinfo("ファイル保存場所", texta + '/指図別不良集計データ.csv')
            with open(texta + '/指図別不良集計データ.csv', 'w', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["日付", "品目", "作業者", "シンボル", "不良項目", "件数", "備考"])
                for column in d_worst_list:
                    writer.writerow(column)
            # open folder
            path = texta
            path = os.path.realpath(path)
            os.startfile(path)

        def defect_sasizu_search_results():
            c_sasizu = self.defect_sasizu_frame_sasizu_input_box.get().replace('\n', '')
            # sasizu data extract
            result = existence_check_sasizu_data(c_sasizu)
            if not result:
                messagebox.showerror("エラー", "データが見つかりませんでした。")
                return
            else:
                self.defect_sasizu_frame_sasizu_box.insert(0, result[0][0])
                self.defect_sasizu_frame_typeid_box.insert(0, result[0][1])
                self.defect_sasizu_frame_process_box.insert(0, result[0][2])
                self.defect_sasizu_frame_solder_box.insert(0, result[0][3])
                self.defect_sasizu_frame_production_number_box.insert(0, result[0][4])
                if not result[0][5]:
                    self.defect_sasizu_frame_multiple_number_box.insert(0, "0")
                else:
                    self.defect_sasizu_frame_multiple_number_box.insert(0, result[0][5])
                self.defect_sasizu_frame_insertion_point_number_box.insert(0, result[0][6])

                # defect volume
                c_defect_volume = sum_result("T_HSDS_data", "defect_number", "orderNumber = '" + c_sasizu + "'")
                self.defect_sasizu_frame_defect_number_box.insert(0, c_defect_volume)

                # defect rate
                denominator = self.defect_sasizu_frame_insertion_point_number_box.get()
                numerator = self.defect_sasizu_frame_defect_number_box.get()
                if int(denominator) == 0:
                    self.defect_sasizu_frame_defect_rate_box.delete(0, tk.END)
                    self.defect_sasizu_frame_defect_rate_box.insert(tk.END, "0")
                else:
                    rate = int(numerator) / int(denominator) * 100
                    self.defect_sasizu_frame_defect_rate_box.delete(0, tk.END)
                    self.defect_sasizu_frame_defect_rate_box.insert(0, str(round(rate, 1)))

                # worst list
                d_worst_list = get_defect_sasizu_worst_list(c_sasizu)
                count_a = 0
                count_y1 = 400
                for column in d_worst_list:
                    if count_a < 20:
                        count_a += 1
                        count_y1 += 30

                        result_1 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[0],
                                                                             font=my_font.myfont(12))
                        result_1.place(x=120, y=count_y1)
                        result_2 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[1],
                                                                             font=my_font.myfont(12))
                        result_2.place(x=280, y=count_y1)
                        result_3 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[2],
                                                                             font=my_font.myfont(12))
                        result_3.place(x=440, y=count_y1)
                        result_4 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[3],
                                                                             font=my_font.myfont(12))
                        result_4.place(x=600, y=count_y1)
                        result_5 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[4],
                                                                             font=my_font.myfont(12))
                        result_5.place(x=760, y=count_y1)
                        result_6 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[5],
                                                                             font=my_font.myfont(12))
                        result_6.place(x=920, y=count_y1)
                        result_6 = self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                                             text=column[6],
                                                                             font=my_font.myfont(12))
                        result_6.place(x=1020, y=count_y1)

                self.defect_sasizu_frame_sasizu_input_box.delete(0, tk.END)

        def goto_defect_sasizu_frame_search_button_click():
            self.defect_sasizu_frame_sasizu_box.delete(0, tk.END)
            self.defect_sasizu_frame_typeid_box.delete(0, tk.END)
            self.defect_sasizu_frame_process_box.delete(0, tk.END)
            self.defect_sasizu_frame_solder_box.delete(0, tk.END)
            self.defect_sasizu_frame_production_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_multiple_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_rate_box.delete(0, tk.END)
            self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_sasizu_frame_label.place(x=120, y=420)
            # goto search results
            defect_sasizu_search_results()

        def goto_defect_sasizu_frame_defect_button_click():
            get_sasizu = self.defect_sasizu_frame_sasizu_box.get().replace('\n', '')
            if get_sasizu is None:
                messagebox.showerror("エラー", "指図が選択されていません。")
                self.defect_sasizu_frame_sasizu_input_box.focus_set()
                goto_defect_sasizu_frame_renew_button_click()
                return

            chk_sasizu = existence_check("T_HSDS_data", "orderNumber", "orderNumber = '" + get_sasizu + "'")

            if chk_sasizu == 0:
                messagebox.showerror("エラー", "指図が存在しません。")
                self.defect_sasizu_frame_sasizu_input_box.focus_set()
                goto_defect_sasizu_frame_renew_button_click()
                return

            get_ask = messagebox.askyesno("確認", "指図の全てを削除しますか？")
            if get_ask is True:
                data_delete("T_HSDS_data", "orderNumber = '" + get_sasizu + "'")

            # reset
            goto_defect_sasizu_frame_renew_button_click()

        def goto_defect_sasizu_frame_renew_button_click():
            self.defect_sasizu_frame_sasizu_input_box.delete(0, tk.END)
            self.defect_sasizu_frame_sasizu_box.delete(0, tk.END)
            self.defect_sasizu_frame_typeid_box.delete(0, tk.END)
            self.defect_sasizu_frame_process_box.delete(0, tk.END)
            self.defect_sasizu_frame_solder_box.delete(0, tk.END)
            self.defect_sasizu_frame_production_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_multiple_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_rate_box.delete(0, tk.END)
            self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_sasizu_frame_label.place(x=120, y=420)

        def goto_menu_from_defect_sasizu_button_click():
            self.defect_sasizu_frame_sasizu_input_box.delete(0, tk.END)
            self.defect_sasizu_frame_sasizu_box.delete(0, tk.END)
            self.defect_sasizu_frame_typeid_box.delete(0, tk.END)
            self.defect_sasizu_frame_process_box.delete(0, tk.END)
            self.defect_sasizu_frame_solder_box.delete(0, tk.END)
            self.defect_sasizu_frame_production_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_multiple_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_number_box.delete(0, tk.END)
            self.defect_sasizu_frame_defect_rate_box.delete(0, tk.END)
            self.defect_sasizu_frame_label = tk.Label(self.defect_sasizu_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_sasizu_frame_label.place(x=120, y=420)
            self.menu_frame.tkraise()

        # -----------------------------defect_typeID_frame-----------------------------
        # define frame
        self.defect_typeid_frame = tk.Frame()
        self.defect_typeid_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text="品目別不良集計",
                                                  font=my_font.myfont(30))
        self.defect_typeid_frame_label.place(x=10, y=10)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text="■検索条件■",
                                                  font=my_font.myfont(20))
        self.defect_typeid_frame_label.place(x=50, y=100)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='期間：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=50, y=150)
        self.defect_typeid_frame_start_day_input_box = tk.Entry(self.defect_typeid_frame,
                                                                width=11,
                                                                font=my_font.myfont(15))
        self.defect_typeid_frame_start_day_input_box.place(x=120, y=150)
        adjustday = datetime.timedelta(weeks=1)
        self.defect_typeid_frame_start_day_input_box.insert(0, str(today - adjustday))
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='~',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=265, y=150)
        self.defect_typeid_frame_end_day_input_box = tk.Entry(self.defect_typeid_frame,
                                                              width=11,
                                                              font=my_font.myfont(15))
        self.defect_typeid_frame_end_day_input_box.place(x=300, y=150)
        self.defect_typeid_frame_end_day_input_box.insert(0, str(today))
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='品目：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=50, y=190)

        # ----- input box -----
        # combo box -typeid-
        self.defect_typeid_frame_typeid_box = ttk.Combobox(self.defect_typeid_frame,
                                                           values=get_combo_typeid(),
                                                           width=12,
                                                           font=my_font.myfont(15))
        self.defect_typeid_frame_typeid_box.place(x=140, y=190)
        self.defect_typeid_frame_typeid_box.insert(0, "*")
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='不良項目：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=510, y=190)
        # combo box -symptom-
        self.defect_typeid_frame_symptom_box = ttk.Combobox(self.defect_typeid_frame,
                                                            values=get_symptom(),
                                                            width=30,
                                                            font=my_font.myfont(15))
        self.defect_typeid_frame_symptom_box.place(x=620, y=190)
        self.defect_typeid_frame_symptom_box.insert(0, "*")
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='作業者：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=510, y=225)
        # combo box -employee-
        self.defect_typeid_frame_employee_box = ttk.Combobox(self.defect_typeid_frame,
                                                             values=get_employee_number_name(),
                                                             width=30,
                                                             font=my_font.myfont(15))
        self.defect_typeid_frame_employee_box.place(x=620, y=225)
        self.defect_typeid_frame_employee_box.insert(0, "*")
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='シンボル：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=50, y=225)
        # combo box symbol--
        get_typeid = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_typeid_box.get())).replace('\n', '')
        self.defect_typeid_frame_symbol_box = ttk.Combobox(self.defect_typeid_frame,
                                                           values=get_symbol(get_typeid),
                                                           width=10,
                                                           font=my_font.myfont(15))
        self.defect_typeid_frame_symbol_box.place(x=140, y=225)
        self.defect_typeid_frame_symbol_box.insert(0, "*")
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_typeid_frame_label.place(x=100, y=260)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text="■検索結果■",
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=100, y=280)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='生産台数：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=120, y=320)
        self.defect_typeid_frame_production_number_box = tk.Entry(self.defect_typeid_frame,
                                                                  width=12,
                                                                  justify="right",
                                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_production_number_box.place(x=230, y=320)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='台',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=380, y=320)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='生産シート数：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=450, y=320)
        self.defect_typeid_frame_multiple_number_box = tk.Entry(self.defect_typeid_frame,
                                                                width=12,
                                                                justify="right",
                                                                font=my_font.myfont(15))
        self.defect_typeid_frame_multiple_number_box.place(x=670, y=320)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='シート',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=820, y=320)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='不良件数：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=120, y=360)
        self.defect_typeid_frame_defect_number_box = tk.Entry(self.defect_typeid_frame,
                                                              width=12,
                                                              justify="right",
                                                              font=my_font.myfont(15))
        self.defect_typeid_frame_defect_number_box.place(x=230, y=360)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='件',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=380, y=360)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='自動はんだ付け部品数：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=450, y=360)
        self.defect_typeid_frame_insertion_point_number_box = tk.Entry(self.defect_typeid_frame,
                                                                       width=12,
                                                                       justify="right",
                                                                       font=my_font.myfont(15))
        self.defect_typeid_frame_insertion_point_number_box.place(x=670, y=360)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='件',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=820, y=360)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='不良率：',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=120, y=400)
        self.defect_typeid_frame_defect_rate_box = tk.Entry(self.defect_typeid_frame,
                                                            width=12,
                                                            justify="right",
                                                            font=my_font.myfont(15))
        self.defect_typeid_frame_defect_rate_box.place(x=230, y=400)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='%',
                                                  font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=380, y=400)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_typeid_frame_label.place(x=100, y=450)

        # worst title
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="■不良一覧 Worst10■", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=100, y=470)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="品目", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=120, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="作業者", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=260, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="工程", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=400, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="不良項目", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=550, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="シンボル", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=670, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="部品番号", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=800, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="件数", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=980, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="備考", font=my_font.myfont(15))
        self.defect_typeid_frame_label.place(x=1060, y=510)
        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                  text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                  font=my_font.myfont(10))
        self.defect_typeid_frame_label.place(x=120, y=540)

        # ----- button setting -----
        # renew button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="リセット",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=10,
                                                    command=lambda: goto_defect_typeid_frame_renew_button_click())
        self.defect_typeid_frame_button.place(x=320, y=10)

        # yesterday button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="前日",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_yesterday_button_click())
        self.defect_typeid_frame_button.place(x=450, y=120)

        # two days before button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="2日前",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_two_days_before_button_click())
        self.defect_typeid_frame_button.place(x=550, y=120)

        # three days before button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="3日前",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_three_days_before_button_click())
        self.defect_typeid_frame_button.place(x=650, y=120)

        # week button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="週間",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_week_button_click())
        self.defect_typeid_frame_button.place(x=750, y=120)

        # month button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="今月",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_month_button_click())
        self.defect_typeid_frame_button.place(x=850, y=120)

        # previous button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="前月",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=5,
                                                    command=lambda: goto_defect_typeid_frame_previous_button_click())
        self.defect_typeid_frame_button.place(x=950, y=120)

        # data button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="指定期間",
                                                    font=my_font.myfont(20),
                                                    height=1,
                                                    width=8,
                                                    command=lambda: goto_defect_typeid_frame_period_button_click())
        self.defect_typeid_frame_button.place(x=1050, y=120)

        # symbol combo box renew button
        self.defect_typeid_frame_button = tk.Button(self.defect_typeid_frame,
                                                    text="シンボル更新",
                                                    font=my_font.myfont(15),
                                                    height=1,
                                                    width=10,
                                                    command=lambda: goto_defect_typeid_frame_symbol_renew_button_click())
        self.defect_typeid_frame_button.place(x=320, y=190)

        # csv output button
        self.defect_typeid_frame_csv_button = tk.Button(self.defect_typeid_frame,
                                                        text="CSV",
                                                        font=my_font.myfont(20),
                                                        height=1,
                                                        width=8,
                                                        command=lambda: goto_defect_typeid_frame_csv_button_click())
        self.defect_typeid_frame_csv_button.place(x=1050, y=200)

        # back button -go to menu_frame-
        self.defect_typeid_back_button = tk.Button(self.defect_typeid_frame,
                                                   text="戻る",
                                                   font=my_font.myfont(20),
                                                   height=1,
                                                   width=10,
                                                   command=lambda: goto_menu_from_defect_typeid_button_click())
        self.defect_typeid_back_button.place(x=520, y=10)

        def goto_defect_typeid_frame_csv_button_click():
            c_start_day = mojimoji.zen_to_han(self.defect_typeid_frame_start_day_input_box.get())
            c_end_day = mojimoji.zen_to_han(self.defect_typeid_frame_end_day_input_box.get())
            combo_typeid = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_typeid_box.get())).replace('\n', '')
            l_typeid = combo_typeid.replace("*", "")
            if combo_typeid == "":
                combo_typeid = "*"
            c_end_typeid = combo_typeid[-1]
            c_symptom = mojimoji.zen_to_han(self.defect_typeid_frame_symptom_box.get())
            c_symbol = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_symbol_box.get())).replace('\n', '')
            c_employee = mojimoji.zen_to_han(self.defect_typeid_frame_employee_box.get())
            if combo_typeid == "" or combo_typeid == "*":
                combo_typeid = ""
            elif c_end_typeid == "*":
                combo_typeid = "AND typeid LIKE'" + l_typeid + "%'"
            else:
                combo_typeid = "AND typeid ='" + combo_typeid + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = " AND T_HSDS_data.defect_symptom ='" + c_symptom[0] + "'"

            if c_symbol == "" or c_symbol == "*":
                c_symbol = ""
            else:
                c_symbol = "AND defect_symbol ='" + c_symbol + "'"

            if c_employee == "" or c_employee == "*":
                c_employee = ""
            else:
                c_employee = " AND T_HSDS_data.employee_number ='" + c_employee[0:5] + "'"

            # worst list
            d_worst_list = get_defect_typeid_worst_list_csv(c_start_day, c_end_day, combo_typeid, c_symptom, c_symbol, c_employee)
            texta = os.getcwd()
            messagebox.showinfo("ファイル保存場所", texta + '/品目別不良集計データ.csv')
            with open(texta + '/品目別不良集計データ.csv', 'w', newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["品目", "作業者", "工程", "不良項目", "シンボル", "部品番号", "件数", "備考"])
                for column in d_worst_list:
                    writer.writerow(column)
            # open folder
            path = texta
            path = os.path.realpath(path)
            os.startfile(path)

        def typeid_search_results():
            c_start_day = mojimoji.zen_to_han(self.defect_typeid_frame_start_day_input_box.get())
            c_end_day = mojimoji.zen_to_han(self.defect_typeid_frame_end_day_input_box.get())
            combo_typeid = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_typeid_box.get())).replace('\n', '')
            l_typeid = combo_typeid.replace("*", "")
            if combo_typeid == "":
                combo_typeid = "*"
            c_end_typeid = combo_typeid[-1]
            c_symptom = mojimoji.zen_to_han(self.defect_typeid_frame_symptom_box.get())
            c_symbol = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_symbol_box.get())).replace('\n', '')
            c_employee = mojimoji.zen_to_han(self.defect_typeid_frame_employee_box.get())
            if combo_typeid == "" or combo_typeid == "*":
                combo_typeid = ""
            elif c_end_typeid == "*":
                combo_typeid = "AND typeid LIKE'" + l_typeid + "%'"
            else:
                combo_typeid = "AND typeid ='" + combo_typeid + "'"

            if c_symptom == "" or c_symptom == "*" or c_symptom == "* ALL":
                c_symptom = ""
            else:
                c_symptom = " AND T_HSDS_data.defect_symptom ='" + c_symptom[0] + "'"

            if c_symbol == "" or c_symbol == "*":
                c_symbol = ""
            else:
                c_symbol = "AND defect_symbol ='" + c_symbol + "'"

            if c_employee == "" or c_employee == "*":
                c_employee = ""
            else:
                c_employee = " AND T_HSDS_data.employee_number ='" + c_employee[0:5] + "'"

            # production volume
            d_production_volume = get_typeid_production_volume(c_start_day, c_end_day, combo_typeid, c_employee)
            list1 = []
            for p_number in d_production_volume:
                list1.append(p_number[1])
            self.defect_typeid_frame_production_number_box.delete(0, tk.END)
            self.defect_typeid_frame_production_number_box.insert(0, sum(list1))

            # production sheet volume
            d_production_sheet_volume = get_typeid_production_sheet_volume(c_start_day, c_end_day, combo_typeid, c_employee)
            list1 = []
            for i_p_number in d_production_sheet_volume:
                list1.append(i_p_number[1])
            self.defect_typeid_frame_multiple_number_box.delete(0, tk.END)
            self.defect_typeid_frame_multiple_number_box.insert(0, sum(list1))

            # insertion point volume
            d_insertion_point_volume = get_typeid_insertion_point_volume(c_start_day, c_end_day, combo_typeid, c_employee)
            list1 = []
            for i_p_number in d_insertion_point_volume:
                list1.append(i_p_number[1])
            self.defect_typeid_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_typeid_frame_insertion_point_number_box.insert(0, sum(list1))

            # defect volume
            d_defect_volume = get_pre_typeid_defect_volume(c_start_day, c_end_day, combo_typeid, c_symptom, c_symbol, c_employee)
            list1 = []
            for d_number in d_defect_volume:
                list1.append(d_number[0])
            self.defect_typeid_frame_defect_number_box.delete(0, tk.END)
            self.defect_typeid_frame_defect_number_box.insert(0, sum(list1))

            # defect rate
            denominator = self.defect_typeid_frame_insertion_point_number_box.get()
            numerator = self.defect_typeid_frame_defect_number_box.get()
            if int(denominator) == 0:
                self.defect_typeid_frame_defect_rate_box.delete(0, tk.END)
                self.defect_typeid_frame_defect_rate_box.insert(tk.END, "0")
            else:
                rate = int(numerator) / int(denominator) * 100
                self.defect_typeid_frame_defect_rate_box.delete(0, tk.END)
                self.defect_typeid_frame_defect_rate_box.insert(0, str(round(rate, 1)))

            # worst list
            d_worst_list = get_defect_typeid_worst_list(c_start_day, c_end_day, combo_typeid, c_symptom, c_symbol, c_employee)
            count_a = 0
            count_y1 = 520
            for column in d_worst_list:
                if count_a < 10:
                    count_a += 1
                    count_y1 += 40
                    if not column:
                        self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame, text="不良無し",
                                                                  font=my_font.myfont(15))
                        self.defect_typeid_frame_label.place(x=10, y=560)
                    else:
                        result_1 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[0],
                                                                             font=my_font.myfont(15))
                        result_1.place(x=120, y=count_y1)
                        result_2 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[1],
                                                                             font=my_font.myfont(15))
                        result_2.place(x=260, y=count_y1)
                        result_3 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[2],
                                                                             font=my_font.myfont(15))
                        result_3.place(x=400, y=count_y1)
                        result_4 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[3],
                                                                             font=my_font.myfont(15))
                        result_4.place(x=550, y=count_y1)
                        result_5 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[4],
                                                                             font=my_font.myfont(15))
                        result_5.place(x=670, y=count_y1)
                        result_6 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[5],
                                                                             font=my_font.myfont(15))
                        result_6.place(x=800, y=count_y1)
                        result_7 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[6],
                                                                             font=my_font.myfont(15))
                        result_7.place(x=980, y=count_y1)
                        result_8 = self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                                             text=column[7],
                                                                             font=my_font.myfont(15))
                        result_8.place(x=1060, y=count_y1)

        def goto_defect_typeid_frame_symbol_renew_button_click():
            # combo box symbol--
            get_c_typeid = mojimoji.zen_to_han(str.upper(self.defect_typeid_frame_typeid_box.get())).replace('\n', '')
            d_symbol = get_symbol(get_c_typeid)
            self.defect_typeid_frame_symbol_box = ttk.Combobox(self.defect_typeid_frame,
                                                               values=d_symbol,
                                                               width=10,
                                                               font=my_font.myfont(15))
            self.defect_typeid_frame_symbol_box.place(x=140, y=225)
            self.defect_typeid_frame_symbol_box.insert(0, "*")

        def goto_defect_typeid_frame_yesterday_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_two_days_before_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=2)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_three_days_before_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=3)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_week_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput yesterday
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today - datetime.timedelta(weeks=1)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today - datetime.timedelta(days=1)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_month_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput month
            d_month = date.today()
            self.defect_typeid_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month + 1, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_previous_button_click():
            # inputbox clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            # inputbox datainput month
            d_month = date.today()
            self.defect_typeid_frame_start_day_input_box.insert(0, str(date(d_month.year, d_month.month - 1, 1)))
            self.defect_typeid_frame_end_day_input_box.insert(0, str(date(d_month.year, d_month.month, 1) - datetime.timedelta(days=1)))
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_period_button_click():
            # search result clear
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            # goto search results
            typeid_search_results()

        def goto_defect_typeid_frame_renew_button_click():
            # search result clear
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today))
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today))
            self.defect_typeid_frame_typeid_box.delete(0, tk.END)
            self.defect_typeid_frame_typeid_box.insert(0, "*")
            self.defect_typeid_frame_symptom_box.delete(0, tk.END)
            self.defect_typeid_frame_symptom_box.insert(0, "*")
            self.defect_typeid_frame_symbol_box.delete(0, tk.END)
            self.defect_typeid_frame_symbol_box.insert(0, "*")
            self.defect_typeid_frame_employee_box.delete(0, tk.END)
            self.defect_typeid_frame_employee_box.insert(0, "*")
            self.defect_typeid_frame_production_number_box.delete(0, tk.END)
            self.defect_typeid_frame_multiple_number_box.delete(0, tk.END)
            self.defect_typeid_frame_defect_number_box.delete(0, tk.END)
            self.defect_typeid_frame_defect_rate_box.delete(0, tk.END)
            self.defect_typeid_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)

        def goto_menu_from_defect_typeid_button_click():
            self.defect_typeid_frame_start_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_start_day_input_box.insert(0, str(today))
            self.defect_typeid_frame_end_day_input_box.delete(0, tk.END)
            self.defect_typeid_frame_end_day_input_box.insert(0, str(today))
            self.defect_typeid_frame_typeid_box.delete(0, tk.END)
            self.defect_typeid_frame_typeid_box.insert(0, "*")
            self.defect_typeid_frame_symptom_box.delete(0, tk.END)
            self.defect_typeid_frame_symptom_box.insert(0, "*")
            self.defect_typeid_frame_symbol_box.delete(0, tk.END)
            self.defect_typeid_frame_symbol_box.insert(0, "*")
            self.defect_typeid_frame_employee_box.delete(0, tk.END)
            self.defect_typeid_frame_employee_box.insert(0, "*")
            self.defect_typeid_frame_production_number_box.delete(0, tk.END)
            self.defect_typeid_frame_multiple_number_box.delete(0, tk.END)
            self.defect_typeid_frame_defect_number_box.delete(0, tk.END)
            self.defect_typeid_frame_defect_rate_box.delete(0, tk.END)
            self.defect_typeid_frame_insertion_point_number_box.delete(0, tk.END)
            self.defect_typeid_frame_label = tk.Label(self.defect_typeid_frame,
                                                      text='   ',
                                                      font=my_font.myfont(999))
            self.defect_typeid_frame_label.place(x=120, y=560)
            self.menu_frame.tkraise()

        # -----------------------------defect_part_number_frame-----------------------------
        # define frame
        self.defect_part_number_frame = tk.Frame()
        self.defect_part_number_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text="部品番号別不良集計",
                                                       font=my_font.myfont(30))
        self.defect_part_number_frame_label.place(x=10, y=10)
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text="■検索条件■",
                                                       font=my_font.myfont(20))
        self.defect_part_number_frame_label.place(x=50, y=100)
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text='期間：',
                                                       font=my_font.myfont(15))
        self.defect_part_number_frame_label.place(x=50, y=150)
        self.defect_part_number_frame_start_day_input_box = tk.Entry(self.defect_part_number_frame,
                                                                     width=11,
                                                                     font=my_font.myfont(15))
        self.defect_part_number_frame_start_day_input_box.place(x=120, y=150)
        self.defect_part_number_frame_start_day_input_box.insert(0, "2000-01-01")
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text='~',
                                                       font=my_font.myfont(15))
        self.defect_part_number_frame_label.place(x=265, y=150)
        self.defect_part_number_frame_end_day_input_box = tk.Entry(self.defect_part_number_frame,
                                                                   width=11,
                                                                   font=my_font.myfont(15))
        self.defect_part_number_frame_end_day_input_box.place(x=300, y=150)
        self.defect_part_number_frame_end_day_input_box.insert(0, str(today))
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text='品番：',
                                                       font=my_font.myfont(15))
        self.defect_part_number_frame_label.place(x=50, y=190)

        # ----- input box -----
        # combo box -part number-
        d_part_number = get_parts_number()
        self.defect_part_number_frame_part_number_box = ttk.Combobox(self.defect_part_number_frame,
                                                                     values=d_part_number,
                                                                     width=12,
                                                                     font=my_font.myfont(15))
        self.defect_part_number_frame_part_number_box.place(x=120, y=190)
        self.defect_part_number_frame_part_number_box.insert(0, "*")
        # combo box -order by-
        c_order = ["件数順", "指図順"]
        self.defect_part_number_frame_orderby_box = ttk.Combobox(self.defect_part_number_frame,
                                                                 values=c_order,
                                                                 width=12,
                                                                 font=my_font.myfont(15))
        self.defect_part_number_frame_orderby_box.place(x=300, y=190)
        self.defect_part_number_frame_orderby_box.insert(0, "件数順")
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                       font=my_font.myfont(10))
        self.defect_part_number_frame_label.place(x=100, y=225)
        self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                       text="■検索結果■",
                                                       font=my_font.myfont(15))
        self.defect_part_number_frame_label.place(x=100, y=250)

        # ----- button setting -----
        # renew button
        self.defect_part_number_frame_button = tk.Button(self.defect_part_number_frame,
                                                         text="リセット",
                                                         font=my_font.myfont(20),
                                                         height=1,
                                                         width=10,
                                                         command=lambda: goto_defect_part_number_frame_renew_button_click())
        self.defect_part_number_frame_button.place(x=400, y=20)
        # defect search button
        self.defect_part_number_frame_button = tk.Button(self.defect_part_number_frame,
                                                         text="不良検索",
                                                         font=my_font.myfont(20),
                                                         height=1,
                                                         width=9,
                                                         command=lambda: goto_defect_part_number_frame_defect_search_button_click())
        self.defect_part_number_frame_button.place(x=480, y=140)
        # csv button
        self.defect_part_number_frame_csv_button = tk.Button(self.defect_part_number_frame,
                                                             text="CSV",
                                                             font=my_font.myfont(20),
                                                             height=1,
                                                             width=9,
                                                             command=lambda: goto_defect_part_number_frame_csv_button_click())
        self.defect_part_number_frame_csv_button.place(x=640, y=140)
        # back button -go to menu_frame-
        self.defect_part_number_frame_button = tk.Button(self.defect_part_number_frame,
                                                         text="戻る",
                                                         font=my_font.myfont(20),
                                                         height=1,
                                                         width=10,
                                                         command=lambda: goto_menu_from_defect_part_number_button_click())
        self.defect_part_number_frame_button.place(x=600, y=20)

        def goto_defect_part_number_frame_csv_button_click():
            c_symbol = mojimoji.zen_to_han(str.upper(self.defect_part_number_frame_part_number_box.get())).replace('\n', '')
            c_symbol = c_symbol.replace('-', '')
            g_order = self.defect_part_number_frame_orderby_box.get()
            c_start_day = self.defect_part_number_frame_start_day_input_box.get()
            c_end_day = self.defect_part_number_frame_end_day_input_box.get()

            if c_symbol == "" or c_symbol == "*":
                # 全ての部品番号の不良件数（期間指定）
                d_parts_number = get_parts_number_defect_number_all(c_start_day, c_end_day)
                texta = os.getcwd()
                messagebox.showinfo("ファイル保存場所", texta + '/部品番号不良件数データ.csv')
                with open(texta + '/部品番号不良件数データ.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["品番", "不良件数", "指図数"])
                    for column in d_parts_number:
                        writer.writerow(column)
                # open folder
                path = texta
                path = os.path.realpath(path)
                os.startfile(path)

            else:
                # 指定された部品番号の品目-シンボル毎の不良件数（期間指定）
                if g_order == "指図順":
                    g_order = "ORDER BY orderNumber DESC"
                else:
                    g_order = "ORDER BY SUM(defect_number) DESC"
                d_parts_number = get_parts_number_defect_number_symbol(c_start_day, c_end_day, c_symbol, g_order)
                texta = os.getcwd()
                messagebox.showinfo("ファイル保存場所", texta + '/部品番号別不良データ.csv')
                with open(texta + '/部品番号別不良データ.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["部品番号", "指図", "品目", "シンボル", "件数", "不良率(%)"])
                    for column in d_parts_number:
                        writer.writerow(column)
                # open folder
                path = texta
                path = os.path.realpath(path)
                os.startfile(path)

        def goto_defect_part_number_frame_defect_search_button_click():
            c_symbol = mojimoji.zen_to_han(str.upper(self.defect_part_number_frame_part_number_box.get())).replace('\n', '')
            c_symbol = c_symbol.replace('-', '')
            g_order = self.defect_part_number_frame_orderby_box.get()
            c_start_day = self.defect_part_number_frame_start_day_input_box.get()
            c_end_day = self.defect_part_number_frame_end_day_input_box.get()

            # result clear
            self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                           text='   ',
                                                           font=my_font.myfont(999))
            self.defect_part_number_frame_label.place(x=100, y=280)

            if c_symbol == "" or c_symbol == "*":
                # 全ての部品番号の不良件数（期間指定）
                d_parts_number = get_parts_number_defect_number_all(c_start_day, c_end_day)

                # title
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="部品番号 不良件数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=100, y=300)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="品番",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=120, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="不良件数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=300, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="指図数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=450, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="品番",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=670, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="不良件数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=850, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="指図数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=1000, y=340)

                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                               text='------------------------------------------------------------------------------                    ---------------------------------------------------------------------------------',
                                                               font=my_font.myfont(10))
                self.defect_part_number_frame_label.place(x=120, y=370)

                count_a = 0
                count_b = 0
                count_x1 = 120
                count_x2 = 300
                count_x3 = 450
                count_y1 = 360

                for column in d_parts_number:
                    if count_a < 26:
                        if count_b < 12:
                            count_a += 1
                            count_b += 1
                            count_y1 += 40

                            result_1 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[0],
                                                                                      font=my_font.myfont(15))
                            result_1.place(x=count_x1, y=count_y1)
                            result_2 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[1],
                                                                                      font=my_font.myfont(15))
                            result_2.place(x=count_x2, y=count_y1)
                            result_3 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[2],
                                                                                      font=my_font.myfont(15))
                            result_3.place(x=count_x3, y=count_y1)

                        else:
                            count_y1 += 40

                            result_1 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[0],
                                                                                      font=my_font.myfont(15))
                            result_1.place(x=count_x1, y=count_y1)
                            result_2 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[1],
                                                                                      font=my_font.myfont(15))
                            result_2.place(x=count_x2, y=count_y1)
                            result_3 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[2],
                                                                                      font=my_font.myfont(15))
                            result_3.place(x=count_x3, y=count_y1)

                            count_a += 1
                            count_b = 0
                            count_x1 = count_x1 + 550
                            count_x2 = count_x2 + 550
                            count_x3 = count_x3 + 550
                            count_y1 = 360

            else:
                # 指定された部品番号の品目-シンボル毎の不良件数（期間指定）
                if g_order == "指図順":
                    g_order = "ORDER BY orderNumber DESC"
                else:
                    g_order = "ORDER BY SUM(defect_number) DESC"
                d_parts_number = get_parts_number_defect_number_symbol_search(c_start_day, c_end_day, c_symbol, g_order)

                # title
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                               text="部品番号：" + c_symbol + " 不良",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=100, y=300)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="指図",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=120, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="品目",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=250, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="シンボル",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=390, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="件数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=510, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="不良率",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=570, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="指図",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=670, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="品目",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=800, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="シンボル",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=940, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="件数",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=1060, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame, text="不良率",
                                                               font=my_font.myfont(15))
                self.defect_part_number_frame_label.place(x=1120, y=340)
                self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                               text='--------------------------------------------------------------------------------------        --------------------------------------------------------------------------------------',
                                                               font=my_font.myfont(10))
                self.defect_part_number_frame_label.place(x=120, y=370)

                count_a = 0
                count_b = 0
                count_x1 = 120
                count_x2 = 250
                count_x3 = 390
                count_x4 = 510
                count_x5 = 580
                count_y1 = 360

                for column in d_parts_number:
                    if count_a < 26:
                        if count_b < 12:
                            count_a += 1
                            count_b += 1
                            count_y1 += 40
                            rate = (column[3] * 100) // column[4]

                            result_1 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[0],
                                                                                      font=my_font.myfont(15))
                            result_1.place(x=count_x1, y=count_y1)
                            result_2 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[1],
                                                                                      font=my_font.myfont(15))
                            result_2.place(x=count_x2, y=count_y1)
                            result_3 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[2],
                                                                                      font=my_font.myfont(15))
                            result_3.place(x=count_x3, y=count_y1)
                            result_4 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[3],
                                                                                      font=my_font.myfont(15))
                            result_4.place(x=count_x4, y=count_y1)
                            result_5 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=str(rate) + "%",
                                                                                      font=my_font.myfont(15))
                            result_5.place(x=count_x5, y=count_y1)

                        else:
                            count_y1 += 40

                            result_1 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[0],
                                                                                      font=my_font.myfont(15))
                            result_1.place(x=count_x1, y=count_y1)
                            result_2 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[1],
                                                                                      font=my_font.myfont(15))
                            result_2.place(x=count_x2, y=count_y1)
                            result_3 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[2],
                                                                                      font=my_font.myfont(15))
                            result_3.place(x=count_x3, y=count_y1)
                            result_4 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=column[3],
                                                                                      font=my_font.myfont(15))
                            result_4.place(x=count_x4, y=count_y1)
                            result_5 = self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                                                      text=str(rate) + "%",
                                                                                      font=my_font.myfont(15))
                            result_5.place(x=count_x5, y=count_y1)

                            count_a += 1
                            count_b = 0
                            count_x1 = count_x1 + 550
                            count_x2 = count_x2 + 550
                            count_x3 = count_x3 + 550
                            count_x4 = count_x4 + 550
                            count_x5 = count_x5 + 550
                            count_y1 = 360

        def goto_defect_part_number_frame_renew_button_click():
            # search result clear
            self.defect_part_number_frame_start_day_input_box.delete(0, tk.END)
            self.defect_part_number_frame_start_day_input_box.insert(0, "2000-01-01")
            self.defect_part_number_frame_end_day_input_box.delete(0, tk.END)
            self.defect_part_number_frame_end_day_input_box.insert(0, str(today))
            self.defect_part_number_frame_part_number_box.delete(0, tk.END)
            self.defect_part_number_frame_part_number_box.insert(0, "*")
            self.defect_part_number_frame_orderby_box.delete(0, tk.END)
            self.defect_part_number_frame_orderby_box.insert(0, "件数順")
            self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                           text='   ',
                                                           font=my_font.myfont(999))
            self.defect_part_number_frame_label.place(x=100, y=280)

        def goto_menu_from_defect_part_number_button_click():
            self.defect_part_number_frame_start_day_input_box.delete(0, tk.END)
            self.defect_part_number_frame_start_day_input_box.insert(0, "2000-01-01")
            self.defect_part_number_frame_end_day_input_box.delete(0, tk.END)
            self.defect_part_number_frame_end_day_input_box.insert(0, str(today))
            self.defect_part_number_frame_part_number_box.delete(0, tk.END)
            self.defect_part_number_frame_part_number_box.insert(0, "*")
            self.defect_part_number_frame_orderby_box.delete(0, tk.END)
            self.defect_part_number_frame_orderby_box.insert(0, "件数順")
            self.defect_part_number_frame_label = tk.Label(self.defect_part_number_frame,
                                                           text='   ',
                                                           font=my_font.myfont(999))
            self.defect_part_number_frame_label.place(x=100, y=280)
            self.menu_frame.tkraise()


        # -----------------------------hs_admin_frame-----------------------------
        # define frame
        self.hs_admin_frame = tk.Frame()
        self.hs_admin_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.hs_admin_frame_label = tk.Label(self.hs_admin_frame,
                                             text="管理画面",
                                             font=my_font.myfont(30))
        self.hs_admin_frame_label.place(x=10, y=10)

        # change page button -go to typeid_input_frame-
        self.change_page_typeid_Button = tk.Button(self.hs_admin_frame,
                                                   text="品目 変更&追加",
                                                   font=my_font.myfont(20),
                                                   height=5,
                                                   width=20,
                                                   command=lambda: goto_typeid_input_frame_button_click())
        self.change_page_typeid_Button.place(x=50, y=200)

        def goto_typeid_input_frame_button_click():
            self.typeid_input_frame_typeid_input_box.focus_set()
            self.typeid_input_frame.tkraise()

        # change page button -go to symbol_input_frame-
        self.change_page_symbol_Button = tk.Button(self.hs_admin_frame,
                                                   text="部品番号 変更&追加",
                                                   font=my_font.myfont(20),
                                                   height=5,
                                                   width=20,
                                                   command=lambda: goto_part_number_input_frame_button_click())
        self.change_page_symbol_Button.place(x=450, y=200)

        def goto_part_number_input_frame_button_click():
            self.part_number_input_frame_typeid_box.focus_set()
            self.part_number_input_frame.tkraise()

        # change page button -go to operator_input_frame-
        self.change_page_operator_Button = tk.Button(self.hs_admin_frame,
                                                     text="作業者 変更&追加",
                                                     font=my_font.myfont(20),
                                                     height=5,
                                                     width=20,
                                                     command=lambda: goto_operator_input_frame_button_click())
        self.change_page_operator_Button.place(x=850, y=200)

        def goto_operator_input_frame_button_click():
            self.operator_input_frame_name_box.focus_set()
            self.operator_input_frame.tkraise()

        # back button -go to menu_frame-
        self.defect_period_back_button = tk.Button(self.hs_admin_frame,
                                                   text="戻る",
                                                   font=my_font.myfont(20),
                                                   height=1,
                                                   width=10,
                                                   command=lambda: goto_menu_frame())
        self.defect_period_back_button.place(x=520, y=10)

        # -----------------------------typeid_input_frame-----------------------------
        # define frame
        self.typeid_input_frame = tk.Frame()
        self.typeid_input_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                 text="品目 変更&追加",
                                                 font=my_font.myfont(30))
        self.typeid_input_frame_label.place(x=10, y=10)

        # combo box -typeID-
        self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                 text="品目:",
                                                 font=my_font.myfont(30))
        self.typeid_input_frame_label.place(x=50, y=150)
        self.typeid_input_frame_typeid_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                values=get_combo_typeid(),
                                                                width=14,
                                                                font=my_font.myfont(30))
        self.typeid_input_frame_typeid_input_box.place(x=200, y=150)
        self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                 text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                 font=my_font.myfont(10))
        self.typeid_input_frame_label.place(x=100, y=260)
        # ----- button setting -----
        # search button
        self.typeid_search_Button = tk.Button(self.typeid_input_frame,
                                              text="検索",
                                              font=my_font.myfont(20),
                                              width=10,
                                              command=lambda: goto_typeid_input_frame_search_button_click())
        self.typeid_search_Button.place(x=600, y=150)
        # back button -go to hs_admin_frame-
        self.typeid_input_frame_back_button = tk.Button(self.typeid_input_frame,
                                                        text="戻る",
                                                        font=my_font.myfont(20),
                                                        height=1,
                                                        width=10,
                                                        command=lambda: goto_hs_admin_frame_from_typeid_input_frame_button_click())
        self.typeid_input_frame_back_button.place(x=520, y=10)

        def goto_typeid_input_frame_add_button_click():
            # input check
            r_typeid = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_typeid2_input_box.get())).replace('\n', '')
            r_process = self.typeid_input_frame_process_input_box.get()
            r_solder = self.typeid_input_frame_solder_input_box.get()
            r_s1 = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_s1_input_box.get()))
            r_sn = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_sn_input_box.get()))
            r_s1sn = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_s1sn_input_box.get()))
            r_multiple = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_multiple_input_box.get()))
            r_remark = self.typeid_input_frame_remark_input_box.get()
            if r_typeid == "":
                messagebox.showerror("NG", "品目を入力してください。")
                self.typeid_input_frame_typeid2_input_box.focus_set()
                return
            if r_process == "":
                messagebox.showerror("NG", "工程を選択してください。")
                self.typeid_input_frame_process_input_box.focus_set()
                return
            if r_solder == "":
                messagebox.showerror("NG", "はんだを選択してください。")
                self.typeid_input_frame_solder_input_box.focus_set()
                return
            if r_s1 == "":
                messagebox.showerror("NG", "S1部品数を選択してください。")
                self.typeid_input_frame_s1_input_box.focus_set()
                return
            if r_sn == "":
                messagebox.showerror("NG", "Sn部品数を選択してください。")
                self.typeid_input_frame_sn_input_box.focus_set()
                return
            if r_s1sn == "":
                messagebox.showerror("NG", "合計部品数を選択してください。")
                self.typeid_input_frame_s1sn_input_box.focus_set()
                return
            if r_multiple == "":
                messagebox.showerror("NG", "取り数を選択してください。")
                self.typeid_input_frame_multiple_input_box.focus_set()
                return

            # typeid duplication check
            combo_typeid = existence_check("T_HSDS_typeID", "typeID", "typeID = '" + r_typeid + "'")
            if combo_typeid == 0:
                insert_typeid_data(r_typeid, r_process, r_solder, r_sn, r_s1, r_s1sn, r_multiple, r_remark)
                self.typeid_input_frame_typeid2_input_box.delete(0, tk.END)
                self.typeid_input_frame_process_input_box.delete(0, tk.END)
                self.typeid_input_frame_solder_input_box.delete(0, tk.END)
                self.typeid_input_frame_s1_input_box.delete(0, tk.END)
                self.typeid_input_frame_sn_input_box.delete(0, tk.END)
                self.typeid_input_frame_s1sn_input_box.delete(0, tk.END)
                self.typeid_input_frame_multiple_input_box.delete(0, tk.END)
                self.typeid_input_frame_remark_input_box.delete(0, tk.END)

                # blind delete button
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text='   ',
                                                         font=my_font.myfont(999))
                self.typeid_input_frame_label.place(x=50, y=300)

            else:
                messagebox.showerror("NG", "既に登録済みの品目です。")
                self.typeid_input_frame_typeid2_input_box.focus_set()

            # combo box -typeID-
            combo_typeid = get_combo_typeid()
            self.typeid_input_frame_typeid_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=combo_typeid,
                                                                    width=14,
                                                                    font=my_font.myfont(30))
            self.typeid_input_frame_typeid_input_box.place(x=200, y=150)

        def goto_typeid_input_frame_search_button_click():
            combo_typeid = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_typeid_input_box.get())).replace('\n', '')
            search_typeid = get_search_typeid(combo_typeid)

            if not search_typeid:  # data not available
                messagebox.showinfo("品目チェック", "品目が存在しないので新規登録します")

                # blind delete button3
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text='   ',
                                                         font=my_font.myfont(999))
                self.typeid_input_frame_label.place(x=50, y=300)

                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="■新規入力■",
                                                         font=my_font.myfont(30))
                self.typeid_input_frame_label.place(x=50, y=300)

                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="品目：",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=400)
                self.typeid_input_frame_typeid2_input_box = tk.Entry(self.typeid_input_frame,
                                                                     width=15,
                                                                     font=my_font.myfont(20))
                self.typeid_input_frame_typeid2_input_box.place(x=270, y=400)
                self.typeid_input_frame_typeid2_input_box.insert(tk.END, mojimoji.zen_to_han(str.upper(self.typeid_input_frame_typeid_input_box.get())))

                # combo box -process-
                d_process = data_select("T_HSDS_process", "process")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="工程:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=450)
                self.typeid_input_frame_process_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                         values=d_process,
                                                                         width=15,
                                                                         font=my_font.myfont(20))
                self.typeid_input_frame_process_input_box.place(x=270, y=450)

                # combo box -solder-
                d_solder = data_select("T_HSDS_solder", "solder")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="はんだ:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=500)
                self.typeid_input_frame_solder_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                        values=d_solder,
                                                                        width=15,
                                                                        font=my_font.myfont(20))
                self.typeid_input_frame_solder_input_box.place(x=270, y=500)

                # combo box -s1-
                d_s1 = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="S1部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=550)
                self.typeid_input_frame_s1_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=d_s1,
                                                                    width=10,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_s1_input_box.place(x=270, y=550)

                # combo box -sn-
                d_sn = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="Sn部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=600)
                self.typeid_input_frame_sn_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=d_sn,
                                                                    width=10,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_sn_input_box.place(x=270, y=600)

                # combo box -s1sn-
                d_s1sn = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="合計部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=650)
                self.typeid_input_frame_s1sn_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                      values=d_s1sn,
                                                                      width=10,
                                                                      font=my_font.myfont(20))
                self.typeid_input_frame_s1sn_input_box.place(x=270, y=650)

                # combo box -multiple-
                d_multiple = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="取り数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=700)
                self.typeid_input_frame_multiple_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                          values=d_multiple,
                                                                          width=10,
                                                                          font=my_font.myfont(20))
                self.typeid_input_frame_multiple_input_box.place(x=270, y=700)

                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="備考：",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=750)
                self.typeid_input_frame_remark_input_box = tk.Entry(self.typeid_input_frame,
                                                                    width=30,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_remark_input_box.place(x=270, y=750)

                # add button -typeid add query-
                self.typeid_input_frame_add_button = tk.Button(self.typeid_input_frame,
                                                               text="新規",
                                                               font=my_font.myfont(20),
                                                               width=10,
                                                               command=lambda: goto_typeid_input_frame_add_button_click())
                self.typeid_input_frame_add_button.place(x=270, y=820)

            else:  # data available
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="■変更or削除■",
                                                         font=my_font.myfont(30))
                self.typeid_input_frame_label.place(x=50, y=300)

                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="品目：",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=400)
                self.typeid_input_frame_typeid2_input_box = tk.Entry(self.typeid_input_frame,
                                                                     width=15,
                                                                     font=my_font.myfont(20))
                self.typeid_input_frame_typeid2_input_box.place(x=270, y=400)

                # combo box -process-
                d_process = data_select("T_HSDS_process", "process")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="工程:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=450)
                self.typeid_input_frame_process_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                         values=d_process,
                                                                         width=15,
                                                                         font=my_font.myfont(20))
                self.typeid_input_frame_process_input_box.place(x=270, y=450)

                # combo box -solder-
                d_solder = data_select("T_HSDS_solder", "solder")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="はんだ:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=500)
                self.typeid_input_frame_solder_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                        values=d_solder,
                                                                        width=15,
                                                                        font=my_font.myfont(20))
                self.typeid_input_frame_solder_input_box.place(x=270, y=500)

                # combo box -s1-
                d_s1 = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="S1部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=550)
                self.typeid_input_frame_s1_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=d_s1,
                                                                    width=10,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_s1_input_box.place(x=270, y=550)

                # combo box -sn-
                d_sn = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="Sn部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=600)
                self.typeid_input_frame_sn_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=d_sn,
                                                                    width=10,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_sn_input_box.place(x=270, y=600)

                # combo box -s1sn-
                d_s1sn = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="合計部品数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=650)
                self.typeid_input_frame_s1sn_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                      values=d_s1sn,
                                                                      width=10,
                                                                      font=my_font.myfont(20))
                self.typeid_input_frame_s1sn_input_box.place(x=270, y=650)

                # combo box -multiple-
                d_multiple = data_select("ST_number100", "number100")
                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="取り数:",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=700)
                self.typeid_input_frame_multiple_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                          values=d_multiple,
                                                                          width=10,
                                                                          font=my_font.myfont(20))
                self.typeid_input_frame_multiple_input_box.place(x=270, y=700)

                self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                         text="備考：",
                                                         font=my_font.myfont(20))
                self.typeid_input_frame_label.place(x=100, y=750)
                self.typeid_input_frame_remark_input_box = tk.Entry(self.typeid_input_frame,
                                                                    width=30,
                                                                    font=my_font.myfont(20))
                self.typeid_input_frame_remark_input_box.place(x=270, y=750)

                self.typeid_input_frame_typeid2_input_box.insert(tk.END, search_typeid[0])
                self.typeid_input_frame_process_input_box.insert(tk.END, search_typeid[1])
                self.typeid_input_frame_solder_input_box.insert(tk.END, search_typeid[2])
                self.typeid_input_frame_s1_input_box.insert(tk.END, search_typeid[3])
                self.typeid_input_frame_sn_input_box.insert(tk.END, search_typeid[4])
                self.typeid_input_frame_s1sn_input_box.insert(tk.END, search_typeid[5])
                self.typeid_input_frame_multiple_input_box.insert(tk.END, search_typeid[6])
                if not search_typeid[7]:
                    pass
                else:
                    self.typeid_input_frame_remark_input_box.insert(tk.END, search_typeid[7])

                self.typeid_input_frame_typeid_input_box.delete(0, tk.END)

                # update button -typeid update query-
                self.typeid_input_frame_update_button = tk.Button(self.typeid_input_frame,
                                                                  text="更新",
                                                                  font=my_font.myfont(20),
                                                                  width=10,
                                                                  command=lambda: goto_typeid_input_frame_update_button_click())
                self.typeid_input_frame_update_button.place(x=270, y=820)

                # delete button -typeid update query-
                self.typeid_input_frame_delete_button = tk.Button(self.typeid_input_frame,
                                                                  text="削除",
                                                                  font=my_font.myfont(20),
                                                                  width=10,
                                                                  command=lambda: goto_typeid_input_frame_delete_button_click())
                self.typeid_input_frame_delete_button.place(x=470, y=820)

        def goto_typeid_input_frame_update_button_click():
            # get typeid
            get_typeid2 = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_typeid2_input_box.get())).replace('\n', '')
            c_process = self.typeid_input_frame_process_input_box.get()
            c_solder = self.typeid_input_frame_solder_input_box.get()
            c_sn = self.typeid_input_frame_sn_input_box.get()
            c_s1 = self.typeid_input_frame_s1_input_box.get()
            c_s1sn = self.typeid_input_frame_s1sn_input_box.get()
            c_multiple = self.typeid_input_frame_multiple_input_box.get()
            c_remark = self.typeid_input_frame_remark_input_box.get()

            # SQL UPDATE
            update_typeid_data(c_process, c_solder, c_sn, c_s1, c_s1sn, c_multiple, c_remark, get_typeid2)
            self.typeid_input_frame_typeid2_input_box.delete(0, tk.END)
            self.typeid_input_frame_process_input_box.delete(0, tk.END)
            self.typeid_input_frame_solder_input_box.delete(0, tk.END)
            self.typeid_input_frame_s1_input_box.delete(0, tk.END)
            self.typeid_input_frame_sn_input_box.delete(0, tk.END)
            self.typeid_input_frame_s1sn_input_box.delete(0, tk.END)
            self.typeid_input_frame_multiple_input_box.delete(0, tk.END)
            self.typeid_input_frame_remark_input_box.delete(0, tk.END)

            # add button -typeid add query-
            self.typeid_input_frame_add_button = tk.Button(self.typeid_input_frame,
                                                           text="新規",
                                                           font=my_font.myfont(20),
                                                           width=10,
                                                           command=lambda: goto_typeid_input_frame_add_button_click())
            self.typeid_input_frame_add_button.place(x=270, y=820)

            # combo box -typeID-
            combo_typeid = get_combo_typeid()
            self.typeid_input_frame_typeid_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=combo_typeid,
                                                                    width=14,
                                                                    font=my_font.myfont(30))
            self.typeid_input_frame_typeid_input_box.place(x=200, y=150)

            # blind delete button3
            self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                     text='   ',
                                                     font=my_font.myfont(999))
            self.typeid_input_frame_label.place(x=50, y=300)

        def goto_typeid_input_frame_delete_button_click():
            # get typeid
            get_typeid2 = mojimoji.zen_to_han(str.upper(self.typeid_input_frame_typeid2_input_box.get())).replace('\n', '')

            # delete query
            data_delete("T_HSDS_typeID", "typeID = '" + get_typeid2 + "'")
            messagebox.showinfo("情報", "情報を削除しました。")

            self.typeid_input_frame_typeid2_input_box.delete(0, tk.END)
            self.typeid_input_frame_process_input_box.delete(0, tk.END)
            self.typeid_input_frame_solder_input_box.delete(0, tk.END)
            self.typeid_input_frame_s1_input_box.delete(0, tk.END)
            self.typeid_input_frame_sn_input_box.delete(0, tk.END)
            self.typeid_input_frame_s1sn_input_box.delete(0, tk.END)
            self.typeid_input_frame_multiple_input_box.delete(0, tk.END)
            self.typeid_input_frame_remark_input_box.delete(0, tk.END)

            # add button -typeid add query-
            self.typeid_input_frame_add_button = tk.Button(self.typeid_input_frame,
                                                           text="新規",
                                                           font=my_font.myfont(20),
                                                           width=10,
                                                           command=lambda: goto_typeid_input_frame_add_button_click())
            self.typeid_input_frame_add_button.place(x=270, y=820)

            # combo box -typeID-
            combo_typeid = get_combo_typeid()
            self.typeid_input_frame_typeid_input_box = ttk.Combobox(self.typeid_input_frame,
                                                                    values=combo_typeid,
                                                                    width=14,
                                                                    font=my_font.myfont(30))
            self.typeid_input_frame_typeid_input_box.place(x=200, y=150)

            # blind delete button
            self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                     text='   ',
                                                     font=my_font.myfont(999))
            self.typeid_input_frame_label.place(x=50, y=300)

        def goto_hs_admin_frame_from_typeid_input_frame_button_click():
            self.typeid_input_frame_typeid_input_box.delete(0, tk.END)

            # blind delete button
            self.typeid_input_frame_label = tk.Label(self.typeid_input_frame,
                                                     text='   ',
                                                     font=my_font.myfont(999))
            self.typeid_input_frame_label.place(x=50, y=300)
            self.hs_admin_frame.tkraise()

        # -----------------------------part_number_input_frame-----------------------------
        # define frame
        self.part_number_input_frame = tk.Frame()
        self.part_number_input_frame.grid(row=0, column=0, sticky="nsew")

        # frame structure
        # Title field
        self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                      text="部品番号 変更&追加",
                                                      font=my_font.myfont(30))
        self.part_number_input_frame_label.place(x=10, y=10)
        self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                      text="■検索条件■",
                                                      font=my_font.myfont(20))
        self.part_number_input_frame_label.place(x=50, y=100)
        self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                      text='品目：',
                                                      font=my_font.myfont(15))
        self.part_number_input_frame_label.place(x=70, y=150)

        # combo box -typeid-
        combo_typeid = get_combo_typeid()
        self.part_number_input_frame_typeid_box = ttk.Combobox(self.part_number_input_frame,
                                                               values=combo_typeid,
                                                               width=12,
                                                               font=my_font.myfont(15))
        self.part_number_input_frame_typeid_box.place(x=140, y=150)
        # symbol addition & change
        self.part_number_input_frame_symbol_change_button = tk.Button(self.part_number_input_frame,
                                                                      text="シンボル追加&変更",
                                                                      font=my_font.myfont(15),
                                                                      width=15,
                                                                      command=lambda: part_number_input_frame_symbol_change_button_click())
        self.part_number_input_frame_symbol_change_button.place(x=320, y=144)
        # symbol search
        self.part_number_input_frame_symbol_search_button = tk.Button(self.part_number_input_frame,
                                                                      text="シンボル検索",
                                                                      font=my_font.myfont(15),
                                                                      width=10,
                                                                      command=lambda: part_number_input_frame_symbol_search_button_click())
        self.part_number_input_frame_symbol_search_button.place(x=530, y=144)
        self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                      text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                      font=my_font.myfont(10))
        self.part_number_input_frame_label.place(x=50, y=190)
        # back button -go to hs_admin_frame-
        self.part_number_input_frame_back_button = tk.Button(self.part_number_input_frame,
                                                             text="戻る",
                                                             font=my_font.myfont(20),
                                                             height=1,
                                                             width=10,
                                                             command=lambda: goto_hs_admin_frame_from_part_number_button_click())
        self.part_number_input_frame_back_button.place(x=520, y=10)

        def goto_hs_admin_frame_from_part_number_button_click():
            # result clear
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='   ',
                                                          font=my_font.myfont(999))
            self.part_number_input_frame_label.place(x=50, y=210)
            self.part_number_input_frame_typeid_box.delete(0, tk.END)
            # jump
            self.hs_admin_frame.tkraise()

        def part_number_input_frame_symbol_change_button_click():
            # result clear
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='   ',
                                                          font=my_font.myfont(999))
            self.part_number_input_frame_label.place(x=50, y=210)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="■変更&追加■",
                                                          font=my_font.myfont(20))
            self.part_number_input_frame_label.place(x=50, y=210)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='品目：',
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=70, y=260)
            self.part_number_input_frame_change_typeid_box = tk.Entry(self.part_number_input_frame,
                                                                      width=14,
                                                                      justify="left",
                                                                      font=my_font.myfont(15))
            self.part_number_input_frame_change_typeid_box.place(x=160, y=260)
            self.part_number_input_frame_change_typeid_box.insert(0, self.part_number_input_frame_typeid_box.get())
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='シンボル：',
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=70, y=310)

            # get typeid
            get_typeid = mojimoji.zen_to_han(str.upper(self.part_number_input_frame_change_typeid_box.get())).replace('\n', '')

            # combo box -symbol-
            d_symbol = data_select_where()
            query = "SELECT symbol FROM T_HSDS_symbol WHERE typeID = '"
            cur.execute(query + get_typeid + "'" + "ORDER BY symbol")
            d_symbol = cur.fetchall()
            self.part_number_input_frame_change_symbol_box = ttk.Combobox(self.part_number_input_frame,
                                                                          values=d_symbol,
                                                                          width=12,
                                                                          font=my_font.myfont(15))
            self.part_number_input_frame_change_symbol_box.place(x=160, y=310)
            if not d_symbol:
                d_symbol = [""]
            self.part_number_input_frame_change_symbol_box.insert(0, d_symbol[0])

            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='部品番号：',
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=70, y=360)

            self.part_number_input_frame_change_part_number_box = tk.Entry(self.part_number_input_frame,
                                                                           width=14,
                                                                           justify="left",
                                                                           font=my_font.myfont(15))
            self.part_number_input_frame_change_part_number_box.place(x=160, y=360)

            # part number addition & change
            self.part_number_input_frame_part_number_change_button = tk.Button(self.part_number_input_frame,
                                                                               text="変更&追加",
                                                                               font=my_font.myfont(15),
                                                                               width=10,
                                                                               command=lambda: part_number_input_frame_part_number_change_button_click())
            self.part_number_input_frame_part_number_change_button.place(x=160, y=410)

            # sample list
            self.part_number_input_frame_part_number_change_sample_list_button = tk.Button(
                self.part_number_input_frame,
                text="サンプルリスト出力",
                font=my_font.myfont(15),
                width=14,
                command=lambda: part_number_input_frame_part_number_change_sample_list_button_click())
            self.part_number_input_frame_part_number_change_sample_list_button.place(x=160, y=460)

            # part number addition & change list
            self.part_number_input_frame_part_number_change_list_button = tk.Button(
                self.part_number_input_frame,
                text="リストで追加",
                font=my_font.myfont(15),
                width=14,
                command=lambda: part_number_input_frame_part_number_change_list_button_click())
            self.part_number_input_frame_part_number_change_list_button.place(x=160, y=510)

            def part_number_input_frame_part_number_change_sample_list_button_click():
                texta = os.getcwd()
                messagebox.showinfo("サンプルファイル出力", texta + '/部品番号登録csvサンプル.csv')
                with open(texta + '/部品番号登録csvサンプル.csv', 'w', newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["品目", "シンボル", "部品番号", "←この行(ヘッダー)は残して2行目から入力して下さい。"])
                    d_part_number = [('UR-5555', 'CN1111', '333333A')]
                    for column in d_part_number:
                        writer.writerow(column)
                # open folder
                path = texta
                path = os.path.realpath(path)
                os.startfile(path)

            def part_number_input_frame_part_number_change_list_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                texta = os.getcwd()
                ftyp = [('csvファイル', '*.csv')]
                directory = texta
                g_file = filedialog.askopenfilename(filetypes=ftyp, initialdir=directory)

                with open(g_file, 'r') as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    for column in reader:
                        query = "SELECT * FROM T_HSDS_symbol WHERE typeID = '"
                        print(query + str.upper(column[0]) + "' AND symbol = '" + str.upper(column[1]) + "'")
                        cur.execute(
                            query + str.upper(column[0]) + "' AND symbol = '" + str.upper(column[1]) + "'")
                        c_column = cur.fetchall()
                        print(c_column)

                        if not c_column:
                            query = "INSERT INTO T_HSDS_symbol (typeID,symbol,part_number) VALUES ('"
                            cur.execute(
                                query + str.upper(column[0]) + "','" + str.upper(column[1]) + "','" + str.upper(
                                    column[2]).replace('-', '') + "')")
                            conn.commit()
                        else:
                            query = "UPDATE T_HSDS_symbol SET part_number = '"
                            print(query + str.upper(column[2]) + "WHERE typeID = '" + str.upper(
                                column[0]) + "' AND symbol = '" + str.upper(column[1]) + "'")
                            cur.execute(query + str.upper(
                                column[2].replace('-', '')) + "' WHERE typeID = '" + str.upper(
                                column[0]) + "' AND symbol = '" + str.upper(column[1]) + "'")
                            conn.commit()

                messagebox.showinfo("完了", "登録完了しました。")

                # database
                cur.close()
                conn.close()

            def part_number_input_frame_part_number_change_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                c_typeid = mojimoji.zen_to_han(
                    str.upper(self.part_number_input_frame_change_typeid_box.get())).replace('\n', '')
                c_symbol = mojimoji.zen_to_han(
                    str.upper(self.part_number_input_frame_change_symbol_box.get())).replace('\n', '')
                c_part_number = mojimoji.zen_to_han(
                    str.upper(self.part_number_input_frame_change_part_number_box.get())).replace('\n', '')
                c_part_number = mojimoji.zen_to_han(c_part_number).replace('-', '')

                if c_typeid == "":
                    messagebox.showerror("エラー", "品目が入力されていません。")
                    self.part_number_input_frame_change_typeid_box.focus_set()
                    return

                if c_symbol == "":
                    messagebox.showerror("エラー", "シンボルが入力されていません。")
                    self.part_number_input_frame_change_symbol_box.focus_set()
                    return

                if c_part_number == "":
                    messagebox.showerror("エラー", "部品番号が入力されていません。")
                    self.part_number_input_frame_change_part_number_box.focus_set()
                    return

                query = "SELECT part_number FROM T_HSDS_symbol WHERE typeID = '"
                cur.execute(query + c_typeid + "' AND symbol = '" + c_symbol + "'")
                x_symbol = cur.fetchone()
                if not x_symbol:
                    messagebox.showinfo("確認", "新規登録します。")
                    query = "INSERT INTO T_HSDS_symbol(typeID,symbol,part_number) VALUES('"
                    cur.execute(query + c_typeid + "','" + c_symbol + "','" + c_part_number + "')")
                    conn.commit()
                else:
                    messagebox.showinfo("確認", "更新します。")
                    query = "UPDATE T_HSDS_symbol SET part_number ='"
                    cur.execute(
                        query + c_part_number + "' WHERE typeID ='" + c_typeid + "' AND symbol ='" + c_symbol + "'")
                    conn.commit()

                # result clear
                self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                              text='   ',
                                                              font=my_font.myfont(999))
                self.part_number_input_frame_label.place(x=50, y=210)
                # focus
                self.part_number_input_frame_typeid_box.focus_set()

                # database
                cur.close()
                conn.close()

            # part number delete
            self.part_number_input_frame_part_number_delete_button = tk.Button(self.part_number_input_frame,
                                                                               text="削除",
                                                                               font=my_font.myfont(15),
                                                                               width=10,
                                                                               command=lambda: part_number_input_frame_part_number_delete_button_click())
            self.part_number_input_frame_part_number_delete_button.place(x=300, y=410)

            def part_number_input_frame_part_number_delete_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                get_typeid = mojimoji.zen_to_han(
                    str.upper(self.part_number_input_frame_change_typeid_box.get())).replace('\n', '')
                get_symbol = mojimoji.zen_to_han(
                    str.upper(self.part_number_input_frame_change_symbol_box.get())).replace('\n', '')

                if get_typeid == "":
                    messagebox.showerror("エラー", "品目が入力されていません。")
                    self.part_number_input_frame_change_typeid_box.focus_set()
                    return

                if get_symbol == "":
                    messagebox.showerror("エラー", "シンボルが入力されていません。")
                    self.part_number_input_frame_change_symbol_box.focus_set()
                    return

                messagebox.showinfo("情報", get_typeid + " " + get_symbol + " を削除します。")
                query = "DELETE FROM T_HSDS_symbol WHERE typeID = '"
                cur.execute(query + get_typeid + "' AND symbol = '" + get_symbol + "'")
                conn.commit()

                # result clear
                self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                              text='   ',
                                                              font=my_font.myfont(999))
                self.part_number_input_frame_label.place(x=50, y=210)
                # focus
                self.part_number_input_frame_typeid_box.focus_set()

                # database
                cur.close()
                conn.close()

            # database
            cur.close()
            conn.close()

        def part_number_input_frame_symbol_search_button_click():
            # database setting & query
            import mysql.connector
            conn = mysql.connector.connect(user='no13792',
                                           password='no13792',
                                           host='nksv560.ad.nkc.co.jp',
                                           database='test')
            cur = conn.cursor(buffered=True)

            # result clear
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text='   ',
                                                          font=my_font.myfont(999))
            self.part_number_input_frame_label.place(x=50, y=210)

            # title
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="■検索結果■",
                                                          font=my_font.myfont(20))
            self.part_number_input_frame_label.place(x=50, y=210)

            get_typeid = mojimoji.zen_to_han(str.upper(self.part_number_input_frame_typeid_box.get())).replace(
                '\n', '')
            self.part_number_input_frame_typeid_box.delete(0, tk.END)

            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text=get_typeid + " シンボル一覧", font=my_font.myfont(20))
            self.part_number_input_frame_label.place(x=70, y=250)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="シンボル",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=70, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="部品番号",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=200, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="-----------------------------------------",
                                                          font=my_font.myfont(10))
            self.part_number_input_frame_label.place(x=70, y=330)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="シンボル",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=370, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="部品番号",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=500, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="-----------------------------------------",
                                                          font=my_font.myfont(10))
            self.part_number_input_frame_label.place(x=370, y=330)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="シンボル",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=670, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="部品番号",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=800, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="-----------------------------------------",
                                                          font=my_font.myfont(10))
            self.part_number_input_frame_label.place(x=670, y=330)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="シンボル",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=970, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame, text="部品番号",
                                                          font=my_font.myfont(15))
            self.part_number_input_frame_label.place(x=1100, y=300)
            self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                          text="-----------------------------------------",
                                                          font=my_font.myfont(10))
            self.part_number_input_frame_label.place(x=970, y=330)

            query = "SELECT symbol,part_number FROM T_HSDS_symbol WHERE typeID = '"
            cur.execute(query + get_typeid + "' ORDER BY symbol")
            q_symbol = cur.fetchall()

            count_a = 0
            count_b = 0
            count_x1 = 70
            count_x2 = 200
            count_y = 320

            for column in q_symbol:
                if count_a < 60:
                    if count_b < 14:
                        count_a += 1
                        count_b += 1
                        count_y += 40

                        result_1 = self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                                                 text=column[0],
                                                                                 font=my_font.myfont(15))
                        result_1.place(x=count_x1, y=count_y)
                        result_2 = self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                                                 text=column[1],
                                                                                 font=my_font.myfont(15))
                        result_2.place(x=count_x2, y=count_y)

                    else:
                        count_y += 40

                        result_1 = self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                                                 text=column[0],
                                                                                 font=my_font.myfont(15))
                        result_1.place(x=count_x1, y=count_y)
                        result_2 = self.part_number_input_frame_label = tk.Label(self.part_number_input_frame,
                                                                                 text=column[1],
                                                                                 font=my_font.myfont(15))
                        result_2.place(x=count_x2, y=count_y)

                        count_a += 1
                        count_b = 0
                        count_x1 = count_x1 + 300
                        count_x2 = count_x2 + 300
                        count_y = 320

        # -----------------------------operator_input_frame-----------------------------
        try:
            # define frame
            self.operator_input_frame = tk.Frame()
            self.operator_input_frame.grid(row=0, column=0, sticky="nsew")

            # frame structure
            # Title field
            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="作業者 変更&追加",
                                                       font=my_font.myfont(30))
            self.operator_input_frame_label.place(x=10, y=10)

            # combo box -employee name-
            query = "SELECT employee_name FROM T_HSDS_operator ORDER BY employee_enrolled DESC,employee_number"
            cur.execute(query)
            d_employee = cur.fetchall()
            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="作業者:",
                                                       font=my_font.myfont(30))
            self.operator_input_frame_label.place(x=50, y=150)
            self.operator_input_frame_name_box = ttk.Combobox(self.operator_input_frame,
                                                              values=d_employee,
                                                              width=14,
                                                              font=my_font.myfont(30))
            self.operator_input_frame_name_box.place(x=200, y=150)

            # search button
            self.operator_input_frame_search_button = tk.Button(self.operator_input_frame,
                                                                text="検索",
                                                                font=my_font.myfont(20),
                                                                height=1,
                                                                width=10,
                                                                command=lambda: goto_operator_input_frame_search_button_click())
            self.operator_input_frame_search_button.place(x=600, y=150)

            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text='-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------',
                                                       font=my_font.myfont(10))
            self.operator_input_frame_label.place(x=50, y=250)

            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="■新規 or 変更内容入力■",
                                                       font=my_font.myfont(30))
            self.operator_input_frame_label.place(x=50, y=300)

            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="社員番号：",
                                                       font=my_font.myfont(20))
            self.operator_input_frame_label.place(x=100, y=400)
            self.operator_input_frame_employee_number_input_box = tk.Entry(self.operator_input_frame,
                                                                           width=15,
                                                                           font=my_font.myfont(20))
            self.operator_input_frame_employee_number_input_box.place(x=250, y=400)

            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="作業者：",
                                                       font=my_font.myfont(20))
            self.operator_input_frame_label.place(x=100, y=450)
            self.operator_input_frame_employee_name_input_box = tk.Entry(self.operator_input_frame,
                                                                         width=15,
                                                                         font=my_font.myfont(20))
            self.operator_input_frame_employee_name_input_box.place(x=250, y=450)

            self.operator_input_frame_label = tk.Label(self.operator_input_frame,
                                                       text="在籍フラグ：",
                                                       font=my_font.myfont(20))
            self.operator_input_frame_label.place(x=100, y=500)

            # combo box -employee enrolled-
            query = "SELECT employee_enrolled,employee_remark FROM T_HSDS_employee_enrolled"
            cur.execute(query)
            d_employee = cur.fetchall()
            self.operator_input_frame_employee_enrolled_input_box = ttk.Combobox(self.operator_input_frame,
                                                                                 values=d_employee,
                                                                                 width=15,
                                                                                 font=my_font.myfont(20))
            self.operator_input_frame_employee_enrolled_input_box.place(x=250, y=500)

            # add button -employee add query-
            self.operator_input_frame_add_button = tk.Button(self.operator_input_frame,
                                                             text="新規",
                                                             font=my_font.myfont(20),
                                                             width=10,
                                                             command=lambda: goto_operator_input_frame_add_button_click())
            self.operator_input_frame_add_button.place(x=250, y=570)

            # back button -go to hs_admin_frame-
            self.operator_input_frame_back_button = tk.Button(self.operator_input_frame,
                                                              text="戻る",
                                                              font=my_font.myfont(20),
                                                              height=1,
                                                              width=10,
                                                              command=lambda: goto_hs_admin_frame_back_button_click())
            self.operator_input_frame_back_button.place(x=520, y=10)

            def goto_operator_input_frame_search_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                self.operator_input_frame_employee_number_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_name_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_enrolled_input_box.delete(0, tk.END)
                query = "SELECT employee_number,employee_name,employee_enrolled FROM T_HSDS_operator WHERE employee_name ='"
                cur.execute(query + self.operator_input_frame_name_box.get() + "'")
                employee = cur.fetchone()

                if not employee:  # data not available
                    messagebox.showerror("NG", "作業者が存在しません")
                else:  # data available
                    self.operator_input_frame_employee_number_input_box.insert(tk.END, employee[0])
                    self.operator_input_frame_employee_name_input_box.insert(tk.END, employee[1])
                    self.operator_input_frame_employee_enrolled_input_box.insert(tk.END, employee[2])
                    # update button -employee update query-
                    self.operator_input_frame_update_button = tk.Button(self.operator_input_frame,
                                                                        text="更新",
                                                                        font=my_font.myfont(20),
                                                                        width=10,
                                                                        command=lambda: goto_operator_input_frame_update_button_click())
                    self.operator_input_frame_update_button.place(x=250, y=570)

                self.operator_input_frame_name_box.delete(0, tk.END)

                # database
                cur.close()
                conn.close()

            def goto_operator_input_frame_update_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                # input check
                r_employee_number = self.operator_input_frame_employee_number_input_box.get()
                r_employee_number_len = len(r_employee_number)
                r_employee_name = self.operator_input_frame_employee_name_input_box.get()
                r_employee_enrolled = self.operator_input_frame_employee_enrolled_input_box.get()
                if r_employee_number == "":
                    messagebox.showerror("NG", "社員番号を入力してください。")
                    self.operator_input_frame_employee_number_input_box.focus_set()
                    return
                if not r_employee_number_len == 5:
                    messagebox.showerror("NG", "社員番号は、5桁で入力してください。")
                    self.operator_input_frame_employee_number_input_box.focus_set()
                    return
                if r_employee_name == "":
                    messagebox.showerror("NG", "作業者名を入力してください。")
                    self.operator_input_frame_employee_name_input_box.focus_set()
                    return
                if r_employee_enrolled == "":
                    messagebox.showerror("NG", "在籍フラグを選択してください。")
                    self.operator_input_frame_employee_name_input_box.focus_set()
                    return

                self.operator_input_frame_employee_number_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_name_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_enrolled_input_box.delete(0, tk.END)

                query = "UPDATE T_HSDS_operator SET employee_name = '"
                cur.execute(query
                            + r_employee_name
                            + "', employee_enrolled = '"
                            + r_employee_enrolled[0]
                            + "' WHERE employee_number = '"
                            + r_employee_number
                            + "'")
                conn.commit()

                # renew combo box -employee name-
                query = "SELECT employee_name FROM T_HSDS_operator WHERE employee_enrolled = '1'"
                cur.execute(query)
                d_employee = cur.fetchall()

                if not d_employee:  # data not available
                    messagebox.showerror("NG", "作業者が存在しません")
                else:  # data available
                    self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                             text="作業者:",
                                                             font=my_font.myfont(30))
                    self.sasizu_input_frame_label.place(x=50, y=350)
                    self.sasizu_input_frame_name_box = ttk.Combobox(self.sasizu_input_frame,
                                                                    values=d_employee,
                                                                    width=19,
                                                                    font=my_font.myfont(30))
                    self.sasizu_input_frame_name_box.place(x=200, y=350)

                messagebox.showinfo("情報", "情報を更新しました。")

                # add button -employee add query-
                self.operator_input_frame_add_button = tk.Button(self.operator_input_frame,
                                                                 text="新規",
                                                                 font=my_font.myfont(20),
                                                                 width=10,
                                                                 command=lambda: goto_operator_input_frame_add_button_click())
                self.operator_input_frame_add_button.place(x=250, y=570)

                # combo box -employee name-
                query = "SELECT employee_name FROM T_HSDS_operator ORDER BY employee_enrolled DESC,employee_number"
                cur.execute(query)
                d_employee = cur.fetchall()
                self.operator_input_frame_name_box = ttk.Combobox(self.operator_input_frame,
                                                                  values=d_employee,
                                                                  width=14,
                                                                  font=my_font.myfont(30))
                self.operator_input_frame_name_box.place(x=200, y=150)

                # database
                cur.close()
                conn.close()

            def goto_operator_input_frame_add_button_click():
                # database setting & query
                import mysql.connector
                conn = mysql.connector.connect(user='no13792',
                                               password='no13792',
                                               host='nksv560.ad.nkc.co.jp',
                                               database='test')
                cur = conn.cursor(buffered=True)

                # input check
                r_employee_number = mojimoji.zen_to_han(
                    str(self.operator_input_frame_employee_number_input_box.get()))
                r_employee_number_len = len(r_employee_number)
                r_employee_name = self.operator_input_frame_employee_name_input_box.get()
                r_employee_enrolled = self.operator_input_frame_employee_enrolled_input_box.get()
                if r_employee_number == "":
                    messagebox.showerror("NG", "社員番号を入力してください。")
                    self.operator_input_frame_employee_number_input_box.focus_set()
                    return
                if not r_employee_number_len == 5:
                    messagebox.showerror("NG", "社員番号は、5桁で入力してください。")
                    self.operator_input_frame_employee_number_input_box.focus_set()
                    return
                if r_employee_name == "":
                    messagebox.showerror("NG", "作業者名を入力してください。")
                    self.operator_input_frame_employee_name_input_box.focus_set()
                    return
                if r_employee_enrolled == "":
                    messagebox.showerror("NG", "在籍フラグを選択してください。")
                    self.operator_input_frame_employee_name_input_box.focus_set()
                    return

                query = "SELECT employee_number FROM T_HSDS_operator WHERE employee_number = "
                cur.execute(query + r_employee_number)
                c_employee_number = cur.fetchone()
                if not c_employee_number:
                    query = "INSERT INTO T_HSDS_operator VALUES ('"
                    cur.execute(query
                                + r_employee_number
                                + "','"
                                + r_employee_name
                                + "','"
                                + r_employee_enrolled[0]
                                + "')")
                    conn.commit()

                    # renew combo box -employee name-
                    query = "SELECT employee_name FROM T_HSDS_operator WHERE employee_enrolled = '1'"
                    cur.execute(query)
                    d_employee = cur.fetchall()

                    if not d_employee:  # data not available
                        messagebox.showerror("NG", "作業者が存在しません")
                    else:  # data available
                        self.sasizu_input_frame_label = tk.Label(self.sasizu_input_frame,
                                                                 text="作業者:",
                                                                 font=my_font.myfont(30))
                        self.sasizu_input_frame_label.place(x=50, y=350)
                        self.sasizu_input_frame_name_box = ttk.Combobox(self.sasizu_input_frame,
                                                                        values=d_employee,
                                                                        width=19,
                                                                        font=my_font.myfont(30))
                        self.sasizu_input_frame_name_box.place(x=200, y=350)

                    messagebox.showinfo("情報", "情報を登録しました。")

                    self.operator_input_frame_employee_number_input_box.delete(0, tk.END)
                    self.operator_input_frame_employee_name_input_box.delete(0, tk.END)
                    self.operator_input_frame_employee_enrolled_input_box.delete(0, tk.END)
                else:
                    messagebox.showerror("NG", "既に登録されている社員番号です。")
                    self.operator_input_frame_employee_number_input_box.focus_set()

                # database
                cur.close()
                conn.close()

            def goto_hs_admin_frame_back_button_click():
                # add button -employee add query-
                self.operator_input_frame_add_button = tk.Button(self.operator_input_frame,
                                                                 text="新規",
                                                                 font=my_font.myfont(20),
                                                                 width=10,
                                                                 command=lambda: goto_operator_input_frame_add_button_click())
                self.operator_input_frame_add_button.place(x=250, y=570)

                self.operator_input_frame_name_box.delete(0, tk.END)
                self.operator_input_frame_employee_number_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_name_input_box.delete(0, tk.END)
                self.operator_input_frame_employee_enrolled_input_box.delete(0, tk.END)
                self.hs_admin_frame.tkraise()

        except mysql.connector.Error as err:
            messagebox.showerror("エラー", "データを追加出来ませんでした。")
            messagebox.showerror("エラー詳細", err)

        # go to home page
        self.menu_frame.tkraise()

        # database close
        cur.close()
        conn.close()


def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()