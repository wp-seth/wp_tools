#!/usr/bin/perl
use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser set_message);
use HTML::Template;
use URI::Escape;
use LWP::UserAgent;
use DateTime::Format::Strptime;
#use URI::Encode qw(uri_decode);
use Data::Dumper;

BEGIN{
	sub handle_errors{
		my $msg = shift;
		print "<p>got an error: $msg</p>";
	}
	set_message(\&handle_errors);
}

$| = 1;

my $cgi = new CGI;
print $cgi->header(-charset=>'utf-8');                                         # output the HTTP header

sub process_form{
	my $cgi = shift;
	my $url = $cgi->param('url');
	my $return_success = 0;
	# google cache
	if($url=~/https?:\/\/webcache\.googleusercontent\.com\/search\?q=cache:[a-zA-Z0-9_=-]{12}:([^+ ]+)/){
		$url = $1;
		$url = 'http://'.$url unless $url =~ /^(?:https?|ftp):\/\//;
		print "<div>".uri_unescape($url)."</div>\n";
		$return_success = 1;
	# google redirects
	}elsif($url=~/[?&](?:img)?url=([^&]+)/ or $url=~/google\.[a-z]+\/url\?.*\bq=(https?:[^&]+)/){
		$url = $1;
		print "<div>".uri_unescape($url)."</div>\n";
		#print "<div>".uri_decode($url)."</div>\n";
		$return_success = 1;
	# archive.today
	}elsif($url=~/https?:\/\/(?:www\.)?archive\.(?:today|is)\/[a-zA-Z0-9_]+(?:#.*)?$/){
		my $ua = LWP::UserAgent->new;
		my $response = $ua->head($url);
		if($response->is_success){
			my $date     = $response->header('Memento-Datetime');
			my $orig_url = $response->header('Link');
			if(defined $date and defined $orig_url and $orig_url =~ /^\s*<([^>]+)>; rel="original"/){
				my $parser = DateTime::Format::Strptime->new(
					pattern => '%a, %d %b %Y %H:%M:%S %Z',
					on_error => 'croak',
				);
				my $dt = $parser->parse_datetime($date);
				$date = $dt->strftime('%Y%m%d%H%M%S');
				$url = "http://archive.today/$date/$1";
				print "<div>".uri_unescape($url)."</div>\n";
				$return_success = 1;
			}else{
				print "<div>could not get information about original url from '$url'.</div>\n";
			}
		}else{
			print "<div>could not get header of '$url'.</div>\n";
		}
	}
	return $return_success;
}

my $template = HTML::Template->new(filename => 'google_url_converter.tpl');
my $script_name = $0;
$script_name =~s/^.*\///;
$template->param(
	css_file => 'format.css',
	version => '0.7.20141019',
	cgi_script => $script_name,
	userinput_url => ($cgi->param('url')) ? ' value="'.$cgi->param('url').'"' : '',
);
print $template->output();

if($cgi->param('url')){ # process form if url is submitted; otherwise display form only
	print '<p class="smallbold">results<br /></p>',"\n";
	print "some error occurred." unless process_form($cgi);
}
print "</body></html>\n";
