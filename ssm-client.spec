%define debug_package %{nil}

%define _GOPATH %{_builddir}/go

Name:           ssm-client
Summary:        Percona Monitoring and Management Client
Version:        %{_version}
Release:        11%{?dist}
Group:          Applications/Databases
License:        AGPLv3
Vendor:         Percona LLC
URL:            https://percona.com
Source:         ssm-client-%{_version}.tar.gz
AutoReq:        no
BuildRequires:  glibc-devel, golang, unzip, gzip, make, perl-ExtUtils-MakeMaker, git

%description
Percona Monitoring and Management (PMM) is an open-source platform for managing and monitoring MySQL and MongoDB
performance. It is developed by Percona in collaboration with experts in the field of managed database services,
support and consulting.
PMM is a free and open-source solution that you can run in your own environment for maximum security and reliability.
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
    go install .

ln -s %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter %{_GOPATH}/src/github.com/prometheus/node_exporter
cd %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter
	%{__make} %{?_smp_mflags} build
	%{__mv} node_exporter %{_GOPATH}/bin

cd %{_GOPATH}/src/github.com/shatteredsilicon/postgres_exporter
	go build github.com/shatteredsilicon/postgres_exporter/cmd/postgres_exporter
	%{__mv} postgres_exporter %{_GOPATH}/bin

go install github.com/shatteredsilicon/mongodb_exporter
go install github.com/shatteredsilicon/proxysql_exporter
go install github.com/shatteredsilicon/ssm-client
go install github.com/shatteredsilicon/mysqld_exporter
go install github.com/shatteredsilicon/pid-watchdog
go install github.com/shatteredsilicon/qan-agent/bin/...

strip %{_GOPATH}/bin/* || true

%{__cp} %{_GOPATH}/src/github.com/shatteredsilicon/node_exporter/example.prom		%{_builddir}/ssm-client/
%{__cp} %{_GOPATH}/src/github.com/shatteredsilicon/mysqld_exporter/queries-mysqld.yml	%{_builddir}/ssm-client/

%install
%if 0%{?rhel} == 5
    install -m 0755 -d $RPM_BUILD_ROOT/usr/bin
    install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/bin/ssm-admin
    install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/bin/pmm-admin
%else
    install -m 0755 -d $RPM_BUILD_ROOT/usr/sbin
    install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/sbin/ssm-admin
    install -m 0755 %{_GOPATH}/bin/ssm-client $RPM_BUILD_ROOT/usr/sbin/pmm-admin
%endif
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/ssm-client
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/qan-agent/bin
install -m 0755 -d $RPM_BUILD_ROOT/opt/ss/ssm-client/textfile-collector
install -m 0755 %{_GOPATH}/bin/node_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/mysqld_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/postgres_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/mongodb_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/proxysql_exporter $RPM_BUILD_ROOT/opt/ss/ssm-client/
install -m 0755 %{_GOPATH}/bin/ssm-qan-agent $RPM_BUILD_ROOT/opt/ss/qan-agent/bin/
install -m 0755 %{_GOPATH}/bin/ssm-qan-agent-installer $RPM_BUILD_ROOT/opt/ss/qan-agent/bin/
install -m 0644 %{_builddir}/ssm-client/queries-mysqld.yml $RPM_BUILD_ROOT/opt/ss/ssm-client
install -m 0755 %{_builddir}/ssm-client/example.prom $RPM_BUILD_ROOT/opt/ss/ssm-client/textfile-collector/

%clean
rm -rf $RPM_BUILD_ROOT

%post
# upgrade
ssm-admin ping > /dev/null
if [ $? = 0 ] && [ "$1" = "2" ]; then
%if 0%{?rhel} == 6
    for file in $(find -L /etc/init.d -maxdepth 1 -name "pmm-*")
    do
        sed -i 's|^name=$(basename $0)|name=$(basename $(readlink -f $0))|' "$file"
    done
    for file in $(find -L /etc/init.d -maxdepth 1 -name "pmm-linux-metrics*")
    do
        sed -i  "s/,meminfo_numa /,meminfo_numa,textfile /" "$file"
    done
    for file in $(find -L /etc/init -maxdepth 1 -name "pmm-linux-metrics*")
    do
        sed -i  "s/,meminfo_numa /,meminfo_numa,textfile /" "$file"
    done
%else
    for file in $(find -L /etc/systemd/system -maxdepth 1 -name "pmm-*")
    do
        network_exists=$(grep -c "network.target" "$file")
        if [ $network_exists = 0 ]; then
            sed -i 's/Unit]/Unit]\nAfter=network.target\nAfter=syslog.target/' "$file"
        fi
    done
    for file in $(find -L /etc/systemd/system -maxdepth 1 -name "pmm-linux-metrics*")
    do
        sed -i  "s/,meminfo_numa /,meminfo_numa,textfile /" "$file"
    done
%endif
    ssm-admin restart --all
fi

%preun
# uninstall
if [ "$1" = "0" ]; then
    ssm-admin uninstall
fi

%postun
# uninstall
if [ "$1" = "0" ]; then
    rm -rf /opt/ss/ssm-client
    rm -rf /opt/ss/qan-agent
    echo "Uninstall complete."
fi

%files
%dir /opt/ss/ssm-client
%dir /opt/ss/ssm-client/textfile-collector
%dir /opt/ss/qan-agent/bin
/opt/ss/ssm-client/textfile-collector/*
/opt/ss/ssm-client/*
/opt/ss/qan-agent/bin/*
%if 0%{?rhel} == 5
    /usr/bin/ssm-admin
    /usr/bin/pmm-admin
%else
    /usr/sbin/ssm-admin
    /usr/sbin/pmm-admin
%endif
