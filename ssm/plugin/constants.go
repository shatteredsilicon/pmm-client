package plugin

// Service names
const (
	NameLinux      = "linux"
	NameMySQL      = "mysql"
	NameMongoDB    = "mongodb"
	NamePostgreSQL = "postgresql"
	NameProxySQL   = "proxysql"
)

// Exporter names
const (
	NodeExporter       = "node_exporter"
	MySQLExporter      = "mysqld_exporter"
	MongoDBExporter    = "mongodb_exporter"
	PostgreSQLExporter = "postgres_exporter"
	ProxySQLExporter   = "proxysql_exporter"
	QanAgent           = "qan-agent"
)

// Data types
const (
	TypeMetrics = "metrics"
	TypeQueries = "queries"
)
