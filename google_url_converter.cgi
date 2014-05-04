#!/usr/bin/perl
use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser set_message);
use HTML::Template;
use URI::Escape;
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

# sub googleurl2url

# convert google.com/...?url=foo to foo
sub googleurl2url{
	my $fn = shift;
	if(defined $fn){
		$fn = 'file_'.$fn;
		$fn=~s/[:\/]/_/g;
	}
	return $fn;
}

sub process_form{
	my $cgi = shift;
	my $url = $cgi->param('url');
	if($url=~/[?&](?:img)?url=([^&]+)/){
		$url = $1;
		print "<div>".uri_unescape($url)."</div>\n";
		#print "<div>".uri_decode($url)."</div>\n";
		return 1;
	}else{
		return 0;
	}
}

my $template = HTML::Template->new(filename => 'google_url_converter.tpl');
my $script_name = $0;
$script_name =~s/^.*\///;
$template->param(
	css_file => 'format.css',
	version => '0.3.20140504',
	cgi_script => $script_name,
	userinput_url => ($cgi->param('url')) ? ' value="'.$cgi->param('url').'"' : '',
);
print $template->output();

if($cgi->param('url')){ # process form if url is submitted; otherwise display form only
	print '<p class="smallbold">results<br /></p>',"\n";
	print "some error occurred." unless process_form($cgi);
}
print "</body></html>\n";
