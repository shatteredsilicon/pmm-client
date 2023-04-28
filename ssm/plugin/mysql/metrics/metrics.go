package metrics

import (
	"context"
	"database/sql"
	"fmt"
	"path"
	"strconv"
	"strings"

	"github.com/shatteredsilicon/ssm-client/ssm/plugin"
	"github.com/shatteredsilicon/ssm-client/ssm/plugin/mysql"
	"github.com/shatteredsilicon/ssm-client/ssm/utils"
	"gopkg.in/ini.v1"
)

var _ plugin.Metrics = (*Metrics)(nil)

// Flags are Metrics Metrics specific flags.
type Flags struct {
	DisableTableStats      bool
	DisableTableStatsLimit uint16
	DisableUserStats       bool
	DisableBinlogStats     bool
	DisableProcesslist     bool
}

// New returns *Metrics.
func New(flags Flags, mysqlFlags mysql.Flags, ssmBaseDir string) *Metrics {
	return &Metrics{
		flags:      flags,
		mysqlFlags: mysqlFlags,
		ssmBaseDir: ssmBaseDir,
	}
}

// Metrics implements plugin.Metrics.
type Metrics struct {
	flags         Flags
	mysqlFlags    mysql.Flags
	ssmBaseDir    string
	port          int
	dsn           string
	optsToDisable []string
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
	info, err := mysql.Init(ctx, m.mysqlFlags, ssmUserPassword)
	if err != nil {
		return nil, err
	}
	m.dsn = info.DSN

	m.optsToDisable, err = optsToDisable(ctx, m.dsn, m.flags)
	if err != nil {
		return nil, err
	}

	cfgPath := path.Join(m.ssmBaseDir, "mysqld_exporter.conf")
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
	m.port = int(port)

	// updates collect args
	for _, args := range m.collectArgs() {
		if args == nil {
			continue
		}

		for k, v := range args {
			cfgFile.Section("collect").Key(k).SetValue(v)
		}
	}

	cfgFile.Section("exporter").Key("dsn").SetValue(m.dsn)
	cfgFile.Section("web").Key("auth-file").SetValue(authFile)
	cfgFile.Section("web").Key("ssl-key-file").SetValue(sslKeyFile)
	cfgFile.Section("web").Key("ssl-cert-file").SetValue(sslCertFile)
	err = cfgFile.SaveTo(cfgPath)
	if err != nil {
		return nil, err
	}

	return info, nil
}

// Name of the exporter.
func (m Metrics) Name() string {
	return plugin.NameMySQL
}

// Port returns bind port.
func (m Metrics) Port() int {
	return m.port
}

// collectArgs is a list of additional collect arguments
// that should be updated in config file
func (m Metrics) collectArgs() []map[string]string {
	// disableArgs is a list of optional ssm-admin args to disable mysqld_exporter args.
	var disableArgs = map[string]map[string]string{
		"tablestats": {
			"auto_increment.columns":   "0",
			"info_schema.tables":       "0",
			"info_schema.tablestats":   "0",
			"perf_schema.indexiowaits": "0",
			"perf_schema.tableiowaits": "0",
			"perf_schema.tablelocks":   "0",
		},
		"userstats":   {"info_schema.userstats": "0"},
		"binlogstats": {"binlog_size": "0"},
		"processlist": {"info_schema.processlist": "0"},
	}

	// Disable exporter options if set so.
	args := make([]map[string]string, 0)
	for _, o := range m.optsToDisable {
		args = append(args, disableArgs[o])
	}
	return args
}

// Executable is a name of exporter executable under SSMBaseDir.
func (m Metrics) Executable() string {
	return plugin.MySQLExporter
}

// KV is a list of additional Key-Value data stored in consul.
func (m Metrics) KV() map[string][]byte {
	kv := map[string][]byte{}
	kv["dsn"] = []byte(utils.SanitizeDSN(m.dsn))
	for _, o := range m.optsToDisable {
		kv[o] = []byte("OFF")
	}
	return kv
}

// Cluster defines cluster name for the target.
func (m Metrics) Cluster() string {
	return ""
}

func optsToDisable(ctx context.Context, dsn string, flags Flags) ([]string, error) {
	// Opts to disable.
	var optsToDisable []string
	if !flags.DisableTableStats {
		tableCount, err := tableCount(ctx, dsn)
		if err != nil {
			return nil, err
		}
		// Disable table stats if number of tables is higher than limit.
		if uint16(tableCount) > flags.DisableTableStatsLimit {
			flags.DisableTableStats = true
		}
	}
	if flags.DisableTableStats {
		optsToDisable = append(optsToDisable, "tablestats")
	}
	if flags.DisableUserStats {
		optsToDisable = append(optsToDisable, "userstats")
	}
	if flags.DisableBinlogStats {
		optsToDisable = append(optsToDisable, "binlogstats")
	}
	if flags.DisableProcesslist {
		optsToDisable = append(optsToDisable, "processlist")
	}

	return optsToDisable, nil
}

func tableCount(ctx context.Context, dsn string) (int, error) {
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return 0, err
	}
	defer db.Close()

	tableCount := 0
	err = db.QueryRowContext(ctx, "SELECT COUNT(*) FROM information_schema.tables").Scan(&tableCount)
	return tableCount, err
}
