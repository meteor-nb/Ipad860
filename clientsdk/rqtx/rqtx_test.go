package rqtx_test

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"sync"
	"testing"

	"wechatdll/clientsdk/rqtx"
)

type oracleCase struct {
	Name     string `json:"name"`
	InputHex string `json:"input_hex"`
	Output   uint32 `json:"output"`
}

type oracleVectors struct {
	Method    string       `json:"method"`
	DLLSHA256 string       `json:"dll_sha256"`
	DatSHA256 string       `json:"dat_sha256"`
	Seed      int64        `json:"seed"`
	Cases     []oracleCase `json:"cases"`
}

func loadVectors(t testing.TB) oracleVectors {
	t.Helper()
	data, err := os.ReadFile("testdata/oracle-vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors oracleVectors
	if err := json.Unmarshal(data, &vectors); err != nil {
		t.Fatal(err)
	}
	if vectors.Method == "" || vectors.DLLSHA256 != "aeab62515c77dcb3e56ce6180a5635d1c16ecd747f9f9b6366b2005544a3f756" ||
		vectors.DatSHA256 != "57def9708a23be4992fc0024754da9eaa8179651d210a3fe5e72cf3d9cdd2c6d" ||
		vectors.Seed != 86020261025 || len(vectors.Cases) != 327 {
		t.Fatalf("unexpected oracle source or case count: method=%q dll=%s dat=%s seed=%d cases=%d",
			vectors.Method, vectors.DLLSHA256, vectors.DatSHA256, vectors.Seed, len(vectors.Cases))
	}
	return vectors
}

func decodeInput(t testing.TB, c oracleCase) [32]byte {
	t.Helper()
	decoded, err := hex.DecodeString(c.InputHex)
	if err != nil {
		t.Fatalf("%s: invalid hex: %v", c.Name, err)
	}
	if len(decoded) != 32 {
		t.Fatalf("%s: got %d input bytes, want 32", c.Name, len(decoded))
	}
	var input [32]byte
	copy(input[:], decoded)
	return input
}

func TestOracleVectors(t *testing.T) {
	vectors := loadVectors(t)
	seenNames := make(map[string]bool, len(vectors.Cases))
	seenInputs := make(map[string]bool, len(vectors.Cases))
	for _, c := range vectors.Cases {
		if c.Name == "" || seenNames[c.Name] || seenInputs[c.InputHex] {
			t.Fatalf("missing or duplicate oracle case: %q", c.Name)
		}
		seenNames[c.Name] = true
		seenInputs[c.InputHex] = true
		input := decodeInput(t, c)
		t.Run(c.Name, func(t *testing.T) {
			for repeat := 0; repeat < 2; repeat++ {
				if got := rqtx.Sum32(input); got != c.Output {
					t.Fatalf("repeat %d: Sum32(%s) = %#08x, want %#08x", repeat, c.InputHex, got, c.Output)
				}
			}
		})
	}
}

func TestConcurrentSum32(t *testing.T) {
	vectors := loadVectors(t)
	type sample struct {
		input [32]byte
		want  uint32
	}
	samples := make([]sample, len(vectors.Cases))
	for i, c := range vectors.Cases {
		samples[i] = sample{input: decodeInput(t, c), want: c.Output}
	}
	const workers = 16
	results := make(chan string, workers)
	var wg sync.WaitGroup
	for worker := 0; worker < workers; worker++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for _, s := range samples {
				before := s.input
				if got := rqtx.Sum32(s.input); got != s.want {
					results <- "concurrent output differs from oracle"
					return
				}
				if s.input != before {
					results <- "input changed"
					return
				}
			}
		}()
	}
	wg.Wait()
	close(results)
	for result := range results {
		t.Error(result)
	}
}

func BenchmarkSum32(b *testing.B) {
	input := [32]byte{'0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0'}
	var output uint32
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		output = rqtx.Sum32(input)
	}
	_ = output
}
