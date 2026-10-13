#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;
use DBI;
use Encode;
use Data::Dumper;
binmode STDOUT, ':utf8';			#Apache error log対策

my $boss_org = "/mnt/nksvasp23_SMT_RCV2/" ;
my $boss_dst = "/mnt/nksvasp23_SMT_RCV3/" ;

&copy_BOSSfile( $boss_org."IFID142.csv", $boss_dst."IFID142.csv" ) ;

sub copy_BOSSfile(){
	# ファイルを属性付き強制上書きコピー
	if (-e $_[0]){
		system "cp --preserve=timestamps ".$_[0]." ".$_[1] ;
		if ( $! eq "" ){
			system "chmod 666 ".$_[1] ;
			print " copy comp.".$!."\n" ;
		}else{
			print " copy fail...!...".$!."\n" ;
		}
	}else{
		print " copy: src file not exist.\n" ;
	}
}