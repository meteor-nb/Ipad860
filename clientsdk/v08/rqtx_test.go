package v08

import (
	"runtime"
	"strings"
	"testing"

	"wechatdll/clientsdk/rqtx"
)

func TestRqtxInputBoundary(t *testing.T) {
	for _, tc := range []struct {
		name  string
		input string
		want  uint32
	}{
		{"empty", "", 0},
		{"short", strings.Repeat("0", 31), 0},
		{"exact", strings.Repeat("0", 32), 0x440b4622},
		{"long-prefix", strings.Repeat("0", 32) + "ignored", 0x440b4622},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := Rqtx(tc.input); got != tc.want {
				t.Fatalf("Rqtx = %#08x, want %#08x", got, tc.want)
			}
		})
	}
}

func TestRqtxPlatformNULBoundary(t *testing.T) {
	prefix := strings.Repeat("0", 32)
	for _, tc := range []struct {
		name  string
		input string
	}{
		{"nul-at-0", "\x00" + prefix[1:]},
		{"nul-at-31", prefix[:31] + "\x00"},
		{"nul-at-32", prefix + "\x00"},
		{"nul-in-tail", prefix + "tail\x00"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var input [32]byte
			copy(input[:], tc.input)
			want := rqtx.Sum32(input)
			if got := rqtxForOS(tc.input, "linux"); got != want {
				t.Fatalf("Linux Rqtx = %#08x, want %#08x", got, want)
			}
			if got := rqtxForOS(tc.input, "windows"); got != 0 {
				t.Fatalf("Windows Rqtx = %#08x, want 0", got)
			}
			if got := Rqtx(tc.input); got != rqtxForOS(tc.input, runtime.GOOS) {
				t.Fatalf("host Rqtx = %#08x, platform helper mismatch", got)
			}
		})
	}
	for _, tc := range []struct {
		name  string
		input string
	}{
		{"exact", prefix},
		{"long", prefix + "tail"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			for _, goos := range []string{"linux", "windows"} {
				if got := rqtxForOS(tc.input, goos); got != 0x440b4622 {
					t.Fatalf("%s Rqtx = %#08x, want 0x440b4622", goos, got)
				}
			}
		})
	}
}
