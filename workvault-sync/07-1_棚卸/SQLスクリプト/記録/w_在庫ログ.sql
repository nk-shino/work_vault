USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  Table [dbo].[W_在庫ログ]    Script Date: 2017/11/04 19:04:18 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[W_在庫ログ](
	[シリアル番号] [nvarchar](30) NULL,
	[品番] [nvarchar](30) NULL,
	[発注番号] [nvarchar](10) NULL
) ON [PRIMARY]

GO

