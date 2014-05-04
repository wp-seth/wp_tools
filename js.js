function get_searched_urls(){
	var l = document.urlform.userdeflang.value;
	var p;
	var handler = document.createAttribute("onchange");
	handler.nodeValue = "get_searched_urls()";
	document.getElementsByName('userdefproj')[0].setAttributeNode(handler);
  for(var i=0; i<document.urlform.userdefproj.length; ++i)
		if(document.urlform.userdefproj.options[i].selected == true)
			p = document.urlform.userdefproj.options[i].text;
	var out = '<br />urls to be used:<br />';
	out += 'http://meta.wikimedia.org/wiki/MediaWiki:Spam-blacklist<br />'
	if(l==''){
	}else{
		if(l>0 && l<58){
			out += '' + l + ' biggest wiki-projects (spam-blacklists and spam-whitelists; max = 57)';
		}else if(/^[a-z0-9]+\z/.test(l)){
			out += 'http://'+l+'.'+p+'.org/wiki/MediaWiki:Spam-blacklist<br />'
			     + 'http://'+l+'.'+p+'.org/wiki/MediaWiki:Spam-whitelist';
			if(l=='en' && p=='wikipedia')
				out += '<br />http://en.wikipedia.org/wiki/User:XLinkBot/RevertList';
		}else{
			// wrong language
		}
	}
	document.getElementById('searchedurls').innerHTML = out;
}
