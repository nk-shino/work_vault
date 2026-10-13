#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;
use DBI;
use Encode;
use Data::Dumper;
binmode STDOUT, ':utf8';			#Apache error log対策

my $boss_org = "/mnt/nksvasp23_SMT_RCV/" ;
my $boss_dst = "/mnt/nksvasp23_SMT_RCV2/" ;
my $fileName = "IFID142.csv" ;

if ( -f $boss_org.$fileName."-2" ){
	system "cp -f -a ".$boss_org.$fileName." ".$boss_dst.$fileName."_2" ;
	system "chmod 666 ".$boss_dst.$fileName."_2" ;
print "(19)".$!."\n" ; # ない時：No such file or directory
print "(20)".$@."\n" ;
}


my @f_sts = stat $boss_dst.$fileName."_2" ;
print localtime($f_sts[9])."\n" ;