#!/usr/bin/perl -w

# 本プログラムは、crontabによって10分毎に起動され、
# 現在時刻より70分前までの実装履歴データを収集する。
# 収集したデータは、nksv560のorderNumber:SMT_result
# データベースに書き込まれる。
# 							2021/02/03 J. Igarashi

my $ver = "1.11" ;
use strict ;
use warnings ;
use utf8 ;
use DBI ;
use Encode ;
use Data::Dumper ;
use Time::HR ;
binmode STDIN, ':utf8' ;
binmode STDOUT, ':utf8' ;
binmode STDERR, ':utf8' ;

# ODBC関連接続情報
my $db_ODBCserver = "dbi:ODBC:EGPro" ;	# DB:EGProKOHDEN-Planに対するDSN
my $db_ODBCuser = "sqluser" ;
my $db_ODBCpasswd = "Pfseg001" ;
my $db_ODBCview  = "T_計画データLog" ;
# mySQLサーバ・ユーザ・パスワード・接続変数
my $db_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db_SMT_result = 'SMT_result' ;
my $db_user = 'process_mgt' ;
my $db_passwd = '7bcsHFk8P7VxRcFD' ;

# 高精度タイマ用変数
my $t0 = gethrtime() ;		# 高精度現在時を取得
# 汎用変数
my $ret1 = "" ;
my $logFile = "./logs/SMT_result.log" ;	# ログファイルの名前とパス
my $data_root = "./cgiData" ;

#***********************************
#		MAIN処理(ここから)
#***********************************
&recLog( &dateTime(time)." SMT_result Ver.".$ver." *** START *** " ) ;
# **** 実装履歴データの取得 ****
# EGProDBから、現在時刻より70分前までのSMT実装計画と
# 最新実績を収集し、戻り値に得る。
my $src_ref = &get_EGPro() ;
if ($src_ref eq "err" ){
	&recLog ($ret1."\n") ;
	goto exit_prog ;
}

# **** 実装履歴データの書込み ****
# EGProDBから取得した履歴データを、データベース
# に書き込む。
if (&write_DB($src_ref) eq "err"){
	&recLog ($ret1."\n") ;
	goto exit_prog ;
}
$ret1 .= " => ".&dateTime(time)." *** normal end *** \n" ;
&recLog ($ret1) ;
goto exit_prog ;

#***********************************
#			SUB処理
#***********************************
# ---- Logの出力 ----
# 引数で渡されるメッセージのlogファイル出力。
# 引数：メッセージテキスト
# 戻り値：常に "0"
sub recLog(){
	open ( OUT, ">>", $logFile) ;
		print OUT ( $_[0] ) ;
	close OUT;
	return 0 ;
}

# EGProからのSMT実装予実データの収集
sub get_EGPro(){
	my ($db, $st, $sql, $ary_ref) ;
	my $timePeri = &dateTime(time - 86400) ;		# 現在時刻より1日前まで遡る
	$sql = "SELECT 管理コード,ライン名称,生産品番,計画開始日時,計画終了日時,実績数量,実績開始日時,実績終了日時,ログ登録日時 " ;
	$sql .= "FROM ".$db_ODBCview." WHERE 実績開始日時 > '".$timePeri."' ;";		# 
	eval{
		$db = DBI->connect($db_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db->{LongTruncOk}=1 ;
		$db->{LongReadLen}=200000 ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
	};
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	&writeFile($db_ODBCview.".csv", $ary_ref ) ;
	return $ary_ref ;
}

# ---- 取得データをnksv560::SMT_result DBに書込み ----
sub write_DB(){
	my ($db, $st, $sql, $ary_ref) ;
	$ret1 = 0 ;
	$sql = "INSERT INTO `".$db_SMT_result."`(`orderNumber`,`lineID`,`typeID_L`," ;
	$sql .= "`sttTime_plan`,`endTime_plan`,`mfgQty`,`sttTime_act`,`endTime_act`,`regDate`) " ;
	$sql .= "VALUES " ;
	my $sql_values = "" ;
	foreach my $line (@{$_[0]} ){
		# 管理コード
		@$line[0] =~ s/^(\d+)-.+$/$1/ ;
		@$line[0] = @$line[0] + 0 ;		# 整数化
		# "秒"以下を削除
		@$line[3] =~ s/^(.+)\.\d{3}$/$1/ ;
		@$line[4] =~ s/^(.+)\.\d{3}$/$1/ ;
		@$line[6] =~ s/^(.+)\.\d{3}$/$1/ ;
		@$line[7] =~ s/^(.+)\.\d{3}$/$1/ ;
		@$line[8] =~ s/^(.+)\.\d{3}$/$1/ ;
		$sql_values .= "('".@$line[0]."','".@$line[1]."','".@$line[2]."','".@$line[3]."','".@$line[4]."',".@$line[5].",'".@$line[6]."','".@$line[7]."','".@$line[8]."')," ;
		$ret1 = $ret1 + 1 ;
	}
	$sql_values =~ s/,$/ / ;
	if ($sql_values ne ""){
		$sql = $sql.$sql_values." ON DUPLICATE KEY UPDATE `lineID`=VALUES(lineID)," ;
		$sql .= "`sttTime_plan`=VALUES(sttTime_plan),`endTime_plan`=VALUES(endTime_plan),`mfgQty`=VALUES(mfgQty)," ;
		$sql .= "`sttTime_act`=VALUES(sttTime_act),`endTime_act`=VALUES(endTime_act),`regDate`=VALUES(regDate) ;" ;
		eval{
			$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
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
	}
	$ret1 .= " records." ;
	return 0 ;
}
	
# ---- 引数のリファレンスをtsvファイルとしてカレントディレクトリに書き出し ----
# 引数：ファイル名[0]、配列のリファレンス[1]
sub writeFile(){
	my $out_text = "" ;
	foreach my $line (@{$_[1]} ){	
		if (!defined $line){ next ;}
		foreach (@$line){
			if (!defined $_){
				$out_text .= "\t" ;
			}else{
				$out_text .= decode('utf8',$_)."\t" ;
			}
		}
		$out_text =~ s/\t$/\r\n/ ;
	}
	if (!open(OUT, ">", $_[0])){
		print $_[0]." cannot open: ".$! ;
		close OUT ;
		return "err" ;
	}else{
		print OUT $out_text ;
#		print $out_text ;
	}
	close OUT ;
}

# ---- 時刻生成処理 ----
# unix時刻を規定形式で戻す
# 引数:unix時刻
# 戻り値:YYYY-MM-DD HH:MM:SS 形式の日時
sub dateTime(){
	my @t = localtime($_[0]) ;
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
