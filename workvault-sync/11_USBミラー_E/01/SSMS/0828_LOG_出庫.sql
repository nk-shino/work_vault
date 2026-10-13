USE [EGProKOHDEN-Warehouse]
GO

SELECT [ID]
      ,[日付]
      ,[時分秒]
      ,[IPアドレス]
      ,[担当者コード]
      ,[品番]
      ,[数量]
      ,[部品バーコード]
      ,[ロケーション名称]
      ,[登録日時]
  FROM [dbo].[LOG_出庫]
GO

