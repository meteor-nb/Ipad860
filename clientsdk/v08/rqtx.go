package v08

import (
	"runtime"
	"strings"

	"wechatdll/clientsdk/rqtx"
)

// Rqtx computes the checksum from the first 32 bytes, matching the native
// function's fixed input length. Short inputs return zero instead of allowing
// the native implementation to read beyond the supplied string.
func Rqtx(md5 string) uint32 {
	return rqtxForOS(md5, runtime.GOOS)
}

func rqtxForOS(md5, goos string) uint32 {
	// The former Windows dynlib.Call rejected NUL anywhere in the string.
	if goos == "windows" && strings.IndexByte(md5, 0) >= 0 {
		return 0
	}
	if len(md5) < 32 {
		return 0
	}
	var input [32]byte
	copy(input[:], md5)
	return rqtx.Sum32(input)
}
