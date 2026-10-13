#!/usr/bin/perl -w

#**********************************************************
# このプログラムは、crontabによって毎深夜2:05に起動され、
# BOSSから出力される指図BOMのtsvファイル(IFID139.csv),
# をローカルフォルダにコピーすると共に、 指図情報のtsvファイル
# (IFID142.csv)をDBに展開するものである。
# また、nksv560にある工程仕掛指図テーブルongoingProcにある
# 仕掛情報も反映するものである。
# これらファイルはEGProアプリが取得後削除するので、削除前に
# 取得する。
#									2021/01/06 J.Igarashi
#**********************************************************

use strict ;
use warnings ;
use utf8 ;
use DBI;
use Time::Local;			# 日付、時刻の処理
use Encode;					# 文字コード変換
use Data::Dumper;
use Time::HR;
binmode STDIN, ':utf8' ;
binmode STDOUT, ':utf8' ;
binmode STDERR, ':utf8';

# BOSSインタフェース関連変数
# ルート：権限755、オーナadministrator
my $boss_org = "/mnt/nksvasp23_SMT_RCV/" ;
my $boss_dst = "/mnt/nksvasp23_SMT_RCV2/" ;
# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60' ;
my $db2_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db_user = 'process_mgt' ;
my $db_passwd = '7bcsHFk8P7VxRcFD' ;
my $db_exepPart = 'exepPart' ;
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db_bossBOM = 'bossBOM' ;
my $db_bomDiff = 'bomDiff' ;
my $db2_ongoing = 'ongoingProc' ;
my $db2_unitInfo = 'unitInfo' ;
my $db2_egproBOM = 'egproBOM' ;
# ODBC関連接続情報
my $db_ODBCserver = "dbi:ODBC:EGPro" ;			# DB:EGProKOHDEN-Planに対するDSN
my $db_ODBCserver2 = "dbi:ODBC:EGPro_MST" ;		# DB:EGProKOHDEN-MSTに対するDSN
my $db_ODBCuser = "sqluser" ;
my $db_ODBCpasswd = "Pfseg001" ;
my $db_ODBCview = "T_部品配列表" ;
my $db_ODBCview2 = "M_製品構成" ;

# 高精度タイマ用変数
my $t0 = gethrtime() ;		# 高精度現在時を取得
# 汎用変数
my $ret1 = "" ;
my $logFile = "./logs/copy_BOSS.log" ;	# ログファイルの名前とパス
my $data_root = "./cgiData" ;
my $boss_src ;				# tsv形式のbossファイル
my %ongoing ;				# 未着手仕掛指図
my %boss_BOM ;				# 指図BOM
my %egpro_BOM ;				# egproBOM
my %mentori ;				# 面取り数テーブル
my %exep ;					# 除外部品テーブル
my $mail_msg = "" ;

#***********************************
#		MAIN処理(ここから)
#***********************************
# **** ログ開始 ****
&recLog( &dateTime(time)." *** START *** " ) ;
# **** 設定ファイルを読む ****
if (!open(IN, "<", "./bom_diff.ini")){
	$ret1 = "'bom_diff.ini' is not be able to open ".$!."\n" ;
	$ret1 .= "System set the initial value. " ;
	&recLog($ret1) ;
}else{
	while (<IN>){
		my $val = $_ ;
		$val =~ s/\r\n|\r|\n//g ;
		if ($val =~ /#/){
			next ;
		}elsif ($val =~ /boss_org.+\s(.+)$/){
			$boss_org = $1 ;
			# for debug
#			 $boss_org = "/mnt/nksvasp23_SMT_RCV2/" ;
#			 $boss_dst = "/mnt/nksvasp23_SMT_RCV3/" ;
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
	$ret1 = "=> system sets 'bom_diff.ini'." ;
	&recLog($ret1) ;
}
close IN ;
# **** 必要情報の取得 ****
# ongoingProcにあるCMDI実績情報から、工程仕掛中指図情報を取得し、
# $ongoing{(指図)}に展開する。
$t0 = gethrtime() ;
if ( &get_ongProc() eq "err" ){
	&recLog("=> get_ongProc Error : ".$ret1."\n" ) ;
	goto exit_prog ;
}
$ret1 = "=> get_ongProc. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;
&writeFile($data_root."/ongoing.tsv", \%ongoing ) ;

# # **** 面取り数の取得 ****
# # 1シートあたりの面取り数を取得し、
# # $mentori{(品目コード)}に展開する。
# $t0 = gethrtime() ;
# if ( &get_mentori() eq "err" ){
	# &recLog("=> get_memtori Error : ".$ret1."\n" ) ;
	# goto exit_prog ;
# }
# $ret1 = "=> get_mentori. ttl:".$ret1.", tm:".int((gethrtime() - $t0)/1000000)."msec " ;
# &recLog ($ret1) ;
# &writeFile($data_root."/mentori.tsv", \%mentori ) ;

# **** 除外部品品目の取得 ****
# 除外部品品目を取得し、$exep{(部品コード)}に展開する。
$t0 = gethrtime() ;
if ( &get_exep() eq "err" ){
	&recLog("=> exeption DB Error : ".$ret1."\n" ) ;
	goto exit_prog ;
}
$ret1 = "=> get_exep. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;
&writeFile($data_root."/execp.tsv", \%exep ) ;

# **** 指図BOM情報の取得 ****
# BOSSからの出力されたファイルをローカルフォルダにコピーと、
# $boss_srcにBOM情報を戻す。
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( "IFID139.csv" ) ;
if ( $boss_src eq "err" ){
	&recLog("=> copy_BOSSfile(1) Error : ".$ret1."\n" ) ;
	goto exit_prog ;
}
$ret1 = "=> copy_BOSSfile(1). ,".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;

# **** BOM情報の展開 ****
# BOM情報を工程仕掛中指図情報でフィルタし
# %boss_BOM{(品目コード)}に展開する。
$t0 = gethrtime() ;
if ( &dply_BOM( $boss_src ) eq "err" ){
	&recLog("=> dply_BOM Error : ".$ret1."\n" ) ;
	goto exit_prog ;
}
$ret1 = "=> dply_BOM. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;
&writeFile($data_root."/boss_BOM.tsv", \%boss_BOM ) ;

# **** 指図情報の取得 ****
# BOSSからの出力されたファイルをローカルフォルダにコピーと、
# $boss_srcに指図情報を戻す。
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( "IFID142.csv" ) ;
if ( $boss_src eq "err" ){
	&recLog("=> copy_BOSSfile(2) Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
$ret1 = "=> copy_BOSSfile(2). ,".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;

# **** 指図情報の反映 ****
# 指図情報(IFID142.csv)からPCBA関連の未生産実績指図を抽出、
# liveOrder_sub DB を更新、%boss_BOM から BOSSbom DB を生成する。
$t0 = gethrtime() ;
if (&upd_DBs($boss_src) eq "err" ){
	&recLog("=> upd_DBs Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
$ret1 = "=> upd_DBs. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;

# **** 所要量の取得 ****
# 有効指図の品目で、EGProDBからの最新部品配列情報を集計し、
# $egpro_BOM{(品目コード)}に展開する。
$t0 = gethrtime() ;
if (&readEG_DB() eq "err" ){
	&recLog("=> readEG_DB Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
$ret1 = "=> readEG_DB. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
# if (&readEG_DB2() eq "err" ){
	# &recLog("=> readEG_DB2 Error : ".$ret1."\n" ) ;
	# goto exit_prog;
# }
# $ret1 = "=> readEG_DB2. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;
&writeFile($data_root."/egpro_BOM.tsv", \%egpro_BOM ) ;

# **** 差分を抽出 ****
# %boss_BOM と %egpro_BOM の差分を求め、bomDiff DB を更新する。
$t0 = gethrtime() ;
if (&calc_sabun() eq "err" ){
	&recLog("=> calc_sabun Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
$ret1 = "=> calc_sabun. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;
&recLog ($ret1) ;

# **** 調達情報の取得(未使用) ****
# BOSSからの出力されたファイルを、サーバの負担軽減のため
# ローカルフォルダにコピーする。
# $boss_srcに調達情報を戻す。
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( "IFID146.csv" ) ;
if ( $boss_src eq "err" ){
	&recLog("=> copy_BOSSfile(3) Error : ".$ret1."\n" ) ;
	goto exit_prog;
}
$ret1 = "=> copy_BOSSfile(3). ,".int((gethrtime() - $t0)/1000000)."msec " ;
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
		print OUT ($_[0]) ;
	close OUT;
	return 0 ;
}

# ---- 工程仕掛中指図の取得 ----
# DLVでなく現在仕掛中(CMDI実績あり)の指図のうち、条件に合致した指図を抽出する。
# 条件：品目が"U～"で、担当が"R～"であるもの。
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数、%ongoing{(指図)}=[(品目コード),(ライン)]
#	　　エラー時:"err"、$ret1:エラー詳細
sub get_ongProc(){
	$ret1 = 0 ;
	my ($db, $st, $ary_ref) ;
	my $sql = "SELECT `sashizu`,`typeID`,`LINE` FROM ".$db2_ongoing." " ;
	$sql .= "WHERE `sashizu` NOT LIKE '-%' AND `typeID` LIKE 'U%' AND `LINE` LIKE 'R%' ;" ;
	eval{
		# CMDI実績収集DB(nksv560.orderNumber.ongoingProc)から工程仕掛中指図を取得
		$db = DBI->connect($db2_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "proc_ongoing DB error : \nsql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		$ongoing{@$_[0]} = [@$_[1], @$_[2] ] ;		# $ongoing{(指図)}=[(品目コード),(ライン)]
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;
}

# # ---- 面取り数テーブルの生成 ----
# # "U"で始まる全品目について、子品目、面取り数を取得して、
# # %mentori{(品目コード)}に保存する。
# # 引数：なし
# # 戻り値：正常時:"0"、$ret1:処理件数、%mentori{(品目コード)}= "H",または "(面取数)"
# #		エラー時:"err"、$ret1:エラー詳細
# sub get_mentori(){
	# $ret1 = 0 ;
	# my ($db, $st, $ary_ref) ;
	# my $sql = "SELECT `typeID`,`chldID` FROM ".$db2_unitInfo." WHERE `typeID` LIKE 'U%' ;" ;
	# eval{
		# $db = DBI->connect($db2_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		# $st = $db->prepare($sql) or die(DBI::errstr) ;
		# $st->execute() or die(DBI::errstr) ;
		# $ary_ref = $st->fetchall_arrayref ;
		# $st->finish ;
		# $db->disconnect ;
	# };
	# #DBでエラーがある場合の処理
	# if ($@){
		# if(defined($db)){$db->disconnect() ;}
		# $ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		# return "err" ;
	# }
	# foreach (@$ary_ref){
		# @$_[1] =~ /(^|\t),(\d+)/ ;			# 品目名に続く数字のみ抽出
		# # $mentori{@$_[0]} = $2 ;
		# $ret1 = $ret1 + 1 ;
	# }
	# return $ret1 ;
# }

# ---- 除外部品品目の取得 ----
# 比較対象としない除外部品を取得して、
# %exep{(品目コード)}に保存する。
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数、%exep{(品目コード)}= "(登録日時)"
#		エラー時:"err"、$ret1:エラー詳細
sub get_exep(){
	$ret1 = 0 ;
	my ($db, $st, $ary_ref) ;
	my $sql = "SELECT `partNo`,`reg_date` FROM ".$db_exepPart." WHERE 1 ;" ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		$exep{@$_[0]} = @$_[1] ;
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;
}

# ---- ファイルをコピーする ----
# 引数で指定されたテキストファイルを取得し、ローカルフォルダに
# コピー、ファイル内容全体を戻す。
# 引数：対象ファイル名(パスは$boss_org,$boss_dst)
# 戻り値：正常時: ファイルテキスト
#		エラー時: "err"、$ret1:エラー詳細
sub copy_BOSSfile(){
	my $src ;
	$ret1 = "" ;
	# ファイルの取得(一気読み)
	if (!open(IN, "<", $boss_org.$_[0])){
		$ret1 = $_[0]." is not be able to open for read : ".$! ;
		close IN ;
		return "err" ;
	}else{
		local $/ ;				# 行末記号をlocalでundefに
		$src = <IN> ;			# ファイル内容を一気に変数に取得
	}
	close IN ;
	# ファイルの書込み(一気書き)
	if (!open(OUT, ">", $boss_dst.$_[0])){
		$ret1 = $_[0]." is not be able to open for write : ".$! ;
		close OUT ;
		return "err" ;
	}else{
		print OUT $src ;		# ファイル内容を一気に書く
	}
	close OUT ;
	return $src ;
}

# ---- 発令指図BOMファイルを読む ----
# ファイルコピー時に取得されたテキストの指図BOM情報から、
# 条件に合致したレコードを抽出して%boss_BOM 配列に展開する。
# 条件：品目が"U～"であり、指図が"4～"でなく、
#		工程仕掛中でなく($ongoing{(指図)}がない）、
# 		構成品目が"ドキュメントコード"でないもの。
# 引数：ファイルのテキスト
# 戻り値：正常時: "0"、%boss_BOM{(品目コード)} = [(指図),(部品コード),(基数)][…][…]… 
#		エラー時: "err"、$ret1:エラー詳細
sub dply_BOM(){
	$ret1 = 0 ;
	# 所要データの抽出(必要品目をフィルタリング)
	foreach (split (/\r\n|\r|\n/, $_[0] )){
		#no warnings 'experimental' ;
		my @col = split ("\t",$_) ;			# bossファイルのデリミタ：tab
		# 指図[0],プラント[1],品目コード[2],資産区分[3],構成品目(部品)[4],必要数[5],基数[6],単位[7]
		if ($col[2] !~ /^U/){next ;}		# 品目が"U～"でなければ次
		$col[0] = $col[0] + 0 ;				# 指図の数値化
		if ($col[0] =~ /^4/ ){next ; }		# 4～指図は次
		if (defined $ongoing{$col[0]} ){next ;	}	# 工程仕掛中指図なら次
		# if (!$mentori{$col[2]}){			# 基数同士での比較が可能になったので、面取り数は不要
			# $mentori{$col[2]} = 1 ;		# 面取り数無しは"1"
		# }
		if ($col[4] =~ /^0\d{9}.?$/ ){next ; }		# すべてのドキュメントコード0xxxyyyyyyZは次
		if (defined $exep{$col[4]}){next ; }		# 除外部品なら次
		$col[6] = $col[6] + 0 ;				# 基数の整数化
		# 戻り値：%boss_BOM{(品目コード)} = [(指図),(部品コード),(基数)]
		push ( @{ $boss_BOM{$col[2]} } , ([ $col[0],$col[4],$col[6] ]) ) ;
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;				# 処理件数を返す
}

# ---- 未生産実績指図情報を保存する ----
# ファイルコピー時に取得されたテキストの発令情報から、
# 条件に合致したレコードを抽出してliveOrder_sub DBに保存する。
# 条件：品目が"U～"であり、担当が"R～"であり、指図が"4～"でなく、
# 		工程仕掛中でない($ongoing{(指図)}がない)、生産実績が"0"であるもの。
# 引数：ファイルのテキスト
# 戻り値：正常時: "0"、liveOrder_sub DB への書き込み
#		エラー時: "err"、$ret1:エラー詳細
sub upd_DBs(){
	$ret1 = 0 ;
	# 所要発令指図情報の抽出
	my ($db, $st, $sql) ;
	eval {
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 仕掛中指図DB(172.254.253.60.orderNumber.liveOrder_sub)に書込み
		# 旧データの削除
		$sql = "TRUNCATE TABLE ".$db_liveOrder_sub." ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
# print "(373)".int((gethrtime() - $t0)/1000000)."msec\n" ;
		# 新データの書込み
		$sql = "INSERT INTO `".$db_liveOrder_sub."` (`orderNumber`,`typeID`,`orderQty`,`reg_date`," ;
		$sql .= "`start_date`,`finish_date`,`prod_result`,`plant_ID`,`sashizu_type`,`update_date`,`LINE`) VALUES " ;
		foreach (split (/\r\n|\r|\n/, $_[0] )){
			#no warnings 'experimental' ;
			my @col = split ("\t",$_) ;		# bossファイルのデリミタ：tab
			# 指図[4],品目コード[6],発令数[11],指図登録日[13],製造開始日[14],
			# 完成予定日[15],生産実績[18],プラント[5],指図タイプ[1],更新日[16],ライン[8]
			if ($col[6] !~ /^U/){next ;}	# 品目が"U～"でなければ次
			if ($col[8] !~ /^R/){next ;}	# 担当ラインが"R*"でなければ
			$col[4] = $col[4] + 0 ;			# 指図の数値化
			if ($col[4] =~ /^4/){next ;}	# 4～指図なら次
			if (defined $ongoing{$col[4]}){next ;}		# 工程仕掛中指図に存在なら次
#			if ($mentori{$col[6]} eq "H" ){next ; }		# 半成-半製の半製品目発令なら次
			$col[18] = int ($col[18]) ;		# 生産実績の整数化
			if ($col[18] > 0){next ;}		# 生産実績ありなら次
			$col[11] = int ($col[11]) ;		# 発令数の整数化
			$col[13] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 指図登録日
			$col[14] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 製造開始日
			$col[15] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 完成予定日
			if (defined $col[16] && $col[16] >= 20210101 ){			# 更新日が有効日付
				$col[16] =~ s/(\d{4})(\d{2})(\d{2})/'$1-$2-$3'/ ;	# null対策、''でくくる)
			}else{
				$col[16] = "NULL" ;
			}
			# $sqlへの追加
			$sql .= "('".$col[4]."','".$col[6]."','".$col[11]."','".$col[13]."','".$col[14]."','" ;
			$sql .= $col[15]."','".$col[18]."','".$col[5]."','".$col[1]."',".$col[16].",'".$col[8]."')," ;
			$ret1 = $ret1 + 1 ;
			if ($ret1 % 1000 == 0){
				$sql =~ s/,$/;/ ;
				$st = $db->prepare($sql) or die(DBI::errstr) ;
				$st->execute() or die(DBI::errstr) ;
				$st = $db->commit ;
				$sql = "INSERT INTO `".$db_liveOrder_sub."` (`orderNumber`,`typeID`,`orderQty`,`reg_date`," ;
				$sql .= "`start_date`,`finish_date`,`prod_result`,`plant_ID`,`sashizu_type`,`update_date`,`LINE`) VALUES " ;
			}
		}
		$sql =~ s/,$/;/ ;					# 末尾の","を";"に置換
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
	} ;
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	return $ret1 ;
}

# ---- EGProデータベースを読む ----
# $boss_BOMの品目コードに必要な所要数を取得して 
# %egpro_BOM 配列に展開する。
# 引数：なし($boss_BOM{(品目コード)}のキー値
# 戻り値：正常時: "0"、$egpro_BOM{(品目コード)} = [(部品コード),(個数),(登録日時)]…
#		エラー時: "err"、$ret1: エラー詳細
sub readEG_DB(){
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
#		&writeFile($data_root."/egpro_Distinct.tsv",\%typeList) ;			# デバグ用
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
				push ( @egpro , ([$_ ,$bom{$_}, $lastUpd ]) ) ;		# egproですべて"1台"データに換算済み
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
		$ret1 = $sql."//egProサーバの読み上げに失敗しました(".$@.")\n" ;
		return "err" ;
	}
	return $ret1 ;
}

# この処理は、旧EGPro対応のため保持する。
sub readEG_DB2(){
	$ret1 = 0 ;
	my ($db, $st, $sql, $ary_ref, $where) ;
	my @egpro ;
	# egProDBを読む
	eval{
		$db = DBI->connect($db_ODBCserver2, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db->{LongTruncOk}=1 ;
		$db->{LongReadLen}=200000 ;
		# EGProDBのマスタから、品目コード,指図,登録日時を取得
		$sql = "SELECT 製品,品番,員数,登録日時 FROM ".$db_ODBCview2." ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
# print "(544)".Dumper($ary_ref)."\n";
		$db->disconnect ;
		# 取得データを自SQL_DBに書込み
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die(DBI::errstr) ;
		$sql = "INSERT INTO ".$db2_egproBOM." (typeID,partNo_egpro,qty,plant,regDate) VALUES " ;
		foreach (@$ary_ref){
			$sql .= "('".@$_[0]."','".@$_[1]."','".@$_[2]."','0','".@$_[3]."')," ;
			$ret1 = $ret1 + 1 ;
			if ($ret1 % 1000 == 0 ){
				$sql =~ s/,$// ;
				$sql .= " ON DUPLICATE KEY UPDATE `qty`=VALUES(qty),`regDate`=VALUES(regDate) ;" ;
				$st = $db->prepare($sql) or die(DBI::errstr) ;
				$st->execute() or die(DBI::errstr) ;
				$st = $db->commit ;
# print "(557)".$ret1."\n";
				$sql = "INSERT INTO ".$db2_egproBOM." (typeID,partNo_egpro,qty,plant,regDate) VALUES " ;
			}
		}
		$sql =~ s/,$// ;
		$sql .= " ON DUPLICATE KEY UPDATE `qty`=VALUES(qty),`regDate`=VALUES(regDate) ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		$db->disconnect ;
	};
	if ($@){
		if (defined($db)){$db->disconnect() ;}
		$ret1 = $sql."//egProサーバの読み上げに失敗しました(".$@.")\n" ;
		return "err" ;
	}
	return $ret1 ;
}

# ---- データベースへの差分出力 ----
# bossBOMとEGProBOMの差分を bomDiff DB に出力する。
# 引数：グローバル変数で、%boss_BOM{(品目コード)}、%egpro_BOM{(品目コード)}
# 戻り値：正常時: "0"
# 		エラー時: "err"、$ret1: エラー詳細
sub calc_sabun(){
	$ret1 = 0 ;
	my ($db, $st, $sql) ;
	my $sql_cont = "" ;				# sqlコマンド出力用変数
	# 品目毎での処理(同一品目で指図毎に比較)
	foreach my $typeID (keys %boss_BOM){
		my %sashizu ;
# print "(554)品名:".$typeID." 指図:" ;
		# 同じ$boss_BOM{(品目コード)}内で、 $sashizu{(指図)} に指図毎に抽出
		# $boss_BOM{(品目コード)} = [(品目コード)[0],(部品コード)[1],(個数)[2]],[…],…
		#  → $sashizu{(指図)} = [(部品コード)[0],(個数)[1]],[…],…
		foreach ( @{ $boss_BOM{$typeID} } ){
			push (@{ $sashizu{@$_[0]} } , ([ @$_[1],@$_[2] ]) );
		}
		# $sashizu{(指図)}で処理
		foreach my $sas_key(keys %sashizu){
			# 部品コードを昇順に並べ替え($egpro_BOMはソート済み)
			@{ $sashizu{$sas_key} } = sort ({@$a[0] cmp @$b[0]} @{ $sashizu{$sas_key} }) ;
			# 部品コード順にポインタを移動して比較、結果を $sql_cont に保存
# print $sas_key."/" ;
			my ($boss_Indx, $egpro_Indx) = (0, 0) ;
			my @partNo = @{ $sashizu{$sas_key} } ;
			while (){
				# 部品毎にboss_BOM,egpro_BOMのEOFまでチェックし、@sql_contを生成
				# @sql_cont = [(品目コード),(指図),(部品コード),(boss基数),(egpro基数),(egpro登録日時)]
# print $boss_Indx."//".$egpro_Indx.".....".$partNo[$boss_Indx][0]."//".$egpro_BOM{$typeID}[$egpro_Indx][0]."\n";
				if (!$partNo[$boss_Indx][0] && !$egpro_BOM{$typeID}[$egpro_Indx][0]){
					# boss/egpro両方がundef(EOF)になったら抜ける
					last ;
				}elsif (!$partNo[$boss_Indx][0]){
					# bossの部品Cがない ==> boss部品が基数"0"、egpro部品が実数、登録日あり
					$sql_cont .= "('".$typeID."','".$sas_key."','".$egpro_BOM{$typeID}[$egpro_Indx][0]."'," ;
					$sql_cont .= "'0','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
					$sql_cont .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
					$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
				}elsif (!$egpro_BOM{$typeID}[$egpro_Indx][0]){
					# egproの部品Cがない ==> egpro部品が基数"0"、boss部品が実数、登録日NULL
					$sql_cont .= "('".$typeID."','".$sas_key."','".$partNo[$boss_Indx][0]."'," ;
					$sql_cont .= "'".$partNo[$boss_Indx][1]."','0'," ;
					$sql_cont .= "NULL)\t" ;
					$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
				}elsif ($partNo[$boss_Indx][0] gt $egpro_BOM{$typeID}[$egpro_Indx][0]) {
					# bossの部品C＞egproの部品C ==> boss部品が基数"0"、egpro部品が実数、登録日あり
					$sql_cont .= "('".$typeID."','".$sas_key."','".$egpro_BOM{$typeID}[$egpro_Indx][0]."'," ;
					$sql_cont .= "'0','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
					$sql_cont .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
					$egpro_Indx = $egpro_Indx + 1 ;	# 次のegpro部品
				}elsif ($partNo[$boss_Indx][0] lt $egpro_BOM{$typeID}[$egpro_Indx][0]) {
					# bossの部品C＜egproの部品C ==> egpro部品が基数"0"、boss部品が実数、登録日NULL
					$sql_cont .= "('".$typeID."','".$sas_key."','".$partNo[$boss_Indx][0]."'," ;
					$sql_cont .= "'".$partNo[$boss_Indx][1]."','0'," ;
					$sql_cont .= "NULL)\t" ;
					$boss_Indx = $boss_Indx + 1 ;	# 次のboss部品
				}elsif ($partNo[$boss_Indx][0] eq $egpro_BOM{$typeID}[$egpro_Indx][0]) {
					# bossの部品C＝egproの部品C ==> 両方が実数 
					$sql_cont .= "('".$typeID."','".$sas_key."','".$partNo[$boss_Indx][0]."'," ;
					$sql_cont .= "'".$partNo[$boss_Indx][1]."','".$egpro_BOM{$typeID}[$egpro_Indx][1]."'," ;
					$sql_cont .= "'".$egpro_BOM{$typeID}[$egpro_Indx][2]."')\t" ;
					$boss_Indx = $boss_Indx + 1 ;
					$egpro_Indx = $egpro_Indx + 1 ;
				}
			}
		}
# print "\n" ;
	}
	# 全品目終了、仕掛中指図BOMDB(172.254.253.60.orderNumber.bomDiff)に書込み
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 旧データの削除
		$sql = "TRUNCATE TABLE ".$db_bomDiff." ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		# 新データの書込み
		$sql = "INSERT INTO `".$db_bomDiff."` " ;
		$sql .= "(`typeID`,`orderNumber`,`subType`,`unitQty`,`eg_unitQty`,`eg_regDate`) VALUES " ;
		foreach (split ("\t", $sql_cont)){
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
		$sql =~ s/,$// ;
		$sql .= " ON DUPLICATE KEY UPDATE " ;
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

# ---- hash内が配列をカレントディレクトリに書き出し ----
# 引数：ファイル名[0]、配列のリファレンス[1]
#	(リファレンス)			(デリファレンス)
#	通常の配列＝渡し:\@～	受取:@$_[n]
#	ハッシュ＝渡し:\%～		受取:%{$_[n]}	(現在はこちら)
sub writeFile(){
	my $out_text = "" ;
	my %arry = %{ $_[1] } ;				# (ハッシュ用)
	foreach my $key (sort keys %{$_[1]} ){	# (ハッシュ用)
		if ($arry{$key} !~ /ARRAY/ ){
			# ARRAYでない：ハッシュ内がスカラー
				$out_text .= $key."\t".$arry{$key}."\r\n" ;
		}else{		
			# ARRAYである：ハッシュ内が1次元以上
			if (@{$arry{$key}}[0] !~ /ARRAY/ ){
				# ARRAYでない：ハッシュ内が1次元
				$out_text .= $key."\t".( join ("\t" , @{$arry{$key}} ) )."\r\n" ;
			}else{
				# ARRAYである：ハッシュ内が2次元
				foreach my $line (@{ $arry{$key} } ){
					$out_text .= $key."\t".( join ("\t" , @$line ) )."\r\n" ;
				}
			}
		}
	}
	open (OUT, ">", $_[0]) ;
		print OUT $out_text ;
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
	$t =~ /(\d{4}).(\d{2}).(\d{2})\s(\d{2}):(\d{2}):(\d{2})/ ;
	return timelocal($6,$5,$4,$3,$2-1,$1-1900) ;
}

exit_prog:
