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
use XML::RSS;

# debug
use Data::Dumper;

exit(main());

sub main()
{
	my $obj = Template::Extract->new;
	
	open(TEMPLATE, "<", "./template.txt") || die('cannont open file.');
	my $template = join('', <TEMPLATE>);
	
	my $proxy = LWP::UserAgent->new;
	$proxy->timeout(10);
	$proxy->agent('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0');
	my $req = HTTP::Request->new(GET => 'http://www.tsuyama-ct.ac.jp/dekigoto.htm');
	my $res = $proxy->request($req);
	
	#my $ext = $obj->extract($template, decode('Shift_JIS', $res->content));
	my $ext = $obj->extract($template, decode('Shift_JIS', $res->content));
	
	print "Content-type: application/xml;\n\n";
	#print $res->header("Last-Modified")."\n";
	
	my $rss = new XML::RSS (version => '2.0');
	$rss->channel(
		'title'			=> '津山高専 最近のできごと',
		'link'			=> 'http://www.tsuyama-ct.ac.jp/',
		'language'		=> 'ja',
		'description'	=> '津山工業高等専門学校の最近のできごとの非公式RSSフィードです',
		'copyright'		=> 'Copyright (C) 1997-2013, Tsuyama National College of Technology',
		'pubDate'		=> $res->header("Last-Modified"),
		'webMaster'		=> $ext->{'webMaster'},
	);
	
	foreach my $item (@{$ext->{'item'}}){
		# 本文の調理
		$item->{'description'} =~ s/<img[^>]*>\r?\n//gi;
		$item->{'description'} =~ s/<br clear="all">\r?\n/<br>\n/gi;
		$item->{'description'} =~ s/　(.+)\r?\n/$1/gi;
		# メディア情報を付加させたい
		my $image = 'http://www.tsuyama-ct.ac.jp/'.$item->{'image'};
		$req = HTTP::Request->new(HEAD => $image);
		$res = $proxy->request($req);
		# RSS追加
		$rss->add_item(
			'title'			=> $item->{'title'},
			'link'			=> 'http://www.tsuyama-ct.ac.jp/dekigoto.htm#'.$item->{'id'},
			'description'	=> $item->{'description'},
			'enclosure'		=> {
				'url'			=> $image,
				'length'		=> $res->header("Content-Length"),
				'type'			=> $res->header("Content-Type"),
			},
		);
	}
	
	print $rss->as_string;
	
	#print Dumper $ext;
	return 0;
}
