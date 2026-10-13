

import pyodbc
import csv
import datetime

f = open('./倉庫検索.csv', 'w', encoding='utf_8_sig', newline='')
writer = csv.writer(f)

con = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=172.25.253.101,1433;"           # ← SQL Server はカンマでポート指定
    "DATABASE=EGProKOHDEN-Warehouse;"
    "UID=sqluser;"
    "PWD=Pfseg001;"
    "Encrypt=no;"                           # 18は既定でEncrypt=yesなので無効化
)

cur = con.cursor()

cur.execute("SELECT\
                シリアル番号,\
                品番,\
                受入数,\
                在庫数,\
                発注番号,\
                ステータス名称,\
                ロケーション名称,\
                RIGHT('00' + CONVERT(varchar, 棚列), 2) + '-' + RIGHT('00' + CONVERT(varchar, 棚位置), 2) + '-' + RIGHT('00' + CONVERT(varchar, 段), 2) + '-' + RIGHT('00' + CONVERT(varchar, 位置), 2) AS 棚,\
                棚分類コード,\
                更新日時\
            FROM\
                [EGProKOHDEN-Warehouse].[dbo].V_在庫データ\
            WHERE\
                品番 LIKE '9000070257' OR 1 = 1\
            ORDER BY\
                'シリアル番号'\
    ")
    # AND 品番 LIKE ''\
    #AND ロケーションコード LIKE 11

data = cur.fetchall()


head = 'シリアル番号,品番,受入数,在庫数,発注番号,ステータス名称,ロケーション名称,棚,棚分類,更新日時'.split(',')

writer.writerow(head)
writer.writerows(data)


cur.close()
con.close()

f.close()