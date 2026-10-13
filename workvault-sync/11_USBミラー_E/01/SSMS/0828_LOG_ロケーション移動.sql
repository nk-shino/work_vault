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
      ,[元ロケーション名称]
      ,[先ロケーション名称]
      ,[区分]
      ,[登録日時]
  FROM [dbo].[LOG_ロケーション移動]
GO

