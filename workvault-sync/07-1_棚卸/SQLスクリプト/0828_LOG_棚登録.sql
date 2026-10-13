USE [EGProKOHDEN-Warehouse]
GO

SELECT [ID]
      ,[日付]
      ,[時分秒]
      ,[IPアドレス]
      ,[担当者コード]
      ,[棚列]
      ,[棚位置]
      ,[段]
      ,[位置]
      ,[品番]
      ,[登録日時]
  FROM [dbo].[LOG_棚登録]
GO

