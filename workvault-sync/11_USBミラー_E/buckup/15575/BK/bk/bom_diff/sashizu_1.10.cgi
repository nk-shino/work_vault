#!/usr/bin/perl -w

#**********************************************************
# このプログラムは、index.cgiで指図が選択されると起動され、
# 当該指図の差分情報詳細を表示する。
#									2021/01/11 J.Igarashi
#**********************************************************

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
my %mentori ;
my $self_scrn = "./sashizu.cgi" ;	# 指図詳細画面
my ($sashizu, $typeID, $qty, $regDate, $line ) ;
my ($sttDate, $finDate) ;

# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60';
my $db_user = 'process_mgt';
my $db_passwd = '7bcsHFk8P7VxRcFD';
my $db_bomDiff = 'bomDiff';
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db_exempt = 'exepPart' ;
my $logFile = './logs/sashizu.log';		# ログファイルの名前
my $data_root = "./cgiData" ;

#********************************************
#          Main処理 ここから
#********************************************
#****************for DEBUG*******************
# print "Content-type:text/html\n\n<!DOCTYPE html>\n<HTML>\n<BODY>\n<meta charset=\"utf-8\" />\n";
my $dbg = 0;	#0:ope 1:dbg...show arguments
#********************************************
# ログファイル開始
if (&recLog("\r\n".&dateTime(time)) eq "err"){
	$ret1 = "<font color=\"ff0000\">ローカルファイル(log)が開けません。<br>処理を終了します。:".$ret1."</font><br>\n";
	&error($ret1);
	goto exit_prog;
}
# cgiから%in{}にパラメータを取得
$CGI::POST_MAX = 2048 * 1024;		# postは最大2Mbytesまで
my $cgi = new CGI;
%in = $cgi->Vars;					# $in{''}はすべて初期化される
&eval_arg();						# cgiからの入力引数の評価

# 抽出引数の一覧(dbg用)
if ($dbg == 1){
	print "Content-type:text/html\n\n<!DOCTYPE html>\n<HTML>\n<BODY>\n<meta charset=\"utf-8\" />\n";
	foreach (keys(%in)){
		print "(61)key(".$_.")=".encode('utf8',$in{$_})."<br>\n";
	}
}
# $in{'mode'} の内容により処理分岐
if (!defined $in{'mode'}){
	# **** 引数ナシで呼び出しエラー ****
	$ret1 = "本画面は直接表示できません。一覧画面から表示してください。<br>" ;
	&error($ret1) ;
	goto exit_prog ;
}elsif ($in{'mode'} eq "exempt"){
	# **** 除外品目追加 ****
	# 除外品 DBに追加
	$in{'partNo'} = join (",", @{$in{'partNo'} }) ;	# csv化
	if (&reg_exempt($in{'partNo'}) eq "err"){
		$ret1 = "除外リストへの登録に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# bomDiff DBから削除
	if (&remv_exempt($in{'partNo'}) eq "err"){ 
		$ret1 = "差分DBからの削除に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# boss_BOM.tsvから削除
	if (&remv_boss_BOM($in{'partNo'}) eq "err"){
		$ret1 = "boss_BOM.tsvからの削除に失敗しました。<br>".$ret1 ;
		&error($ret1) ;
		goto exit_prog ;
	}
	# 親ウィンドウをリロード
	print "Content-type:text/html\n\n<html><body>\n";
	# print "<script type=\"text/javascript\">\n";
	# print "window.onload = function(){\n";
	# print "    window.opener.location.reload();\n";
	# print "    open('about:blank', '_self').close();\n";	# 自ウィンドウを閉じる
	# print "}\n";
	# print "</script>\n</body></html>\n";
}elsif ($in{'mode'} eq "mentori"){
	# **** 面取り数変更 ****
	# unitInfo DBの更新
	# mentori.tsvの更新
}else{
	# 通常画面表示
	print "Content-type:text/html\n\n";
}

# **** 画面(再)表示の処理 ****
# # 面取り数を取得
# if ( &get_mentori() eq "err" ){
	# $ret1 = "面取り数の取得に失敗しました。<br>".$ret1 ;
	# &error($ret1) ;
	# goto exit_prog ;
# }

# データベースからデータを取得
my $db_Data = &getDB($in{'sashizu'}) ;
if ($db_Data eq "err"){
	$ret1 = "指図DBからの取得に失敗しました。<br>".$ret1 ;
	&error($ret1) ;
	goto exit_prog ;
}
# htmlの組立て(DBデータを配列化して渡す)
my $html_cont = &make_html(@$db_Data) ;
# htmlの戻り値で画面描画
&drw_scrn($html_cont) ;

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
		# $mentori{$col[0]} = $col[1] ;
		# $ret1 = $ret1 + 1 ;
	# }
	# return $ret1 ;
# }

# ---- DBからのデータ取得 ----
# 差分チェック結果のbomDiff DBから指定された指図の結果を取得する。
# 引数：指図
# 戻り値：正常時は取得内容のリファレンス
#		エラー時は"err"、詳細は$ret1
sub getDB(){
	$ret1 = "" ;
	my ($db, $st, $sql, $ary_ref) ;
	my $colList = $db_liveOrder_sub.".typeID,".$db_liveOrder_sub.".orderNumber,".$db_liveOrder_sub.".orderQty," ;
	$colList .= $db_bomDiff.".subType,".$db_bomDiff.".unitQty,".$db_bomDiff.".eg_unitQty," ;
	$colList .= $db_bomDiff.".eg_regDate,".$db_liveOrder_sub.".start_date,".$db_liveOrder_sub.".finish_date," ;
	$colList .= $db_liveOrder_sub.".LINE " ;
	$sql = "SELECT ".$colList."FROM ".$db_liveOrder_sub." " ;
	$sql .= "LEFT OUTER JOIN ".$db_bomDiff." " ;
	$sql .= "ON ".$db_bomDiff.".orderNumber = ".$db_liveOrder_sub.".orderNumber " ;
	$sql .= "WHERE ".$db_liveOrder_sub.".orderNumber LIKE '".$_[0]."' " ;
	$sql .= "ORDER BY ".$db_bomDiff.".subType ASC ;" ;
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
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "liveOrder_sub or bomDiff DB error : \nsql : ".$sql."\n ==> ".$@ ;
		return "err" ;
	}
	return $ary_ref ;
}
# ---- html文の生成 ----
# 取得された差分チェックされたデータをDBから取得する。
# 引数：DBから取得したデータ(配列)
# 戻り値：正常時はhtmlソーステキスト
#		[(品目コード)[0],(指図)[1],(発令数)[2],(部品コード)[3],(boss所要数)[4],
#		(egpro所要数)[5],egpro登録日時[6],製造開始日[7],完成予定日[8],担当[9]],[],…
#		エラー時は"err"、詳細は$ret1
sub make_html(){
	my $cont = "" ;
	my $row = 0 ;
	$typeID = $_[0]->[0] ;		# 品目コード
	$sashizu = $_[0]->[1] ;		# 指図
	$qty = $_[0]->[2] + 0 ;		# 発令台数
	$sttDate = $_[0]->[7] ;		# 製造開始日
	$finDate = $_[0]->[8] ;		# 完成予定日
	$line = $_[0]->[9] ;		# 担当
	# 1行目の部品が"空"の場合の注意表示
	if (!defined $_[0]->[3]){
		$cont = "\t\t<tr>\n" ;
		$cont .= "\t\t\t<td colspan=\"4\">実装対象の部品がありません。（除外品）</td>\n" ;
		$cont .= "\t\t</tr>\n" ;
		goto end_sub ;
	}
	foreach my $dbData(@_){
		if (defined @$dbData[6]){
			$regDate = @$dbData[6] ;		# egpro登録日時
		}		
		my $partNo =@$dbData[3] ;
		if ( (@$dbData[4] - @$dbData[5]) > 0 ){
			@$dbData[3] = "<b>".@$dbData[3]."</b>" ;	# 品目コード
			@$dbData[4] = "<b>".@$dbData[4]."</b>" ;	# BOSS基数
			@$dbData[5] = "<font color = \"ff4040\"><b>".@$dbData[5]."</b></font>" ;	# EGpro基数
		}elsif ( (@$dbData[4] - @$dbData[5]) < 0 ){
			@$dbData[3] = "<b>".@$dbData[3]."</b>" ;	# 品目コード
			@$dbData[4] = "<b>".@$dbData[4]."</b>" ;	# BOSS基数
			@$dbData[5] = "<font color = \"4040ff\"><b>".@$dbData[5]."</b></font>" ;	# EGpro基数
		}
		if ($row % 2){
			$cont .= "\t\t<tr class=\"even\">\n" ;
		}else{
			$cont .= "\t\t<tr class=\"odd\">\n" ;
		}
		$cont .= "\t\t\t<td>".@$dbData[3]."</td><td>".@$dbData[4]."</td><td>".@$dbData[5]."</td>" ;
		$cont .= "<td><input type=\"checkbox\" name=\"".$partNo."\" value=\"partNo\"></td>\n" ;
		$cont .= "\t\t</tr>\n" ;
		$row = $row + 1 ;
	}
end_sub:
	return $cont ;
}

# ---- 除外リスト登録 ----
# 指定された部品コードを除外リストDBに登録する。
# 追番を除いて同一コードに上書き。
# 引数：(部品コード)のcsv
# 戻り値：正常時:登録件数
#		エラー時:"err"、$ret1:エラー詳細
sub reg_exempt(){
	$ret1 = 0 ;	
	my ($db, $st, $sql) ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 全追番も含めて削除
		foreach (split (",", $_[0])){
			$_ =~ /^(\d{6,10}).*/;
			$sql = "DELETE FROM `".$db_exempt."` WHERE `partNo` LIKE '".$1."%' ;" ;
			$st = $db->prepare($sql) or die(DBI::errstr) ;
			$st->execute() or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		# 最新追番のみ追加
		$sql = "INSERT INTO `".$db_exempt."` (`partNo`) VALUES (?) " ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		foreach (split (",", $_[0])){
			$st->execute($_) or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "exempt DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	return $ret1 ;
}

# ---- 差分 DBから削除 ----
# 指定された部品コードを差分 DBから削除する。
# 引数：(部品コード)のcsv
# 戻り値：正常時:削除件数
#		エラー時:"err"、$ret1:エラー詳細
sub remv_exempt(){
	$ret1 = 0 ;	
	my ($db, $st, $sql) ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		# 構成品目コード(部品コード)でDBから削除
		$sql = "DELETE FROM `".$db_bomDiff."` WHERE `subType` LIKE ? ;" ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		foreach (split (",", $_[0])){
			$st->execute($_) or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "bomDiff DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		return "err" ;
	}
	return $ret1 ;
}

# ---- ファイルの行を削除する ----
# boss_BOM.tsvファイルを読み、指定内容を含む行を削除し上書きする。
# 引数：削除対象部品コード(csv)
# 戻り値：正常時:"0"
#		エラー時: "err"、$ret1:エラー詳細
sub remv_boss_BOM(){
	my $src ;
	my $out_text = "" ;
	$ret1 = 0 ;
	# ファイルの取得(一気読み)
	if (!open(IN, "<", $data_root."/boss_BOM.tsv")){
		$ret1 = "boss_BOM.tsv cannot open(R): ".$! ;
		close IN ;
		return "err" ;
	}else{
		local $/ ;				# 行末記号をlocalでundefに
		$src = <IN> ;			# ファイル内容を一気に変数に取得
	}
	close IN ;
	# 所要データの抽出(必要品目をフィルタリング)
	foreach (split (",", $_[0] )){
		if ($src =~ /(^|\r\n)(.+$_.+\r\n)(.+)/){
#			print "(326)".$2."<br>\n" ;
			$ret1 = $ret1 + 1 ;
		}
		$src =~ s/(^|\r\n).+$_.+\r\n(.+)/$1$2/g ;
	}
	# ファイルの書込み(一気書き)
	if (!open(OUT, ">", $data_root."/boss_BOM.tsv")){
		$ret1 = "boss_BOM.tsv cannot open(W): ".$! ;
		close OUT ;
		return "err" ;
	}else{
		print OUT $src ;		# ファイル内容を一気に書く
	}
	close OUT ;
	return $ret1 ;
}

# ---- Logの出力 ----
# 引数で渡されるメッセージのlogファイル出力。
# バッファリングを解除、書込み禁止して排他処理して更新。
# 引数：メッセージテキスト
# 戻り値：エラーなしはNULL、ありはメッセージを返す。
sub recLog(){
	# if (open (FH, ">>", $logFile)){
		# print FH @_;
		# close FH;
	# }else{
		# $ret1 = "Log File Error:".$!;
		# close FH;
		# return "err";
	# }
	# close FH;
	return 0;
}

# ---- 入力引数の評価 ----
# %in{''}で渡された入力引数を評価。
# 引数：なし(グローバル変数で%in
# 戻り値：なし(グローバル変数で%in)
sub eval_arg(){
	# モードの設定(部品コードの取得とモード設定)
	foreach (keys %in){
		if ($_ eq "sashizu"){			# keyが"sashizu"なら指図
			$in{'mode'} = "sashizu" ;
		}
		if ($in{$_} eq "partNo"){	# 値が"partNo"なら除外部品コード(複数)
			$in{'mode'} = "exempt" ;
			push (@{$in{'partNo'}}, $_)
		}
		if ($_ eq "exempt"){		# keyが"exempt"なら除外部品登録
			$in{'mode'} = "exempt" ;
		}
		if ($_ eq "mentori"){		# keyが"mentori"なら面取り数変更
			$in{'mode'} = "mentori" ;
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
<!DOCTYPE html>
<html lang="jp">
<head>
	<title>SMT実装部品 差分表示プログラム</title>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<link rel="shortcut icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<link rel="icon" href="/img/bom_diff/favicon.ico" type="image/vnd.microsoft.icon" />
	<script type="text/javascript" src="./jquery/fixed_midashi.js"></script>
	<script type="text/javascript">
		// 結果のダウンロード
		function dlFile() {
			var content = ""; 
			var filename = document.getElementById('sashizu').innerText + ".csv";
			const myTbl = document.getElementById('sashizu_t');
			// ファイル内容の生成
			content = content + document.getElementById('sashizu').innerText + "," ;
			content = content + document.getElementById('typeID').innerText + "," ;
			content = content + document.getElementById('qty').innerText + "\\r\\n" ;
			for(var j = 1 ;j <= myTbl.rows.length - 2 ; j++){				//trの数だけループ(表題欄含まず)
				content = content + "'" + myTbl.rows[j].cells[0].innerText + "'," ;	//品目コード
				content = content + myTbl.rows[j].cells[1].innerText + "," ;		//BOSS基数
				content = content + myTbl.rows[j].cells[2].innerText ;				//EGPro基数
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
		td {text-align: center; border:solid 1px #ffcdcd; border-collapse: collapse;}
		td.left {text-align: left;}
		td.right {text-align: right;}
		td.button {padding:5px; border-left:hidden; border-bottom:hidden; border-right:hidden;}
		/* FixMidashiの設定 */
		div.scroll_div {overflow: auto;}
	</style>
</head>
<body style="font-family: sans-serif; margin: 30px;" onLoad="FixedMidashi.create();">
<h2>【差分チェックシステム】（指図毎詳細）</h2>
<hr width="560" size="5" color="d0d0ff" align="left">
HTML
	$html .= "指図：<b><span id=\"sashizu\">".$sashizu."</span></b>" ;
	$html .= "　担当：<b><span id=\"line\">".$line."</span></b>" ;
	$html .= "　品目：<b><span id=\"typeID\">".$typeID."</span></b>" ;
	$html .= "　発令台数：<b><span id=\"qty\">".$qty."</span></b><br>\n" ;
	$html .= "製造開始日：<b><span id=\"sttDate\">".$sttDate."</span></b>" ;
	$html .= "　完成予定日：<b><span id=\"finDate\">".$finDate."</span><br></b>" ;
	$html .= "<hr width=\"560\" size=\"1\" color=\"d0d0ff\" align=\"left\">\n" ;
# 	$html .= "面取り数：<b>".$mentori{$typeID}."</b>" ;
	$html .= "　差分：" ;
		if ($in{'sts'} eq "1"){			# 不一致：赤
			$html .= "<img src=\"./cgiData/red.png\">" ;
		}elsif ($in{'sts'} eq "-1"){	# 登録今日：青
			$html .= "<img src=\"./cgiData/blu.png\">" ;
		}elsif ($in{'sts'} eq "0"){		# 一致：緑
			$html .= "<img src=\"./cgiData/grn.png\">" ;
		}else{							# これ以外
			$html .= "N.A." ;
		}
	$html .= " (登録日時：<b>" ;
	if (defined $regDate){
		$html .= $regDate."</b>)\n" ;
	}else{
		$html .= "未登録</b>)\n" ;
	}
	$html .= "<form name=\"form1\" method=\"get\" action=\"".$self_scrn."\">" ;
	$html .= "<div class=\"scroll_div\">\n" ;
	$html .= "\t<table border=\"0\" id=\"sashizu_t\" style=\"margin-left: 0px; padding: 5px; background-color: #ffffff;\" class=\"fixedHead\" _fixedhead=\"rows:1; cols:0;\">\n" ;	
	$html .= "\t\t<thead>" ;
	$html .= "\t\t\t<tr>\n" ;
	$html .= "\t\t\t<th style=\"width: 150px;\">品目コード</th>\n" ;
	$html .= "\t\t\t<th style=\"width: 120px;\">BOSS基数</th>\n" ;
	$html .= "\t\t\t<th style=\"width: 120px;\">EGPro基数</th>\n" ;
	$html .= "\t\t\t<th style=\"width: 100px;\">除外登録</th>\n" ;
	$html .= "\t\t\t</tr>\n" ;
	$html .= "\t\t</thead>\n" ;
	$html .= "\t\t<tbody>\n" ;
	$html .= $_[0] ;
	$html .= "\t\t<input type=\"hidden\" name=\"sashizu\" value=\"".$sashizu."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"jig\" value=\"".$in{'jig'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"jigID\" value=\"".$in{'jigID'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"wkrID\" value=\"".$in{'wkrID'}."\">\n";
	# $html .= "\t\t<input type=\"hidden\" name=\"line\" value=\"".$in{'line'}."\">\n";
	$html .= <<"HTML";
		<tr>
			<td colspan="2" class="button" style="text-align: left;">
				<input type="button" value="csv出力" onClick="dlFile()" id="dnload" style="background-color:#d0ffff;"/>
			</td>
			<td colspan="2" class="button" style="text-align: right;">
				<input type="submit" name="exempt" value="除外登録" style="background-color:#d0ffff;"/>
			</td>
		</tr>
		</tbody>
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