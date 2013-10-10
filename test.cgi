#!/usr/bin/perl

# default
use strict;
use warnings;
use utf8;

# debug
use Data::Dumper;
use CGI::Carp qw(fatalsToBrowser);

# lib
use lib './lib';
use Template::Extract;
use LWP::UserAgent;
use Encode;
use XML::RSS;
#use XML::FeedPP;

exit(main());

sub main()
{
	# RSS生成対象の取得
	my $proxy = LWP::UserAgent->new;
	$proxy->timeout(5);
	$proxy->agent('Mozilla/5.0 (compatible; TdekigotoRSS/1.0; +https://github.com/windyakin/TdekigotoRSS)');
	my $req = HTTP::Request->new(GET => 'http://www.tsuyama-ct.ac.jp/dekigoto.htm');
	my $res = $proxy->request($req);
	
	# 解析用テンプレートの読み込み
	open(TEMPLATE, "<", "./template.txt") || die('cannont open file.');
	my $template = join('', <TEMPLATE>);
	close(TEMPLATE);
	
	# 取得してきた内容のテンプレート解析
	my $obj = Template::Extract->new;
	my $ext = $obj->extract($template, decode('Shift_JIS', $res->content));
	
	my $rss = new XML::RSS (version => '2.0');
	
	# 基本情報
	$rss->channel(
		'title'			=> '津山高専 最近のできごと',
		'link'			=> 'http://www.tsuyama-ct.ac.jp/',
		'language'		=> 'ja',
		'description'	=> '津山工業高等専門学校の最近のできごとの非公式RSSフィードです',
		'copyright'		=> 'Copyright (C) 1997-2013, Tsuyama National College of Technology',
		'webMaster'		=> 'webmaster@tsuyama-ct.ac.jp',
	);
	
	
	# 取得したアイテムから差分を取り出す
	foreach my $item (@{$ext->{'items'}})
	{
		# 本文の処理
		$item->{'description'} =~ s/<img[^>]*>\r?\n//gi;
		$item->{'description'} =~ s/<br clear="all">\r?\n/<br>\n/gi;
		$item->{'description'} =~ s/　(.+)\r?\n/$1\n/gi;
		
		# 画像の情報を取得
		my $image = 'http://www.tsuyama-ct.ac.jp/'.$item->{'image'};
		$req = HTTP::Request->new(HEAD => $image);
		$res = $proxy->request($req);
		
		# アイテムをRSSに追加
		$rss->add_item(
			'title'			=> $item->{'title'},
			'link'			=> 'http://www.tsuyama-ct.ac.jp/dekigoto.htm#'.$item->{'id'},
			'description'	=> $item->{'description'},
			'enclosure'		=> {
				'url'			=> $image,
				'length'		=> $res->header("Content-Length"),
				'type'			=> $res->header("Content-Type"),
			},
			# 画像の最終更新日時≒記事の公開日時
			'pubDate'		=> $res->header("Last-Modified"),
			#'mode'			=> 'insert',
		);
	}
	
	print "Content-type: text/plain;\n\n";
	print $rss->as_string();
	$rss->save("dekigoto.rdf");
	
	#print "OK!\n";
	
	return 0;
}
