#!/usr/bin/perl

# default
use strict;
use warnings;
use utf8;

# lib
use lib './lib';
use Template::Extract;
use LWP::UserAgent;
use Encode;
use XML::RSS::LibXML;
use XML::Simple;

# debug
use Data::Dumper;
use CGI::Carp qw(fatalsToBrowser);

exit(main());

sub main()
{
	
	my $rss = XML::RSS::LibXML->new;
	$rss->parsefile("dekigoto.rdf");
#	my $xml = XML::Simple->new;
#	my $a = $xml->XMLin('dekigoto.rdf');
	
	print "Content-type: text/plain\n\n";
	print Dumper $rss;
	
	return 0;
}
