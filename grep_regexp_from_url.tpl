<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
<head>
	<title>search spamlists</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 	<meta http-equiv="Content-Script-Type" content="text/javascript">
	<meta http-equiv="Content-Style-Type" content="text/css">
	<link rel="stylesheet" type="text/css" href="<TMPL_VAR NAME="css_file">">
	<script src="js.js" type="text/javascript">
	</script>
</head>
<body onload="get_searched_urls()">
	<p>search some wikipedia spamlists for a given url. <span class="xxsmall">(version: <TMPL_VAR NAME="version">; report bugs at <a href="//meta.wikimedia.org/wiki/user_talk:lustiger_seth" class="external">meta:user talk:lustiger_seth</a>)</span></p>
	<form name="urlform" method="post" action="<TMPL_VAR NAME="cgi_script">">
		<fieldset><legend><span class="smallbold">.url</span></legend>
			<label for="url">type in url (e.g. "http://www.example.org/something.html" or without "http://"):<br /></label>
			<input type="text" class="urlinput normalinput" name="url" id="url"<TMPL_VAR NAME="userinput_url"> />&nbsp;
			<input type="submit" name="fsubmit" />
		</fieldset>
		<fieldset><legend><span class="smallbold">.languages and projects</span></legend>
			<input type="text" class="langinput normalinput" name="userdeflang" id="userdeflang" onkeyup="get_searched_urls()"<TMPL_VAR NAME="userdeflang"> />
			<label for="userdeflang">user-defined language, e.g. <em>de</em>, <em>en</em> or <em>fr</em> (default = empty = search meta only).</label><br />
			<TMPL_VAR NAME="userdefproj_select">
			<label for="userdefproj">user-defined project, e.g. <em>wikipedia</em> (default = wikipedia).</label>
			<div id="searchedurls"></div>
		</fieldset>
<!--		<fieldset><legend><span class="smallbold">.logfiles</span></legend>
		<input type="checkbox" name="forcelogs" id="forcelogs"<TMPL_VAR NAME="forcelogs"> /><label for="forcelogs">search logfiles even if url is not on spamlist (default = off = search logfiles only if url is in some spamlist).</label>
		</fieldset>-->
	</form>
	<hr />
<!-- </body></html> -->
