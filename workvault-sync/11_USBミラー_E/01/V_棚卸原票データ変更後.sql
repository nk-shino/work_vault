USE [EGProKOHDEN-Warehouse]
GO

/****** Object:  View [dbo].[V_棚卸原票データ]    Script Date: 2018/01/14 22:30:17 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE VIEW [dbo].[V_棚卸原票データ]
AS
SELECT            dbo.T_棚卸原票データ.実地棚卸伝票, dbo.T_棚卸原票データ.会計年度, dbo.T_棚卸原票データ.プラント, dbo.T_棚卸原票データ.プラント名称, dbo.T_棚卸原票データ.保管場所, 
                        dbo.T_棚卸原票データ.保管場所テキスト, dbo.T_棚卸原票データ.明細番号, dbo.T_棚卸原票データ.品目コード, dbo.T_棚卸原票データ.品目テキスト, 
                        dbo.T_棚卸原票データ.ロット番号, dbo.T_棚卸原票データ.仕入先ロット, dbo.T_棚卸原票データ.シリアル番号, dbo.T_棚卸原票データ.仕入先シリアル, 
                        dbo.T_棚卸原票データ.在庫タイプ, dbo.T_棚卸原票データ.在庫タイプテキスト, dbo.T_棚卸原票データ.販売数量, dbo.T_棚卸原票データ.販売単位, 
                        dbo.T_棚卸原票データ.販売数量の端数, dbo.T_棚卸原票データ.基本数量単位, dbo.T_棚卸原票データ.実地棚卸販売数量, dbo.T_棚卸原票データ.実地棚卸販売単位, 
                        dbo.T_棚卸原票データ.実地棚卸販売数量の端数, dbo.T_棚卸原票データ.実地棚卸基本数量単位, dbo.T_棚卸原票データ.仕入先コード, dbo.T_棚卸原票データ.仕入先名称, 
                        dbo.T_棚卸原票データ.得意先コード, dbo.T_棚卸原票データ.得意先名称, dbo.T_棚卸原票データ.受注伝票番号, dbo.T_棚卸原票データ.受注明細番号, 
                        dbo.T_棚卸原票データ.WBS要素, dbo.T_棚卸原票データ.原価, dbo.T_棚卸原票データ.通貨コード, dbo.T_棚卸原票データ.ファイル名,dbo.T_棚卸原票データ.登録日時, dbo.T_棚卸原票データ.更新日時, [EGProKOHDEN-MST].dbo.M_品番.棚列, 
                        [EGProKOHDEN-MST].dbo.M_品番.棚位置, [EGProKOHDEN-MST].dbo.M_品番.段, [EGProKOHDEN-MST].dbo.M_品番.位置, [EGProKOHDEN-MST].dbo.M_品番.棚分類コード
FROM              dbo.T_棚卸原票データ LEFT OUTER JOIN
                        [EGProKOHDEN-MST].dbo.M_品番 ON dbo.T_棚卸原票データ.品目コード = [EGProKOHDEN-MST].dbo.M_品番.品番

GO

EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPane1', @value=N'[0E232FF0-B466-11cf-A24F-00AA00A3EFFF, 1.00]
Begin DesignProperties = 
   Begin PaneConfigurations = 
      Begin PaneConfiguration = 0
         NumPanes = 4
         Configuration = "(H (1[40] 4[20] 2[20] 3) )"
      End
      Begin PaneConfiguration = 1
         NumPanes = 3
         Configuration = "(H (1 [50] 4 [25] 3))"
      End
      Begin PaneConfiguration = 2
         NumPanes = 3
         Configuration = "(H (1 [50] 2 [25] 3))"
      End
      Begin PaneConfiguration = 3
         NumPanes = 3
         Configuration = "(H (4 [30] 2 [40] 3))"
      End
      Begin PaneConfiguration = 4
         NumPanes = 2
         Configuration = "(H (1 [56] 3))"
      End
      Begin PaneConfiguration = 5
         NumPanes = 2
         Configuration = "(H (2 [66] 3))"
      End
      Begin PaneConfiguration = 6
         NumPanes = 2
         Configuration = "(H (4 [50] 3))"
      End
      Begin PaneConfiguration = 7
         NumPanes = 1
         Configuration = "(V (3))"
      End
      Begin PaneConfiguration = 8
         NumPanes = 3
         Configuration = "(H (1[56] 4[18] 2) )"
      End
      Begin PaneConfiguration = 9
         NumPanes = 2
         Configuration = "(H (1 [75] 4))"
      End
      Begin PaneConfiguration = 10
         NumPanes = 2
         Configuration = "(H (1[66] 2) )"
      End
      Begin PaneConfiguration = 11
         NumPanes = 2
         Configuration = "(H (4 [60] 2))"
      End
      Begin PaneConfiguration = 12
         NumPanes = 1
         Configuration = "(H (1) )"
      End
      Begin PaneConfiguration = 13
         NumPanes = 1
         Configuration = "(V (4))"
      End
      Begin PaneConfiguration = 14
         NumPanes = 1
         Configuration = "(V (2))"
      End
      ActivePaneConfig = 0
   End
   Begin DiagramPane = 
      Begin Origin = 
         Top = 0
         Left = 0
      End
      Begin Tables = 
         Begin Table = "T_棚卸原票データ"
            Begin Extent = 
               Top = 6
               Left = 38
               Bottom = 221
               Right = 259
            End
            DisplayFlags = 280
            TopColumn = 30
         End
         Begin Table = "M_品番 (EGProKOHDEN-MST.dbo)"
            Begin Extent = 
               Top = 6
               Left = 297
               Bottom = 150
               Right = 467
            End
            DisplayFlags = 280
            TopColumn = 0
         End
      End
   End
   Begin SQLPane = 
   End
   Begin DataPane = 
      Begin ParameterDefaults = ""
      End
      Begin ColumnWidths = 36
         Width = 284
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
      End
   End
   Begin CriteriaPane = 
      Begin ColumnWidths = 11
         Column = 1440
         Alias = 900
         Table = 1170
         Output = 720
         Append = 1400
         NewValue = 1170
         SortType = 1350
         SortOrder = 1410
   ' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'V_棚卸原票データ'
GO

EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPane2', @value=N'      GroupBy = 1350
         Filter = 1350
         Or = 1350
         Or = 1350
         Or = 1350
      End
   End
End
' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'V_棚卸原票データ'
GO

EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPaneCount', @value=2 , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'V_棚卸原票データ'
GO

