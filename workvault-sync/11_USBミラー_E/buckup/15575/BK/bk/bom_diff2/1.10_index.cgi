#!/usr/bin/perl -w

#**********************************************************
# このプログラムは、オペレータがwebページをアクセスするときに
# 起動され、定時処理されたBOM DBと、EGproの最新BOMの差分集計
# 結果を表示するものである。
#									2021/01/10 J.Igarashi
# Ver. 1.00:初回リリース。
# Ver. 1.10:差分をチェックボックスで表示選択
#			一覧画面にcsvダウンロードを追加
#**********************************************************
my $ver = "1.10" ;

use strict ;
use warnings ;
use utf8 ;
use DBI ;
use Time::Local ;			# 日付、時刻の処理
use CGI ;					# POSTリクエストを生成
use Encode ;
use Encode 'decode' ;
use Data::Dumper ;			# Data構造表示用モジュールの読み込み(DBG用)
use Time::HR ;				# インターバル高精度タイマ
binmode STDIN, ':utf8' ;	#Apache error log対策
binmode STDOUT, ':utf8' ;
binmode STDERR, ':utf8' ;

# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60';
my $db2_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db_user = 'process_mgt';
my $db_passwd = '7bcsHFk8P7VxRcFD';
my $db_bomDiff = 'bomDiff';
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db2_unitInfo = 'unitInfo' ;
# ODBC関連接続情報
my $db_ODBCserver = "dbi:ODBC:EGPro" ;	# DB:EGProKOHDEN-Planに対するDSN
my $db_ODBCuser = "sqluser" ;
my $db_ODBCpasswd = "Pfseg001" ;
my $db_ODBCview = "T_部品配列表" ;

# 飛び先画面
my $indv_scrn = "./sashizu.cgi" ;	# 指図詳細画面

# 高精度タイマ用変数
my $t0 = gethrtime() ;		# 高精度現在時を取得
# 汎用変数
my $ret1 = "" ;				# エラーメッセージ戻り値
my $logFile = './logs/index.log' ;		# ログファイルの名前
my %in = () ;				# 入力・前画面からの引数
my %boss_BOM ;				# 指図BOM
my %egpro_BOM ;				# egproBOM
my %mentori ;				# 面取り数
my $bomDiff ;				# 差分明細
#********************************************
#          Main処理 ここから
#********************************************
#****************for DEBUG*******************
# print "Content-type:text/html\n\n<!DOCTYPE html>\n<HTML>\n<BODY>\n<meta charset=\"utf-8\" />\n" ;
my $dbg = 0;	#0:ope 1:dbg...show arguments
#********************************************
# **** ログ開始 ****
if (&recLog("\r\n".&dateTime(time)) eq "err"){
	$ret1 = "<font color=\"ff0000\">ローカルファイル(log)が開けません。<br>処理を終了します。:".$ret1."</font><br>\n" ;
	&error($ret1) ;
	goto exit_prog ;
}
# **** 設定ファイルを読む ****
if (!open(IN, "<", "./bom_diff.ini")){
	$ret1 = "<font color=\"ff0000\">設定ファイル(ini)が開けません。<br>処理を終了します。:".$ret1."</font><br>\n" ;
	&error($ret1) ;
	$ret1 = "'bom_diff.ini' is not be able to open ".$!."\n" ;
	$ret1 .= "System set the initial value. " ;
	&recLog($ret1) ;
}else{
	while (<IN>){
		my $val = $_ ;
		$val =~ s/\r\n|\r|\n//g ;
		if ($val =~ /#/){
			next ;
		}elsif ($val =~ /db_source.+\s(.+)$/){
			$val = $1 ;
			$db_source =~ s/(.+:)(.+)$/$1$val/ ;
		}elsif ($val =~ /db2_source.+\s(.+)$/){
			$val = $1 ;
			$db2_source =~ s/(.+:)(.+)$/$1$val/ ;
		}elsif ($val =~ /db_ODBCserver.+\s(.+)$/){
			$val = $1 ;
			$db_ODBCserver =~ s/(.+:)(.+)$/$1$val/ ;
		}
	}
	$ret1 = " =>system sets 'bom_diff.ini'" ;
	&recLog($ret1) ;
}
close IN ;
# cgiから%in{}にパラメータを取得
$CGI::POST_MAX = 2048 * 1024 ;		# postは最大2Mbytesまで
my $cgi = new CGI ;
%in = $cgi->Vars ;					# $in{''}はすべて初期化される
if (!%in){
	$in{'mode'} = "init" ;
}
&eval_arg() ;						# cgiからの入力引数の評価
# 抽出引数の一覧
if ($dbg == 1){
	foreach (keys(%in)){
		print "(73)key(".$_.")=".encode('utf8',$in{$_})."<br>\n" ;
	}
}
&recLog(" =>".$in{'mode'}) ;

# **** モードにより処理を分岐 ****
# **** 差分一覧画面 ****
if ($in{mode} eq "init"){}

# # **** 面取り数の取得 ****
# # 1シートあたりの面取り数を取得し、
# # $mentori{(品目コード)}に展開する。
# $t0 = gethrtime() ;
# if ( &get_mentori() eq "err" ){
	# &recLog(" => get_memtori Error : ".$ret1."\n" ) ;
	# goto exit_prog ;
# }
# &recLog(" =>mentori:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** SMT未着手指図BOM情報を読む ****
# 夜間バッチで出力され、SMT済み仕掛を除くBOM情報の
# ./cgiData/boss_BOM.tsvファイルを配列に展開する。
$t0 = gethrtime() ;
if ( &read_BOM()  eq "err" ){
	&recLog(" =>read_BOM Error : ".$ret1."\n" ) ;
	goto exit_prog ;
}
&recLog(" =>read_BOM:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** 所要量の取得 ****
# 有効指図の品目で、EGProDBからの最新部品配列情報を集計し、
# $egpro_BOM{(品目コード)}に展開する。
$t0 = gethrtime() ;
if (&read_egDB() eq "err" ){
	&recLog(" =>read_egDB Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
&recLog(" =>read_eg:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** 未着手指図の取得 ****
# SMT未着手の指図(liveOrder_sub)情報を取得し、
# 戻り値は取得内容のリファレンス
$t0 = gethrtime() ;
my $db_Data = &get_liveOrder() ;
if ($db_Data eq "err" ){
	&recLog(" =>get_liveOrder Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
&recLog(" =>get_livOrd:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** 指図毎に差分を抽出 ****
# $liveOrderに従い、%boss_BOM と %egpro_BOM の差分を求める。
# 戻り値は指図毎差分のリファレンス
$t0 = gethrtime() ;
$db_Data = &calc_sabun($db_Data) ;
if ($db_Data eq "err" ){
	&recLog(" =>sabun Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
&recLog(" =>sabun:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** htmlの組立て ****
# 指図毎差分データを渡す。
# 
$t0 = gethrtime() ;
my $html_cont = &make_html($db_Data) ;
&recLog(" =>mk_html:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** 画面の描画 ****
$| = 1;						# キャッシュしないようにする
$t0 = gethrtime() ;
&drw_scrn($html_cont) ;
$| = 0;						# キャッシュを戻す
&recLog(" =>drw_scrn:".int((gethrtime() - $t0)/1000000)."msec") ;

# **** 差分をDB出力(指図毎表示用) ****
# 
$t0 = gethrtime() ;
&upd_bomDiff($bomDiff) ;
$ret1 = " =>put_bomDiff:".int((gethrtime() - $t0)/1000000)."msec" ;
$ret1 .= " => ".&dateTime(time)." *** normal end *** \n" ;
&recLog ($ret1) ;
goto exit_prog ;

#********************************************
#                 Sub処理
#********************************************

# # ---- 面取り数テーブルの生成 ----
# # copy_BOSSで出力されたmentori.tsvを取得して、
# # %mentori{(品目コード)}に保存する。
# # 引数：なし
# # 戻り値：正常時:"0"、$ret1:処理件数、%mentori{(品目コード)}= "H",または "(面取数)"
# #		エラー時:"err"、$ret1:エラー詳細
# sub get_mentori(){
	# $ret1 = 0 ;
	# my $src ;
	# # ファイルの取得(一気読み)
	# if (!open(IN, "<", "./cgiData/mentori.tsv")){
		# $ret1 = "./cgiData/mentori.tsv cannot open: ".$! ;
		# close IN ;
		# return "err" ;
	# }else{
		# local $/ ;				# 行末記号をlocalでundefに
		# $src = <IN> ;			# ファイル内容を一気に変数に取得
	# }
	# close IN ;
	# foreach (split (/\r\n|\r|\n/, $src )){
		# my @col = split ("\t",$_) ;			# bossファイルのデリミタ：tab
		# # $mentori{$col[0]} = $col[1] ;
		# $ret1 = $ret1 + 1 ;
	# }
	# return $ret1 ;
# }

# ---- 未着手指図BOMを読む ----
# 未着手SMT指図BOM(./cgiData/boss_BOM.tsv)から指図BOMを取得して、
# %boss_BOM{(品目コード)}に保存する。
# 引数：なし
#　　boss_BOM.tsv：(品目)\t(指図)\t(部品コード)\t(基数)\r\n
# 戻り値：正常時:"0"、$ret1:処理件数、%boss_BOM{(品目コード)}= [(指図),(部品コード),(基数)],[]…
#		エラー時:"err"、$ret1:エラー詳細
sub read_BOM(){
	$ret1 = 0 ;
	my $src ;
	# ファイルの取得(一気読み)
	if (!open(IN, "<", "./cgiData/boss_BOM.tsv")){
		$ret1 = "./cgiData/boss_BOM.tsv cannot open: ".$! ;
		close IN ;
		return "err" ;
	}else{
		local $/ ;				# 行末記号をlocalでundefに
		$src = <IN> ;			# ファイル内容を一気に変数に取得
	}
	close IN ;
	foreach (split (/\r\n|\r|\n/, $src )){
		my @col = split ("\t",$_) ;			# bossファイルのデリミタ：tab
		push ( @{ $boss_BOM{$col[0]} } , ([ $col[1],$col[2],$col[3] ]) ) ;
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;
}

# ---- EGProデータベースを読む ----
# $boss_BOMの品目コードに必要な所要数を取得して 
# %egpro_BOM 配列に展開する。
# 引数：なし($boss_BOM{(品目コード)}のキー値
# 戻り値：正常時: "0"、$egpro_BOM{(品目コード)} = [(部品コード),(個数),(登録日時)]…
#		エラー時: "err"、$ret1: エラー詳細
sub read_egDB(){
	$ret1 = 0 ;
	my ($db, $st, $sql, $ary_ref, $where) ;
	my %bom ;
	my @egpro ;
	my ($lastUpd, $partNo, $qty) ; 
	# egProDBを読む
	eval{
		$db = DBI->connect($db_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db->{LongTruncOk}=1 ;
		$db->{LongReadLen}=200000 ;
		# 品目コード,指図,登録日時で重複を避けて登録日古い順に取得
		$sql = "SELECT DISTINCT 製品,管理コード,登録日時 FROM ".$db_ODBCview." ORDER BY 登録日時 ASC ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		my %typeList ;
		# 品目コードをキーにして、指図と登録日時を昇順で上書き→最後の上書きが最新
		foreach (@$ary_ref){
			$typeList{@$_[0]} = [@$_[1],@$_[2]] ;		# $typeList{(品目コード)} = [指図,登録日時]
		}
		foreach my $typeID (keys %boss_BOM){
			if (!$typeList{$typeID}){
# print $typeID."->no egpro\n" ;
				next;
			}
			$typeList{$typeID}[0] =~ s/^(\d{8,}).+/$1/ ;	# 指図部分を切り出し 
			$lastUpd = $typeList{$typeID}[1] ;				# 最新登録日時を取得
			# 同一管理コードを"含む"全品番(部品)を実装機全台から取得
			$sql = "SELECT 品番1,員数,管理コード,生産品番,登録日時 FROM ".$db_ODBCview." " ;
			$sql .= "WHERE 製品 LIKE ? AND 管理コード LIKE '".$typeList{$typeID}[0]."%' ;" ;
			$st = $db->prepare($sql) or die(DBI::errstr) ;
			$st->execute($typeID) or die(DBI::errstr) ;
			$ary_ref = $st->fetchall_arrayref ;
			# 品番(部品)コードのハッシュ配列化して合計計算
			%bom = () ;
			foreach my $eachNPM(@$ary_ref){
				# @$ary_refからの戻り値：品番1[0],員数[1],管理コード[2],生産品番[3],登録日時[4]
				# [2],[3],[4]は未使用
				if (!$bom{@$eachNPM[0]}){
					# 初出
					$bom{@$eachNPM[0]} = @$eachNPM[1] ;
				}else{
					# 既出なら累計を計算
					$bom{@$eachNPM[0]} = $bom{@$eachNPM[0]} + @$eachNPM[1] ;
				}
			}
			# 所要数を面取り数で1台毎に換算しながら通常配列へ変換
			@egpro = () ;
#			if ( !$mentori{$typeID} ){ $mentori{$typeID} = 1 ; }	# 面取り数未登録時のエラーを回避
			foreach (keys %bom){								# 部品コード毎に1台毎基数にして配列化
				# @egpro = [(部品コード),(個数),(登録日時)][…]…
#				push ( @egpro , ([$_ ,int ($bom{$_}/$mentori{$typeID}), $lastUpd ]) ) ;
				push ( @egpro , ([$_ ,$bom{$_}, $lastUpd ]) ) ;
			}
			@egpro = sort ({@$a[0] cmp @$b[0]} @egpro ) ;		# 部品コードを昇順にソート(boss_BOMも同順序)
			push (@{ $egpro_BOM{$typeID} } , @egpro) ;			# egpro_BOMに配列として追加
			$ret1 = $ret1 + 1 ;
# print $typeID."->saved\n";
		}
# print "(531)ALL saved\n" ;
		$db->disconnect ;
	};
	if ($@){
		if (defined($db)){$db->disconnect() ;}
		$ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	return $ret1 ;
}

# ---- liveOrderDBからのデータ取得 ----
# SMT未着手指図をDBから取得する。
# 引数：なし
# 戻り値：正常時は取得内容のリファレンス
#		[(品目)[0],(指図)[1],(発令台数)[2],
#		 (指図登録日)[3],(製造開始日)[4],(完成予定日)[5],
# 		 (指図タイプ)[6],(担当ライン)[7]]
#		エラー時は"err"、詳細は$ret1
sub get_liveOrder(){
	$ret1 = "" ;
	my ($db, $st, $sql, $ary_ref) ;
	my $colList = $db_liveOrder_sub.".typeID,".$db_liveOrder_sub.".orderNumber,".$db_liveOrder_sub.".orderQty," ;
	$colList .= $db_liveOrder_sub.".reg_date,".$db_liveOrder_sub.".start_date,".$db_liveOrder_sub.".finish_date," ;
	$colList .= $db_liveOrder_sub.".sashizu_type,".$db_liveOrder_sub.".LINE " ;
	$sql = "SELECT ".$colList."FROM ".$db_liveOrder_sub." " ;
	$sql .= "WHERE 1 " ;
	$sql .= "ORDER BY ".$db_liveOrder_sub.".orderNumber ASC ;" ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish() ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	return $ary_ref ;		# ref渡し
}

# ---- 未着手指図の差分出力 ----
# liveOrder_subの指図に従い、bossBOMとEGProBOMの差分を配列に出力する。
# 引数：liveOrder_subの内容、%boss_BOM{(品目コード)}、%egpro_BOM{(品目コード)}
#	[(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],(完成予定日)[5],
# 	 (指図タイプ)[6],(担当ライン)[7]]
# 戻り値：正常時: "0"
# 		エラー時: "err"、$ret1: エラー詳細
sub calc_sabun(){
	my @liveOrder = @{$_[0]} ;		# de-refして2次元配列
	$ret1 = 0 ;
	# $boss_BOM{(品目コード)} = [(品目コード)[0],(品目コード)[1],(部品コード)[2],(個数)[3]],…
	#  → $sashizu_BOM{(指図)} = [(部品コード)[0],(個数)[1]],…
	my %sashizu_BOM ;
	foreach my $typeID (keys %boss_BOM ){
		foreach ( @{ $boss_BOM{$typeID} } ){
#	print "(355)".@$_[0]."/".@$_[1]."/".@$_[2]."<br>\n";
			push (@{ $sashizu_BOM{@$_[0]} } , ([ @$_[1], @$_[2] ]) );
		}
	}
	# 指図毎に処理
	while ($liveOrder[$ret1]){
		my $typeID = $liveOrder[$ret1][0] ;		# 品目の取得
		my $sas_key = $liveOrder[$ret1][1] ;	# 指図の取得
# print "(360)".$typeID."//".$sas_key."<br>\n" ;
		# 当該指図で部品Cを昇順に並べ替え($egpro_BOMはソート済み)
		@{ $sashizu_BOM{$sas_key} } = sort ({@$a[0] cmp @$b[0]} @{ $sashizu_BOM{$sas_key} }) ;
		# 部品コード順にポインタを移動して比較、結果を $bomDiff に保存
		my ($boss_Indx, $egpro_Indx) = (0, 0) ;
		my @partNo = @{ $sashizu_BOM{$sas_key} } ;
		my $diff = "0" ;
		my $regDate ;
		while (){
			my $boss = $partNo[$boss_Indx][0] ;
			my $egpr = $egpro_BOM{$typeID}[$egpro_Indx][0] ;
#		print "(370)".$boss."/".$egpr."<br>\n";
			# 部品毎にboss_BOM,egpro_BOMのEOFまでチェックし、@liveOrder,@bomDiffを生成
			# @bomDiff = [(品目コード),(指図),(部品コード),(boss基数),(egpro基数),(egpro登録日時)]
			if (!$boss && !$egpr){
				# boss/egpro両方がundef(EOF)になったら抜ける
				last ;
			}elsif (!$boss){
				# bossの部品Cがない ==> boss部品が基数"0"、egpro部品が実数、登録日あり
				$bomDiff .= "('".$typeID."','".$sas_key."','".$egpr."'," ;
				$bomDiff .= "'0','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
				$bomDiff .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
				$diff = "1" ;						# 差分ありフラグ
				$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
			}elsif (!$egpr){
				# egproの部品Cがない ==> egpro部品が基数"0"、boss部品が実数、登録日NULL
				$bomDiff .= "('".$typeID."','".$sas_key."','".$boss."'," ;
				$bomDiff .= "'".$partNo[$boss_Indx][1]."','0'," ;
				$bomDiff .= "NULL)\t" ;
				$diff = "1" ;						# 差分ありフラグ
				$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
			}elsif ($boss gt $egpr) {
				# bossの部品C＞egproの部品C ==> boss部品が基数"0"、egpro部品が実数、登録日あり
				$bomDiff .= "('".$typeID."','".$sas_key."','".$egpr."'," ;
				$bomDiff .= "'0','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
				$bomDiff .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
				$diff = "1" ;						# 差分ありフラグ
				$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
			}elsif ($boss lt $egpr) {
				# bossの部品C＜egproの部品C ==> egpro部品が基数"0"、boss部品が実数、登録日NULL
				$bomDiff .= "('".$typeID."','".$sas_key."','".$boss."'," ;
				$bomDiff .= "'".$partNo[$boss_Indx][1]."','0'," ;
				$bomDiff .= "NULL)\t" ;
				$diff = "1" ;						# 差分ありフラグ
				$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
			}elsif ($boss eq $egpr) {
				# bossの部品C＝egproの部品C ==> 両方が実数 
				$bomDiff .= "('".$typeID."','".$sas_key."','".$boss."'," ;
				$bomDiff .= "'".$partNo[$boss_Indx][1]."','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
				$bomDiff .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
				if ($partNo[$boss_Indx][1] != $egpro_BOM{$typeID}[$egpro_Indx][1]){
					$diff = "1" ;					# 差分ありフラグ
				}
				$boss_Indx = $boss_Indx + 1 ;
				$egpro_Indx = $egpro_Indx + 1 ;
			}
			if (defined $egpro_BOM{$typeID}[$egpro_Indx][2]){
				$regDate = $egpro_BOM{$typeID}[$egpro_Indx][2] ;
			}
		}
		# EGPro更新済判定(差分なしで今日の登録日なら変更済:"-1")
		if (defined $regDate){
			$regDate =~ s/^(\d{4}-\d{2}-\d{2}).+/$1/ ;
			&dateTime(time) =~ /^(.+)\s/ ;
			my $today = $1 ;
			if (($diff eq "0") && ($regDate eq $1)){ $diff = "-1" ;}
# print "(422)".$typeID."/".$sas_key.":".$regDate." / ".$today." / ".$diff."<br>\n";
		}
		# 配列の当該要素の末尾要素として追加
		push ( @{$liveOrder[$ret1]} , $diff ) ;
		$ret1 = $ret1 + 1 ;
	}
	return \@liveOrder ;		# ref化して渡し
}


# ---- 差分詳細DBの更新 ----
# 差分チェックされたデータから生成されたsqlコマンドで
# bomDiff DBを更新する。
# 引数：差分チェック結果のリファレンス
#		[(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],
# 			(完成予定日)[5],(指図タイプ)[6],(担当ライン)[7],(差分フラグ)[8]]
# 戻り値：正常時は "0"
#		エラー時は"err"、詳細は$ret1
sub upd_bomDiff(){
	my ($db, $st, $sql) ;
	$ret1 = 0 ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 仕掛中指図BOMDB(172.254.253.60.orderNumber.bomDiff)に差分詳細を書込み
		# 旧データの削除
		$sql = "TRUNCATE TABLE ".$db_bomDiff." ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		# 新データの書込み
		$sql = "INSERT INTO `".$db_bomDiff."` " ;
		$sql .= "(`typeID`,`orderNumber`,`subType`,`unitQty`,`eg_unitQty`,`eg_regDate`) VALUES " ;
		foreach (split ("\t", $bomDiff)){
			$sql .= $_."," ;
			$ret1 = $ret1 + 1 ;
			if ($ret1 % 10000 == 0){
				$sql =~ s/,$// ;
				$sql .= " ON DUPLICATE KEY UPDATE " ;
				$sql .= "`unitQty`=VALUES(unitQty),`eg_unitQty`=VALUES(eg_unitQty),`eg_regDate`=VALUES(eg_regDate) ;" ;
				$st = $db->prepare($sql) or die(DBI::errstr) ;
				$st->execute() or die(DBI::errstr) ;
				$st = $db->commit ;
				$sql = "INSERT INTO `".$db_bomDiff."` " ;
				$sql .= "(`typeID`,`orderNumber`,`subType`,`unitQty`,`eg_unitQty`,`eg_regDate`) VALUES " ;			
			}
		}
		$sql =~ s/,$/ / ;
		$sql .= "ON DUPLICATE KEY UPDATE " ;
		$sql .= "`unitQty`=VALUES(unitQty),`eg_unitQty`=VALUES(eg_unitQty),`eg_regDate`=VALUES(eg_regDate) ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	return $ret1 ;
}


# ---- html文の生成 ----
# 差分チェックされたデータからhtmlを生成する。
# 引数：差分チェック結果のリファレンス
#		[(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],
# 			(完成予定日)[5],(指図タイプ)[6],(担当ライン)[7],(差分フラグ)[8]]
# 戻り値：正常時はhtmlテキスト
#		エラー時は"err"、詳細は$ret1
sub make_html(){
	my @eachRec = @{$_[0]} ;		# de-refして2次元配列
	my $cont = "" ;
	my $row = 0 ;
	foreach (@eachRec){
# print "(488)".Dumper($_)."<br>\n" ;		
		my @col = @$_ ;
		my $sts ;
		$col[2] = $col[2] + 0 ;				# 発令台数を整数化
		$col[3] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# yyyy-mm-dd
		$col[4] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;
		$col[5] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;
		if ($col[8] eq "1"){						# 不一致：赤
			$sts = "<img src=\"./cgiData/red.png\">" ;
		}elsif ($col[8] eq "-1"){					# 登録今日：青
			$sts = "<img src=\"./cgiData/blu.png\">" ;
		}elsif ($col[8] eq "0"){					# 一致：緑
			$sts = "<img src=\"./cgiData/grn.png\">" ;
		}else{
			$sts = "N.A." ;
		}
		$sts = "<span onclick=\"openWindow(\'".$indv_scrn."?sashizu=".$col[1]."&sts=".$col[8]."\'); return false;\">".$sts."</span>" ;
		if ($row % 2){								# 行毎の色変え
			$cont .= "\t\t<tr class=\"even\">\n" ;
		}else{
			$cont .= "\t\t<tr class=\"odd\">\n" ;
		}
		$cont .= "\t\t\t<td onclick=\"openWindow(\'".$indv_scrn."?sashizu=".$col[1]."&sts=".$col[8]."\'); return false;\">" ;
		$cont .= "<b><font color=\"4040ff\"><a class=\"hov\">".$col[1]."</a></font></b></td>\n" ;
		$cont .= "\t\t\t<td>".$col[7]."</td><td>".$col[0]."</td><td>".$col[2]."</td>" ;
		$cont .= "<td>".$col[3]."</td><td>".$col[4]."</td><td>".$col[5]."</td>\n" ;
		$cont .= "\t\t\t<td>".$col[6]."</td><td>".$sts."</td>\n" ;
		$cont .= "\t\t</tr>\n" ;
		$row = $row + 1 ;
	}
	return $cont ;						# htmlを戻す
}

# ---- Logの出力 ----
# 引数で渡されるメッセージのlogファイル出力。
# バッファリングを解除、書込み禁止して排他処理して更新。
# 引数：メッセージテキスト
# 戻り値：エラーなしはNULL、ありはメッセージを返す。
sub recLog(){
	if (open (FH, ">>", $logFile)){
		print FH @_ ;
		close FH ;
	}else{
		$ret1 = "Log File Error:".$! ;
		close FH;
		return "err" ;
	}
	close FH ;
	return 0 ;
}

# ---- 入力引数の評価 ----
# %in{''}で渡された入力引数を評価。
# 引数：なし(グローバル変数で%in
# 戻り値：なし(グローバル変数で%in)
sub eval_arg(){
	# モードの設定(uploadは入力画面、それ以外は他画面)
	# if (defined $in{'upload'}){$in{'mode'} = 'upload' ;}			# 「保存」
	# if (defined $in{'restrt'}){$in{'mode'} = 'restrt' ;}			# 「戻る」
	# if (defined $in{'trend'}){$in{'mode'} = 'trend' ;}				# 「トレンド」
	# if (defined $in{'setRef'}){$in{'mode'} = 'setRef' ;}			# 「基準にする」
	# # 「ch変更」、「参照」は$in{'mode'}に取り込まない
}

# ---- エラー表示処理 ----
# エラーメッセージを表示
# 引数:エラーテキスト
# 戻り値:なし
sub error(){
		print "Content-type:text/html\n\n" ;
		print "<html>\n<body><meta charset=\"utf-8\" />\n" ;
		print "\t<br>".$_[0]."<br>\n" ;
		print "</body>\n</html>\n" ;
}

# ---- 画面の生成 ----
# 差分を表示する。
# 引数：なし
# 戻り値：なし
sub drw_scrn(){
	my $html = <<"HTML" ;
Content-type:text/html

<!DOCTYPE html>
<html lang="jp">
<head>
	<title>SMT実装部品 差分表示プログラム</title>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<link rel="shortcut icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="stylesheet" href="./jquery/themes/blue/style.css" type="text/css" media="print, projection, screen" />
	<script type="text/javascript" src="./jquery/fixed_midashi.js"></script>
	<script src="./jquery/jquery-latest.js" type="text/javascript"></script> 
	<script src="./jquery/jquery.tablesorter.min.js" type="text/javascript"></script>
 	<script type="text/javascript">
		// tablesorterの並べ替え
		\$(document).ready(function() { 
			\$("#tablstr").tablesorter({
				headers: {
					3:	 { sorter: false },
					4:	 { sorter: false },
					7:	 { sorter: false },
					8:	 { sorter: false }
				}
			});
		}); 
		// サブウィンドウのサイズ他パラメータ設定
		function openWindow(url) {
			window.open(url,"subw","width=650, height=650, scrollbars=1");
		}
		// 結果のダウンロード
		function dlFile() {
			var content = ""; 
			var filename = "sabun.csv";
			const myTbl = document.getElementById('tablstr');
			// ファイル内容の生成
			for(var j = 1 ;j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
				content = content + myTbl.rows[j].cells[0].innerText + "," ;	//指図
				content = content + myTbl.rows[j].cells[1].innerText + "," ;	//担当
				content = content + "'" + myTbl.rows[j].cells[2].innerText + "'," ;	//品目コード
				content = content + myTbl.rows[j].cells[3].innerText + "," ;	//台数
				content = content + myTbl.rows[j].cells[4].innerText + "," ;	//指図登録日
				content = content + myTbl.rows[j].cells[5].innerText + "," ;	//製造開始日
				content = content + myTbl.rows[j].cells[6].innerText + "," ;	//完成予定日
				content = content + myTbl.rows[j].cells[7].innerText + "," ;	//タイプ
				if (myTbl.rows[j].cells[8].innerHTML.match(/red/)) {
					content = content + "NG"							//差分あり
				}else if (myTbl.rows[j].cells[8].innerHTML.match(/blu/)) {
					content = content + "DONE"							//差分修正済
				}else if (myTbl.rows[j].cells[8].innerHTML.match(/grn/)) {
					content = content + "OK"							//差分なし
				}
				content = content + "\\r\\n";
			}
			var blob = new Blob([content], { "type" : "text/plain" });
			// ブラウザで処理を分岐
			if (window.navigator.msSaveBlob) { 
				// IEの場合
				//window.navigator.msSaveBlob(blob, filename); 		// ファイルを"保存"
				window.navigator.msSaveOrOpenBlob(blob, filename);	// ファイルを"保存"or"開く"
			}else{
				// IE以外の場合
				var url = window.URL.createObjectURL(blob);
				// 仮想的に"a"要素を生成
				const a = document.createElement("a");
				document.body.appendChild(a);
				a.style = "display:none";
				a.href = url;
				a.download = filename;
				a.click();							// clickをシミュレートして自動ダウンロード
				window.URL.revokeObjectURL(url); 	// release the used object.
				a.parentNode.removeChild(a); 		// delete the temporary "a" element
			}
		}
		function selSabun(col) {
			// checkboxの状態を取得
			const btn_grn = document.getElementById("chkGrn").checked ;
			const btn_red = document.getElementById("chkRed").checked ;
			const btn_blu = document.getElementById("chkBlu").checked ;
			// 行の表示/非表示を選択
			const myTbl = document.getElementById('tablstr');
			// ファイル内容の生成
			for(var j = 1 ;j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
				if (myTbl.rows[j].cells[8].innerHTML.match(/red/)) {
					if (btn_red == false){
						myTbl.rows[j].style.display = "none" ;
					}else{
						myTbl.rows[j].style.display = "" ;
					}
				}else if (myTbl.rows[j].cells[8].innerHTML.match(/blu/)) {
					if (btn_blu == false){
						myTbl.rows[j].style.display = "none" ;
					}else{
						myTbl.rows[j].style.display = "" ;
					}
				}else if (myTbl.rows[j].cells[8].innerHTML.match(/grn/)) {
					if (btn_grn == false){
						myTbl.rows[j].style.display = "none" ;
					}else{
						myTbl.rows[j].style.display = "" ;
					}
				}
			}
		}
	</script>
	<style>
		/* テーブルの書式・色 	*/
		table {
			border:solid 1px #ffcdcd; border-collapse: collapse;
			margin:10px 0px 15px 0px;
		}
		th {
			border:solid 1px #ffcdcd; border-collapse: collapse;
			background-color:#e6eeee; 
			font-size: 1.0em;
			text-align: center;
		}
		th.sel {
			background-color:#d0d8d8; 
		}
		tr.odd {
			border:solid 1px #ffcdcd; border-collapse: collapse;
			background-color:#ffe4e4;
			text-align:center; 
		}
		tr.even {
			border:solid 1px #ffcdcd; border-collapse: collapse;
			background-color:#e4e4ff;
			text-align:center; 
		}
		td {text-align: center;}
		td.left {text-align: left;}
		td.right {text-align: right;}
		span.sabunR {
			font-size:1.5em;
			color:#ff0000;
		}
		span.sabunG {
			font-size:1.5em;
			color:#40ff40;
		}
		/* hoverの設定*/
		a.hov:hover {color: #a0a0ff;}
		/* FixedMidashiの設定 */
		div.scroll_div {overflow: auto;}
		
	</style>
</head>
HTML

	$html .= "<body style=\"font-family: sans-serif; margin: 30px;\" onLoad=\"FixedMidashi.create();\">" ;
	$html .= "<span style=\"font-size: 3ex; font-weight: bold;\">【差分チェックシステム】</span> <span>WWW-0084 ver. ".$ver."</span>" ;
	$html .= <<"HTML";
<hr width="1020" size="5" color="e0e0f0" align="left">
<form name="form" method="post" action="/cgi/bom_diff/index.cgi">
「指図」、「差分」をクリックで指図毎詳細ウィンドウが開く。<br>
　スライダーが最上位で <img src=./jquery/themes/blue/bg.gif> 項目欄をクリックで昇順/降順の並べ替え。
	差分一致：<img src="./cgiData/grn.png"><input type="checkbox" onClick="selSabun('grn');" id="chkGrn" checked="checked">
	　不一致：<img src="./cgiData/red.png"><input type="checkbox" onClick="selSabun('red');" id="chkRed" checked="checked">
	　修正済：<img src="./cgiData/blu.png"><input type="checkbox" onClick="selSabun('blu');" id="chkBlu" checked="checked"><br>
</form>
<form name="form1" method="post" action="/cgi/bom_diff/index.cgi">
	<div class="scroll_div">
	<table border="0" style="margin-left: 0px; padding: 5px; background-color: #ffffff;" class="fixedHead tablesorter" _fixedhead="rows:1; cols:0;" id="tablstr">
		<thead>
			<tr>
			<th style="width: 100px;">指図</td>
			<th style="width: 50px;">担当</td>
			<th style="width: 130px;">品目コード</td>
			<th style="width: 70px;">台数</td>
			<th style="width: 120px;">指図登録日</td>
			<th style="width: 120px;">製造開始日</td>
			<th style="width: 120px;">完成予定日</td>
			<th style="width: 80px;">タイプ</td>
			<th style="width: 50px;">差分</td>
			</tr>
		</thead>
		<tbody>
HTML
	$html .= $_[0] ;
	# $html .= "\t\t<input type=\"hidden\" name=\"dut_file\" value=\"".$in{'dut_file'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"jig\" value=\"".$in{'jig'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"jigID\" value=\"".$in{'jigID'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"wkrID\" value=\"".$in{'wkrID'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"line\" value=\"".$in{'line'}."\">\n";
	$html .= <<"HTML";
		</tbody>
		<tfoot>
			<tr>
				<td><input type="button" value="csv出力" onClick="dlFile()" id="dnload" style="background-color:#d0ffff;"/></td>
				<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
			<tr>
		</tfoot>
	</table>
	</div>
</form>
</body>
</html>
HTML
	print $html;
}

# ---- 時刻生成処理 ----
# unix時刻を規定形式で戻す
# 引数:unix時刻
# 戻り値:YYYY-MM-DD HH:MM:SS 形式の日時
sub dateTime(){
	my @t = localtime($_[0]);
	return sprintf("%04d-%02d-%02d %02d:%02d:%02d",$t[5]+1900,$t[4]+1,$t[3],$t[2],$t[1],$t[0]);
}

# ---- 時刻をunix時刻に変換 ----
# 時刻をunix時刻に変換して戻す
# 引数:YYYY-MM-DD HH:MM:SS形式、またはYYYY/MM/DD HH:MM:SS形式の時刻
# 戻り値:unix時刻
sub unixTime(){
	my $t = $_[0] ;
	$t =~ s/\//-/g ;
	$t =~ /(\d{4}).(\d{2}).(\d{2}) (\d{2}):(\d{2}):(\d{2})/ ;
	return timelocal($6,$5,$4,$3,$2-1,$1-1900) ;
}

exit_prog: