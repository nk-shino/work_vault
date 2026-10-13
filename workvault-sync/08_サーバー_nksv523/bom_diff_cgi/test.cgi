#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;

my @del_partNo ;
@del_partNo = ('A123456','12345A','123456','123456A','1234567','1234567A','1234567890A','12345678901A','A','1');

foreach (@del_partNo){
	if ($_ =~ /(^[A-Za-z]\d{6}$)/) {
		print "dummy:".$1."\n" ;
	}elsif ($_ =~ /^(\d{6}|\d{10})[A-Za-z]?$/) {
		print "DELETE FROM `db_exempt` WHERE `partNo` LIKE '".$1."%\n" ;
	}
}
