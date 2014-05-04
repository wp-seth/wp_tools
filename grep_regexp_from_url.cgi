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
print $cgi->header(-charset=>'utf-8');                                         # output the HTTP header

# sub min
# 	calc special min(array of array refs)
# sub url2filename
# 	make filename out of url by 1. prefix 'file_' and 2. replacing ':' and '/' by '_'
# sub unixtime2iso_
# sub unixtime2time_diff_to_now
# 	result is in minutes
# sub current_year
# sub get_file_mod_date
# 	get date of last file modification
# sub get_url_content
# 	get content of web page (between pre-tags)
# sub log_user_input
# 	used for logging requests
# sub is_regexp
# 	returns true if params can be treates as a regexp
# sub quote_html
# sub unquote_html
# sub get_last_updates
# 	get last updates of sbl, swl and logs
# sub search_logs
# sub gen_cgi_request
# 	generate a GET-string (url)
# sub process_form
# 	process user input


# calc special min(array of array refs)
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

# make filename out of url by 1. prefix 'file_' and 2. replacing ':' and '/' by '_'
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
	my ($Second, $Minute, $Hour, $Day, $Month, $Year, $WeekDay, $DayOfYear, $IsDST) = localtime(time);
	return $Year + 1900;
}

# get date of last file modification
sub get_file_mod_date{
	my $filename = shift;
	my @info = ();
	my $date = undef;
	if(defined $filename && -e $filename){
		@info = stat($filename);
		$date = $info[9];
	}
	return $date;
}

# get content of web page (between pre-tags)
sub get_url_content{
	my $mech = shift;
	my $sbl_ptr = shift; # [0]=projekt, [1]=url
	my $last_update_ptr = shift;
	my $forcepurge = shift;
	my $url = $sbl_ptr->[1];
	my $is_log = ($last_update_ptr->{$sbl_ptr->[0]}{$url}[0] eq 'log'); # otherwise it's a list
	my ($precontent, $content);
	my $filename = url2filename($url);
	my $url_wiki_content = $url;
	$url_wiki_content=~s/wiki\/(.*)/w\/index.php?title=$1&action=raw&sb_ver=1/ if not $is_log;
	my $response = $mech->mirror($url_wiki_content, $filename) or die "could not open url: $!"; # mirror webpage to file
	# my $sys_res = `wget -o wgetlog -N ${url}?action=purge -O $filename`; # mirror webpage to file
	# $response->is_success or die "could not read url\n";
	# $precontent = $response->content;
	if(not -e $filename){
		print 'could not retrieve information. perhaps there is no url '.$url.'?'."\n";
		$precontent = '';
		$content = '';
	}else{
		my $age_of_file = time-get_file_mod_date($filename);
		if($forcepurge && $age_of_file>60*5 || $age_of_file>60*60*24){
			my $purge_url = $url;
			# http://meta.wikimedia.org/w/index.php?title=Spam_blacklist&action=raw&sb_ver=1
			$purge_url=~s/wiki\/(.*)/w\/index.php?title=$1&action=purge/;
			$mech->post($purge_url, ['submit'=>'OK']) or die "could not open url: $!"; # purge webpage
			$response = $mech->mirror($url_wiki_content, $filename) or die "could not open url: $!"; # mirror webpage to file
			# $response->is_success or die "could not read url\n";
		}
		$last_update_ptr->{$sbl_ptr->[0]}{$url}[1] = get_file_mod_date($filename); # refresh value in "last_update"
		#print STDERR $url.': '.unixtime2time_diff_to_now(get_file_mod_date($filename))."\n";
		open(datFILE, '<'.$filename) || die "$!\n";
			my @file = <datFILE>;
		close(datFILE);
		$precontent = join '', @file;
		die 'not a valid file: '.$url."\n" if $precontent!~/<pre\b[^>]*>/;
		$content = $precontent if $is_log;
		$precontent =~ s/.*?<pre\b[^>]*>(.*?)<\/pre>(?:.(?!<pre\b))*/$1/gs;   # remove non-pre items
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
	my $log_entry = time.' ';
	open(datFILE, '>>grep_regexp_from_url.log') || die "$!\n";
		for(@names){
			$log_entry .= $_.'='.$cgi->param($_).' ' if $_ ne 'fsubmit';
		}
		chop $log_entry;
		print datFILE $log_entry."\n";
	close(datFILE);
}

sub is_regexp{
	eval{qr/@_/ && 'foo'=~/@_/};
	return ($@ ? 0 : 1);
}

sub quote_html{
	my $q = shift;
	$q=~s/&/&amp;/g;
	$q=~s/</&lt;/g;
	$q=~s/>/&gt;/g;
	return $q;
}

sub unquote_html{
	my $q = shift;
	$q=~s/&lt;/</g;
	$q=~s/&gt;/>/g;
	$q=~s/&amp;/&/g;
	return $q;
}

# get last updates of sbl, swl and logs
sub get_last_updates{
	my $lists_ptr = shift;
	my $logs_ptr = shift;
	# put all possible types of sbls/logs into %last_updates
	my %last_updates;
	while(my ($sll_project, $sll) = each %{$logs_ptr}){
		for(@$sll){
			$last_updates{$sll_project}{$_} = ['log', get_file_mod_date(url2filename($_))];
		}
	}
	for(my $i=0; $i<@{$lists_ptr}; ++$i){
		$last_updates{$$lists_ptr[$i][0]}{$$lists_ptr[$i][1]} = ['list', get_file_mod_date(url2filename($$lists_ptr[$i][1]))];
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
	my $log_used = defined $spamlistlogs->{$project};      # is a log defined for that project?
	my ($precontent, $content, $domain, $reason, $i, $log_entry);
	if($log_used){
		for my $sll (@{$spamlistlogs->{$project}}){            # for each spamlistlog (belonging to the project)
			$sll =~m~https?://([a-z]+\..+?/)~;                   # get domain (including trailing slash)
			$domain = $1;
			print STDERR $sll.' '.$project."\n" if $debug;
			print STDERR $entry."\n" if $debug;
			print STDERR $url."\n" if $debug;
			# get spamlist log
			($precontent, $content) = get_url_content($mech, [$project, $sll], $last_updates, $forcepurge);
			#print STDERR $sll.': '.unixtime2time_diff_to_now($last_updates->{$project}{$sll}[1])."\n";
			# maybe todo in future: <span class="mw-headline">January 2008</span>
			# split entries to lines; grep those, which contain current entry or reasons
			@sbllogentries = grep {   $_=~/^#|\Q$entry\E/       # comment or literal entry
														 || ($_=~/^\s*([^#\s]+)/      # regexp-entry (not just comment)
																 && is_regexp($1)         # valid regexp (some entries are invalid!)
																 && $url=~/https?:\/\/+[a-z0-9_.-]*(?:$1)/i # matches url
															  )
														 || ($_=~/^\s*[^#\s]+\s*→\s*([^#\s]+)/          # regexp-entry (cope with regexp changes, i.e., a special log syntax)
																 && is_regexp($1)                           # valid regexp (some entries are invalid!)
																 && $url=~/https?:\/\/+[a-z0-9_.-]*(?:$1)/i # matches url
																);
											 }
											 split /\n/, $precontent;
			print STDERR ''.(join "\n", @sbllogentries)."\n" if $debug>=2;
			for($i=0; $i<@sbllogentries; ++$i){                 # for each relevant spamlistlog entry
				next if $sbllogentries[$i]=~/^ *#|^[\s|]*$/;      # skip comments (=reasons); |^[\s|]*$ is just a workaround, because of examples in the log-manual. should be fixed at some time.
				$reason = 'no reason found';
				$log_entry = '';
				if($sbllogentries[$i]=~/^\s*([^#]+[^# ])\s*(#.*)/){ # found reason in same line as log-entry
					$log_entry = $1;
					$reason = $2;
				}else{
					if($i>0){
						$reason = $sbllogentries[$i-1];               # get reason of grouped spamlisting
						$log_entry = $1 if $sbllogentries[$i]=~/^\s*([^# ]+)/;# log-entry
					}
					$reason =~s/.*?#/#/;
				}
				$reason =~s/href="\/(?!\/)/href="\/\/$domain/g; # keep links working (href="/foo"  -> href="//domain/foo")
				# expand abbreviations
				$reason =~s/>\Kw\+(?=<\/a>)/added to whitelist/;
				$reason =~s/>\Kw\-(?=<\/a>)/removed from whitelist/;
				$reason =~s/>\Kw\*(?=<\/a>)/modified whitelist entry/;
				$reason =~s/>\Kb\+(?=<\/a>)/added to blacklist/;
				$reason =~s/>\Kb\-(?=<\/a>)/removed from blacklist/;
				$reason =~s/>\Kb\*(?=<\/a>)/modified blacklist entry/;
				$$output.="\t\t\t\t".'<li class="log">log entry: '.$log_entry.' '.$reason."</li>\n";
			}
		}
	}else{ # if $log_used==0
		$$output.="\t\t\t\t".'<li class="log">no log defined for this project. ask <a href="//meta.wikimedia.org/wiki/User_talk:Lustiger_seth">there</a> if you want this script to use the log.</li>'."\n";
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

sub process_form{
	my $cgi = shift;
	my $projects = shift;
	my $url = $cgi->param('url');
	$url=~s/^\s+|\s+$//g;                                                # trim url
	my $ud_lang = (defined $cgi->param('userdeflang')) ? $cgi->param('userdeflang') : '';
	my $ud_proj = (defined $cgi->param('userdefproj')) ? $cgi->param('userdefproj') : 'w';
	die 'project does not exist.' if $ud_proj!~/^[a-z]{1,4}\z/;
	my $forcepurge = ($cgi->param('purge'));
	my $forcelogs = ($cgi->param('forcelogs') && $cgi->param('forcelogs')==1);
	my $debug = 0;
	my $mech = LWP::UserAgent->new;
	$mech->agent('Mozilla/5.0 seth_bot');
	$url =~ s/^(?!https?:\/\/)/http:\/\//;                              # prefix http:// automatically, if not existing
	my @spamlists = (['meta black', 'http://meta.wikimedia.org/wiki/Spam_blacklist', 'meta blacklist']);
	# chose whiteliste and blacklists depending on user-defined language (and user-defined project)
	if($ud_lang=~/^\d+\z/ && $ud_lang>0 && $ud_lang<58){
		# beta state function: use biggest n wikis
		my $response = $mech->mirror('http://s23.org/wikistats/wikipedias_csv.php', 'wikipedias_csv') or die "could not open url: $!"; # mirror webpage to file
		# $response->is_success or die "could not read url\n";
		open(datFILE, '<wikipedias_csv') || die "$!\n";
			while(<datFILE>){
				if(/(\d+),\d+,([a-z]{2,3}),/){
					last if $1>$ud_lang;
					push @spamlists,
						[$ud_proj.':'.$2.' black', 'http://'.$2.'.'.$projects->{$ud_proj}.'.org/wiki/MediaWiki:Spam-blacklist', $2.'-'.$projects->{$ud_proj}.' blacklist'],
						[$ud_proj.':'.$2.' white', 'http://'.$2.'.'.$projects->{$ud_proj}.'.org/wiki/MediaWiki:Spam-whitelist', $2.'-'.$projects->{$ud_proj}.' whitelist'];
						if($2 eq 'en' && $ud_proj eq 'w'){
							push @spamlists, ['w:en:XLinkBot revert', 'http://en.wikipedia.org/wiki/User:XLinkBot/RevertList', 'XBotLink revertlist'];
						}
				}
			}
		close(datFILE);
	}elsif($ud_lang eq ''){
		# search meta lists only
	}else{
		die 'wrong language. only /^[a-z]{2,10}\z/ allowed.' if $ud_lang!~/^[a-z]{2,10}\z/;
		push @spamlists,
		[$ud_proj.':'.$ud_lang.' black', 'http://'.$ud_lang.'.'.$projects->{$ud_proj}.'.org/wiki/MediaWiki:Spam-blacklist', $ud_lang.'-'.$projects->{$ud_proj}.' blacklist'],
		[$ud_proj.':'.$ud_lang.' white', 'http://'.$ud_lang.'.'.$projects->{$ud_proj}.'.org/wiki/MediaWiki:Spam-whitelist', $ud_lang.'-'.$projects->{$ud_proj}.' whitelist'];
		if($ud_lang eq 'en' && $ud_proj eq 'w'){
			push @spamlists, ['w:en:XLinkBot revert', 'http://en.wikipedia.org/wiki/User:XLinkBot/RevertList', 'XBotLink revertlist'];
		}
	}
	my %spamlistlogs = (
			 'meta black'    => ['http://meta.wikimedia.org/wiki/Spam_blacklist/Log'],
			 'w:en black'    => ['http://en.wikipedia.org/wiki/MediaWiki_talk:Spam-blacklist/log'],
			 'w:en white'    => ['http://en.wikipedia.org/wiki/MediaWiki_talk:Spam-whitelist/Log'],
			 'w:en:XLinkBot revert' => ['http://en.wikipedia.org/wiki/User:XLinkBot/RevertList_requests/log'],
			 'w:de black'    => ['http://de.wikipedia.org/wiki/Wikipedia:Spam-blacklist/log'],
			 'w:de white'    => ['http://de.wikipedia.org/wiki/Wikipedia:Spam-blacklist/log']);
	push @{$spamlistlogs{'meta black'}}, map {"http://meta.wikimedia.org/wiki/Spam_blacklist/Log/$_"} (2004..current_year());
	my %last_updates = get_last_updates(\@spamlists, \%spamlistlogs);
	my $entry_mod;
	my $entry_comment;
	my $output;
	my $project;
	my $last_update;
	my @sblentries; 
	my %log_used; # project=>X    X: 0=not used; 1=used
	my $found_entry; # 0=not found; 1=found
	for(my $spamlist_ctr=0; $spamlist_ctr<@spamlists; ++$spamlist_ctr){ # for each spamlist
		$project = $spamlists[$spamlist_ctr][0];                          # just a shortcut
		my $present_spamlist_url = $spamlists[$spamlist_ctr][1];
		$present_spamlist_url =~s/^https?://;
		$output = "\t".'<div>list: <a href="'.$present_spamlist_url.'">'.$spamlists[$spamlist_ctr][2]."</a></div>\n\t<ul>\n";
		$log_used{$project} = 0 if not defined $log_used{$project};
		$found_entry = 0;
		@sblentries = split /\n/, get_url_content($mech, $spamlists[$spamlist_ctr], \%last_updates, $forcepurge);# get spamlist and split entries to lines
		#print STDERR $spamlists[$spamlist_ctr][1].': '.unixtime2time_diff_to_now($last_updates{$project}{$spamlists[$spamlist_ctr][1]}[1])."\n";
		for(@sblentries){
#			s/&lt;/</g;                                               # html-entity
#			s/&gt;/>/g;                                               # html-entity
#			s/&amp;/&/g;                                              # html-entity
			s~\\*/~\/~g;                                              # 'repair' slashes (just like the spamextension does)
		}
		@sblentries = grep !/^ *(?:#.*)?$/, @sblentries;            # remove empty and comments lines
		for my $entry (@sblentries){                                # search patterns, which match given $url
			$entry_comment = '';
			if($entry=~/#/){
				$entry =~ s/ *# *(.*)//;                                  # remove (but save) comments
				$entry_comment = $1;
			}
			$entry =~ s/\s+$//;
			$entry_mod = $entry;
			while($entry_mod=~/(.*)\(\?<([!=])([^()]+)\|([^()]+)\)(.*)/){ # cope with: old-perl vs. new-php
				$entry_mod = $1.'(?<'.$2.$3.')'.$5.'|'.$1.'(?<'.$2.$4.')'.$5;
			}
			if($url =~ /https?:\/\/+[a-z0-9_.-]*(?:$entry_mod)/i){    # if url in current spamlist
				$found_entry = 1;
				$output.="\t\t".'<li class="'.(($project=~/white/) ? 'whiteentry': 'blackentry').'">'."\n\t\t\t".'<span class="foundentry">'.quote_html($entry)."</span>\n\t\t\t<ul>\n";
				$output.="\t\t\t\t".'<li class="comment">additional comment: '.$entry_comment."</li>\n" if $entry_comment ne '';
				$log_used{$project} = search_logs(\$output, $debug, \%spamlistlogs, $project, $entry, $url, $mech, \%last_updates, $forcepurge);
				$output.="\t\t\t</ul>\n\t\t</li>\n";
			}
		}
		if(defined $last_updates{$project}){
			#print STDERR Dumper $last_updates{$project};
			$output.="\t\t".'<li class="noentries">no entries here.</li>'."\n" if !$found_entry;
			if((not defined $last_update) || $last_update>min({'list'=>1, 'log'=>$log_used{$project}}, [values %{$last_updates{$project}}])){
				$last_update = min({'list'=>1, 'log'=>$log_used{$project}}, [values %{$last_updates{$project}}]);
			}
			# if each list should have the information of last update
			# $last_update = min({'list'=>1, 'log'=>$log_used{$project}}, [values %{$last_updates{$project}}]);
			# $output.="\t\t".'<li class="lastupdate">'.
			#	 '(last update of '.$project.'list: '.unixtime2time_diff_to_now($last_update).
			#	 ' minutes ago;';
			# $output.=' if you want to fetch live data, click on <a href="'.gen_cgi_request($cgi, {'purge'=>1}).'">purge</a>)' if unixtime2time_diff_to_now($last_update) >4;
			#$output.='</li>'."\n";
			$output.="\n";
		}
		$output.="\t</ul>\n";
		$output =~s/class="(?:external text|mw-redirect)"/class="external"/g;         # just for my css-file
		$output =~s/(href="[^"]+")((?:[^>](?!class="))*>)/$1 class="external"$2/g;
		print $output;
	}
	$last_update = unixtime2time_diff_to_now($last_update);
	$output = '(last update of lists: '.$last_update.' minutes ago';
	$output.= '; if you want to fetch live data, click on <a href="'.gen_cgi_request($cgi, {'purge'=>1}).'" class="external">purge</a>' if $last_update>4;
	$output.= ')';
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
die 'wrong project. please choose one of the above mentioned projects, e.g., wikipedia' if(defined $cgi->param('userdefproj') && ($cgi->param('userdefproj')!~/^[a-z]{1,4}\z/ || not defined $labels{$cgi->param('userdefproj')}));

my $template = HTML::Template->new(filename => 'grep_regexp_from_url.tpl');
my $script_name = $0;
$script_name =~s/^.*\///;
$template->param(
	css_file => 'format.css',
	version => '1.2.20131225',
	cgi_script => $script_name,
	userinput_url => ($cgi->param('url')) ? ' value="'.$cgi->param('url').'"' : '',
	userdeflang => ($cgi->param('userdeflang')) ? ' value="'.$cgi->param('userdeflang').'"' : '',
	userdefproj_select => $cgi->popup_menu('userdefproj', [keys %labels], (($cgi->param('userdefproj')) ? $cgi->param('userdefproj') : 'wikipedia'), \%labels),
	forcelogs => ($cgi->param('forcelogs') && $cgi->param('forcelogs')==1) ? ' checked="checked"' : ''
);
print $template->output();

if($cgi->param('url')){ # process form if url is submitted; otherwise display form only
	log_user_input($cgi);
	print '<p class="smallbold">results<br /><span id="lastupdate" class="xsmall"></span></p>',"\n";
	process_form($cgi, \%labels);
}
print "</body></html>\n";
