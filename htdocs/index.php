<!DOCTYPE html
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title>namingmuse</title>
    <meta http-equiv="Content-Type"
    content="text/xml; charset=iso-8859-1" />
<style type="text/css" media="screen">@import "new.css";</style>
</head>
<body>


<div class="content">
    <h1 id="synopsis">Namingmuse</h1>

<h3>A music file naming program.</h3>
<p>Renames files, folders. Sets tags.</p>
<h3>Ambitions</h3>
<p>
The overall goal is to automatically provide good and plentiful metainformation for your digitized music collection from an online source, especially focused on automating the selection of "good" metainformation such that large music collections can be tagged speedily with the least possible user intervention. 
<br /><br />
Consistent naming policies and automated touchup of downloaded metainformation will be supported. Good default naming policies will be a priority, but they will be made configurable. In its current incarnation, namingmuse is a library/application for accessing the online discography site <a href="//freedb.org">freedb</a> and renaming and tagging music albums with the metainformation from the site (such as year, genre, album name, title, artist etc). 
<br /><br />
It currently supports freedb disc id generation from the music file types supported by <a href="http://http://developer.kde.org/~wheeler/taglib.html">TagLib</a>, and full text search using a HTML-parser on the freedb website. Future version will support multiple backends for metainformation with the possibilty to merge these for optimal result.
<br /><br />
Namingmuse is an album oriented tagger. It assumes that the files are already organized as one album pr directory.
</p>
</div>

<div class="content">
    <h1 id="download">Version 1.0.0 Released!</h1>
    <pre>
        * Add musicbrainz support with puid.
        * Fix mpc and flac support.
        * Add ncurses interface for manual namebinding.
        * Add rollback support for incomplete renames.
        * Add ignore option for ignoring directories in recursive mode.
        * Documentation updates.
        * Added test suite.
    </pre>
    <h2>Download</h2>
	<ul>
		<li><a href="http://download.berlios.de/namingmuse/namingmuse-1.0.0.tar.gz">Namingmuse 1.0.0</a></li>
	<li><a href="http://developer.berlios.de/project/showfiles.php?group_id=2066">Namingmuse file releases at berlios</a></li>
	</ul>
</div>


<div class="content">
    <h1 id="download">Version 0.9.2 Released!</h1>
    <p>
        Switched from python-taglib to tagpy bindings. Should ease installation significantly. Requires tagpy 0.94.5 for full encoding support.
    </p>
    <h2>Download</h2>
	<ul>
		<li><a href="http://download.berlios.de/namingmuse/namingmuse-0.9.2.tar.gz">Namingmuse 0.9.2</a></li>
	<li><a href="http://developer.berlios.de/project/showfiles.php?group_id=2066">Namingmuse file releases at berlios</a></li>
	</ul>
</div>

<div class="content">
<p>
    A screenshot showing full-text search and string approximation in action.
</p>
<img src="nmuse.png" alt="Namingmuse Screenshot" />
</div>

<div id="navAlpha">
    <h3>
       Navigation 
    </h3>
    <a href="#synopsis">- Synopsis</a><br />
    <a href="#download">- Download</a><br />
    <a href="//developer.berlios.de/projects/namingmuse/">- Development</a><br />
    
    <h3>
        Contact
    </h3>
    <a href="mailto:namingmuse-devel @ lists berlios de">Project mailing list</a>
    <h3>
	Authors
    </h3>
    <a href="mailto:hvidevold @ gmail dot com">Eivind M. Hvidevold</a><br />
    <a href="mailto:tor @ bash dot no">Tor Hveem</a><br />
</div>


<div id="navBeta">
    <h2>Links</h2>
        <p>
            <a href="//developer.kde.org/~wheeler/taglib.html">TagLib</a><br />
        </p>
    <h2>Classifier</h2>
	<p>
	<b>Development Status</b>:<br /> 5 - Production/Stable<br />
	<b>Environment</b> :<br /> Console<br />
	<b>Intended Audience</b> :<br /> End Users/Desktop<br />
	<b>License</b> :<br /> GNU General Public License (GPL)<br />
	<b>Natural Language </b>:<br /> English<br />
	<b>Operating> System </b>:<br /> Linux<br />
	<b>Programming Language </b>:<br /> Python<br />
	<b>Topic </b>:<br /> Multimedia : Sound/Audio<br />
	</p>

        <p>
         <a href="http://validator.w3.org/check/referer"><img
              src="http://www.w3.org/Icons/valid-xhtml10"
              alt="Valid XHTML 1.0!" height="31" width="88" /></a>
	 <a href="http://jigsaw.w3.org/css-validator/check/referer">
	  <img style="border:0;width:88px;height:31px"
	       src="http://jigsaw.w3.org/css-validator/images/vcss" 
	       alt="Valid CSS!" />
	 </a>
	 <a href="http://developer.berlios.de" title="BerliOS Developer">
	  <img style="border:0;height:32px;width:124px;" src="http://developer.berlios.de/bslogo.php?group_id=2066" alt="BerliOS Developer Logo" />
         </a>
	</p>
</div>

</body>
</html>



