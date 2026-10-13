USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  Table [dbo].[T_棚卸原票データ]    Script Date: 2018/01/14 16:47:00 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[T_棚卸原票データ](
	[実地棚卸伝票] [nvarchar](10) NULL,
	[会計年度] [nvarchar](4) NULL,
	[プラント] [nvarchar](4) NULL,
	[プラント名称] [nvarchar](30) NULL,
	[保管場所] [nvarchar](4) NULL,
	[保管場所テキスト] [nvarchar](16) NULL,
	[明細番号] [nvarchar](3) NULL,
	[品目コード] [nvarchar](18) NOT NULL,
	[品目テキスト] [nvarchar](40) NULL,
	[ロット番号] [nvarchar](40) NOT NULL,
	[仕入先ロット] [nvarchar](20) NULL,
	[シリアル番号] [nvarchar](18) NULL,
	[仕入先シリアル] [nvarchar](20) NULL,
	[在庫タイプ] [nvarchar](1) NULL,
	[在庫タイプテキスト] [nvarchar](20) NULL,
	[販売数量] [nvarchar](13) NULL,
	[販売単位] [nvarchar](3) NULL,
	[販売数量の端数] [nvarchar](13) NULL,
	[基本数量単位] [nvarchar](3) NULL,
	[実地棚卸販売数量] [nvarchar](13) NULL,
	[実地棚卸販売単位] [nvarchar](3) NULL,
	[実地棚卸販売数量の端数] [nvarchar](13) NULL,
	[実地棚卸基本数量単位] [nvarchar](3) NULL,
	[仕入先コード] [nvarchar](10) NULL,
	[仕入先名称] [nvarchar](35) NULL,
	[得意先コード] [nvarchar](10) NULL,
	[得意先名称] [nvarchar](35) NULL,
	[受注伝票番号] [nvarchar](10) NULL,
	[受注明細番号] [nvarchar](6) NULL,
	[WBS要素] [nvarchar](8) NULL,
	[原価] [nvarchar](14) NULL,
	[通貨コード] [nvarchar](5) NULL,
	[ファイル名] [nvarchar](50) NULL,
	[登録日時] [datetime] NULL,
	[更新日時] [datetime] NULL,
 CONSTRAINT [PK_T_棚卸原票データ] PRIMARY KEY CLUSTERED 
(
	[品目コード] ASC,[ロット番号] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO

