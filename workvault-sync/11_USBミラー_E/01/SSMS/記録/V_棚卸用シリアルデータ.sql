USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  View [dbo].[V_棚卸用シリアルデータ]    Script Date: 2018/02/06 17:47:18 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO


CREATE VIEW [dbo].[V_棚卸用シリアルデータ]
AS
SELECT
		 T5.保管場所
		,T5.品番
		,T5.ロット
		,T5.シリアル番号
		,T5.在庫数
FROM	(
		SELECT
				 '0001' AS 保管場所
				,T1.品番
				,T1.発注番号 AS ロット
				,T1.シリアル番号
				,T1.在庫数
		FROM	 T_在庫データ T1 
		UNION ALL
		SELECT
				 T3.出庫先 AS 保管場所
				,T3.品番
				,T3.発注番号 AS ロット
				,T3.シリアル番号
				,T3.在庫数
		FROM	 T_外部出庫 T3
		) T5


GO

