package utils

var (
	iniTrueValues  = []string{"1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"}
	iniFalseValues = []string{"0", "flase", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"}
)

// CompareINIValues returns
// -1 if val1 < val2
// 0 if val1 = val2
// 1 if val1 > val2
func CompareINIValues(val1, val2 string) int {
	if val1 == val2 ||
		(SliceContains(iniTrueValues, val1) && SliceContains(iniTrueValues, val2)) ||
		(SliceContains(iniFalseValues, val1) && SliceContains(iniFalseValues, val2)) {
		return 0
	}

	if val1 < val2 {
		return -1
	}

	return 1
}
