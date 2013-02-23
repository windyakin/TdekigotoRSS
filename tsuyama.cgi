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
	# RSS生成対象の取得
	my $proxy = LWP::UserAgent->new;
	$proxy->timeout(10);
	$proxy->agent('Mozilla/5.0 (compatible; TdekigotoRSS/1.0; +https://github.com/windyakin/TdekigotoRSS)');
	my $req = HTTP::Request->new(GET => 'http://www.tsuyama-ct.ac.jp/dekigoto.htm');
	my $res = $proxy->request($req);
	
	# テンプレートの読み込み
	open(TEMPLATE, "<", "./template.txt") || die('cannont open file.');
	my $template = join('', <TEMPLATE>);
	close(TEMPLATE);
	
	# 取得してきた内容のテンプレート解析
	my $obj = Template::Extract->new;
	my $ext = $obj->extract($template, decode('Shift_JIS', $res->content));
	
	my $rss = new XML::RSS (version => '2.0');
	$rss->parsefile("dekigoto.rdf");
	
	$rss->channel(
		'title'			=> '津山高専 最近のできごと',
		'link'			=> 'http://www.tsuyama-ct.ac.jp/',
		'language'		=> 'ja',
		'description'	=> '津山工業高等専門学校の最近のできごとの非公式RSSフィードです',
		'copyright'		=> 'Copyright (C) 1997-2013, Tsuyama National College of Technology',
		'webMaster'		=> 'webmaster@tsuyama-ct.ac.jp',
	);
	
	# 最後に取得したアイテムのURL
	my $last = $rss->{'items'}[0]->{'link'};
	
	my @diff = ();
	
	# 取得したアイテムから差分を取り出す
	foreach my $item (@{$ext->{'items'}})
	{
		# アイテムのURL
		my $url = 'http://www.tsuyama-ct.ac.jp/dekigoto.htm#'.$item->{'id'};
		
		# 既に登録されている記事があるようだったら終わり
		if ( $last eq $url ) {
			last;
		}
		
		# 差分配列に追加
		unshift(@diff, $item);
	}
	
	# いよいよ追加します
	foreach my $item (@diff)
	{
		# 10件以上の登録があるようならアイテムを削除
		if (@{$rss->{'items'}} == 10) {
			pop(@{$rss->{'items'}}) 
		}
		
		# 本文の調理
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
			'pubDate'		=> $res->header("Last-Modified"),
			'mode'			=> 'insert',
		);
	}
	
	print "Content-type: text/plain;\n\n";
	print $rss->as_string();
	#$rss->save("dekigoto.rdf");
	
#	print "OK!\n";
	
	return 0;
}
