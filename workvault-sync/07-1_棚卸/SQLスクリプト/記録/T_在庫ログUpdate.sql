update T_在庫データ
set 発注番号 = '0000' + 発注番号
where len([発注番号]) = 6

update T_在庫データ
set 発注番号 = '000' + 発注番号
where len([発注番号]) = 7

update T_在庫データ
set 発注番号 = '00' + 発注番号
where len([発注番号]) = 8

update T_在庫ログ
set 発注番号 = '0000' + 発注番号
where len([発注番号]) = 6

update T_在庫ログ
set 発注番号 = '000' + 発注番号
where len([発注番号]) = 7

update T_在庫ログ
set 発注番号 = '00' + 発注番号
where len([発注番号]) = 8

update T_外部出庫
set 発注番号 = '00' + 発注番号
where len([発注番号]) = 8

update T_外部出庫
set 発注番号 = '000' + 発注番号
where len([発注番号]) = 7

update T_外部出庫
set 発注番号 = '000' + 発注番号
where len([発注番号]) = 6

