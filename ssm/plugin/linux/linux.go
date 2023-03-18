package linux

import (
	"syscall"

	"github.com/shatteredsilicon/ssm-client/ssm/plugin"
)

func int8ToStr(arr []int8) string {
	b := make([]byte, 0, len(arr))
	for _, v := range arr {
		if v == 0x00 {
			break
		}
		b = append(b, byte(v))
	}
	return string(b)
}

func GetInfo() (*plugin.Info, error) {
	var uname syscall.Utsname
	if err := syscall.Uname(&uname); err != nil {
		return nil, err
	}

	return &plugin.Info{
		Distro:  int8ToStr(uname.Sysname[:]),
		Version: int8ToStr(uname.Release[:]),
	}, nil
}
