/*
	Copyright (c) 2016, Percona LLC and/or its affiliates. All rights reserved.

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>
*/

package ssm

import (
	"errors"
	"fmt"
	"time"
)

const (
	qanAPIBasePath     = "qan-api"
	managedAPIBasePath = "managed"
	noMonitoring       = "No monitoring registered for this node identified as"
	apiTimeout         = 10 * time.Second
	NameRegex          = `^[-\w:\.]{2,60}$`
)

var (
	// you can use `-ldflags -X github.com/shatteredsilicon/ssm-client/pmm.Version=`
	// to set build version number
	Version = "1.17.4"

	// you can use `-ldflags -X github.com/shatteredsilicon/ssm-client/pmm.RootDir=`
	// to set root filesystem for ssm-admin
	RootDir = ""

	PMMBaseDir   = "/usr/local/percona/pmm-client"
	SSMBaseDir   = RootDir + "/opt/ss/ssm-client"
	AgentBaseDir = RootDir + "/opt/ss/qan-agent"

	ConfigFile  = fmt.Sprintf("%s/ssm.yml", SSMBaseDir)
	SSLCertFile = fmt.Sprintf("%s/server.crt", SSMBaseDir)
	SSLKeyFile  = fmt.Sprintf("%s/server.key", SSMBaseDir)

	ErrDuplicate  = errors.New("there is already one instance with this name under monitoring.")
	ErrNoService  = errors.New("no service found.")
	errNoInstance = errors.New("no instance found on QAN API.")
)

type Errors []error

func (e Errors) Error() string {
	return join(e, ", ")
}

// join concatenates the elements of a to create a single string. The separator string
// sep is placed between elements in the resulting string.
func join(a []error, sep string) string {
	if len(a) == 0 {
		return ""
	}
	if len(a) == 1 {
		return a[0].Error()
	}
	nilErr := fmt.Sprintf("%v", error(nil))
	n := len(sep) * (len(a) - 1)
	for i := 0; i < len(a); i++ {
		if a[i] == nil {
			n += len(nilErr)
		} else {
			n += len(a[i].Error())
		}
	}

	b := make([]byte, n)
	bp := copy(b, a[0].Error())
	for _, s := range a[1:] {
		bp += copy(b[bp:], sep)
		if s == nil {
			bp += copy(b[bp:], nilErr)
		} else {
			bp += copy(b[bp:], s.Error())
		}
	}
	return string(b)
}