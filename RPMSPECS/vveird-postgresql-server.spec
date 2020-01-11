Name:           vveird-postgresql-server
Version:        12.1
Release:        0%{?dist}
Summary:        PostgreSQL Server with separate install path
License:        PostgreSQL License
URL:            https://github.com/VVEIRD/pgBackup
Source:         https:/raw.githubusercontent.com/VVEIRD/pgBackup/master/PG_SOURCES/postgresql-%{version}.tar.gz
BuildRoot:      %[_tmppath}/%{name}-buildroot/%{version}
BuildArch:      x86_64

BuildRequires: gcc
BuildRequires: make
BuildRequires: zlib-devel
BuildRequires: readline-devel
BuildRequires: openssl
BuildRequires: readline
BuildRequires: zlib      
BuildRequires: tar
Requires: readline
Requires: openssl
Requires: zlib
Requires: tar

%description
Custom PostgreSQL build with seperate install path

%global debug_package %{nil}

%prep
# pushd %{_sourcedir}
# wget %{source}
# tar -xvf postgresql-%{version}.tar.gz
# mv postgresql-%{version} vveird-postgresql-server-%{version}
# rm postgresql-%{version}.tar.gz
# tar -zcvf postgresql-%{version}.tar.gz vveird-postgresql-server-%{version}
# rm -rf vveird-postgresql-server-%{version}
# popd
%setup -q


%build
./configure --prefix=/u00/pgsql/12
%make_build


%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"
%make_install

%pre
if [ $(getent passwd postgres | wc -l) -eq 0 ]; then
   groupadd -g 4141 postgres &&
   useradd -c "PostgreSQL Server" -g postgres -d /u01/pgdata -u 4141 postgres
fi

%post
ln -s /u00/pgsql/12/lib/libpq.so.5 /usr/lib/libpq.so.5
ln -s /u00/pgsql/12/lib/libpq.so.5 /usr/lib64/libpq.so.5

%postun
rm /usr/lib/libpq.so.5
rm /usr/lib64/libpg.so.5
rm -R /u00/pgsql/12

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(-,root,root,-)
#%attr(755,root,root) /u00/pgsql/12/bin/*
#%attr(755,root,root) /u00/pgsql/12/include/*
#%attr(755,root,root) /u00/pgsql/12/lib/*
#%attr(644,root,root) /u00/pgsql/12/share/*
%dir /u00/pgsql/12
/u00/pgsql/12

%changelog
* Tue Jan  7 2020 build
- 
