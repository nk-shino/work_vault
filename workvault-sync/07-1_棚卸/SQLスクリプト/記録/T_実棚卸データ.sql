USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  Table [dbo].[T_実棚卸データ]    Script Date: 2018/02/03 14:33:58 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T_実棚卸データ](
	[シリアル番号] [nvarchar](30) NOT NULL,
	[品番] [nvarchar](30) NULL,
	[保管場所] [nvarchar](4) NULL,
	[ロット番号] [nvarchar](40) NULL,
	[実棚数] [int] NULL,
	[区分] [int] NULL,
	[ファイル名] [nvarchar](50) NULL,
	[担当者コード] [nvarchar](20) NULL,
	[修正フラグ] [int] NULL,
	[未入庫フラグ] [int] NULL,
	[登録日時] [datetime] NULL,
	[更新日時] [datetime] NULL,
PRIMARY KEY CLUSTERED 
(
	[シリアル番号] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

