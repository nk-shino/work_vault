USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  Table [dbo].[W_棚卸用在庫ログ]    Script Date: 2017/12/07 7:47:20 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[W_棚卸用在庫ログ](
	[シリアル番号] [nvarchar](30) NULL,
	[品番] [nvarchar](30) NULL,
	[ロット] [nvarchar](10) NULL
) ON [PRIMARY]

GO

