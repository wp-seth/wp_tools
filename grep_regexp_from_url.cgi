#!/usr/bin/perl
use strict;
use warnings;
use LWP::UserAgent;
use Data::Dumper;
#use Date::Parse;
use POSIX qw(strftime mktime);
use CGI;
use CGI::Carp qw(fatalsToBrowser set_message);
use HTML::Template;

BEGIN{
	sub handle_errors{
		my $msg = shift;
		print "<p>got an error: $msg</p>";
	}
	set_message(\&handle_errors);
}

$| = 1;

my $cgi = new CGI;
# output the HTTP header
print $cgi->header(-charset=>'utf-8');

# sub min
# 	calc special min(array of array refs)
#
# sub url2filename
# 	make filename out of url by 
# 	1. prefix 'file_' and 
# 	2. replacing ':' and '/' by '_'
#
# sub unixtime2iso_
#
# sub unixtime2time_diff_to_now
# 	result is in minutes
#
# sub current_year
#
# sub get_file_mod_date
# 	get date of last file modification
#
# sub get_url_content
# 	get content of web page (between pre-tags)
#
# sub log_user_input
# 	used for logging requests
#
# sub is_regexp
# 	returns true if params can be treates as a regexp
#
# sub quote_html
#
# sub unquote_html
#
# sub get_last_updates
# 	get last updates of sbl, swl and logs
#
# sub search_logs
#
# sub gen_cgi_request
# 	generate a GET-string (url)
#
# sub choose_spamlists
#
# sub process_form
# 	process user input

sub min{
	my $types_ptr = shift; # hash ref
	my $arr_ptr = shift; # array ref of array refs
	my $min = undef;
	# find min_X of $arr_ptr->[X][1] where $types_ptr->{$arr_ptr->[X][0]}==1;
	for my $val (@$arr_ptr){ # for each array ref
		if($types_ptr->{$val->[0]}){
			$min = $val->[1] if not defined $min;
			if(defined $min){
				$min = $val->[1] if(defined $val->[1] && $val->[1]<$min);
			}
		}
	}
	return $min;
}

sub url2filename{
	my $fn = shift;
	if(defined $fn){
		$fn = 'file_'.$fn;
		$fn=~s/[:\/]/_/g;
	}
	return $fn;
}

sub unixtime2iso_{
	my $unixtime = shift;
	return undef if not defined $unixtime;
	return strftime('%Y-%m-%dT%H:%M:%S', localtime($unixtime));
}

sub unixtime2time_diff_to_now{
	my $unixtime = shift;
	return time if not defined $unixtime;
	return sprintf('%.0f', (time-$unixtime)/60); # minutes
}

sub current_year{
	my ($s, $min, $h, $d, $mon, $year, $wday, $dayofyear, $isdst) = localtime(time);
	return $year + 1900;
}

sub get_file_mod_date{
	my $filename = shift;
	my $date;
	if(defined $filename and -e $filename){
		$date = (stat $filename)[9];
	}
	return $date;
}

sub get_url_content{
	my $mech            = shift;
	my $sbl_ptr         = shift; # [0]=projekt, [1]=url
	my $last_update_ptr = shift;
	my $forcepurge      = shift;
	my $url             = $sbl_ptr->[1];
	# otherwise it's a list
	my $is_log          = ($last_update_ptr->{$sbl_ptr->[0]}{$url}[0] eq 'log'); 
	my ($precontent, $content);
	my $filename = url2filename($url);
	my $url_wiki_content = $url;
	unless($is_log){
		$url_wiki_content =~ s/wiki\/(.*)/w\/index.php?title=$1&action=raw&sb_ver=1/;
	}
	#print STDERR "filename: '$filename'\n";
	#print STDERR "url '$url_wiki_content'\n";
	# mirror webpage to file
	my $response = $mech->mirror($url_wiki_content, $filename)
		or die "could not open url: $!"; 
	# mirror webpage to file
	# my $sys_res = `wget -o wgetlog -N ${url}?action=purge -O $filename`; 
	# $response->is_success or die "could not read url\n";
	# $precontent = $response->content;
	if(not -e $filename){
		print "could not retrieve information. " 
			. "perhaps there is no url '$url' or its content is empty.\n";
		$precontent = '';
		$content = '';
	}else{
		my $age_of_file = time - get_file_mod_date($filename);
		if($forcepurge and $age_of_file > 60*5 or $age_of_file > 60 * 60 * 24){
			my $purge_url = $url;
			# //meta.wikimedia.org/w/index.php?title=Spam_blacklist&action=raw&sb_ver=1
			$purge_url =~ s/wiki\/(.*)/w\/index.php?title=$1&action=purge/;
			# purge webpage
			$mech->post($purge_url, ['submit'=>'OK']) or die "could not open url: $!";
			# mirror webpage to file
			$response = $mech->mirror($url_wiki_content, $filename) 
				or die "could not open url: $!";
			# $response->is_success or die "could not read url\n";
		}
		# refresh value in "last_update"
		$last_update_ptr->{$sbl_ptr->[0]}{$url}[1] = get_file_mod_date($filename);
		#print STDERR $url . ': ' 
		#	. unixtime2time_diff_to_now(get_file_mod_date($filename))."\n";
		open(my $dat_file, '<', $filename) or die "cannot read '$filename': $!\n";
			my @file = <$dat_file>;
		close($dat_file);
		$precontent = join '', @file;
		die 'not a valid file: ' . $url . "\n" if $precontent !~ /<pre\b[^>]*>/;
		$content = $precontent if $is_log;
		# remove non-pre items
		$precontent =~ s/.*?<pre\b[^>]*>(.*?)<\/pre>(?:.(?!<pre\b))*/$1/gs;
	}
	if($is_log){
		return ($precontent, $content);
	}else{
		return $precontent;
	}
}

sub log_user_input{
	my $cgi = shift;
	my @names = $cgi->param;
	my $log_entry = time . ' ';
	open(my $dat_file, '>>', 'grep_regexp_from_url.log') or die "$!\n";
		for(@names){
			$log_entry .= $_ . '=' . $cgi->param($_) . ' ' if $_ ne 'fsubmit';
		}
		chop $log_entry;
		print $dat_file $log_entry."\n";
	close($dat_file);
}

sub is_regexp{
	eval{qr/@_/ && 'foo' =~ /@_/};
	return ($@ ? 0 : 1);
}

sub quote_html{
	my $q = shift;
	$q =~ s/&/&amp;/g;
	$q =~ s/</&lt;/g;
	$q =~ s/>/&gt;/g;
	return $q;
}

sub unquote_html{
	my $q = shift;
	$q =~ s/&lt;/</g;
	$q =~ s/&gt;/>/g;
	$q =~ s/&amp;/&/g;
	return $q;
}

sub get_last_updates{
	my $lists_ptr = shift;
	my $logs_ptr = shift;
	# put all possible types of sbls/logs into %last_updates
	my %last_updates;
	while(my ($sll_project, $sll) = each %{$logs_ptr}){
		for(@$sll){
			$last_updates{$sll_project}{$_} = 
				['log', get_file_mod_date(url2filename($_))];
		}
	}
	for(my $i = 0; $i < @{$lists_ptr}; ++$i){
		$last_updates{$$lists_ptr[$i][0]}{$$lists_ptr[$i][1]} = 
			['list', get_file_mod_date(url2filename($$lists_ptr[$i][1]))];
	}
	return %last_updates;
}

sub search_logs{
	my $output = shift;
	my $debug = shift;
	my $spamlistlogs = shift;
	my $project = shift;
	my $entry = shift;
	my $url = shift;
	my $mech = shift;
	my $last_updates = shift;
	my $forcepurge = shift;
	my @sbllogentries; 
	# is a log defined for that project?
	my $log_used = defined $spamlistlogs->{$project};      
	my ($precontent, $content, $domain, $reason, $i, $log_entry);
	if($log_used){
		# for each spamlistlog (belonging to the project)
		for my $sll (@{$spamlistlogs->{$project}}){
			# get domain (including trailing slash)
			$sll =~ m~https?://([a-z]+\..+?/)~;
			$domain = $1;
			print STDERR $sll . ' ' . $project . "\n" if $debug;
			print STDERR $entry . "\n" if $debug;
			print STDERR $url . "\n" if $debug;
			# get spamlist log
			($precontent, $content) = get_url_content(
				$mech, [$project, $sll], $last_updates, $forcepurge);
			#print STDERR $sll . ': ' . unixtime2time_diff_to_now(
			#	$last_updates->{$project}{$sll}[1])."\n";
			# maybe todo in future: <span class="mw-headline">January 2008</span>
			# split entries to lines; grep those, which contain current entry or reasons
			@sbllogentries = grep { 
				# comment or literal entry
				$_ =~ /^#|\Q$entry\E/ 
				  || # regexp-entry (not just comment) and 
				 		 # valid regexp (some entries are invalid!)
				 		($_ =~ /^\s*([^#\s]+)/ && is_regexp($1) 
				 		 # match url
				 		 && $url =~ /https?:\/\/+[a-z0-9_.-]*(?:$1)/iaa
				 	  )
				  || # regexp-entry (cope with regexp changes, i.e., a special log syntax)
						 # and valid regexp (some entries are invalid!)
						($_ =~ /^\s*[^#\s]+\s*→\s*([^#\s]+)/ && is_regexp($1) 
						 # match url
				 		 && $url =~ /https?:\/\/+[a-z0-9_.-]*(?:$1)/iaa
				 		);
			} split /\n/, $precontent;
			print STDERR '' . (join "\n", @sbllogentries) . "\n" if $debug >= 2;
			# for each relevant spamlistlog entry
			for($i = 0; $i < @sbllogentries; ++$i){
				# skip comments (=reasons); 
				# |^[\s|]*$ is just a workaround, because of examples in the log-manual.
				# should be fixed at some time.
				next if $sbllogentries[$i] =~ /^ *#|^[\s|]*$/;
				$reason = 'no reason found';
				$log_entry = '';
				# found reason in same line as log-entry
				if($sbllogentries[$i] =~ /^\s*([^#]+[^# ])\s*(#.*)/){ 
					$log_entry = $1;
					$reason = $2;
				}else{
					if($i > 0){
						# get reason of grouped spamlisting
						$reason = $sbllogentries[$i - 1];
						# log-entry
						$log_entry = $1 if $sbllogentries[$i] =~ /^\s*([^# ]+)/;
					}
					$reason =~ s/.*?#/#/;
				}
				# keep links working (href="/foo"  -> href="//domain/foo")
				$reason =~ s/href="\/(?!\/)/href="\/\/$domain/g; 
				# expand abbreviations
				$reason =~ s/>\Kw\+(?=<\/a>)/added to whitelist/;
				$reason =~ s/>\Kw\-(?=<\/a>)/removed from whitelist/;
				$reason =~ s/>\Kw\*(?=<\/a>)/modified whitelist entry/;
				$reason =~ s/>\Kb\+(?=<\/a>)/added to blacklist/;
				$reason =~ s/>\Kb\-(?=<\/a>)/removed from blacklist/;
				$reason =~ s/>\Kb\*(?=<\/a>)/modified blacklist entry/;
				$$output .= "\t\t\t\t".'<li class="log">log entry: ' . $log_entry . ' ' 
					. $reason . "</li>\n";
			}
		}
	}else{ # if $log_used==0
		$$output .= "\t\t\t\t" . 
			'<li class="log">no log defined for this project. ' . 
			'ask <a href="//meta.wikimedia.org/wiki/User_talk:Lustiger_seth">there</a> ' .
			'if you want this script to use the log.</li>' . "\n";
	}
	return $log_used;
}

# generate a GET-string (url)
sub gen_cgi_request{
	my $cgi = shift;
	my $newparams = shift;
	my @names = $cgi->param;
	my $querystring = '';
	for(@names){
		$querystring .= $_.'='.$cgi->param($_).'&' if $_ ne 'fsubmit';
	}
	while(my ($param, $value) = each %{$newparams}){
		$querystring .= $param.'='.$value.'&';
	}
	chop $querystring;
	my $script_name = $0;
	$script_name =~s/^.*\///;
	return $script_name.'?'.$querystring;
}

sub choose_spamlists{
	my $ud_lang  = shift;
	my $ud_proj  = shift;
	my $projects = shift;
	my $mech     = shift;
	my @spamlists = ([
			'meta black', 
			'http://meta.wikimedia.org/wiki/Spam_blacklist', 
			'meta blacklist'
		]
	);
	# chose whiteliste and blacklists depending on user-defined language (and 
	# user-defined project)
	# if ud_lang is a number, then use biggest n wikis
	# if ud_lang is empty, then use meta only
	# else interpret ud_lang as language abbreviation
	if($ud_lang =~ /^[0-9]+\z/ and $ud_lang > 0 and $ud_lang < 58){
		# get list of languages, sorted by size of wikipedia
		# mirror webpage to file
		my $response = $mech->mirror(
			'http://s23.org/wikistats/wikipedias_csv.php', 
			'wikipedias_csv',
		) or die "could not open url: $!";
		# $response->is_success or die "could not read url\n";
		open(my $dat_file, '<', 'wikipedias_csv') 
			or die "cannot read 'wikipedias_csv': $!\n";
			while(<$dat_file>){
				if(/(\d+),\d+,([a-z]{2,3}),/){
					my $lang_index = $1;
					my $lang       = $2;
					last if $lang_index > $ud_lang;
					for my $bw('black', 'white'){
						push @spamlists, [
							$ud_proj . ':' . $lang . ' ' . $bw, 
							'http://' . $lang . '.' . $projects->{$ud_proj} . 
								'.org/wiki/MediaWiki:Spam-'.$bw.'list',
							$lang . '-' . $projects->{$ud_proj} . ' ' . $bw . 'list',
						];
					}
					if($lang eq 'en' && $ud_proj eq 'w'){
						push @spamlists, [
							'w:en:XLinkBot revert', 
							'http://en.wikipedia.org/wiki/User:XLinkBot/RevertList', 
							'XBotLink revertlist',
						];
					}
				}
			}
		close($dat_file);
	}elsif($ud_lang eq ''){
		# search meta lists only
	}else{
		if($ud_lang !~ /^[a-z]{2,10}\z/){
			die 'wrong language. only /^[a-z]{2,10}\z/ allowed.';
		}
		for my $bw('black', 'white'){
			push @spamlists, [
				$ud_proj.':'.$ud_lang.' '.$bw, 
				'http://' . $ud_lang . '.' . $projects->{$ud_proj} . 
					'.org/wiki/MediaWiki:Spam-' . $bw . 'list',
				$ud_lang . '-' . $projects->{$ud_proj} . ' ' . $bw . 'list',
			];
		}
		if($ud_lang eq 'en' && $ud_proj eq 'w'){
			push @spamlists, [
				'w:en:XLinkBot revert', 
				'http://en.wikipedia.org/wiki/User:XLinkBot/RevertList', 
				'XBotLink revertlist'
			];
		}
	}
	return \@spamlists;
}

sub process_form{
	my $cgi      = shift;
	my $projects = shift;
	my $url      = $cgi->param('url'); # external url to be checked
	$url =~ s/^\s+|\s+$//g; # trim url
	# user defined language
	my $ud_lang = $cgi->param('userdeflang') // '';
	# user defined project
	my $ud_proj = $cgi->param('userdefproj') // 'w';
	die 'project does not exist.' if $ud_proj !~ /^[a-z]{1,4}\z/;
	my $forcepurge = ($cgi->param('purge'));
	my $forcelogs = ($cgi->param('forcelogs') && $cgi->param('forcelogs') == 1);
	my $debug = 0;
	my $mech = LWP::UserAgent->new;
	$mech->agent('Mozilla/5.0 seth_bot');
	# set prefix http:// automatically, if not existing
	$url =~ s/^(?!https?:\/\/)/http:\/\//;
	my $spamlists = choose_spamlists($ud_lang, $ud_proj, $projects, $mech);
	my %spamlistlogs = (
		'meta black' => ['http://meta.wikimedia.org/wiki/Spam_blacklist/Log'],
		'w:en black' => 
			['http://en.wikipedia.org/wiki/MediaWiki_talk:Spam-blacklist/log'],
		'w:en white' => 
			['http://en.wikipedia.org/wiki/MediaWiki_talk:Spam-whitelist/Log'],
		'w:en:XLinkBot revert' => 
			['http://en.wikipedia.org/wiki/User:XLinkBot/RevertList_requests/log'],
		'w:de black' => ['http://de.wikipedia.org/wiki/Wikipedia:Spam-blacklist/log'],
		'w:de white' => ['http://de.wikipedia.org/wiki/Wikipedia:Spam-blacklist/log'],
	);
	push @{$spamlistlogs{'meta black'}}, 
		map {"http://meta.wikimedia.org/wiki/Spam_blacklist/Log/$_"} 
			(2004..current_year());
	my %last_updates = get_last_updates($spamlists, \%spamlistlogs);
	#print STDERR Dumper \%last_updates;
	my ($entry_mod, $entry_comment, $output, $project, $last_update);
	my @sblentries; 
	my %log_used; # project=>X    X: 0=not used; 1=used
	my $found_entry; # 0=not found; 1=found
	# for each spamlist: search for blocking entries
	#print STDERR Dumper $spamlists;
	for(my $spamlist_ctr = 0; $spamlist_ctr < @$spamlists; ++$spamlist_ctr){
		$project = $spamlists->[$spamlist_ctr][0]; # just a shortcut
		#print STDERR "project '$project'\n";
		my $present_spamlist_url = $spamlists->[$spamlist_ctr][1];
		$present_spamlist_url =~s/^https?://;
		$output = "\t" . '<div>list: <a href="' . $present_spamlist_url . '">' .
			$spamlists->[$spamlist_ctr][2] . "</a></div>\n\t<ul>\n";
		$log_used{$project} = 0 if not defined $log_used{$project};
		$found_entry = 0;
		# get spamlist and split entries to lines
		@sblentries = split /\n/, get_url_content(
			$mech, 
			$spamlists->[$spamlist_ctr], 
			\%last_updates, 
			$forcepurge
		);
		#print STDERR $spamlists->[$spamlist_ctr][1].': '.
		#	unixtime2time_diff_to_now(
		#		$last_updates{$project}{$spamlists->[$spamlist_ctr][1]}[1]
		#	) . "\n";
		for(@sblentries){
#			s/&lt;/</g;   # html-entity
#			s/&gt;/>/g;   # html-entity
#			s/&amp;/&/g;  # html-entity
			s~\\*/~\/~g;  # 'repair' slashes (just like the spamextension does)
		}
		# remove empty and comments lines
		@sblentries = grep !/^ *(?:#.*)?$/, @sblentries;
		# search patterns that match given $url
		for my $entry (@sblentries){
			$entry_comment = '';
			if($entry =~ /#/){
				# remove (but save) comments
				$entry =~ s/ *# *(.*)//;
				$entry_comment = $1;
			}
			$entry =~ s/\s+$//;
			$entry_mod = $entry;
			# cope with: old-perl vs. new-php
			while($entry_mod =~ /(.*)
				\(\?<    # look-behind pattern (begin)
				([!=])   # negative or positive
				([^()]+) # first option
				\|       # alternative
				([^()]+) # second option
				\)       # look-behind pattern (end)
				(.*)/x){
				# replace by multiple look-behinds
				$entry_mod = 
					$1 . '(?<' . $2 . $3 . ')' . $5 . '|' . $1 . '(?<' . $2 . $4 . ')' . $5;
			}
			# if url in current spamlist
			if($url =~ /https?:\/\/+[a-z0-9_.-]*(?:$entry_mod)/iaa){
				$found_entry = 1;
				$output .= "\t\t" . '<li class="' . 
					(($project=~/white/) ? 'whiteentry': 'blackentry') . '">' . "\n\t\t\t" . 
					'<span class="foundentry">' . quote_html($entry) . "</span>" . 
					"\n\t\t\t<ul>\n";
				if($entry_comment ne ''){
					$output .= "\t\t\t\t" . '<li class="comment">additional comment: ' . 
						$entry_comment . "</li>\n";
				}
				$log_used{$project} = search_logs(
					\$output, $debug, \%spamlistlogs, $project, $entry, $url, $mech, 
					\%last_updates, $forcepurge);
				$output .= "\t\t\t</ul>\n\t\t</li>\n";
			}
		}
		if(defined $last_updates{$project}){
			#print STDERR "last_updates{$project}\n";
			#print STDERR Dumper $last_updates{$project};
			if(!$found_entry){
				$output .= "\t\t" . '<li class="noentries">no entries here.</li>' . "\n";
			}
			#print STDERR " last update: $last_update\n" if defined $last_update;
			if((not defined $last_update) or $last_update > (min(
					{'list'=>1, 'log'=>$log_used{$project}}, 
					[values %{$last_updates{$project}}]
				) // 0)
			){
				$last_update = min({'list'=>1, 'log'=>$log_used{$project}}, 
					[values %{$last_updates{$project}}]);
			}
			# if each list should have the information of last update
			# $last_update = min({'list'=>1, 'log'=>$log_used{$project}}, 
			#		[values %{$last_updates{$project}}]);
			# $output .= "\t\t" . '<li class="lastupdate">' . 
			#	 '(last update of ' . $project . 'list: ' . 
			#	 unixtime2time_diff_to_now($last_update) .
			#	 ' minutes ago;';
			# if(unixtime2time_diff_to_now($last_update) > 4){
			#		$output .= ' if you want to fetch live data, click on <a href="' . 
			#			gen_cgi_request($cgi, {'purge'=>1}) . '">purge</a>)';
			#	}
			#$output .= '</li>' . "\n";
			$output .= "\n";
		}
		$output .= "\t</ul>\n";
		# just for my css-file
		$output =~ s/class="(?:external text|mw-redirect)"/class="external"/g;
		$output =~ s/(href="[^"]+")((?:[^>](?!class="))*>)/$1 class="external"$2/g;
		print $output;
	}
	$last_update = unixtime2time_diff_to_now($last_update);
	$output = '(last update of lists: ' . $last_update . ' minutes ago';
	if($last_update > 4){
		$output .= '; if you want to fetch live data, click on <a href="' . 
			gen_cgi_request($cgi, {'purge'=>1}) . '" class="external">purge</a>';
	}
	$output .= ')';
	print <<EOD;
	<script type="text/javascript">
		document.getElementById('lastupdate').innerHTML = '$output';
	</script>
EOD
}

# GUI form
my %labels = (
	'w' => 'wikipedia',
	'wikt' => 'wiktionary',
	'b' => 'wikibooks',
	'n' => 'wikinews',
	'q' => 'wikiquote',
	's' => 'wikisource',
	'v' => 'wikiversity');
	if(defined $cgi->param('userdefproj') && (
			$cgi->param('userdefproj')!~/^[a-z]{1,4}\z/ 
			|| not defined $labels{$cgi->param('userdefproj')}
		)
	){
		die 'wrong project. ' . 
			'please choose one of the above mentioned projects, e.g., wikipedia';
	}

my $template = HTML::Template->new(filename => 'grep_regexp_from_url.tpl');
my $script_name = $0;
$script_name =~ s/^.*\///;
$template->param(
	css_file => 'format.css',
	version => '1.3.20141226',
	cgi_script => $script_name,
	userinput_url => ($cgi->param('url')) ? 
		' value="' . $cgi->param('url') . '"' : '',
	userdeflang => ($cgi->param('userdeflang')) ? 
		' value="' . $cgi->param('userdeflang') . '"' : '',
	userdefproj_select => $cgi->popup_menu('userdefproj', [keys %labels], 
		(($cgi->param('userdefproj')) ? $cgi->param('userdefproj') : 'wikipedia'), 
		\%labels),
	forcelogs => ($cgi->param('forcelogs') && $cgi->param('forcelogs') == 1) ? 
		' checked="checked"' : ''
);
print $template->output();

# process form if url is submitted; otherwise display form only
if($cgi->param('url')){ 
	log_user_input($cgi);
	print '<p class="smallbold">results<br />' . 
		'<span id="lastupdate" class="xsmall"></span></p>' . "\n";
	process_form($cgi, \%labels);
}
print "</body></html>\n";
