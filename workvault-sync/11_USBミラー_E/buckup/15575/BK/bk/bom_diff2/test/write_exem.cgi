#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;
use DBI;
use Encode;
use Data::Dumper;
binmode STDOUT, ':utf8';			#Apache error log対策

# SQLサーバ・ユーザ・パスワード・関連変数
my $db_source = 'DBI:mysql:orderNumber:172.25.253.60';
my $db_user = 'process_mgt';
my $db_passwd = '7bcsHFk8P7VxRcFD';
my $db_bomDiff = 'bomDiff';
my $db_liveOrder_sub = 'liveOrder_sub' ;
my $db_exempt = 'exepPart' ;
my $ret1 = "" ;
# ファイルの取得(一気読み)
if (!open(IN, "<", "../20210127.csv")){
	$ret1 = $_[0]." cannot open: ".$! ;
	close IN ;
	print $ret1 ;
}else{
	my ($db, $st, $sql) ;
	eval{
		$db = DBI->connect($db_source, $db_user, $db_passwd, {PrintError => 0, AutoCommit => 0}) or die($DBI::errstr) ;
		$sql = "INSERT INTO `".$db_exempt."` (`partNo`) VALUES (?) " ;
		$st = $db->prepare($sql) or die(DBI::errstr) ;
		while (my $src = <IN>){
			$src =~ s/\r\n|\r|\n// ;
			$st->execute($src) or die(DBI::errstr) ;
		}
		$st = $db->commit ;
		$db->disconnect ;
	};
	#DBでエラーがある場合の処理
	if ($@){
		$st = $db->rollback ;
		if(defined($db)){$db->disconnect() ;}
		$ret1 .= "exempt DB error : <br>sql : ".$sql."<br> ==> ".$@ ;
		print $ret1 ;
	}
}
close IN ;
