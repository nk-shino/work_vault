#!/usr/bin/perl -w

# exemptで画面再描画する際、hidden属性で渡している$in{'sts'}のでstsが更新されない。
# reloadされるindex2.cgiは更新後DBの内容で評価されるので、sashizu.cgiのstsと整合しない。
# 
#******************************************************************
# このプログラムは、index.cgi画面で指図が選択されると起動され、
# 1.index.cgiが出力するEGprowebサーバのbomDiff DBから、
#   当該指図の差分情報を取得し、タイトル部分はorderNumber_sub DBから
#   取得して表示する。
# 2.差分ありで、nksv569サーバのECN DBに品目がある場合はECNの内容を表示、
#   無い場合は"ECN未発行"を表示する。
# 3.「変更」ボタンで、生産場所とBOSS基数をEGProwebサーバのegproBPM DBに
#   反映する。
# 4.除外登録のチェックボックス、「除外登録」のボタンで、
#   EGprowebサーバのexepPart DBへ対象部品の除外登録を行う。
#   ---(以下はbom_diff.js内で行う)---
# 5.「CSV出力」ボタンで、表示内容をcsv形式でファイルダウンロードする。
#									2021/01/11 J.Igarashi
# Ver. 1.00:初回リリース。
# Ver. 2.00:社外生産品への対応
#			(社内/社外の表示、自DBの生産場所stsを変更可)
#			ECNとの連携(ファイル有無を示す)
# Ver. 2.10:copy_BOSS.cgi,index.cgiを変更
# Ver. 2.11:除外コードで、試作ダミーコード登録に対応
# Ver. 2.20:差分フィルタ機能を追加(bom_diff.js)
#******************************************************************
my $ver = "2.20" ;
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

# SQLサーバ・ユーザ・パスワード・関連変数(bom_diff.iniにより上書き)
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60' ;
my $db2_source = 'DBI:mysql:orderNumber:nksv560.ad.nkc.co.jp' ;
my $db3_source = 'DBI:mysql:orderNumber:nksv569.ad.nkc.co.jp' ;
my $db_user = 'process_mgt' ;
my $db_passwd = '7bcsHFk8P7VxRcFD' ;
my $db_bossBOM = 'bossBOM' ;
my $db_egproBOM = 'egproBOM' ;
my $db_exempt = 'exepPart' ;
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db2_unitInfo = 'unitInfo' ;
my $db_ecn = 'ECN' ;
# Javascript
my $bom_diff_js = "bom_diff.js" ;
my $win_man_js ;			# 自画面、親画面制御用javascript

# 自画面
my $self_scrn = "./sashizu.cgi" ;	# 指図詳細画面

# 汎用変数
my $ret1 = "" ;				# エラーメッセージ戻り値
my $recLog = "" ;			# ログテキスト
my $logFile = './logs/sashizu.log';		# ログファイルの名前
my $data_root = "./cgiData" ;
my %in ;					# 入力・前画面からの引数
my %mentori ;
my ($sashizu, $typeID, $qty, $regDate, $line, $plant ) ;
my ($sttDate, $finDate) ;
# 高精度タイマ用変数
my ($t0, $t1) ;	
$t0 = gethrtime() ;			# 高精度現在時を取得
#********************************************
#          Main処理 ここから
#********************************************
#****************for DEBUG*******************
my $dbg = 0 ;	#0:ope 1:dbg...show arguments 2:dbg...show html
my $dbg_msg = "<font color=\"ff0000\">(DEBUG MODE)</font><br>\n" ;
# DBの一時変更
if ( $dbg > 0 ){
	$db_bossBOM = 'bossBOM2' ;
	$db_egproBOM = 'egproBOM2' ;
	$db_exempt = 'exepPart2' ;
	$db_liveOrder_sub = 'liveOrder_sub2' ;
	$self_scrn = './sashizu2.cgi' ;
	$logFile = './logs/sashizu2.log';		# ログファイルの名前
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
	<script type="text/javascript" src="./jquery/fixed_midashi.js"></script>
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
		}elsif ($val =~ /db3_source.+\s(.+)$/){
			$val = $1 ;
			$db3_source	=~ s/(.+:)(.+)$/$1$val/ ;
		}
	}
	$recLog .= "=> reads'bom_diff.ini' " ;
}
close IN ;
# cgiから%in{}にパラメータを取得
$CGI::POST_MAX = 2048 * 1024;		# postは最大2Mbytesまで
my $cgi = new CGI ;
%in = $cgi->Vars ;					# $in{''}はすべて初期化される
$recLog .= "=>strt =>sashizu:".$in{'sashizu'}." " ;
if ( !defined $in{'sashizu'} ){		# sashizuなし → 抜ける
	goto exit_prog ;
}
# 抽出引数の一覧(dbg用)
foreach (keys( %in )){
	$dbg_msg .= "(137)key(".$_.")=".decode('utf8',$in{$_})."<br>\n" ;
}

# 各DB、bomDiff.tmpファイル(csv形式2次元)からデータを取得 → $db_Data にcsv形式で出力
$t1 = gethrtime() ;
my $db_Data = &get_bomDiff($in{'sashizu'}) ;
if ($db_Data eq "err"){
	$recLog .= "failed to get bomDiff.tmp :".$ret1." " ;
	$ret1 = "bomDiff.tmpからの取得に失敗しました。<br>".$ret1 ;
	&error($ret1) ;
	goto exit_prog ;
}
$recLog .= "=>done get_bomDiff:".int((gethrtime() - $t1)/1000000)."msec " ;  

# **** 入力引数により処理分岐 ****
$t1 = gethrtime() ;
if( defined $in{'chgplant'} ){					# **** 生産場所変更 ****
	$recLog .= "=> chg plant:".int((gethrtime() - $t1)/1000000)."msec " ; 
	if (!$in{'plantName'}){$in{'plantName'} = "0" ;}
	$in{'plantName'} =~ s/\s|　//g ;	# 全/半角スペース取る
	$in{'plantName'} = decode('utf8',$in{'plantName'}) ;
	$dbg_msg .= "change plant:".$in{'plantName'}."<br>\n" ; 
	# egproBOM を変更
	if (&upd_egproBOM( $in{'sashizu'}, $typeID, $in{'plantName'} ) eq "err"){
		$recLog .= "=>failed for changing plant of egproBOM DB. :".$ret1 ; 
		$ret1 = "SMT基数・生産場所の更新に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# 親ウィンドウ/自画面を更新・閉じる
	$win_man_js = <<"HTML" ;
	<script type="text/javascript">
		window.onload = function(){
			window.opener.location.reload(false);		// 親ウィンドウをキャッシュなしリロード
//			open('about:blank', '_self').close();		// 自ウィンドウを閉じる
		}
	</script>
HTML
	$recLog .= "success changing plnat : ".$in{'sashizu'}." / ".$in{'plantName'}.":".int((gethrtime() - $t1)/1000000)."msec " ; 

}elsif ( defined $in{'exempt'} ){				# **** 除外部品に追加 ****
	$recLog .= "=> reg exempt:".int((gethrtime() - $t1)/1000000)."msec " ; 
	foreach ( keys %in ){
		if ( $in{ $_ } eq "partNo" ){ $in{'partNo'} .= $_."," ; }	# 複数部品コードをcsv化
	}
	$in{'partNo'} =~ s/,$// ;					# 末尾の","を取る
	$dbg_msg .= "(183)exempt parts:".$in{'partNo'}."<br>\n" ;
	if ( !$in{'partNo'} ){
		$recLog .= "=>no entry. " ; 
		&error( "除外登録する部品が選択されていません。<br>" ) ;
		goto exit_prog ;
	}
	# exepPartへの登録
	if (&reg_exempt($in{'partNo'}) eq "err"){
		$recLog .= "=>failed for adding item(s) to exempt DB.\n".$ret1."\n" ; 
		$ret1 = "除外リストへの登録に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# bossBOM,egproBOM DBから除外部品を削除(copy_BOSS.cgi実行の代わり)
	if (&remv_BOM($in{'partNo'}) eq "err"){ 
		$recLog .= "=>failed for removal item(s) from BOM DB.\n".$ret1."\n" ; 
		$ret1 = "BOMからの削除に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# 親ウィンドウを更新(更新後のbossBOM,egproBOMでbomDiff.tmpも数秒で更新)
	$win_man_js = <<"HTML";
	<script type="text/javascript">
		window.onload = function(){
			window.opener.location.reload();			// 親ウィンドウをリロード
//			open('about:blank', '_self').close();		// 自ウィンドウを閉じる
		}
	</script>
HTML
	# 自画面データ($db_Data)から除外部品($in{'partNo'})を削除
	&remv_Diff() ;
	$recLog .= "=>done exempt added and update bomDiff.tmp".$in{'partNo'}." :".int((gethrtime() - $t1)/1000000)."msec " ;  
} 
# 差分ステータスを抽出
$t1 = gethrtime() ;
$in{'sts'} = &chk_sts($db_Data) ;
$recLog .= "=>done chk_sts:".int((gethrtime() - $t1)/1000000)."msec " ;  
# <table>の中身を生成
$t1 = gethrtime() ;
my $html_cont = &make_html($db_Data) ;
$recLog .= "=>done make_html:".int((gethrtime() - $t1)/1000000)."msec " ;  
# htmlの戻り値で画面描画
$t1 = gethrtime() ;
if ( $dbg != 1 ){
	&drw_scrn($html_cont) ;
}
$recLog .= "=>done drw_scrn:".int((gethrtime() - $t1)/1000000)."msec success." ;
$recLog .= " => ".&dateTime(time)." *** normal end ***" ;
goto exit_prog ;

#********************************************
#                 Sub処理
#********************************************

# ---- bom_Diffからのデータ取得 ----
# 指定された指図の諸元、生産場所、同・差分詳細(bomDiff.tmp)を取得する。
# 引数：指図[0]
# 戻り値：正常時は差分詳細のcsv、グローバル変数で品目、台数、着手日、完了日、生産場所、担当ライン
#		エラー時は"err"、詳細は$ret1
sub get_bomDiff(){
	$dbg_msg .= "(243)strt get_bomDiff() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my @db_ary ;
	my ($db, $st, $rv, $sql, $ary_ref) ;
	$sashizu = $_[0] ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 1}) or die($DBI::errstr) ;
		# liveOrderテーブルから指図をキーに指図情報を取得
		$sql = "SELECT typeID,orderQty,start_date,finish_date,LINE FROM ".$db_liveOrder_sub." " ;
		$sql .= "WHERE `orderNumber` LIKE '".$sashizu."' ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchrow_arrayref ;
		$dbg_msg .= "(256)'".$db_liveOrder_sub."'(".$sashizu.") res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
		( $typeID, $qty, $sttDate, $finDate, $line ) = @$ary_ref ;
		# egproBOMテーブルから品目をキーに生産場所情報を取得
		$sql = "SELECT plant FROM ".$db_egproBOM." " ;
		$sql .= "WHERE `typeID` LIKE '".$typeID."' ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$rv = $st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchrow_arrayref ;
		$plant = @$ary_ref[0] ;		# 生産場所(社内/協力会社)
		$st->finish() ;
		$db->disconnect ;
		$dbg_msg .= "(267)'".$db_egproBOM."' res. ".int((gethrtime() - $t0)/1000000)."msec #:".$rv."recs=> " ;
	};
	# DBでエラーがある場合の処理
	if ($@){
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "'".$db_liveOrder_sub."' or '".$db_egproBOM."' error : \nsql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	# 差分ファイル(bomDiff.tmp)から指定指図のbomを取得、戻り値として戻す
	# [0]:指図、[1]:部品コード、[2]:boss所要数、[3]:egpro所要数、[4]egpro登録日時(LF)
	$ary_ref = "" ;
	if (open (FH, "<", "./bomDiff.tmp")){
		$ret1 = 0 ;
		$in{'sts'} = undef ;			# 差分チェック初期値
		while (<FH>){
			my @diff = split(/,/, $_) ;
			if ( $diff[0] eq $sashizu ){
				$ary_ref .= $diff[1].",".$diff[2].",".$diff[3]."\n" ;		# 取得したcsvの行末はLF
				if ( $diff[3] ne 'NULL' ){ $regDate = $diff[4] ; }			# egproに有効値があれば登録日時を取得
				$regDate =~ s/\r|\n//g ;
				$ret1 = $ret1 + 1 ;
			}
		}
		close FH ;
	}else{
		$ret1 = "tmp File Error:".$! ;
		close FH;
		return "err" ;
	}
	close FH ;
	$dbg_msg .= "(297)exit get_bomDiff ".int((gethrtime() - $t0)/1000000)."msec #:".$ret1."items => <br>\n" ;
	return $ary_ref ;
}

# ---- 差分ステータス抽出 ----
# 差分チェックデータから除外部品を除いた差分ファイルからstsを抽出する。
# 引数：DBから取得したcsvデータ
# [0]:部品コード、[1]:boss所要数、[2]:egpro所要数
# 戻り値：なし(グローバル変数で$in{'sts'})
sub chk_sts(){
	$dbg_msg .= "(307)strt chk_sts() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my $sts = undef ;
	foreach ( split ( /\n/, $_[0] ) ){
#		$dbg_msg .= "<br>(311)".$_."\n" ;
		my @diff = split( /,/, $_ ) ;
		if ( !defined( $sts ) ){		# 1レコードの差異を初期値とする
			if ( $diff[1] eq $diff[2] ){
				$sts = "0" ;			# 差異なしに初期設定(NULL,NULLはない)
			}elsif ( $diff[2] ne 'NULL' ){
				$sts = "egp" ;			# 差異ありに初期設定
			}							# $diff[2]='NULL'の時のみ$sts='undef'が保存
		}elsif ( $diff[1] ne $diff[2] ){
			$sts = "egp" ;
		}
		$ret1 = $ret1 + 1 ;
	}
	if ( $ret1 == 0 ){ $sts = "na" ; }				# レコードが1件も無し:bossBOMなし
	if ( !defined( $sts ) ){ $sts = "noegp" ; }	# 最後までundefの場合は、egproBOMなし
	my $today = &dateTime(time) ;
	$today =~ s/^(\d{4}-\d{2}-\d{2}).+/$1/ ;
#	$today = "2021-06-24" ;
	$regDate =~ /^(\d{4}-\d{2}-\d{2}).+/ ;
	if ( $sts eq "0" && $today eq $1 ){ $sts = "upd" ; }	# 差異なしで登録日が今日
	$dbg_msg .= "(331)exit chk_sts ".int((gethrtime() - $t0)/1000000)."msec sts:".$sts."=> <br>\n" ;
	return $sts ;
}

# ---- html文の生成 ----
# 取得された差分チェックデータを<table>化する。
# 引数：bomDiff.tmpから取得したcsvデータ
#		[0]:部品コード、[1]:boss所要数、[2]:egpro所要数
# 戻り値：正常時はhtmlソーステキスト
#		エラー時は"err"、詳細は$ret1
sub make_html(){
	$dbg_msg .= "(342)strt make_html() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;
	my $cont = "" ;
	# 中身が"空"の場合の注意表示
	if (!$_[0]){
		$cont .= "\t\t<tr>\n" ;
		$cont .= "\t\t\t<td colspan=\"4\">実装対象の部品が発令されていません。（または適用除外品）</td>\n" ;
		$cont .= "\t\t</tr>\n" ;
	}else{
		foreach ( split( /\n/, $_[0] ) ){
			my @diff = split (/,/, $_ ) ;
			if ($ret1 % 2){
				$cont .= "\t\t<tr class=\"even\">\n" ;
			}else{
				$cont .= "\t\t<tr class=\"odd\">\n" ;
			}
			if (! $diff[1] || $diff[1] eq 'NULL' ){$diff[1] = "" ;}		# bossBOM基数
			if (! $diff[2] || $diff[2] eq 'NULL' ){$diff[2] = "" ;}		# egpro基数
			if ( $diff[2] eq "" || ($diff[1] > $diff[2]) ){				# EGproに無いか少ない
				$cont .= "\t\t\t<td><font color = \"ff4040\"><b>".$diff[0]."</b></font></td>" ;	# 部品コード
				$cont .= "<td><b>".$diff[1]."</b></td>" ;				# BOSS基数
				$cont .= "<td><font color = \"ff4040\"><b>".$diff[2]."</b></font></td>" ;	# EGpro基数
			}elsif ( $diff[1] eq "" || ($diff[1] < $diff[2]) ){			# BOSSに無いか少ない
				$cont .= "\t\t\t<td><font color = \"4040ff\"><b>".$diff[0]."</b></font></td>" ;	# 部品コード
				$cont .= "<td><b>".$diff[1]."</b></td>" ;				# BOSS基数
				$cont .= "<td><font color = \"4040ff\"><b>".$diff[2]."</b></font></td>" ;	# EGpro基数
			}else{
				$cont .= "\t\t\t<td>".$diff[0]."</td><td>".$diff[1]."</td><td>".$diff[2]."</td>" ;
			}
			# 除外登録のチェックボックス
			$cont .= "<td><input type=\"checkbox\" name=\"".$diff[0]."\" value=\"partNo\"></td>\n" ;
			$cont .= "\t\t</tr>\n" ;
			$ret1 = $ret1 + 1 ;
		}
	# 表下段のボタン
	$cont .= <<"HTML";
		<tr>
			<td colspan="2" class="button" style="text-align: left;">
				<input type="button" value="csv出力" onClick="dlFile('sashizu')" id="dnload" style="background-color:#d0ffff;"/>
			</td>
			<td colspan="2" class="button" style="text-align: right;">
				<input type="submit" name="exempt" value="除外登録" style="background-color:#d0ffff;"/>
			</td>
		</tr>
HTML
	}
	$dbg_msg .= "(388)exit make_html ".int((gethrtime() - $t0)/1000000)."msec => <br>\n" ;
	return $cont ;
}

# ---- egproBOMの更新 ----
# 引数で指定された指図のbossBOMの品目・部品・基数と生産場所を元にegproテーブルを更新する。
# 引数：指図[0]、品目コード[1]、プラント名[2]
# 戻り値：正常時:登録件数
#		エラー時:"err"、$ret1:エラー詳細
sub upd_egproBOM(){
	$dbg_msg .= "(398)strt upd_egproBOM() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;	
	($sashizu, $typeID, $plant ) = ( $_[0], $_[1], $_[2] ) ;
	my ($db, $st, $ary_ref, $sql) ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 指図(品目)のBOMをbossBOM DB から取得
		$sql = "SELECT `typeID`,`partNo`,`qty` FROM `".$db_bossBOM."` WHERE `orderNumber` LIKE '".$sashizu."' ;" ;
		$dbg_msg .= "(406)".$sql."<br>\n" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;		# [0]:品目C,[1]:部品C,[2]:基数,
		if (!@$ary_ref){
			$ret1 = "empty ".$db_bossBOM." sashizu:".$sashizu."\n" ;
			return "err" ;
		}
		$dbg_msg .= "(414)'".$db_bossBOM."'(".$sashizu.") SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
		# 既存egproBOM DBの当該品目を削除
		$sql = "DELETE FROM `".$db_egproBOM."` WHERE `typeID` LIKE '".$typeID."' ;" ;
		$dbg_msg .= "(417)".$sql."<br>\n" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		$dbg_msg .= "(421)'".$db_egproBOM."'(".$typeID.") DELETE res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
		# 指図(品目)のBOMと生産場所をegproBOMに書込む
		if ( $plant eq "社内" ){ $plant = "0" ; }
		$sql = "INSERT INTO ".$db_egproBOM." (typeID,partNo_egpro,qty,plant,regDate) VALUES " ;
		my $nowTime = &dateTime(time) ;
		foreach (@$ary_ref){
#			# bomDiffのbossBOM側基数がNULLまたは"0"のものは書き込まない
#			if ( ! @$_[2] ){ next ; }
			$sql .= "('".$typeID."','".@$_[1]."',".@$_[2].",'".$plant."','".$nowTime."')," ;
			$ret1 = $ret1 + 1 ;
		}
		$sql =~ s/,$/ ;/ ;
		$dbg_msg .= "(433)".$sql."<br>\n" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$st = $db->commit ;
		$dbg_msg .= "(437)'".$db_egproBOM."'(".$sashizu.") INSERT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "egproBOM DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	$dbg_msg .= "(447)exit upd_egproBOM".int((gethrtime() - $t0)/1000000)."msec => " ;
	return $ret1 ;
}

# ---- ECN連携の確認 ----
# ECN DBから、全ECN情報を取得する。
# 引数：なし
# 戻り値：正常時:取得情報のリファレンス
#		エラー時:"err"、$ret1:エラー詳細
sub ecnLink(){
	$dbg_msg .= "(457)strt ecnLink() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	my ($db, $st, $sql, $ary_ref) ;
	eval{
		$db = DBI->connect($db3_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		$sql = "SELECT `ECNid`,`docNo`,`typeID`,`path`,`comm` FROM `".$db_ecn."` WHERE 1 ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$st->execute() or die(DBI::errstr) ;
		$ary_ref = $st->fetchall_arrayref ;
		$st->finish() ;
		$db->disconnect ;
		$dbg_msg .= "(467)'".$db_ecn."'(".$typeID.") SELECT res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "exempt DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	$dbg_msg .= "(476)exit ".int((gethrtime() - $t0)/1000000)."msec => <br>\n" ;
	return $ary_ref ;
}

# ---- 除外リスト登録 ----
# 指定された部品コードを除外リストDBに登録する。
# 追番を除いて同一コードに上書き。
# 引数：(部品コード)のcsv
# 戻り値：正常時:登録件数
#		エラー時:"err"、$ret1:エラー詳細
sub reg_exempt(){
	$dbg_msg .= "(487)strt reg_exempt() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;	
	my ($db, $st, $rv, $sql) ;
	my $partNo = $_[0] ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		$sql = "DELETE FROM `".$db_exempt."` WHERE `partNo` LIKE ? ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
#		$dbg_msg .= "(495)".$sql."<br>\n" ;
		# 全追番も含めてプレースホルダで削除
		foreach (split (",", $partNo)){
			if ($_ =~ /^(\d{6}|\d{10})[A-Za-z]?$/) {	# 部品コード:数字6または10ケタ+英字0-1ケタ
				$st->bind_param( 1, $1."%" ) ;			# プレースホルダに " % " を使う場合
				$rv = $st->execute() or die(DBI::errstr) ;		# 戻り値：レコード数(0:0E0)
				if ($rv ne "0E0"){ $ret1 = $ret1 + $rv ; }
			}
		}
		$st = $db->commit ;
		$dbg_msg .= "(505)'".$db_exempt."' DELETE res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
#		if ( $dbg > 0 ){ $dbg_msg .= "(506)".$ret1."recs. deleted.<br>\n" ; }
		# バルクインサートで追加
		$ret1 = 0 ;
		$sql = "INSERT INTO `".$db_exempt."` (`partNo`) VALUES " ;
		$partNo =~ s/,/') , ('/g ;
		$sql .= "('".$partNo."') ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		$rv = $st->execute() or die(DBI::errstr) ;
		if ($rv ne "0E0"){ $ret1 = $rv ; }
#		$dbg_msg .= "(515)".$sql."//".$ret1."recs. insereted.<br>\n" ;
		$st = $db->commit ;
		$dbg_msg .= "(517)'".$db_exempt."' INSERT resp2. ".int((gethrtime() - $t0)/1000000)."msec => " ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "exempt DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	$dbg_msg .= "(527)exit. ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ret1 ;
}

# ---- bossBOM,egproBOM DBから削除 ----
# 指定された部品コードをbossBOM,egproBOM DBから削除する。
# 引数：(部品コード)のcsv
# 戻り値：正常時:削除件数
#		エラー時:"err"、$ret1:エラー詳細
sub remv_BOM(){
	$dbg_msg .= "(537)strt remv_BOM() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	$ret1 = 0 ;	
	my ($db, $st, $sql) ;
	my $partNo = $_[0] ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 構成品目コード(部品コード)でbossDBから削除
		$sql = "DELETE FROM `".$db_bossBOM."` WHERE `partNo` LIKE ? ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
#		$dbg_msg .= "(546)".$sql."/" ;
		foreach (split (/,/, $partNo)){
#			$dbg_msg .= $_."/" ;
			$st->execute($_) or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		$dbg_msg .= "(552)'".$db_bossBOM."' DELETE res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
#		$dbg_msg .= "<br>\n" ;
		# 構成品目コード(部品コード)でegproDBから削除
		$sql = "DELETE FROM `".$db_egproBOM."` WHERE `partNo_egpro` LIKE ? ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
#		$dbg_msg .= "(557)".$sql."/" ;
		foreach (split (/,/, $partNo)){
#			$dbg_msg .= $_."/" ;
			$st->execute($_) or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		$dbg_msg .= "(563)'".$db_egproBOM."' DELETE res. ".int((gethrtime() - $t0)/1000000)."msec => " ;
#		$dbg_msg .= "<br>\n" ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 = "bomDiff DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	$dbg_msg .= "(574)exit remv_BOM ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
	return $ret1 ;
}

# ---- 差分詳細データ($db_Data) ----
# $db_Dataから、$in{'partNo'}のある行を除く
# 引数：(部品コード)のcsv、(グローバル変数で$db_Data)
# 戻り値：なし。
sub remv_Diff(){
	$dbg_msg .= "(583)strt get_bomDiff() ".int((gethrtime() - $t0)/1000000)."msec => " ;
	my $db_Data2 = "" ;
	my $exepParts = $_[0] ;
	$exepParts =~ s/,/,|/g ;		# csvのデリミタ","も含め、テンプレートの区切りとする
	$dbg_msg .= "(587)".$exepParts."=> " ;
	foreach my $eachLine ( split (/\n/, $db_Data ) ){
		if ( $eachLine =~ /$exepParts/ ){
			$dbg_msg .= "(590)".$eachLine."<br>\n" ;
			next ;					# 除外部品の行なら次
		}
		$db_Data2 .= $eachLine."\n" ;
	}
	$db_Data = $db_Data2 ;
	$dbg_msg .= "(596)exit remv_Diff ".int((gethrtime() - $t0)/1000000)."msec => <br>\n" ;
	return ;
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
	$dbg_msg .= "(613)strt drw_scrn() ".int((gethrtime() - $t0)/1000000)."msec => <br>" ;
	my $html = <<"HTML" ;
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
		td {text-align: center; border:solid 1px #ffcdcd; border-collapse: collapse;}
		td.left {text-align: left;}
		td.right {text-align: right;}
		td.button {padding:5px; border-left:hidden; border-bottom:hidden; border-right:hidden;}
		/* FixMidashiの設定 */
		div.scroll_div {overflow: auto;}
	</style>
</head>
<body style="font-family: sans-serif; margin: 30px;" onLoad="FixedMidashi.create();">
HTML
	$html .= $win_man_js."\n" ;
	if ( $dbg > 0 ){
		$html .= $dbg_msg."\n" ; 
		$dbg_msg = "" ;
	}
	$html .= "<h2>【差分チェックシステム】（指図毎詳細）</h2>\n" ;
	$html .= "<hr width=\"560\" size=\"5\" color=\"d0d0ff\" align=\"left\">\n" ;
	# 指図関連情報の表示
	$html .= "<form name=\"form1\" method=\"get\" action=\"".$self_scrn."\">\n" ;
	$html .= "\t指図：<b><span id=\"sashizu\">".$in{'sashizu'}."</span></b>" ;
	$html .= "　担当：<b><span id=\"line\">".$line."</span></b>" ;
	$html .= "　品目：<b><span id=\"typeID\">".$typeID."</span></b>" ;
	$html .= "　発令台数：<b><span id=\"qty\">".$qty."</span></b><br>\n" ;
	$html .= "\t製造開始日：<b><span id=\"sttDate\">".$sttDate."</span></b>" ;
	$html .= "　完成予定日：<b><span id=\"finDate\">".$finDate."</span></b><br>\n" ;
	$html .= "\t生産場所：<b><span>" ;
	if (!defined $plant){
		$html .= "未登録</span></b>" ;
	}elsif ($plant eq "0"){
		$html .= "社内</span></b>" ;
	}else{
		$html .= decode('utf8',$plant)."</span></b>" ;
	}
	$html .= "　<input type=\"button\" onClick=\"chgPlant();\" id=\"chgBtn\" value=\"変更\" style=\"background-color:#ffd0d0;\"><br>\n" ;
	$html .= "\t<hr width=\"560\" size=\"1\" color=\"d0d0ff\" align=\"left\">\n" ;
	# 差分表示
	$html .= "\t差分：" ;
	if ($in{'sts'} eq "egp" || $in{'sts'} eq "bos"){	# 不一致：赤
		$html .= "<img src=\"./cgiData/red.png\">" ;
	}elsif ($in{'sts'} eq "upd"){					# 登録今日：青
		$html .= "<img src=\"./cgiData/blu.png\">" ;
	}elsif ($in{'sts'} eq "0"){						# 一致：緑
		$html .= "<img src=\"./cgiData/grn.png\">" ;
	}elsif ($in{'sts'} eq "noegp"){					# 未登録：白
		$html .= "<img src=\"./cgiData/wht.png\">" ;
	}elsif ($in{'sts'} eq "na"){					# 引当部品なし：N.A.
		$html .= "N.A." ;
	}else{											# これ以外
		$html .= "N.A.(".$in{'sts'}.")" ;
	}
	$html .= "（EGpro登録日時：" ;
	if (!$regDate || $regDate eq "NULL" ){
		$html .= "N.A.）\n" ;
	}else{
		$html .= "<b>".$regDate."</b>）\n" ;
	}
	# 差分のみ表示チェックボックス
	$html .= "\t差分のみ<input type=\"checkbox\" onClick=\"selSabun2('diff');\" id=\"diff\" ><br>\n" ;
	# 不一致のときECN連携表示
	if ( $in{'sts'} =~ /bos|egp/ ){ 
		$html .= "\t<div style=\"float: left; padding-left: 0px;\">\n\t\tECN：\n\t</div>\n" ;
		my $ecn = &ecnLink() ;
		if ($ecn eq "err"){
			$html .= "ECN連携に失敗しました。<br>".$ret1."\n" ;
		}else{
			$typeID =~ /([A-Z\-]{3,4}\d{4})/ ;						# "UR-nnnn"を抽出
			my $keytypeID = $1 ;
			my $ecn_html = "" ;
			foreach (@$ecn){
				if ( @$_[2] =~ /($keytypeID[0-9\-X]{0,4})/ ){		# 対象品目群の該当UR-nnnnm-xyも含め抽出
					# 該当品目抽出
					$ecn_html .= "\t\t".@$_[0]." / ".$1." / ".@$_[1] ;
					if (!@$_[4]){
						$ecn_html .= "<br>\n" ;
					}else{
						$ecn_html .= " (".decode('utf8',@$_[4]).")<br>\n" ;
					}
				}
			}
			if (!$ecn_html){
				$html .= "\t未発行\n" ;
			}else{
				$html .= "\t<div style=\"float: left; background-color: #fcfcff;\">\n".$ecn_html."\t</div>\n" ;
			}
		}
	}
	# 差分詳細一覧表の表示
	$html .= <<"HEAD" ;
	<div class="scroll_div" style="clear: both;">
	<table border="0" id="sashizu_t" style="margin-left: 0px; padding: 5px; background-color: #ffffff;" class="fixedHead" _fixedhead="rows:1; cols:0;">
		<thead>
		<tr>
			<th style="width: 150px;">部品コード</th>
			<th style="width: 120px;">BOSS基数</th>
			<th style="width: 120px;">SMT基数</th>
			<th style="width: 100px;">除外登録</th>
		</tr>
		</thead>
		<tbody>
HEAD
	$html .= $_[0] ;
	$html .= <<"FOOT" ;
		</tbody>
	</table>
	<input type="hidden" name="sashizu" value="$in{'sashizu'}">
	</div>
	</form>
</body>
</html>
FOOT
	print $html;
	$dbg_msg .= "(747)exit drw_scrn ".int((gethrtime() - $t0)/1000000)."msec <br>\n" ;
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
# ---- Logの出力 ----
# ログテキストをファイル出力。
open (FH, ">>", $logFile) ;
	print FH $recLog."\r\n" ;
close FH ;
chmod 0666, $logFile ;
