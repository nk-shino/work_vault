#!/usr/bin/perl -w

#**********************************************************
# このプログラムは、index.cgiで除外部品復活ボタンが押下される
# と起動され、入力部品コードが除外品リストから削除される。
#									2021/01/11 J.Igarashi
# Ver. 2.00:初回リリース(新規画面として追加)
# Ver. 2.10:copy_BOSS.cgi,index.cgiを変更
# Ver. 2.11:除外復活の品目コード判定を厳密化(tbl全消え対策)
#**********************************************************
my $ver = "2.11" ;
use strict;
use warnings;
use utf8;
use DBI;
use Time::Local;			# 日付、時刻の処理
use CGI;					# POSTリクエストを生成
use Encode;
use Encode 'decode';
use Data::Dumper;			# Data構造表示用モジュールの読み込み(DBG用)
use Time::HR;				# インターバル高精度タイマ
binmode STDOUT, ':utf8';	#Apache error log対策
binmode STDOUT, ':utf8';
binmode STDERR, ':utf8';

# 一般変数
my $ret1 = '';				# エラーメッセージ戻り値
my %in ;					# 入力・前画面からの引数
my $self_scrn = "./exemp.cgi" ;		# 自画面
my $parent_scrn = "./sashizu.cgi" ;
my ($sashizu, $typeID, $qty, $regDate, $line ) ;
my ($sttDate, $finDate) ;

# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60';
my $db_user = 'process_mgt';
my $db_passwd = '7bcsHFk8P7VxRcFD';
my $db_exempt = 'exepPart' ;
my $logFile = './logs/exemp.log';		# ログファイルの名前
my $data_root = "./cgiData" ;

#********************************************
#          Main処理 ここから
#********************************************
#****************for DEBUG*******************
my $dbg = 0;	#0:ope 1:dbg...show arguments
if ($dbg == 1){
	print "Content-type:text/html\n\n<!DOCTYPE html>\n<HTML>\n<BODY>\n<meta charset=\"utf-8\" />\n";
	$self_scrn = "./exemp.cgi" ;
	$parent_scrn = "./sashizu.cgi" ;
}
#********************************************
# **** ログ開始 ****
if (&recLog("\r\n".&dateTime(time)." *** exempt.cgi Ver.".$ver." START *** " ) eq "err"){
	$ret1 = "<font color=\"ff0000\">ローカルファイル(log)が開けません。<br>処理を終了します。:".$ret1."</font><br>\n";
	&error($ret1);
	goto exit_prog;
}
# **** 設定ファイルを読む ****
if (!open(IN, "<", "./bom_diff.ini")){
	$ret1 = "'bom_diff.ini' is not be able to open ".$!." " ;
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
		}
	}
	$ret1 = "=> system reads 'bom_diff.ini' " ;
	&recLog($ret1) ;
}
close IN ;
# cgiから%in{}にパラメータを取得
$CGI::POST_MAX = 2048 * 1024;		# postは最大2Mbytesまで
my $cgi = new CGI;
%in = $cgi->Vars;					# $in{''}はすべて初期化される
&eval_arg();						# cgiからの入力引数の評価

# 抽出引数の一覧(dbg用)
if ($dbg == 1){
	foreach (keys(%in)){
		print "(87)key(".$_.")=".decode('utf8',$in{$_})."<br>\n";
	}
}
# $in{'mode'} の内容により処理分岐
if (!$in{'mode'}){
	$in{'mode'} = 'init' ;
}
if ($in{'mode'} eq "exempt"){
	# **** 除外品目から復活 ****
	# exemp DBから削除
	if (&remv_exempt($in{'partNo'}) eq "err"){ 
		&recLog( "=> failed exemp DB manipulate ".$ret1 ) ;
		$ret1 = "除外DBからの削除に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	if ($ret1 > 0){
		# 親ウィンドウをリロード
		print "Content-type:text/html\n\n<html><body>\n";
		print "<script type=\"text/javascript\">\n";
		print "window.onload = function(){\n";
		print "    window.opener.location.reload();\n";
		print "    open('about:blank', '_self').close();\n";	# 自ウィンドウを閉じる
		print "}\n";
		print "</script>\n</body></html>\n";
		&recLog( "=> success update exemp partNo ".$in{'partNo'} ) ;
	}else{
		&recLog("=> partNo (".$in{'partNo'}.") is not exist." ) ;
		$ret1 = "該当する品目コード ".$in{'partNo'}." がありません。<br>" ;
		$ret1 .= "確認してください。<br>" ;
		&error($ret1) ;
		goto exit_prog ;
	}
}

# 画面描画
&drw_scrn() ;

goto exit_prog ;

#********************************************
#                 Sub処理
#********************************************


# ---- 除外リスト登録 ----
# 指定された部品コードを除外リストDBから削除する。
# 引数：部品コード
# 戻り値：正常時:処理件数(=1)、または該当なし(=0)
#		エラー時:"err"、$ret1:エラー詳細
sub remv_exempt(){
	$ret1 = "" ;	
	my ($db, $st, $rv, $sql) ;
	$_[0] =~ s/-// ;
	# 部品コード:数字6または10ケタ+英字0-1ケタまたは、試作ダミーコード
	if ( $_[0] =~ /(^(\d{6}|\d{10})[A-Za-z]?$)|(^[A-Za-z]\d{6}$)/ ) {
		eval{
			$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
			$sql = "DELETE FROM `".$db_exempt."` WHERE `partNo` LIKE ? ;" ;
			$st = $db->prepare($sql) or die(DBI::errstr) ;
			$rv = $st->execute($_[0]) or die(DBI::errstr) ;
			if ($rv eq "0E0"){
				$ret1 = 0 ;
			}else{
				$ret1 = $rv ;
			}
			$db->disconnect ;
		};
		#DBでエラーがある場合の処理
		if ($@){
			$st = $db->rollback ;
			if(defined($db)){$db->disconnect() ; }
			$ret1 .= "exempt DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
			return "err" ;
		}
		return $ret1 ;
	}else{
		return 0 ;
	}
}

# ---- Logの出力 ----
# 引数で渡されるメッセージのlogファイル出力。
# バッファリングを解除、書込み禁止して排他処理して更新。
# 引数：メッセージテキスト
# 戻り値：エラーなしはNULL、ありはメッセージを返す。
sub recLog(){
	if (open (FH, ">>", $logFile)){
		print FH @_;
		close FH;
	}else{
		$ret1 = "Log File Error:".$!;
		close FH;
		return "err";
	}
	close FH;
	return 0;
}

# ---- 入力引数の評価 ----
# %in{''}で渡された入力引数を評価。
# 引数：なし(グローバル変数で%in
# 戻り値：なし(グローバル変数で%in)
sub eval_arg(){
	# モードの設定(部品コードの取得とモード設定)
	foreach (keys %in){
		if ($_ eq "exempt"){		# keyが"exempt"なら除外部品登録
			$in{'mode'} = "exempt" ;
		}
	}
}

# ---- エラー表示処理 ----
# エラーメッセージを表示
# 引数:エラーテキスト
# 戻り値:なし
sub error(){
		print "Content-type:text/html\n\n";
		print "<html>\n<body><meta charset=\"utf-8\" />\n";
		print "\t<br>".$_[0]."<br>\n";
		print "</body>\n</html>\n";
}

# ---- 画面の生成 ----
# 差分を表示する。
# 引数：なし
# 戻り値：なし
sub drw_scrn(){
	my $html = <<"HTML";
Content-type:text/html

<!DOCTYPE html>
<html lang="jp">
<head>
	<title>SMT実装部品 差分表示プログラム</title>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<link rel="shortcut icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
</head>
<body style="font-family: sans-serif; margin: 30px;">
<h2>【差分チェックシステム】（除外品復活画面）</h2>
<hr width="560" size="5" color="d0d0ff" align="left">
HTML
	$html .= "<form name=\"form\" method=\"get\" action=\"".$self_scrn."\">\n" ;
	$html .= "\t部品コード：<input type=\"text\" name=\"partNo\" size=\"10\"/>\n" ;
	$html .= "\t<input type=\"submit\" name=\"exempt\" value=\"除外復活\" style=\"background-color:#d0ffff;\"/>\n" ;
	$html .= "</form>\n" ;
	$html .= "</body>\n" ;
	$html .= "</html>\n" ;
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