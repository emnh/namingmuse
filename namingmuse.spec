%define python_site %(python -c 'from distutils import sysconfig; print sysconfig.get_python_lib()')

Summary: A music file tagger/renamer.
Name: namingmuse
Version: 0.9.0
Release: 1emh
URL: http://namingmuse.berlios.de
Source: http://download.berlios.de/namingmuse/namingmuse-%{version}.tar.gz
Group: Applications/Multimedia
License: GPL
BuildRoot: %{_tmppath}/%name-%version-buildroot-%(id -nu)
Requires: python, taglib, python-taglib
BuildArch: noarch

%description
The overall goal is to automatically provide good and plentiful
metainformation for music libraries from an online source, especially
focused on automating the selection of "good" metainformation such that
large music libraries can be tagged speedily with the least possible
user intervention. Consistent naming policies and automated touchup
of downloaded metainformation will be supported. Good default naming
policies will be a priority, but they will be made configurable. In
its current incarnation, namingmuse is a library/application for
accessing the online discography site freedb (http://www.freedb.org)
and renaming and tagging music albums with the metainformation from
the site (such as year, genre, album name, title, artist etc). It
supports freedb disc id generation from the music file types supported
by taglib, and full text search using a HTML-parser on the freedb website.

%prep
%setup -q

%build
%{__make} doc
%{__python} setup.py build

%install
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=%{buildroot}

%clean
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
%doc COPYING README TODO Changelog PKG-INFO tools
%{python_site}/namingmuse
%{_bindir}/nmuse

%changelog
* Fri Sep 17 2004 Eivind Magnus Hvidevold <emh at hvidevold dot cjb dot net>
- Namingmuse 0.8.3.

* Thu Sep 16 2004 Eivind Magnus Hvidevold <emh at hvidevold dot cjb dot net>
- Spec file for namingmuse 0.8.2, initial release. Tested on tinysofa.
