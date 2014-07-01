<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html>
<head>
	<title>convert google redirects to original url</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
 	<meta http-equiv="Content-Script-Type" content="text/javascript">
	<meta http-equiv="Content-Style-Type" content="text/css">
	<link rel="stylesheet" type="text/css" href="<TMPL_VAR NAME="css_file">">
</head>
<body>
	<p>
		convert redirects to original url. <span class="xxsmall">(version: <TMPL_VAR NAME="version">; report bugs at <a href="http://meta.wikimedia.org/wiki/user_talk:lustiger_seth" class="external">meta:user talk:lustiger_seth</a>)</span>
	</p>
	<form name="urlform" method="post" action="<TMPL_VAR NAME="cgi_script">">
		<fieldset><legend><span class="smallbold">.url</span></legend>
			<label for="url">
				type in url<br />
				supported redirect types: google, achive.today<br />
				(e.g. "http://www.google.com/url?url=http%3A%2F%2Fen.wikipedia.org"):<br /><br /></label>
			<input type="text" class="urlinput normalinput" name="url" id="url"<TMPL_VAR NAME="userinput_url"> />&nbsp;
			<input type="submit" name="fsubmit" />
		</fieldset>
	</form>
	<hr />
<!-- </body></html> -->
