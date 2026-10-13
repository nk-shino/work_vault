#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;
use DBI;
use Encode;
use Data::Dumper;
use Time::HR ;						# インターバル高精度タイマ
binmode STDOUT, ':utf8';			#Apache error log対策

#ODBC関連接続情報
my $db_name = "EGPro" ;				# DB:EGProKOHDEN-Planに対するDSN
#$db_name = "EGPro-MST" ;			# DB:EGProKOHDEN-MSTに対するDSN
my $db_ODBCserver = "dbi:ODBC:".$db_name;
my $db_ODBCuser = "sqluser";
my $db_ODBCpasswd = "Pfseg001";
my $db_ODBCview ;
my ($sql,$db,$st,$ary_ref,$ret1) ;
# テーブル名一覧の取得
#$sql = "SELECT * FROM sys.objects WHERE type ='U' ;";

# 各テーブル情報の取得(予想レコード数に注意)
$db_ODBCview = "T_部品配列表";
#$db_ODBCview = "T_計画データ";
#$db_ODBCview = "T_計画データLog";
#$db_ODBCview = "T_計画データ_Sub";
#$db_ODBCview = "D_ジョブ実行";
#$db_ODBCview = "D_ジョブ実行Log";
#$db_ODBCview = "D_指図実行";
#$db_ODBCview = "D_指図実行Log";
#$db_ODBCview = "T_生産連携";
#$db_ODBCview = "W_在庫情報";
#$db_ODBCview = "W_作業工数";
#$db_ODBCview = "W_作業実績";
#$db_ODBCview = "[D_ProductPlanNow]";	# 中身なし
#$db_ODBCview = "[D_ジョブ実行Tmp]";		# 中身なし
#$db_ODBCview = "[T_生産連携NPM]";		# 中身なし

my $t0 = gethrtime() ;
my $ct = 0 ;
eval{
	$db = DBI->connect($db_ODBCserver, $db_ODBCuser, $db_ODBCpasswd, {PrintError => 0, AutoCommit => 1}) or die(DBI::errstr);
	$db->{LongTruncOk}=1;
	$db->{LongReadLen}=200000;
print "46:".(int((gethrtime()-$t0)/1000000)."msec\n") ;
#$sql = "SELECT * FROM sys.columns WHERE object_id = (SELECT object_id FROM sys.tables WHERE name = '".$db_ODBCview."' ) ;";		# カラム名
	#$st = $db->prepare($sql) or die(DBI::errstr);
	#$st->execute() or die(DBI::errstr);
	#$ary_ref = $st->fetchall_arrayref;	# fetchrow:@$ary_ref[n],fetchall:@$ary_ref[n]->[m]
#&writeFile($db_name."_tbl.csv", $ary_ref ) ;
#&writeFile($db_ODBCview."_col.csv", $ary_ref ) ;
#	$sql = "SELECT * FROM ".$db_ODBCview." WHERE 品目コード LIKE 'UR-39721_P1' ;";		# 中身
# 	$sql = "SELECT * FROM ".$db_ODBCview." ;";		# 全中身
	$sql = "SELECT 製品,管理コード,品番1,員数,登録日時 FROM ".$db_ODBCview." ORDER BY 登録日時 DESC, 製品 ASC, 品番1 ASC ;" ;
#	$sql = "SELECT 製品,管理コード,品番1,員数,登録日時 FROM ".$db_ODBCview." ;" ;
#	$sql = "SELECT 製品,管理コード,登録日時 FROM ".$db_ODBCview." ORDER BY 登録日時 DESC ;" ;
#	$sql = "SELECT 製品,管理コード,登録日時 FROM ".$db_ODBCview." ;" ;
#	$sql = "SELECT * FROM ".$db_ODBCview." ;" ;
	$st = $db->prepare($sql) or die(DBI::errstr);
print "58:".(int((gethrtime()-$t0)/1000000)."msec\n") ;
	$st->execute() or die(DBI::errstr);		# 約200msec@DISTINCTなし124万件、550～660msecDISTINCTあり8万件。
print "60:".(int((gethrtime()-$t0)/1000000)."msec\n") ;
	$ary_ref = $st->fetchall_arrayref;		# 約3～3.5秒@124万件、300～600msecDISTINCTあり8万件。
#print "62:".(int((gethrtime()-$t0)/1000000)."msec\n") ;
#print "66:".(int((gethrtime()-$t0)/1000000)."msec\n") ;
my ($typeID, $lastUpd, $partNo, $qty) ; 
my %typeList ;
# 品目コードをキーとして、登録日時昇順で上書き → 最後の上書きが最新
foreach (@$ary_ref){						# 124万件で3000msec、8万件で50msec
#foreach (@{$st->fetchall_arrayref}){						# 124万件で3000msec、8万件で50msec
	$typeID = @$_[0] ;
	$partNo = @$_[2] ;
	$qty = @$_[3] ;
	$lastUpd = @$_[4] ;		# 登録日時を取得
	$lastUpd =~ s/^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).+/$1/ ;
	if (!defined($typeList{($typeID.",".$partNo)})){	# 品目コード・部品コードが %typeList にあるか？
		# 全く無し、初出(=最新)で追加、面取り数計算
		# ( $typeList{(品目コード),(部品コード)} = [(登録日時),(員数)] )
		$typeList{($typeID."_".$partNo)} = [$lastUpd , $qty] ;
	}else{
		# 有り、先頭レコードの登録日時と同じなら員数を累計加算
		if ($typeList{($typeID."_".$partNo)} -> [0] == $lastUpd){
			# 登録日時と同じ、面取り数計算
			$typeList{($typeID."_".$partNo)} = [$lastUpd , $typeList{($typeID."_".$partNo)} -> [1] + $qty ] ;
		}else{
			# 登録日時と違う
		}
	}
	$ct = $ct + 1 ;
#print "101:".Dumper(%typeList)."\n" ;	
#last ;
}
print "103:".(int((gethrtime()-$t0)/1000000)."msec, COUNT=".$ct."\n") ;
#print "104:".Dumper(%typeList)."\n" ;	
	$st->finish;
	$db->disconnect;
};
if ($@){
	if (defined($db)){$db->disconnect();}
	$ret1 = $sql."//".$@."\n";
	print "(34)".$ret1."\n";
}



# ---- hash内が配列をカレントディレクトリに書き出し ----
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
		print $out_text ;
	}
	close OUT ;
}

end_prog:
