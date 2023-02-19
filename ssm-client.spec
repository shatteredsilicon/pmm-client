%define debug_package %{nil}

%define _GOPATH %{_builddir}/go

Name:           ssm-client
Summary:        Shattered Silicon Monitoring Client
Version:        %{_version}
Release:        1%{?dist}
Group:          Applications/Databases
License:        AGPLv3
Vendor:         Shattered Silicon
URL:            https://shatteredsilicon.net
Source:         ssm-client-%{_version}.tar.gz
AutoReq:        no
BuildRequires:  glibc-devel, golang, unzip, gzip, make, perl-ExtUtils-MakeMaker, git, systemd

Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd

%description
Shattered Silicon Monitoring (SSM) is an open-source platform for managing and monitoring MySQL and MongoDB
performance. It is a fork of Percona Monitoring and Management (PMM), which is developed by Percona in collaboration
with experts in the field of managed database services, and further improved by Shattered Silicon.
SSM is a free and open-source solution that you can run in your own environment for maximum security and reliability.
It provides thorough time-based analysis for MySQL and MongoDB servers to ensure that your data works as efficiently
as possible.

%prep
%setup -q -n ssm-client

%build
mkdir -p %{_GOPATH}

export GOPATH=%{_GOPATH}
export GO111MODULE=off

%{__mkdir_p} %{_GOPATH}/src/github.com/prometheus
%{__mkdir_p} %{_GOPATH}/src/github.com/shatteredsilicon
%{__mkdir_p} %{_GOPATH}/bin

tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/mongodb_exporter-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/mysqld_exporter-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/node_exporter-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/pid-watchdog-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/ssm-client-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/postgres_exporter-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/proxysql_exporter-*.tar.gz
tar -C %{_GOPATH}/src/github.com/shatteredsilicon -zxf %{_builddir}/ssm-client/qan-agent-*.tar.gz

# install promu
mv %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/vendor/github.com/prometheus/promu %{_GOPATH}/src/github.com/prometheus/
cp -R %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/vendor %{_GOPATH}/src/github.com/prometheus/promu/
cd %{_GOPATH}/src/github.com/prometheus/promu/
    go install -ldflags="-s -w" .

ln -s %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter %{_GOPATH}/src/github.com/prometheus/node_exporter
cd %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter
	%{__make} %{?_smp_mflags} build
	%{__mv} node_exporter %{_GOPATH}/bin

go install -ldflags="-s -w" github.com/shatteredsilicon/postgres_exporter/cmd/postgres_exporter
go install -ldflags="-s -w" github.com/shatteredsilicon/mongodb_exporter
go install -ldflags="-s -w" github.com/shatteredsilicon/proxysql_exporter
go install -ldflags="-s -w -X 'github.com/shatteredsilicon/ssm-client/pmm.Version=%{_version}'" github.com/shatteredsilicon/ssm-client
go install -ldflags="-s -w" github.com/shatteredsilicon/mysqld_exporter
go install -ldflags="-s -w" github.com/shatteredsilicon/pid-watchdog
go install -ldflags="-s -w" github.com/shatteredsilicon/qan-agent/bin/...

strip %{_GOPATH}/bin/* || true

%{__cp} %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/example.prom                       %{_builddir}/ssm-client/
%{__cp} %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/queries-mysqld.yml               %{_builddir}/ssm-client/
%{__cp} %{_GOPATH}/src/github.com/shatteredsilicon/ssm-client/scripts/ssm-dashboard                 %{_builddir}/ssm-client/

%install
install -m 0755 -d $RPM_BUILD_ROOT/usr/sbin
install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/sbin/ssm-admin
install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/sbin/pmm-admin
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/ssm-client
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/qan-agent/bin
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/ssm-client/textfile-collector
install -m 0755 -d $RPM_BUILD_ROOT/lib/systemd/system
install -m 0755 -d $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0755 -d $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0755 %{_GOPATH}/bin/node_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/mysqld_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/postgres_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/mongodb_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/proxysql_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/ssm-qan-agent $RPM_BUILD_ROOT/opt/ss/qan-agent/bin/
install -m 0755 %{_GOPATH}/bin/ssm-qan-agent-installer $RPM_BUILD_ROOT/opt/ss/qan-agent/bin/
install -m 0644 %{_builddir}/ssm-client/queries-mysqld.yml $RPM_BUILD_ROOT/opt/ss/ssm-client
install -m 0755 %{_builddir}/ssm-client/example.prom $RPM_BUILD_ROOT/opt/ss/ssm-client/textfile-collector/
install -m 0755 %{_builddir}/ssm-client/ssm-dashboard $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/support-files/config/node_exporter.conf $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/support-files/config/mysqld_exporter.conf $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mongodb_exporter/support-files/config/mongodb_exporter.conf $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/postgres_exporter/support-files/config/postgres_exporter.conf $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/proxysql_exporter/support-files/config/proxysql_exporter.conf $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/ssm-linux-metrics.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-linux-metrics.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/ssm-mysql-metrics.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-mysql-metrics.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/qan-agent/ssm-mysql-queries.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-mysql-queries.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mongodb_exporter/ssm-mongodb-metrics.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-mongodb-metrics.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/qan-agent/ssm-mongodb-queries.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-mongodb-queries.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/postgres_exporter/ssm-postgresql-metrics.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-postgresql-metrics.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/proxysql_exporter/ssm-proxysql-metrics.service $RPM_BUILD_ROOT/lib/systemd/system/ssm-proxysql-metrics.service
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mongodb_exporter/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/postgres_exporter/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/proxysql_exporter/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/qan-agent/support-files/rsyslog.d/* $RPM_BUILD_ROOT/etc/rsyslog.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/mongodb_exporter/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/postgres_exporter/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/proxysql_exporter/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/
install -m 0644 %{_GOPATH}/src/github.com/shatteredsilicon/qan-agent/support-files/logrotate.d/* $RPM_BUILD_ROOT/etc/logrotate.d/

%clean
rm -rf $RPM_BUILD_ROOT

%post
%systemd_post ssm-linux-metrics.service
%systemd_post ssm-mysql-metrics.service
%systemd_post ssm-mysql-queries.service
%systemd_post ssm-mongodb-metrics.service
%systemd_post ssm-mongodb-queries.service
%systemd_post ssm-postgresql-metrics.service
%systemd_post ssm-proxysql-metrics.service

%preun
# uninstall
if [ "$1" = "0" ]; then
    ssm-admin uninstall
fi

%systemd_preun ssm-linux-metrics.service
%systemd_preun ssm-mysql-metrics.service
%systemd_preun ssm-mysql-queries.service
%systemd_preun ssm-mongodb-metrics.service
%systemd_preun ssm-mongodb-queries.service
%systemd_preun ssm-postgresql-metrics.service
%systemd_preun ssm-proxysql-metrics.service

%postun
# uninstall
if [ "$1" = "0" ]; then
    rm -rf /opt/ss/ssm-client
    rm -rf /opt/ss/qan-agent
    echo "Uninstall complete."
fi

%systemd_postun ssm-linux-metrics.service
%systemd_postun ssm-mysql-metrics.service
%systemd_postun ssm-mysql-queries.service
%systemd_postun ssm-mongodb-metrics.service
%systemd_postun ssm-mongodb-queries.service
%systemd_postun ssm-postgresql-metrics.service
%systemd_postun ssm-proxysql-metrics.service

%files
%dir /opt/ss/ssm-client
%dir /opt/ss/ssm-client/textfile-collector
%dir /opt/ss/qan-agent/bin
/opt/ss/ssm-client/textfile-collector/*
/opt/ss/ssm-client/*
/opt/ss/qan-agent/bin/*
/usr/sbin/ssm-admin
/usr/sbin/pmm-admin
/lib/systemd/system/ssm-linux-metrics.service
/lib/systemd/system/ssm-mysql-metrics.service
/lib/systemd/system/ssm-mysql-queries.service
/lib/systemd/system/ssm-mongodb-metrics.service
/lib/systemd/system/ssm-mongodb-queries.service
/lib/systemd/system/ssm-postgresql-metrics.service
/lib/systemd/system/ssm-proxysql-metrics.service
/etc/rsyslog.d/ssm-*.conf
/etc/logrotate.d/ssm-*
