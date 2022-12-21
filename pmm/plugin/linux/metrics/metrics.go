package metrics

import (
	"context"
	"fmt"
	"path"
	"strconv"
	"strings"

	"github.com/shatteredsilicon/ssm-client/pmm/plugin"
	"github.com/shatteredsilicon/ssm-client/pmm/plugin/linux"
	"gopkg.in/ini.v1"
)

var _ plugin.Metrics = (*Metrics)(nil)

// New returns *Metrics.
func New(ssmBaseDir string) *Metrics {
	return &Metrics{
		ssmBaseDir: ssmBaseDir,
	}
}

// Metrics implements plugin.Metrics.
type Metrics struct {
	ssmBaseDir string
	port       int
}

// Init initializes plugin.
func (m *Metrics) Init(
	ctx context.Context,
	ssmUserPassword string,
	bindAddress string,
	authFile string,
	sslKeyFile string,
	sslCertFile string,
) (*plugin.Info, error) {
	cfgPath := path.Join(m.ssmBaseDir, "node_exporter.conf")
	cfgFile, err := ini.Load(cfgPath)
	if err != nil {
		return nil, err
	}

	parts := strings.Split(cfgFile.Section("web").Key("listen-address").Value(), ":")
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid configuration for web.listen-address")
	}
	port, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil || port <= 0 {
		return nil, fmt.Errorf("invalid configuration for web.listen-address")
	}

	cfgFile.Section("web").Key("listen-address").SetValue(fmt.Sprintf("%s:%d", bindAddress, port))
	cfgFile.Section("web").Key("ssl-key-file").SetValue(sslKeyFile)
	cfgFile.Section("web").Key("ssl-cert-file").SetValue(sslCertFile)
	err = cfgFile.SaveTo(cfgPath)
	if err != nil {
		return nil, err
	}

	m.port = int(port)
	return linux.GetInfo()
}

// Name of the exporter.
func (Metrics) Name() string {
	return plugin.NameLinux
}

// Port returns default port.
func (m Metrics) Port() int {
	return m.port
}

// Executable is a name of exporter executable under PMMBaseDir.
func (Metrics) Executable() string {
	return plugin.NodeExporter
}

// KV is a list of additional Key-Value data stored in consul.
func (Metrics) KV() map[string][]byte {
	return nil
}

// Cluster defines cluster name for the target.
func (Metrics) Cluster() string {
	return ""
}
