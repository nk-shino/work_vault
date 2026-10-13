#!/usr/bin/perl -w

#**********************************************************
# このプログラムは、crontabによって毎深夜2:05に、または
# index.cgiの「更新」ボタン押下で起動され、
# 1.EGprosrvからSMT生産実績(=完了)指図情報を取得する。
# 2.BOSSが出力する発令指図情報ファイル(IFID142.csv)をコピーし、
#   自担当で、SMT生産実績有・入庫実績有等を除いた自仕掛中指図を、
#   EGprowebサーバのliveOrder_sub DBに展開する。
# 3.SMT対象外部品(除外部品)を取得する。
# 4.BOSSが出力する指図BOMファイル(IFID139.csv)をコピーし、
#   自仕掛中指図BOMで、除外部品や非SMT部品をフィルタ、さらに
#   複合基板は同一指図内で集計し、
#   EGprowebサーバのbossBOM DBに展開する。
# 5.EGProサーバから面取数情報を取得し、nksv560サーバの
#   unitInfo DBを更新する。
# 6.BOSSが出力する指図BOMファイル(IFID139.csv)をコピーする。
# これらファイルはPanasonicEGProアプリが取得後削除するので、
# 削除前に取得しなければならない。
# Ver. 1.00:初回リリース。
# Ver. 2.00:アプリ設定値をiniファイルから上書き読込み追加。
#			面取り数情報を取得しLocalDBの更新処理を追加。
# 			後段処理へのデータ渡しをファイルからDBに変更。
# Ver. 2.10:SMT完了の情報をCMDI(ongoingProc)から、EGprosrvの
#			[D_指図実行Log]から取得に変更。
# Ver. 2.11:BOSSファイルがない時、1つ前のファイルを読む。
# Ver. 2.20:タイムスタンプ保存のため、cp -a コマンドでコピー
#									2021/01/06 J.Igarashi
#**********************************************************
my $ver = "2.20" ;
use strict ;
use warnings ;
use utf8 ;
use DBI ;
use Time::Local ;			# 日付、時刻の処理
use Encode ;				# 文字コード変換
use Data::Dumper ;
use Time::HR ;
use File::Copy ;
binmode STDIN, ':utf8' ;
binmode STDOUT, ':utf8' ;
binmode STDERR, ':utf8';

# BOSSインタフェース関連変数
# ルート：権限755、オーナadministrator
my $boss_org = "/mnt/nksvasp23_SMT_RCV/" ;						# リモートサーバをマウント
my $boss_dst = "/mnt/nksvasp23_SMT_RCV2/" ;						# 実在のローカルディレクトリ
#				/mnt/nksvasp23_SMT_RCV3/						# デバグ用
# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60' ;			# EGprowebサーバ
my $db2_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db_user = 'process_mgt' ;
my $db_passwd = '7bcsHFk8P7VxRcFD' ;
my $db_exepPart = 'exepPart' ;
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db_bossBOM = 'bossBOM' ;
my $db_egproBOM = 'egproBOM' ;

my $db2_unitInfo = 'unitInfo' ;
# ODBC関連接続情報
my $db_ODBCserver = "dbi:ODBC:EGPro" ;			# DB:EGProKOHDEN-Planに対するDSN
my $db2_ODBCserver = "dbi:ODBC:EGPro_MST" ;		# DB:EGProKOHDEN-MSTに対するDSN
my $db_ODBCuser = "sqluser" ;
my $db_ODBCpasswd = "Pfseg001" ;
my $db_ODBCview = "T_部品配列表" ;
my $db_ODBCview2= "D_指図実行Log" ;
my $db2_ODBCview = "M_生産品番マスタ" ;
my $db2_ODBCview2 = "M_製品構成" ;

# 高精度タイマ用変数
my $t0 = gethrtime() ;		# 高精度現在時を取得
# 汎用変数
my $ret1 = "" ;
my $logFile = "./logs/copy_BOSS.log" ;	# ログファイルの名前とパス
my $data_root = "./cgiData" ;
my $boss_src ;				# tsv形式のbossファイル
my %ongoing ;				# 着手済み指図
my %boss_Sashizu ;			# 発令指図M
my %boss_BOM ;				# 指図BOM
my %mentori ;				# 面取り数
my %exep ;					# 除外部品テーブル
my $mail_msg = "" ;
my $recLog ;				# ログテキスト
my @fileStat ;				# ファイルの属性

#***********************************
#		MAIN処理(ここから)
#***********************************
#****************for DEBUG*******************
# DBの一時変更
# $db_exepPart = 'exepPart2' ;
# $db_liveOrder_sub = 'liveOrder_sub2' ;
# $db_bossBOM = 'bossBOM2' ;
# $db_egproBOM = 'egproBOM2' ;
#********************************************
# **** ログ開始 ****
$recLog = &dateTime(time)." ***copy_BOSS.cgi Ver.".$ver." START *** "  ;
# **** 設定ファイルを読む ****
if (!open(IN, "<", "./bom_diff.ini")){
	$recLog .= "'bom_diff.ini' is not be able to open ".$!." System set the initial value. " ;
}else{
	while (<IN>){
		my $val = $_ ;
		$val =~ s/\r\n|\r|\n//g ;
		if ($val =~ /#/){
			next ;
		}elsif ($val =~ /boss_org.+\s(.+)$/){
			$boss_org = $1 ;
		}elsif ($val =~ /db_source.+\s(.+)$/){
			$val = $1 ;
			$db_source =~ s/(.+:)(.+)$/$1$val/ ;
		}elsif ($val =~ /db2_source.+\s(.+)$/){
			$val = $1 ;
			$db2_source	=~ s/(.+:)(.+)$/$1$val/ ;
		}elsif ($val =~ /db_ODBCserver.+\s(.+)$/){
			$val = $1 ;
			$db_ODBCserver =~ s/(.+:)(.+)$/$1$val/ ;
		}elsif ($val =~ /db2_ODBCserver.+\s(.+)$/){
			$val = $1 ;
			$db2_ODBCserver =~ s/(.+:)(.+)$/$1$val/ ;
		}
	}
	$recLog .= "=> 'bom_diff.ini' OK! " ;
}
close IN ;

# **** SMT完了指図の取得 ****
# EGprosrvの[D_指図実行Log]から、現時点より1年前までのSMT生産実績指図を取得、
# SMT完了指図として$ongoing{(指図)}に展開する。
$t0 = gethrtime() ;
if ( &get_doneSMT() eq "err" ){
	$recLog ."=> get_doneSMT Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> get_doneSMT. rec:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 指図情報の取得 ****
# ファイルをコピーし、そのテキストの発令情報から、自部門担当指図を抽出、
# 改造指図(4～)、SMT完了指図を除いて、
# 該当指図を$bossSashizu{(指図)}に展開、liveOrder_sub DBに保存する。
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( $boss_org."IFID142.csv", $boss_dst."IFID142.csv" ) ;
if ( $boss_src eq "err" ){
	$recLog ."=> copy_BOSSfile(1) Error : ".$ret1 ;
	goto exit_prog;
}

@fileStat = stat $boss_dst."IFID142.csv" ;
$fileStat[9] = &dateTime( $fileStat[9] );				# boss出力日時
$recLog .= $ret1."=> copy_BOSSfile(1), time".int((gethrtime() - $t0)/1000000)."msec " ;
$t0 = gethrtime() ;
if (&upd_liveOrderDB($boss_src) eq "err" ){
	$recLog .= "=> upd_liveOrderDB Error : ".$ret1 ;
	goto exit_prog;
}
$recLog .= "=> upd_liveOrderDB. rec:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 除外部品の取得 ****
# 差分比較対象としない除外部品を取得して、
# $exep{(品目コード)} に保存する。
$t0 = gethrtime() ;
if ( &get_exep() eq "err" ){
	$recLog .= "=> exempt DB Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> get_exep. rec:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 指図BOM情報の取得 ****
# テキストの指図BOM情報から、$bossSashizu{(指図)}にある指図のうち、
# 除外部品、ドキュメント等の部品を除いて、bossBOM DBに展開する。
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( $boss_org."IFID139.csv", $boss_dst."IFID139.csv" ) ;
if ( $boss_src eq "err" ){
	$recLog .= "=> copy_BOSSfile(2) Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> copy_BOSSfile(2),time:".int((gethrtime() - $t0)/1000000)."msec " ;
$t0 = gethrtime() ;
if ( &upd_bossBOM( $boss_src ) eq "err" ){
	$recLog .= "=> upd_bossBOM Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> upd_bossBOM. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 未登録BOMの取得 ****
# EGprosrvの[M_製品構成]の未生産(初めから社外生産)品目は[D_部品配列表]
# に出力されないので、EGproweb:egproBOM に無い品目を初回のみコピーする。
# 以降は1.D_部品配列表、2.sashizu.cgiでboss_BOMからのみ登録される。
# if ( &upd_egproBOM()  eq "err" ){
	# $recLog .= "=> upd_egproBOM Error : ".$ret1 ;
	# goto exit_prog ;
# }
# $recLog .= "=> upd_egproBOM. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 面取り数の取得 ****
# EGprosrvの[M_生産品番マスタ]から1シートあたりの面取り数を取得して、
# nksv560サーバの unitInfo DBのchldIDカラムを更新する。
$t0 = gethrtime() ;
if ( &get_mentori() eq "err" ){
	$recLog .= "=> get_memtori Error : ".$ret1 ;
	goto exit_prog ;
}
$recLog .= "=> get_mentori. totl:".$ret1.", time:".int((gethrtime() - $t0)/1000000)."msec " ;

# **** 調達情報ファイルの取得(未使用) ****
$t0 = gethrtime() ;
$boss_src = &copy_BOSSfile( $boss_org."IFID146.csv", $boss_dst."IFID146.csv" ) ;
if ( $boss_src eq "err" ){
	$recLog .= "=> copy_BOSSfile(3) Error : ".$ret1 ;
	goto exit_prog;
}
$recLog .= "=> copy_BOSSfile(3), time:".int((gethrtime() - $t0)/1000000)."msec " ;
$recLog .= " => ".&dateTime(time)." *** normal end *** " ;
goto exit_prog ;

#***********************************
#			SUB処理
#***********************************

# ---- SMT完了指図の取得 ----
# EGprosrvの[D_指図実行Log]から、現時点より1年前までのSMT生産実績指図を取得、
# SMT完了指図として$ongoing{(指図)}に展開する。
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数、%ongoing{(指図)}=(品目コード)
#	　　エラー時:"err"、$ret1:エラー詳細
sub get_doneSMT(){
	$ret1 = 0 ;
	my ($db, $st, $ary_ref, $sql) ;
	$sql = "SELECT 指図番号,生産品番 FROM ".$db_ODBCview2." " ;
	$sql .= "WHERE 開始日時 > '".&dateTime( time - ( 86400*365 ) )."' ;" ;
	# EGProサーバ($db_ODBCserver)の［D_指図実行Log］から実行済指図を取得
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
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "get_doneSMT DB error : \nsql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		@$_[0] = int (@$_[0]) ;
		@$_[1] =~ s/^(U.+)_P\d$/$1/ ;	# 実装面IDを削除
		$ongoing{@$_[0]} = @$_[1] ;		# $ongoing{(指図)}=(品目コード)
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;
}

# ---- ファイルをコピーする ----
# 引数で指定されたテキストファイルを取得し、ローカルフォルダにコピーし、
# コピーしたファイル内容全体を戻り値で戻す。
# 引数：コピー元パス・ファイル名、コピー先パス・ファイル名
# 戻り値：正常時: ファイルテキスト
#		エラー時: "err"、$ret1:エラー詳細
sub copy_BOSSfile(){
	my $src ;
	$ret1 = "copy: " ;
	# ファイルをタイムスタンプ属性付きコピー
	# 手動更新時は、所有者："www-data"、crontab実行時は、所有者："administrator"
	if (-e $_[0]){
		$ret1 .= "strting=> " ;
		eval{
			system ( "rm ".$_[1] ) == 0 or die "rm ".$_[1]." err:".$! ;				# 所有者違いの上書きではタイムスタンプ属性は禁止される
			system ( "cp --preserve=timestamps ".$_[0]." ".$_[1] ) == 0 or die "cp err:".$! ;
			system ( "chmod 666 ".$_[1] ) == 0 or die "chmod ".$_[1]." err:".$! ;	# 属性"666"でないと所有者者違いを削除できない
		} ;
		if ( $@ ){
			$ret1 .= $@."=> " ;
		}else{
			$ret1 .= "comp. => " ;
		}
	}else{
		$ret1 .= "src file not exist.=> " ;
	}
	# コピー先ファイルの一気読み
	if (!open( IN, "<", $_[1] ) ){
		close IN ;
		sleep 1 ;				# 1秒待つ                                                   
		if ( !open(IN, "<", $_[1] ) ){
			$ret1 .= $_[1]." is not be able to read : ".$! ;
			close IN ;
			return "err" ;
		}
	}
	local $/ ;				# 行末記号をlocalでundefに
	$src = <IN> ;			# ファイル内容を一気に変数に取得
	close IN ;
	$ret1 .= "Done. " ;
	return $src ;
}

# ---- 未SMT指図情報を保存する ----
# ファイルのテキストにある発令情報から、担当が"R～"であり、
# 指図が"4～"でなく、SMT完了指図($ongoing{(指図)})、生産実績あり指図を除いて、
# 未生産指図としてliveOrder_sub DBに保存、指図を$bossSashizu{(指図)}に展開する。
# 引数：テキスト
# 条件：がない、
# 生産実績が"0"であるもの。
# 戻り値：正常時: "0"、liveOrder_sub DB への書き込み
#		エラー時: "err"、$ret1:エラー詳細
sub upd_liveOrderDB(){
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
		# 新データの書込み
		$sql = "INSERT INTO `".$db_liveOrder_sub."` (`orderNumber`,`typeID`,`orderQty`,`reg_date`," ;
		$sql .= "`start_date`,`finish_date`,`prod_result`,`plant_ID`,`sashizu_type`,`update_date`,`LINE`) VALUES " ;
		$ret1 = 0 ;
		foreach (split (/\r\n|\r|\n/, $_[0] )){
			#no warnings 'experimental' ;
			my @col = split ("\t",$_) ;		# bossファイルのデリミタ：tab
			# 指図[4],品目コード[6],発令数[11],指図登録日[13],製造開始日[14],
			# 完成予定日[15],生産実績[18],プラント[5],指図タイプ[1],更新日[16],ライン[8]
			if ($col[6] =~ /^\d/ ){next ; }	# 品目が数字で始まるものは次
			if ($col[6] =~ /^[QP|CD|QS|SG|XX]/ ){next ; }	# 品目が左記で始まるものは次(R-,M-の試作品目あり)
			if ($col[8] !~ /^R/ ){next ; }	# 担当ラインが"R*"でなければ次
			$col[4] = $col[4] + 0 ;			# 指図の数値化
			if ($col[4] =~ /^4/ ){next ; }	# 4～指図なら次
			if (defined $ongoing{$col[4]} ){next ; }	# SMT完指図なら次
			$col[18] = int ($col[18] ) ;	# 生産実績の整数化
			if ($col[18] > 0){next ; }		# 生産実績ありなら次
			$col[11] = int ($col[11] ) ;	# 発令数の整数化
			$col[13] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 指図登録日抽出
			$col[14] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 製造開始日抽出
			$col[15] =~ s/(\d{4})(\d{2})(\d{2})/$1-$2-$3/ ;	# 完成予定日抽出
			if (defined $col[16] && $col[16] >= 20210101 ){			# 更新日が有効日付
				$col[16] =~ s/(\d{4})(\d{2})(\d{2})/'$1-$2-$3'/ ;	# null対策、''でくくる)
			}else{
				$col[16] = "NULL" ;
			}
			# $sqlへの追加
			$sql .= "('".$col[4]."','".$col[6]."','".$col[11]."','".$col[13]."','".$col[14]."','" ;
			$sql .= $col[15]."','".$col[18]."','".$col[5]."','".$col[1]."',".$col[16].",'".$col[8]."')," ;
			# 発令中指図ハッシュに追加
			$boss_Sashizu{$col[4]} = "" ;
			$ret1 = $ret1 + 1 ;
			if ($ret1 % 1000 == 0){
				$sql =~ s/,$/ ;/ ;
				$st = $db->prepare($sql) or die(DBI::errstr) ;
				$st->execute() or die(DBI::errstr) ;
				$st = $db->commit ;
				$sql = "INSERT INTO `".$db_liveOrder_sub."` (`orderNumber`,`typeID`,`orderQty`,`reg_date`," ;
				$sql .= "`start_date`,`finish_date`,`prod_result`,`plant_ID`,`sashizu_type`,`update_date`,`LINE`) VALUES " ;
			}
		}
		$sql =~ s/,$/ ;/ ;					# 末尾の","を";"に置換
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

# ---- 除外部品を取得する ----
# nksv560サーバのunitInfo DBから比較対象としない除外部品を取得して、
# %exep{(品目コード)} に保存する。
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
		$ret1 = "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	foreach (@$ary_ref){
		$exep{@$_[0]} = @$_[1] ;
		$ret1 = $ret1 + 1 ;
	}
	return $ret1 ;
}

# ---- 指図BOMファイルを読む ----
# テキストの指図BOM情報から、$bossSashizu{(指図)}にある指図のうち、
# 除外部品、ドキュメント等の部品を除いて、複合基板を累計しながら
# bossBOM DBに展開する。
# 引数：ファイルのテキスト、グローバル変数$bossUpdでBOSS出力日時
# 戻り値：正常時: "0"、boss_BOM DB
#		エラー時: "err"、$ret1:エラー詳細
sub upd_bossBOM(){
	my ($db, $st, $sql, $ary_ref) ;
	eval {
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 指図BOM DB(172.254.253.60.orderNumber.bossBOM)に書込み
		# 旧データの全削除
		$sql = "TRUNCATE TABLE ".$db_bossBOM." ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		# 新データの書込み
		$sql = "INSERT INTO `".$db_bossBOM."` (`typeID`,`orderNumber`,`partNo`,`qty`,`regDate`) VALUES " ;
		$sql .= "('bossUpd','000000000','000000',0,'".$fileStat[9]."') ; " ;		# ファイルのタイプスタンプをレコードに保存
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$sql = "INSERT INTO `".$db_bossBOM."` (`typeID`,`orderNumber`,`partNo`,`qty`) VALUES " ;
		$ret1 = 0 ;
		foreach (split (/\r\n|\r|\n/, $_[0] )){
			#no warnings 'experimental' ;
			my @col = split ("\t",$_) ;			# bossファイルのデリミタ：tab
			# 指図[0],プラント[1],品目コード[2],資産区分[3],構成品目(部品)[4],必要数[5],基数[6],単位[7]
			$col[0] = int ($col[0]) ;				# 指図の数値化
			if (!defined $boss_Sashizu{$col[0]}){next ; }	# 発令指図に無ければ次
			if (defined $ongoing{$col[0]} ){next ;	}		# SMT完指図に有れば次
			if ($col[4] =~ /^0\d{9}.?$/ ){next ; }			# すべてのdocコード(0+9ケタ+追番)は次
			if (defined $exep{$col[4]}){next ; }			# 除外部品tblにあれば次
			$col[6] = int ($col[6]) ;						# 基数の整数化
			# $sqlへの追加
			$sql .= "('".$col[2]."','".$col[0]."','".$col[4]."',".$col[6].")," ;
			$ret1 = $ret1 + 1 ;
			if ($ret1 % 10000 == 0){
				$sql =~ s/,$/ / ;				# 末尾の","を" "に
				# 複合基板は複数レコードで同一部品なので集計必要
				$sql .= "ON DUPLICATE KEY UPDATE `qty` = qty + VALUES(qty) ;" ;
				$st = $db->prepare($sql) or die(DBI::errstr) ;
				$st->execute() or die(DBI::errstr) ;
				$st = $db->commit ;
				$sql = "INSERT INTO `".$db_bossBOM."` (`typeID`,`orderNumber`,`partNo`,`qty`) VALUES " ;
			}
		}
		$sql =~ s/,$/ / ;
		$sql .= "ON DUPLICATE KEY UPDATE `qty` = qty + VALUES(qty) ;" ;
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
	return $ret1 ;				# レコード数を返す
}

# # ---- 未登録BOMをEGprosrvからコピー[M_製品構成]の反映 ----
# # EGprosrvの[M_製品構成]の未生産(初めから社外生産)品目は[D_部品配列表]
# # に出力されないので、EGproweb:egproBOM に無い品目をコピーする。
# sub upd_egproBOM(){
	# $ret1 = 0 ;
	# my ($db, $st, $ary_ref) ;
	# my %egproBOM ;
	# # EGproweb:egproBOM の品目を取得
	# my $sql = "SELECT DISTINCT `typeID`, `regDate` FROM ".$db_egproBOM." ;" ;
	# eval {
		# $db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		# $st = $db->prepare($sql) or die(DBI::errstr) ;
		# $st->execute() or die(DBI::errstr) ;
		# $ary_ref = $st->fetchall_arrayref ;
		# $db->disconnect ;
	# };
	# if ($@){
		# if(defined($db)){$db->disconnect() ;}
		# $ret1 = "sql : ".$sql."\n ==> ".$@ ;
		# return "err" ;
	# }
	# foreach (@$ary_ref){
		# $egproBOM{@$_[0]} = @$_[1] ;
	# }
	# # EGProサーバ($db2_ODBCserver)の［M_製品構成］から製品,品番,員数,登録日時を取得
	# $sql = "SELECT 製品,品番,員数,登録日時 FROM ".$db2_ODBCview2." ;" ;
	# eval{
		# $db = DBI->connect($db2_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		# $db->{LongTruncOk}=1 ;
		# $db->{LongReadLen}=200000 ;
		# $st = $db->prepare($sql) or die(DBI::errstr) ;
		# $st->execute() or die(DBI::errstr) ;
		# $ary_ref = $st->fetchall_arrayref ;
		# $st->finish ;
		# $db->disconnect ;
	# };
	# #DBでエラーがある場合の処理
	# if ($@){
		# if(defined($db)){$db->disconnect() ;}
		# $ret1 = "sql : ".$sql."\n ==> ".$@ ;
		# return "err" ;
	# }
	# my $last_typeID = "" ;
	# $sql = "" ;
	# eval {
		# $db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		# foreach (@$ary_ref){
			# if (defined $egproBOM{@$_[0]}){next ; }		# EGproweb:egproBOMに既存なら次
			# # if (@$_[0] =~ /^[C|M|R]/ ){next ; }
			# if ($last_typeID ne @$_[0]){
# #print "(369)typeID:".@$_[0]."\n" ;
				# $last_typeID = @$_[0] ;
			# }
			# @$_[3] =~ s/\.?\d*$// ;						# 末尾の小数点以下を削除
			# $sql .= "('".@$_[0]."','".@$_[1]."','".@$_[2]."','".@$_[3]."')," ;
			# $ret1 = $ret1 + 1 ;
			# if ($ret1 % 10000 == 0){
				# $sql =~ s/,$/ / ;				# 末尾の","を" "に
				# $sql = "INSERT INTO ".$db_egproBOM." (`typeID`, `partNo_egpro`, `qty`, `regDate`) VALUES ".$sql." " ;
				# # 複合基板は複数レコードで同一部品なので集計必要
				# $sql .= "ON DUPLICATE KEY UPDATE `qty` = qty + VALUES(qty) ;" ;
				# $st = $db->prepare($sql) or die(DBI::errstr) ;
				# $st->execute() or die(DBI::errstr) ;
			# }
		# }
		# # 更新あり
		# if ($sql ne "" ){
			# $sql =~ s/,$/ / ;
			# $sql = "INSERT INTO ".$db_egproBOM." (`typeID`, `partNo_egpro`, `qty`, `regDate`) VALUES ".$sql." " ;
			# $sql .= "ON DUPLICATE KEY UPDATE `qty` = qty + VALUES(qty) ;" ;
			# $st = $db->prepare($sql) or die(DBI::errstr) ;
			# $st->execute() or die(DBI::errstr) ;
		# }
		# $db->disconnect ;
	# };
	# #DBでエラーがある場合の処理
	# if ($@){
		# if(defined($db)){$db->disconnect() ;}
		# $ret1 = "sql : ".$sql."\n ==> ".$@ ;
		# return "err" ;
	# }
	# return $ret1 ;
# }

# ---- 面取り数の取得とDB展開 ----
# EGprosrvの[M_生産品番マスタ]から1シートあたりの面取り数を取得して、
# nksv560サーバの unitInfo DBのchldIDカラムを更新する。
# 更新後、品目:U%だけを $mentori{(品目コード)} に展開
# 引数：なし
# 戻り値：正常時:"0"、$ret1:処理件数
#		エラー時:"err"、$ret1:エラー詳細
sub get_mentori(){
	$ret1 = 0 ;
	my ($db, $st, $ary_ref) ;
	my $sql = "SELECT DISTINCT 品名,基板取数 FROM ".$db2_ODBCview." ;" ;
	# EGProサーバ($db2_ODBCserver)の［M_生産品番マスタ］から、品名,基板取数を取得(約4000件)
	eval{
		$db = DBI->connect($db2_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr) ;
		$db->{LongTruncOk}=1 ;
		$db->{LongReadLen}=200000 ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "sql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	# 取得値を変数に展開しsql文の組立
	# SMT品目は子品目なし → chldIDは上書き置換え
	$sql = "" ;
	foreach (@$ary_ref){
		@$_[0] =~ s/_\w*// ;			# "_"以降(実装面)を削除
		@$_[1] =~ /(\d{1,3})/ ;			# 数字部分のみを抽出、なければNULL
		$sql .= "('".@$_[0]."',',".@$_[1]."')," ;
		$ret1 = $ret1 + 1 ;
	}
	$sql =~ s/,$/ / ;
	eval{
		# nksv560サーバ($db2_source)への書込み
		$db = DBI->connect($db2_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		$sql = "INSERT INTO ".$db2_unitInfo." (`typeID`, `chldID`) VALUES ".$sql ;
		$sql .= "ON DUPLICATE KEY UPDATE `chldID` = VALUES(chldID) ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st->finish ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
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
#	ハッシュ＝渡し:\%～		受取:%{$_[n]}	(現在はこちらのみ)
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
	my $sec = $6 ;
	$sec =~ s/\.?\d*$// ;				# 小数点以下の秒を削除
	return timelocal($sec,$5,$4,$3,$2-1,$1-1900) ;
}

# プログラム終了
exit_prog:
# ---- Logの出力 ----
# メッセージテキストのlogファイル出力。
open ( OUT, ">>", $logFile) ;
	print OUT decode('utf8',$recLog)."\n" ;
close OUT;
