section Section1;

shared #"CycleTime (集計用)" = let
    ソース = Odbc.Query("Driver={MySQL ODBC 8.0 Unicode Driver};Server=nksv1359.ad.nkc.co.jp;Database=QCD;", "SELECT ID, orderNumber, typeID, jobName, createrName, Pn, cycleTime, points, turn, addData FROM ( SELECT *, ROW_NUMBER() OVER (PARTITION BY typeID ORDER BY addData DESC) AS row_rank FROM QCD.CycleTime_Points ) AS ranked WHERE ranked.row_rank <= 10;#(lf)"),
    追加されたカスタム = Table.AddColumn(ソース, "サイクルタイム(下限28秒)", each if [cycleTime] < 28 then 28 else [cycleTime]),
    変更された型 = Table.TransformColumnTypes(追加されたカスタム,{{"サイクルタイム(下限28秒)", type number}}),
    グループ化された行 = Table.Group(変更された型, {"typeID", "Pn"}, {{"平均サイクルタイム", each List.Average([#"サイクルタイム(下限28秒)"]), type nullable number}, {"実装点数(中央値)", each List.Median([points]), type number}}),
    グループ化された行1 = Table.Group(グループ化された行, {"typeID"}, {{"平均サイクルタイム(表裏合計)", each List.Sum([平均サイクルタイム]), type nullable number}, {"実装点数(表裏合計)", each List.Sum([#"実装点数(中央値)"]), type number}})
in
    グループ化された行1;

shared 組取り数 = let
    ソース = Odbc.Query("Driver={MySQL ODBC 8.0 Unicode Driver};Server=nksv1359.ad.nkc.co.jp;Database=scheduled;", "SELECT `typeID`, `chldID` FROM `unitInfo` WHERE `chldID` LIKE "",%"" AND `chldID` NOT LIKE "",%,%"";"),
    置き換えられた値 = Table.ReplaceValue(ソース,",","",Replacer.ReplaceText,{"chldID"}),
    変更された型 = Table.TransformColumnTypes(置き換えられた値,{{"chldID", Int64.Type}})
in
    変更された型;

shared 固定グループ = let
    ソース = Access.Database(File.Contents("\\nksv523.ad.nkc.co.jp\第二工場実装課用\1係用\AccessDB\SMT_Schedule2\マスタ.accdb"), [CreateNavigationProperties=true]),
    _固定グループ = ソース{[Schema="",Item="固定グループ"]}[Data]
in
    _固定グループ;