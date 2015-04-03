#!/usr/bin/perl

# default
use strict;
use warnings;
use utf8;

# debug
#use Data::Dumper;
#use CGI::Carp qw(fatalsToBrowser);

# lib
use lib './perllib/lib/perl5';
use local::lib './perllib';
no lib './perllib/lib/perl5';
use Template::Extract;
use LWP::UserAgent;
use Encode;
use XML::FeedPP;

exit(main());

sub main
{
	# 出力ファイル名
	my $rdfname = "dekigoto.rdf";
	
	# RSS生成対象の取得
	my $proxy = LWP::UserAgent->new;
	$proxy->timeout(5);
	$proxy->agent('Mozilla/5.0 (compatible; TdekigotoRSS/1.0; +https://github.com/windyakin/TdekigotoRSS)');
	my $req = HTTP::Request->new(GET => 'http://www.tsuyama-ct.ac.jp/dekigoto.htm');
	my $res = $proxy->request($req);
	
	# 正しく取得できていないようであればdie
	die $res->status_line if ( !$res->is_success );
	
	# 解析用テンプレートの読み込み
	open(TEMPLATE, "<", "./template.txt") || die('cannont open file.');
	my $template = join('', <TEMPLATE>);
	close(TEMPLATE);
	
	# 取得してきた内容のテンプレート解析
	my $obj = Template::Extract->new;
	my $ext = $obj->extract($template, decode('Shift_JIS', $res->content));
	
	# インスタンスを作成
	my $rss = XML::FeedPP::RSS->new(
		'title'			=> '津山高専 最近のできごと',
		'link'			=> 'http://www.tsuyama-ct.ac.jp/',
		'language'		=> 'ja',
		'description'	=> '津山工業高等専門学校の最近のできごとの非公式RSSフィードです',
		'copyright'		=> 'Copyright (C) 1997-2015, Tsuyama National College of Technology',
		'webMaster'		=> 'webmaster@tsuyama-ct.ac.jp',
		'pubDate'		=> $res->{"Last-Modified"},
	);
	
	
	# 今まで作成したRSSがあれば読み込み
	if ( -e "./$rdfname" ) {
		# XML::FeedPPはファイルをmergeできますがエンコード処理があやしいので一度変数に入れてから読み込みませます
		open(RSS, "<", "./$rdfname") || die('cannot open file');
		my $xml = join('', <RSS>);
		close(RSS);
		$rss->merge(decode('UTF-8', $xml));
	}
	print "Content-type: text/plain;\n\n";
	
	# 取得したアイテムを追加
	foreach my $item (@{$ext->{'items'}})
	{
		# アイテムのURL
		my $url = 'http://www.tsuyama-ct.ac.jp/dekigoto.htm#'.$item->{'id'};
		
		# アイテムが既に取得済みであればスキップ
		# 画像取得処理の軽減
		if ( $rss->match_item('link' => qr(^$url$)) ) {
			print "skip:$url\n";
			next;
		}
		else {
			print "add :$url\n";
		}
		
		# 本文の処理
		$item->{'description'} =~ s/<img[^>]*>\r?\n//gi;
		$item->{'description'} =~ s/<br clear="all">\r?\n/<br>\n/gi;
		$item->{'description'} =~ s/　(.+)\r?\n/$1\n/gi;
		
		# 画像の情報を取得
		my $image = 'http://www.tsuyama-ct.ac.jp/'.$item->{'image'};
		$req = HTTP::Request->new(HEAD => $image);
		$res = $proxy->request($req);
		# 正しく取得できていないようであればdie
		die $res->status_line if ( !$res->is_success );
		
		# 本文の内容に画像のリンクタグを追加
		$item->{'description'} = '<a href="'.$url.'" target="_blank"><img src="'.$image.'"></a><br>'."\n".$item->{'description'};
		
		# アイテムをRSSに追加
		$rss->add_item(
			'title'			=> $item->{'title'},
			'link'			=> $url,
			'description'	=> \$item->{'description'},
			'enclosure'		=> {
				'url'			=> $image,
				'length'		=> $res->header("Content-Length"),
				'type'			=> $res->header("Content-Type"),
			},
			# 画像の最終更新日時≒記事の公開日時
			'pubDate'		=> $res->header("Last-Modified"),
		);
	}
	
	# 重複判定・ソート
	$rss->normalize();
	# アイテム数の制限
	$rss->limit_item(15);
	
	if ( $rss->to_file($rdfname, "UTF-8") ) {
		if ( open("LAST", ">", "./dekigoto_lastupdate.txt") ) {
			print LAST time;
		}
		print "finish\n";
	}
	else {
		print "error!\n";
	}
	
	return 0;
}
