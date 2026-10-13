#!/usr/bin/perl -w

#******************************************************************
# このプログラムは、オペレータがwebページをアクセスするときに
# 最初に起動され、
# 1.定時処理されたcopy_BOSS.cgiが出力するEGprowebサーバの
#   bossBOM DBと、EGprowebサーバが持つ実装BOM情報である
#   egproBOM DBとの差分集計結果を指図毎に一覧表示する。
# 2.差分結果は、指図別表示のためEGprowebサーバのbomDiff DB
#   に展開される。
# 3.「指図」または「差分結果」のクリックで指図毎画面の表示を行う。
#   (javascript)
# 4.「適用除外解除」ボタンで、EGprowebサーバのexepPart DBから
#   対象部品の登録削除(復活)処理を行う。
#   ---(以下はbom_diff.js内で行う)---
# 5.差分結果のチェックボックスで結果のフィルタを行う。
# 6.「CSV出力」ボタンで、表示内容をcsv形式でファイルダウンロードする。
#									2021/01/10 J.Igarashi
#【変更履歴】
# Ver. 1.00:初回リリース。
# Ver. 1.10:差分をチェックボックスで表示選択
#			一覧画面にcsvダウンロードを追加
# Ver. 2.00:アプリ設定値をiniファイルから上書き読込み追加。
# 			未登録品を白マルで表示
#			社外生産品の差分チェックに対応
#			(自DBで生産場所stsをEGPro登録日で自動更新)
#			除外部品復活画面のボタンを追加
#			(exemptDBの更新)
# Ver. 2.10:bossBOMの取得日時の表示と手動による更新を追加
# Ver. 2.11:試作ダミーコード登録(不正データ登録対策の強化)に対応
# Ver. 2.20:egproBOM更新、bomDiff更新を高速化
#			フィルタに未登録、NA追加
#			(sashizu.cgi)面取り数変更、差分フィルタ機能を追加
# Ver. 2.21:csv出力時に<table>の<tr>タグ不良でエラー発生を修正
#******************************************************************
my $ver = "2.21" ;
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
binmode STDIN, ':utf8' ;	# Apache error log対策
binmode STDOUT, ':utf8' ;
binmode STDERR, ':utf8' ;

# SQLサーバ・ユーザ・パスワード・関連変数(bom_diff.iniにより上書き)
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60';
my $db2_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db_user = 'process_mgt';
my $db_passwd = '7bcsHFk8P7VxRcFD';
my $db_bossBOM = 'bossBOM' ;
my $db_egproBOM = 'egproBOM' ;
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db2_unitInfo = 'unitInfo' ;
# ODBC関連接続情報
my $db_ODBCserver = "dbi:ODBC:EGPro" ;	# DB:EGProKOHDEN-Planに対するDSN
my $db_ODBCuser = "sqluser" ;
my $db_ODBCpasswd = "Pfseg001" ;
my $db_ODBCview = "T_部品配列表" ;
my $db_ODBCview2= "D_指図実行Log" ;
# Javascript
my $bom_diff_js = "bom_diff.js" ;

# 飛び先画面
my $self_scrn = "./index.cgi" ;		# 自画面
my $indv_scrn = "./sashizu.cgi" ;	# 指図詳細画面
my $indv_scrn2 = "./exemp.cgi" ;	# 除外部品修正画面
my $copy_BOSS_cgi = "./copy_BOSS.cgi" ;

# 汎用変数
my $ret1 = "" ;				# エラーメッセージ戻り値
my $recLog = "" ;			# ログテキスト
my $logFile = './logs/index.log' ;		# ログファイルの名前
my %in = () ;				# 入力・前画面からの引数
my %boss_BOM ;				# 指図BOM
my %egpro_BOM ;				# egproBOM
my %mentori ;				# 面取り数
my %ongoing ;				# 着手済み指図
my $bomDiff ;				# 差分明細
my $regDate ;				# 登録日時
my $newestDate ;			# 最新登録日時
my $bossUpd ;				# boss出力日時
# 高精度タイマ用変数
my ($t0, $t1) ;	
$t0 = gethrtime() ;			# 高精度現在時を取得
#********************************************
#          Main処理 ここから
#********************************************
#****************for DEBUG*******************
my $dbg = 0	; 	#0:ope 1:dbg...show arguments 2:dbg...show html
my $dbg_msg = "<font color=\"ff0000\">(DEBUG MODE)</font><br>\n" ;
# DBの一時変更
if ( $dbg > 0 ){
	$db_bossBOM = 'bossBOM2' ;
	$db_egproBOM = 'egproBOM2' ;
	$db_liveOrder_sub = 'liveOrder_sub2' ;
	$self_scrn = "./index2.cgi" ;
	$indv_scrn = "./sashizu2.cgi" ;
	$logFile = './logs/index2.log' ;
}
#$bom_diff_js = "bom_diff2.js" ;
#********************************************
print <<"HEAD" ;
Content-type:text/html

<!DOCTYPE html>
<html lang="ja">
<head>
	<meta charset="utf-8" />
	<meta http-equiv="content-language" content="ja" />
	<meta name="google" content="notranslate" />
	<title>SMT実装部品 差分表示プログラム</title>
	<meta http-equiv="X-UA-Compatible" content="IE=edge" />
	<link rel="shortcut icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="stylesheet" href="./jquery/themes/blue/style.css" type="text/css" media="print, projection, screen" />
	<script type="text/javascript" src="./jquery/fixed_midashi.js"></script>
	<script src="./jquery/jquery-latest.js" type="text/javascript"></script> 
	<script src="./jquery/jquery.tablesorter.min.js" type="text/javascript"></script>
HEAD
print "\t<script src=\"./".$bom_diff_js."\" type=\"text/javascript\"></script>\n" ;

# **** ログ開始 ****
$recLog = &dateTime(time)." from ".$ENV{'REMOTE_ADDR'}."(Ver.".$ver.") START ===" ;
# **** 設定ファイルを読む ****
if (!open(IN, "<", "./bom_diff.ini")){
	$recLog .= "'bom_diff.ini' is not be able to open ".$!." System set the initial value. " ;
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
	$recLog .= "=> reads'bom_diff.ini' " ;
}
close IN ;
# cgiから%in{}にパラメータを取得
$CGI::POST_MAX = 2048 * 1024 ;		# postは最大2Mbytesまで
my $cgi = new CGI ;
%in = $cgi->Vars ;					# $in{''}はすべて初期化される
$recLog .="=>strt =>mode:" ;
if (!%in){
	$in{'mode'} = "init" ;
	$recLog .= "init=> " ;
}
# 抽出引数の一覧
foreach (keys(%in)){
	$dbg_msg .= "(163)key(".$_.")=".decode('utf8',$in{$_})."<br>\n" ;
}

# **** 入力引数により処理分岐 ****
if (defined $in{'updBOM'}){				# **** "BOM取得更新"ボタンの押下 ****
	$recLog .= " => updBOM" ;
	$dbg_msg .= "(169)strt ".$copy_BOSS_cgi." ".int((gethrtime() - $t0)/1000000)."msec => " ; 
	system "perl ".$copy_BOSS_cgi ;		# copy_BOSS.cgiの再起動
	$recLog .= "(done) " ;
	$dbg_msg .= "done ".$copy_BOSS_cgi." ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
}

# **** 面取り数の取得 ****
# 1シートあたりの面取り数を取得し、$mentori{(品目コード)}に展開する。
$t1 = gethrtime() ;
if ( &get_mentori() eq "err" ){
	$recLog .= " => get_memtori Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> mentori:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 指図BOM情報の取得 ****
# EGprowebサーバのbossBOM DBを%boss_BOM{(品目コード)}に展開する。
$t1 = gethrtime() ;
if ( &read_BOM()  eq "err" ){
	$recLog .= " => read_BOM Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> read_bossBOM:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 所要量情報の取得 ****
# EGProサーバのDBから最新部品配列情報を集計し、
# 新しいBOMがあればEGprowebサーバのegproBOM DBを更新、
# $egpro_BOM{(品目コード)}にも展開する。
$t1 = gethrtime() ;
if (&read_egDB() eq "err" ){
	$recLog .= " => read_egproBOM Error : ".$ret1 ;
	goto exit_prog;
}
$recLog .= "=> read_egDB:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 未着手指図情報の取得 ****
# EGprowebサーバのliveOrder_sub DB情報を取得し、
# 取得内容のリファレンスとして戻す。
$t1 = gethrtime() ;
my $db_Data = &get_liveOrder() ;
if ($db_Data eq "err" ){
	$recLog .= " => get_liveOrder Error : ".$ret1 ;
	goto exit_prog;
}
$recLog .= "=> get_livOrd:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 指図毎に差分を抽出 ****
# リファレンスで受けたliveOrder_subの内容に従い、
# %boss_BOM と %egpro_BOM の差分を求めて指図毎差分のリファレンスとして戻す。
$t1 = gethrtime() ;
$db_Data = &calc_sabun($db_Data) ;
if ($db_Data eq "err" ){
	$recLog .= " => sabun Error : ".$ret1 ;
	goto exit_prog;
}
$recLog .= "=> sabun:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** htmlの組立て ****
# 指図毎差分データを渡して、表内のhtmlを生成する。
$t1 = gethrtime() ;
my $html_cont = &make_html($db_Data) ;
$recLog .= "=> mk_html:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 画面の描画 ****
# 画面全体のhtmlを生成する。
$t1 = gethrtime() ;
if ( $dbg != 1){
	&drw_scrn($html_cont) ;
}
$recLog .= "=> drw_scrn:".int((gethrtime() - $t1)/1000000)."msec " ;

# **** 差分をDB出力(指図毎表示用) ****
# 詳細差分をDBに書き込む。
$t1 = gethrtime() ;
if (&upd_bomDiff($bomDiff) eq "err"){
	$ret1 = "=> put_bomDiff Error : ".$ret1 ; 
	$recLog .= $ret1." => ".&dateTime(time)." *** abnormal end ***" ;
}else{
	$ret1 = "=> put_bomDiff(".$ret1."Recs):".int((gethrtime() - $t1)/1000000)."msec " ;
	$recLog .= $ret1." => ".&dateTime(time)." *** normal end ***" ;
}
goto exit_prog ;

#********************************************
#                 Sub処理
#********************************************

# ---- 面取り数テーブルの生成 ----
# nksv560サーバの unitInfo DBにある面取数情報を取得して、
# %mentori{(品目コード)}に展開する。
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数、%mentori{(品目コード)}= (面取数)
#		エラー時:"err"、$ret1:エラー詳細
sub get_mentori(){
	$dbg_msg .= "(263)strt get_mentori ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my ($db, $st, $sql, $ary_ref) ;
	# nksv560サーバ($db2_source)のunitInfoテーブルから品目、基板取数を取得
	$sql = "SELECT `typeID`,`chldID` FROM ".$db2_unitInfo." WHERE `typeID` LIKE 'U%' ;" ;
	eval{
		$db = DBI->connect($db2_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
		$dbg_msg .= "(275)'".$db2_unitInfo."' SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		if ( !defined (@$_[1]) ){			# 面取り数がない時は"1"とする。
			$mentori{@$_[0]} = 1 ;
		}else{
			@$_[1] =~ /(\d{1,3})/ ;			# 数字1～3ケタ部分のみを抽出
			$mentori{@$_[0]} = $1 ;
		}
		$ret1 = $ret1 + 1 ;
	}
	$dbg_msg .= "(292)exit get_mentori ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ret1 ;
}

# ---- 未着手指図BOMを読む ----
# 定時起動されるcopy_BOSS.cgiで更新されるbossBOM DB (未着手SMT指図BOM)から
# さらに更新時以降の実績データも反映した指図BOMを取得して、
# %boss_BOM{(品目コード)}に保存と、bossの出力日時(タイムスタンプ)を取得する。
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数、%boss_BOM{(品目コード)}= [(指図),(部品コード),(基数)],[]…
#		エラー時:"err"、$ret1:エラー詳細
sub read_BOM(){
	$dbg_msg .= "(304)strt read_BOM ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my ($db, $st, $sql, $ary_ref) ;
	$sql = "SELECT `typeID`,`orderNumber`,`partNo`,`qty`,`regDate` FROM ".$db_bossBOM." " ;
	$sql .= "WHERE 1 ORDER BY `partNo` ASC ;" ;
	# EGprowebサーバ($db_source)のbossBOMテーブルから品目、指図、部品コード、基数(1台)、登録日を取得
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
		$dbg_msg .= "(317)'".$db_bossBOM."' SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		if ( @$_[0] eq "bossUpd" ){
			$bossUpd = @$_[4] ; 		# boss出力日
		}else{
			push ( @{ $boss_BOM{@$_[0]} } , ([ @$_[1],@$_[2],@$_[3] ]) ) ;
			$ret1 = $ret1 + 1 ;
		}
#if ( @$_[0] eq "UR-1234" ){ $dbg_msg .= "(329)UR-1234/".@$_[1]."/".@$_[2]."=>" ; }
	}
	$dbg_msg .= "(334)exit read_BOM ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ret1 ;
}

# ---- EGProのDBを読んでローカルのDBを更新 ----
# EGProの［T_部品配列表］の所要数を集計して、
# ローカルの egproBOM DB より新しい、または、当日の日付の場合は、
# 基数を一台あたりに変換して egproBOM DB を更新、さらに、
# 社外生産分を含む egproBOM DB 全体を %egpro_BOM 配列に展開する。
# 引数：なし($boss_BOM{(品目コード)}のキー値
# 戻り値：正常時: "0"、$egpro_BOM{(品目コード)} = [(部品コード),(個数),(登録日時)]…
#		エラー時: "err"、$ret1: エラー詳細
sub read_egDB(){
	$dbg_msg .= "(347)strt read_egDB ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my ( $db, $st, $sql, $ary_ref, $ary_ref2 ) ;
	my ($kanri, $typeID, $partNo, $qty, $lastUpd) ; 
	# EGProweb:egproBOMを読む(9.5万件/約650msec→1300件/約150msec)
	my %egproweb_lastUpd ;	# $egproweb_lastUpd{$typeID}=[$lastUpd]
	eval{
		# EGProwebサーバ(172.25.253.60)のegproBOMから、全品目毎の更新日時を%egproweb_lastUpdに取得する。
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$sql = "SELECT DISTINCT `typeID`,`regDate` FROM `".$db_egproBOM."` WHERE 1 ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
		$dbg_msg .= "(362)'".$db_egproBOM."' SELECT DISTINCT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
	};
	if ($@){
		if (defined($db)){$db->disconnect() ;}
		$ret1 = "mysql:sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	$ret1 = 0 ;
	$newestDate = "2021-01-01 00:00:00" ;
	foreach ( @$ary_ref ){
		$egproweb_lastUpd{@$_[0]} = @$_[1] ;	# $egproweb_lastUpd{品目コード} = 生産日時
		if ( @$_[1] gt $newestDate ){ $newestDate = @$_[1] ; }	;	# 新しい登録日時に更新
		$ret1 = $ret1 + 1 ;
	}
#	$newestDate =~ s/\.\d{3}$// ;				# 秒の小数点以下を削除
	$dbg_msg .= "(377)'".$db_egproBOM."' EGProweb end. ".int((gethrtime() - $t0)/1000000)."msec #:".$ret1."items=> <br>\n" ;

	# EGprosrv:［T_部品配列表］を読む(124万件/5sec→8.5万件/約700msec)
	my %egpro_lastUpd ;		# $egpro_lastUpd{$typeID}=[$kanri,$lastUpd]
	eval{
		# EGprosrvサーバの［T_部品配列表］から、全品目毎に最新の更新日時と管理コード(指図)を取得
		$db = DBI->connect($db_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db->{LongTruncOk}=1 ;
		$db->{LongReadLen}=200000 ;
		$sql = "SELECT DISTINCT 製品,管理コード,登録日時 FROM ".$db_ODBCview." " ;
		$sql .= "ORDER BY 登録日時 DESC ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$dbg_msg .= "(391)'".$db_ODBCview."' SELECT DISTINCT2 res1. ".int((gethrtime() - $t0)/1000000)."msec => \n" ;
		# EGProsrvサーバの［D_指図実行Log］から実行済指図を取得
		$sql = "SELECT 指図番号,生産品番 FROM ".$db_ODBCview2." " ;
		$sql .= "WHERE 開始日時 > '".&dateTime( time - 86400 )."' ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref2 = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
		$dbg_msg .= "(400)'".$db_ODBCview2."' SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => <br>\n" ;
	};
	if ($@){
		if (defined($db)){$db->disconnect() ;}
		$ret1 = "ODBC:sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	# 登録日時と管理コードをegpro_lastUpdに取得
	$ret1 = 0 ;
	&dateTime(time) =~ /^(\d{4}-\d{2}-\d{2}).+/ ;
	my $today = $1 ;
	foreach ( @$ary_ref ){
		($typeID, $kanri, $regDate ) = @$_ ;
		if ( !defined( $egpro_lastUpd{ $typeID } ) ){			# 初出品目の管理コード
			$regDate =~ s/\.\d{3}$// ;							# .sssを削除
			if ( !$egproweb_lastUpd{ $typeID } ) {						# egproweb_lastUpdに無い
				$egpro_lastUpd{ $typeID } = [ $kanri , $regDate ] ;
			}elsif ( $regDate gt $egproweb_lastUpd{ $typeID } ){		# egpro_lastUpdが新しい
				$egpro_lastUpd{ $typeID } = [ $kanri , $regDate ] ;	
			}else{
				if ( $regDate =~ /$today/ ){							# egpro_lastUpdが今日
					$egpro_lastUpd{ $typeID } = [ $kanri , $regDate ] ;
				}
			}
		}
		$ret1 = $ret1 + 1 ;
	}
	$dbg_msg .= "(427)scan'd newest ".int((gethrtime() - $t0)/1000000)."msec #:".$ret1."=> <br>\n" ;
	# 取得したegpro_lastUpdの管理コードからegproBOMを取得 → $egpro_BOM{$typeID}に戻す
	foreach $typeID (keys %egpro_lastUpd){
		&get_egproBOM($typeID, $egpro_lastUpd{ $typeID } -> [0], $egpro_lastUpd{ $typeID } -> [1]) ;
	}
	foreach (@$ary_ref2){
		@$_[0] = int (@$_[0]) ;
		@$_[1] =~ s/^(U.+)_P\d{1,2}$/$1/ ;		# 生産品番の面情報を削除。
		$ongoing{@$_[0]} = @$_[1] ;				# $ongoing{指図} = 品目コード
		$ret1 = $ret1 + 1 ;
	}
	$dbg_msg .= "(438)got all BOMs ".int((gethrtime() - $t0)/1000000)."msec => " ;

	# egproBOM DBを更新する。
	eval{
		# EGProwebサーバ(172.25.253.60)のegproBOMから、各品目毎の更新日時を取得する。
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die(DBI::errstr) ;
		foreach $typeID (keys %egpro_lastUpd){
			$lastUpd = $egpro_lastUpd{ $typeID } -> [1] ;
			# egproBOMを削除
			$sql = "DELETE FROM ".$db_egproBOM." WHERE `typeID` LIKE '".$typeID."' ;" ;
			$st = $db->prepare($sql) or die(DBI::errstr) ;
			$st->execute() or die(DBI::errstr) ;
			# 新egproBOMを追加
			$sql = "INSERT INTO ".$db_egproBOM." (typeID,partNo_egpro,qty,plant,regDate) VALUES " ;
			foreach ( @{$egpro_BOM{$typeID}} ){
				$sql .= "('".$typeID."','".@$_[0]."','".@$_[1]."','0','".$lastUpd."')," ;
			}
			$sql =~ s/,$/ ;/ ;
			$st = $db->prepare($sql) or die(DBI::errstr) ;
			$st->execute() or die(DBI::errstr) ;
			$st = $db->commit ;
			$ret1 = $ret1 + 1 ;
		}
		$dbg_msg .= "(461)'".$db_egproBOM."' DEL-INSERT res. ".int((gethrtime() - $t0)/1000000)."msec => \n" ;
		# 更新済egproBOM DBを%egpro_BOMに取得
		$sql = "SELECT typeID,partNo_egpro,qty,plant,regDate FROM `".$db_egproBOM."` WHERE 1 ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish() ;
		$db->disconnect ;
		$dbg_msg .= "(469)'".$db_egproBOM."' SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => \n" ;
	};
	if ($@){
		if (defined($db)){$db->disconnect() ;}
		$ret1 = "mysql2:sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	%egpro_BOM = () ;
	foreach (@$ary_ref){				# $egpro_BOM{(品目)}で配列を生成
		push (@{ $egpro_BOM{@$_[0]} } , ([ @$_[1], @$_[2], @$_[4]]) );
	}
	$dbg_msg .= "(480)exit read_egDB #:".$ret1." t:".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
}

# ---- EGProのBOMを読む ----
# EGProの［T_部品配列表］から、指定の管理コードの品番1,員数を取得する。
# 引数：品目コード[0]、管理コード[1]、登録日時[2]
# 戻り値：正常時: "0"、$egpro_BOM{(品目コード)} = [(部品コード),(個数)]…
#		エラー時: "err"、$ret1: エラー詳細
sub get_egproBOM(){
	my ( $typeID, $kanri, $regDate ) = ( $_[0], $_[1], $_[2] ) ;
	my ( $db2, $st2, $sql2, $ary_ref2 ) ;
	$kanri =~ s/^(\d{8,14})\-.+$/$1/ ;
#	$dbg_msg .= "(492)strt get_egproBOM ".int((gethrtime() - $t0)/1000000)."msec  品目=".$typeID."/管理C=".$kanri."/日時=".$regDate." => \n" ;
	# EGprosrvに接続
	$sql2 = "SELECT 品番1,員数 FROM ".$db_ODBCview." " ;
	$sql2 .= "WHERE 管理コード LIKE '".$kanri."%' ORDER BY 品番1 ASC ;" ;
	eval{
		$db2 = DBI->connect($db_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db2->{LongTruncOk}=1 ;
		$db2->{LongReadLen}=200000 ;
		$st2 = $db2->prepare($sql2) or die(DBI::errstr) ;
		$st2->execute() or die(DBI::errstr) ;
		$ary_ref2 = $st2->fetchall_arrayref ;
		$db2->disconnect ;
	};
	if ($@){
		if (defined($db2)){$db2->disconnect() ;}
		$ret1 = "sql : ".$sql2."\n ==> ".$@ ;
		return "err" ;
	}
#	$dbg_msg .= "(510)'".$db_ODBCview."' SELECT res. ".int((gethrtime() - $t0)/1000000)."msec  (".scalar(@$ary_ref2)."件)\n" ;
	my ($partNo, $qty, $per_sheet ) ;
	if ( !$mentori{$typeID}){ $per_sheet = 1 ; }else{ $per_sheet = $mentori{$typeID} ; }
	foreach (@$ary_ref2){
		# [0]:品番1、[1]:員数
		if ( !$partNo ){	# 部品コードがundefは初回のみ
			# 前回値の初期値を設定
			$partNo = @$_[0] ;	# 品番1(部品コード)
			$qty = 0 ;			# 員数
		}
		# 部品コードが前回と同じか？
		if ( $partNo eq @$_[0] ){
			# 同じ品番:累計して次
			$qty = $qty + @$_[1] ;
		}else{
			# 違う品番:累計終了、面取り数換算、配列に追加
			if ( $regDate gt '2021-02-21 00:00:00' ){ 
				$qty = $qty / $per_sheet ;
			}
			# @egpro = [(部品コード),(個数)][…]…　で追加
			push (@{ $egpro_BOM{$typeID} } , ( [ $partNo, $qty ] ) ) ;
			$partNo = @$_[0] ;
			$qty = @$_[1] ;
		}
		$ret1 = $ret1 + 1 ;			# 処理レコード数(部品数)
	}
	# 最終レコードを追加
	if ( $regDate gt '2021-02-21 00:00:00' ){ 
		$qty = $qty / $per_sheet ;
	}
	push (@{ $egpro_BOM{$typeID} } , ( [ $partNo, $qty ] ) ) ;
#	$dbg_msg .= "(541)exit get_egproBOM ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
}

# ---- liveOrderDBからのデータ取得 ----
# SMT未着手指図をDBから指図順に取得する。
# 引数：なし
# 戻り値：正常時は取得内容のリファレンス
#		[(品目)[0],(指図)[1],(発令台数)[2],
#		 (指図登録日)[3],(製造開始日)[4],(完成予定日)[5],
# 		 (指図タイプ)[6],(担当ライン)[7]]
#		エラー時は"err"、詳細は$ret1
sub get_liveOrder(){
	$dbg_msg .= "(553)strt get_liveOrder ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = "" ;
	my ($db, $st, $sql, $ary_ref) ;
	my $colList = "`typeID`,`orderNumber`,`orderQty`," ;
	$colList .= "`reg_date`,`start_date`,`finish_date`," ;
	$colList .= "`sashizu_type`,`LINE` " ;
	$sql = "SELECT ".$colList."FROM ".$db_liveOrder_sub." " ;
	$sql .= "WHERE 1 " ;
	$sql .= "ORDER BY `orderNumber` ASC ;" ;
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
if ( @$_[0] eq "UR-1234" ){ $dbg_msg .= "(577)UR-1234/".@$_[1]."/".@$_[2]."<br>\n" ; }
	$dbg_msg .= "(578)exit get_liveOrder ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ary_ref ;		# ref渡し
}

# ---- 未着手指図の差分出力 ----
# liveOrder_subの指図に従い、boss_BOMとegpro_BOMの差分を配列に出力する。
# 引数：liveOrder_subの内容(指図順)
#		[(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],(完成予定日)[5],
#		(指図タイプ)[6],(担当ライン)[7]]
#		%boss_BOM{(品目コード)}、%egpro_BOM{(品目コード)}
# 戻り値：正常時: "0"
# 		エラー時: "err"、$ret1: エラー詳細
sub calc_sabun(){
	$dbg_msg .= "(591)strt calc_sabun ".int((gethrtime() - $t0)/1000000)."msec => " ;
	# $egpro_BOM{(品目)}の中を部品コード順に並べ替え($boss_BOMと同一OS環境でソート)
	foreach (keys %egpro_BOM){
			@{$egpro_BOM{$_}} = sort ( {@$a[0] cmp @$b[0]} @{$egpro_BOM{$_}} ) ;
	}
	my @liveOrder = @{$_[0]} ;		# de-refして2次元配列
	$ret1 = 0 ;
	# $boss_BOM{(品目コード)} = [(指図)[0],(部品コード)[1],(基数)[2]],…
	#  → $sashizu_BOM{(指図)} = [(部品コード)[0],(個数)[1]],…
	my %sashizu_BOM ;
	foreach my $typeID (keys %boss_BOM ){
		foreach ( @{ $boss_BOM{$typeID} } ){
# $dbg_msg .= "(603)".@$_[0]."/".@$_[1]."/".@$_[2]."<br>\n";
			push (@{ $sashizu_BOM{@$_[0]} } , ([ @$_[1], @$_[2] ]) );
		}
	}
	# 指図毎に処理
	while ($liveOrder[$ret1]){
		my $typeID = $liveOrder[$ret1][0] ;		# 品目コードの取得
		my $sas_key = $liveOrder[$ret1][1] ;	# 指図の取得
		if (!$sashizu_BOM{$sas_key}){			# 発令部品無しは差分N.A.
			$ret1 = $ret1 + 1 ;
			next ; 
		}
		if ($ongoing{$sas_key}){				# 本日着手済み指図は次
			$ret1 = $ret1 + 1 ;
			next ;
		}
		# 当該指図で部品Cを昇順に並べ替え($egpro_BOMはソート済み)
		@{ $sashizu_BOM{$sas_key} } = sort ({@$a[0] cmp @$b[0]} @{ $sashizu_BOM{$sas_key} }) ;
		# 部品コード順にポインタを移動して比較、結果を $bomDiff に保存
		my ($boss_Indx, $egpro_Indx) = (0, 0) ;
		my @partNo = @{ $sashizu_BOM{$sas_key} } ;
		my $diff = "0" ;						# 差分ありフラグ(0/差数/bos/egp/URS/upd)
		my $regDate ;
		if (defined $egpro_BOM{$typeID}[$egpro_Indx][2]){		# EGpro登録日あれば取得
			$regDate = $egpro_BOM{$typeID}[$egpro_Indx][2] ;
		}
		my $itemDiff = "" ;						# 1品目毎の差分結果(csv形式)
		my $comp ;								# itemDiffの１行(1部品毎)
		if ( $typeID eq "UR-1234" ){ $dbg_msg .= "(631)UR-1234/".$typeID."/".$sas_key."=> " ; }
		while (){
			my $boss = $partNo[$boss_Indx][0] ;
			my $egpr = $egpro_BOM{$typeID}[$egpro_Indx][0] ;
			$comp = "" ;
			my $order = "211517136" ;
			# boss_BOM,egpro_BOMの部品毎にEOFまでチェックし、@liveOrder,@bomDiffを生成
			# $bomDiff = ((指図),(部品コード),(boss基数),(egpro基数),(egpro登録日時))\n
			if (!$boss && !$egpr){
# 0.		boss/egpro両方がundef(EOF)になったら比較終了
				last ;
			}elsif (!$boss){
# 1.		bossの部品Cがない		==> boss部品が基数NULL、egpro部品が実数、登録日あり
				#if ( $sas_key eq $order){ $dbg_msg .= "(644)".$boss."！＞".$egpr."<br>\n" ;} 
				$comp = $sas_key.",".$egpr."," ;
				$comp .= "NULL,".$egpro_BOM{$typeID}[$egpro_Indx][1]."," ;
				$comp .= $egpro_BOM{$typeID}[$egpro_Indx][2]."\n" ;
				$diff = "bos" ;					# 差分ありフラグ(=bos)
				$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
			}elsif ($boss =~ /U.S/){
				# boss部品でURS/UTS/UESが存在 ==> 差分に"URS"を入れて即判定を抜ける
				$diff = "URS" ;					# 差分ありフラグ(URS)
				last ;
			}elsif (!$egpr){
# 2.		egproの部品Cがない		==> boss部品が実数、egpro部品が基数NULL、登録日NULL
				#if ( $sas_key eq $order ){ $dbg_msg .= "(656)".$boss."＞！".$egpr."<br>\n" ;} 
				$comp = $sas_key.",".$boss."," ;
				$comp .= $partNo[$boss_Indx][1].",NULL," ;
				$comp .= "NULL\n" ;
				$diff = "egp" ;					# 差分ありフラグ(=egp)
				$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
			}elsif ($boss gt $egpr) {
# 3.		bossの部品C ＞ egproの部品C	==> boss部品が基数NULL、egpro部品が実数、登録日あり
				#if ( $sas_key eq $order ){ $dbg_msg .= "(664)".$boss."＞＞".$egpr."<br>\n" ;} 
				$comp = $sas_key.",".$egpr."," ;
				$comp .= "NULL,".$egpro_BOM{$typeID}[$egpro_Indx][1]."," ;
				$comp .= $egpro_BOM{$typeID}[$egpro_Indx][2]."\n" ;
				$diff = "egp" ;					# 差分ありフラグ(=egp)
				$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
			}elsif ($boss lt $egpr) {
# 4. 		bossの部品C ＜ egproの部品C	==> boss部品が実数、egpro部品が基数NULL、登録日NULL
				#if ( $sas_key eq $order ){ $dbg_msg .= "(672)".$boss."＜＜".$egpr."<br>\n" ;} 
				$comp = $sas_key.",".$boss."," ;
				$comp .= $partNo[$boss_Indx][1].",NULL," ;
				$comp .= "NULL\n" ;
				$diff = "bos" ;					# 差分ありフラグ(=bos)
				$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
			}elsif ($boss eq $egpr) {
# 5.		bossの部品C ＝ egproの部品C	==> 両方が実数、差分を計算 
				#if ( $sas_key eq $order ){ $dbg_msg .= "(680)".$boss."＝＝".$egpr."<br>\n" ;} 
				$comp = $sas_key.",".$boss."," ;
				$comp .= $partNo[$boss_Indx][1].",".$egpro_BOM{$typeID}[$egpro_Indx][1]."," ;
				$comp .= $egpro_BOM{$typeID}[$egpro_Indx][2]."\n" ;
				if ($partNo[$boss_Indx][1] != $egpro_BOM{$typeID}[$egpro_Indx][1]){		# 実数に差分あり？
					$diff = "egp" ;				# 差分ありフラグ(=egp)
				}
				$boss_Indx = $boss_Indx + 1 ;
				$egpro_Indx = $egpro_Indx + 1 ;
			}
#if ( $sas_key eq $order){ $dbg_msg .= "(690)".$comp." ＝＝＞ ".$diff."<br>\n" ;}
#if ( $sas_key eq $order){ $dbg_msg .= "(691)".$order.":".$regDate."<br>\n" ;}
			$itemDiff .= $comp ;
		}
		# bossの部品で半成品あり(フラグ："URS"(=URS/UTS/UES)) ==> 何も追加しない、当該のliveOrder行を削除。
		if ($diff eq "URS"){
			splice ( @liveOrder, $ret1, 1 ) ;	# spliceするのでポインタは変えない
		}else{
			$bomDiff .= $itemDiff ;			# 結果を追加して抜ける。
			# EGPro差分：有/無/更新済/未登録の判定("無"で"登録日＝今日"なら変更済:"bos")
			if (defined $regDate){
				$regDate =~ s/^(\d{4}-\d{2}-\d{2}).+/$1/ ;
				&dateTime(time) =~ /^(.+)\s/ ;
				if (($diff eq "0") && ($regDate eq $1)){ $diff = "upd" ;}
			}else{
				$diff = "noegp" ;			# EGproDB未登録
			}
			# 配列の当該要素の末尾要素として追加
			push ( @{$liveOrder[$ret1]} , $diff ) ;
			$ret1 = $ret1 + 1 ;
		}
	}
	$dbg_msg .= "(712)exit calc_sabun ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return \@liveOrder ;		# ref化して渡し
}

# ---- 差分詳細ファイルの出力 ----
# 差分チェックで生成されたcsv形式のファイルを出力する。
# 引数：差分チェック結果のcsv形式データ
#		(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],
# 			(完成予定日)[5],(指図タイプ)[6],(担当ライン)[7],(差分フラグ)[8]\r\n
# 戻り値：正常時は "0"、カレントディレクトリへcsvファイルとしてbomDiff.tmp
#		エラー時は"err"、詳細は$ret1
sub upd_bomDiff(){
	$dbg_msg .= "(724)strt upd_bomDiff ".int((gethrtime() - $t0)/1000000)."msec => " ;
	my ($db, $st, $sql) ;
	$ret1 = 0 ;
	# csvファイル生成
	if (open (FH, ">", "./bomDiff.tmp")){
		print FH $_[0] ;
		close FH ;
	}else{
		$ret1 = "Tmp File Error:".$! ;
		close FH;
		return "err" ;
	}
	close FH ;
	chmod 0666, "./bomDiff.tmp" ;
	$dbg_msg .= "(738)exit upd_bomDiff ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ret1 ;
}

# ---- html文の生成 ----
# 差分チェックされたデータから、差分表のhtmlを生成する。
# 引数：差分チェック結果のリファレンス
#		[(品目)[0],(指図)[1],(発令台数)[2],(指図登録日)[3],(製造開始日)[4],
# 			(完成予定日)[5],(指図タイプ)[6],(担当ライン)[7],(差分フラグ)[8]]
# 戻り値：正常時はhtmlテキスト
#		エラー時は"err"、詳細は$ret1
sub make_html(){
	$dbg_msg .= "(750)strt make_html ".int((gethrtime() - $t0)/1000000)."msec => " ;
	my @eachRec = @{$_[0]} ;		# de-refして2次元配列
	my $cont = "" ;
	my $row = 0 ;
	foreach (@eachRec){
		# 要素の生成
		my @col = @$_ ;
		my $sts ;
		$col[2] = $col[2] + 0 ;				# 発令台数
		$col[3] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 指図登録日(yyyy-mm-dd)
		$col[4] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 製造開始日
		$col[5] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 完成予定日
		if (!defined $col[8]){							# boss_BOMなし
			$col[8] = "na" ;
			$sts = "N.A." ;
		}else{
			if ($col[8] eq "egp" || $col[8] eq "bos" ){	# 差分不一致：赤
				$sts = "<img src=\"./cgiData/red.png\">" ;
			}elsif ($col[8] eq "upd"){					# 登録今日：青
				$sts = "<img src=\"./cgiData/blu.png\">" ;
			}elsif ($col[8] eq "0"){					# 差分一致：緑
				$sts = "<img src=\"./cgiData/grn.png\">" ;
			}elsif ($col[8] eq "noegp"){					# EGpro未登録：白
				$sts = "<img src=\"./cgiData/wht.png\">" ;
			}else{
				$sts = "---" ;
			}
		}
		# 毎行の生成
		if ($row % 2){								# 行毎の色変え
			$cont .= "\t\t<tr class=\"even\">\n" ;
		}else{
			$cont .= "\t\t<tr class=\"odd\">\n" ;
		}
		$cont .= "\t\t\t<td onclick=\"openWindow(\'".$indv_scrn."?sashizu=".$col[1]."&sts=".$col[8]."\'); return false;\">" ;
		$cont .= "<b><font color=\"4040ff\"><a class=\"hov\">".$col[1]."</a></font></b></td>\n" ;
		$cont .= "\t\t\t<td>".$col[7]."</td><td>".$col[0]."</td><td>".$col[2]."</td>" ;
		$cont .= "<td>".$col[3]."</td><td>".$col[4]."</td><td>".$col[5]."</td>\n" ;
		$sts = "<span onclick=\"openWindow(\'".$indv_scrn."?sashizu=".$col[1]."&sts=".$col[8]."\'); return false;\">".$sts."</span>" ;
		$cont .= "\t\t\t<td>".$col[6]."</td><td>".$sts."</td>\n" ;
		$cont .= "\t\t</tr>\n" ;
		$row = $row + 1 ;
	}
	$dbg_msg .= "(793)exit make_html ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $cont ;						# htmlを戻す
}

# ---- エラー表示処理 ----
# エラーメッセージを表示
# 引数:エラーテキスト
# 戻り値:なし
sub error(){
	print "</head>\n<body>\n".$_[0]."<br>\n";
}

# ---- 画面の生成 ----
# 差分を表示する。
# 引数：なし
# 戻り値：なし
sub drw_scrn(){
	$dbg_msg .= "(810)strt drw_scrn() ".int((gethrtime() - $t0)/1000000)."msec => <br>" ;
	my $html = <<"HTML" ;
 	<script type="text/javascript">
		// tablesorterの並べ替え
		\$(document).ready(function() { 
			\$("#tablstr").tablesorter({
				headers: {
					3:	 { sorter: false },
					7:	 { sorter: false },
					8:	 { sorter: false }
				}
			});
		}); 
		// サブウィンドウのサイズ他パラメータ設定
		function openWindow(url) {
			window.open(url,"subw","width=650, height=650, scrollbars=1");
		}
		function resExem(url) {
			window.open(url,"subw","width=650, height=250, scrollbars=0");
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
<body style="font-family: sans-serif; margin: 30px;" onLoad="FixedMidashi.create();">
HTML
	if ( $dbg > 0 ){
		$html .= $dbg_msg."\n" ; 
		$dbg_msg = "" ;
	}
	$html .= "<span style=\"font-size: 3ex; font-weight: bold;\">【差分チェックシステム】</span> <span>WWW-0084 ver. ".$ver."</span>\n" ;
	$html .= "<hr width=\"960\" size=\"5\" color=\"e0e0f0\" align=\"left\">\n" ;
	$html .= "<form name=\"form\" method=\"post\" action=\"".$self_scrn."\">\n" ;
	$html .= "\t<div style=\"padding-left: 10px;\">\n" ;
	$html .= "\t\tBOSS出力：".$bossUpd."（深夜2:30の処理で、指図、BOMがシステムに自動更新されます。)　" ;
	$html .= "<input type=\"submit\" value=\"手動更新\" name=\"updBOM\" style=\"background-color:#d0ffff;\"/><br>\n" ;
	$html .= "\t\t差分チェックは ".dateTime(time)." に実行されました。(最新EGpro登録：".$newestDate.")<br>\n" ;
	$html .= "\t</div>\n" ;
	$html .= <<"HTML";
	<div style="float: left; padding-left: 10px;">
		「指図」,「差分」をクリックで指図毎詳細ウィンドウが開きます。<br>
		スライダーが最上位で <img src=./jquery/themes/blue/bg.gif> 項目欄をクリックで並べ替えます。
	</div>
	<div style="float: left; padding-left: 10px;">
		差分一致：<img src="./cgiData/grn.png"><input type="checkbox" onClick="selSabun('grn');" id="chkGrn" checked="checked">
		　　不一致：<img src="./cgiData/red.png"><input type="checkbox" onClick="selSabun('red');" id="chkRed" checked="checked">
		　修正済：<img src="./cgiData/blu.png"><input type="checkbox" onClick="selSabun('blu');" id="chkBlu" checked="checked"><br>
		　未登録：<img src="./cgiData/wht.png"><input type="checkbox" onClick="selSabun('wht');" id="chkWht" checked="checked">
		　実装なし：N.A.<input type="checkbox" onClick="selSabun('na');" id="chkNA" checked="checked">
	</div>
</form>
HTML
	$html .= "<form name=\"form1\" method=\"post\" action=\"".$self_scrn."\">" ;
	$html .= <<"HTML";
	<div class="scroll_div" style="clear: both;">
	<table border="0" style="margin-left: 0px; padding: 5px; background-color: #ffffff;" class="fixedHead tablesorter" _fixedhead="rows:1; cols:0;" id="tablstr">
		<thead>
		<tr>
			<th style="width: 100px;">指図</th>
			<th style="width: 50px;">担当</th>
			<th style="width: 130px;">品目コード</th>
			<th style="width: 70px;">台数</th>
			<th style="width: 120px;">指図登録日</th>
			<th style="width: 120px;">製造開始日</th>
			<th style="width: 120px;">完成予定日</th>
			<th style="width: 80px;">タイプ</th>
			<th style="width: 50px;">差分</th>
		</tr>
		</thead>
		<tbody>
HTML
	# テーブル本体部分を挿入
	$html .= $_[0] ;
	$html .= <<"HTML";
		<tr>
			<td><input type="button" value="csv出力" onClick="dlFile('index')" id="dnload" style="background-color:#d0ffff;"/></td>
			<td colspan="8"></td>
		</tr>
		</tbody>
	</table>
	</div>
HTML
	$html .= "\t<br><input type=\"button\" value=\"除外部品復活\" onClick=\"resExem('".$indv_scrn2."')\" id=\"rExem\" style=\"background-color:#d0ffff;\"/>\n" ;
	$html .= "</form>\n" ;
	print $html ;
	$dbg_msg .= "(937)exit drw_scrn ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
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
# htmlの終端処理
if ( $dbg > 0 ){ print $dbg_msg."\n" ; }
print "</body>\n</html>\n" ;
# ログテキストをファイル出力。
open (FH, ">>", $logFile) ;
	print FH $recLog."\r\n" ;
close FH ;
chmod 0666, $logFile ;
