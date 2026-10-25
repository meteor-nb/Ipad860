// Package rqtx implements the fixed 32-byte rqtx calculation recovered from
// v08.dll and rqtx.dat. It requires no native library or external data file.
package rqtx

import (
	"encoding/binary"
	"math/bits"
)

// Sum32 returns the rqtx value for exactly 32 input bytes. Callers passing an
// MD5 digest must supply its 32 ASCII hexadecimal bytes, not its 16 raw bytes.
// All working state belongs to this call; concurrent calls are independent.
func Sum32(input [32]byte) uint32 {
	inner := keyed256(input, 0xec)
	outer := keyed256(inner, 0xdf)
	digest := digest128(outer)
	var folded [3]byte
	for start := range folded {
		for _, b := range digest[start : start+14] {
			folded[start] = folded[start]*133 + b
		}
	}
	return 0x44000000 | uint32(folded[2]&0x7b)<<16 |
		uint32(folded[1]&0x6f)<<8 | uint32(folded[0]&0x3f)
}

// keyed256 hashes (key XOR pad) || input using the recovered 256-bit variant.
// Both rqtx stages have a 96-byte message, so their padding is always one block.
func keyed256(input [32]byte, pad byte) [32]byte {
	h := initial256
	var block [64]byte
	for i, b := range key {
		block[i] = b ^ pad
	}
	compress256(&h, &block)
	block = [64]byte{}
	copy(block[:], input[:])
	block[32] = 0xfc
	binary.BigEndian.PutUint64(block[56:], ^uint64(96*8))
	compress256(&h, &block)
	var out [32]byte
	for i, word := range h {
		binary.BigEndian.PutUint32(out[i*4:], word)
	}
	return out
}

func compress256(h *[8]uint32, block *[64]byte) {
	var w [64]uint32
	for i := 0; i < 16; i++ {
		b := block[i*4 : i*4+4]
		w[i] = uint32(b[0])<<24 | uint32(b[3])<<16 | uint32(b[2])<<8 | uint32(b[1])
	}
	for i := 16; i < len(w); i++ {
		x, y := w[i-2], w[i-15]
		s0 := bits.RotateLeft32(y, -3) ^ bits.RotateLeft32(y, -11) ^ (y >> 5)
		s1 := bits.RotateLeft32(x, -5) ^ bits.RotateLeft32(x, -9) ^ (x >> 2)
		w[i] = w[i-16] + w[i-7] + s0 + s1
	}
	a, b, c, d, e, f, g, z := h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]
	for i := range w {
		s1 := bits.RotateLeft32(e, -7) ^ bits.RotateLeft32(e, -13) ^ bits.RotateLeft32(e, -17)
		ch := (e & f) | (^e & g)
		t1 := z + w[i] + round256[i] + s1 + ch
		s0 := bits.RotateLeft32(a, -5) ^ bits.RotateLeft32(a, -11) ^ bits.RotateLeft32(a, -19)
		maj := ((b ^ c) & a) ^ (b & c)
		t2 := s0 + maj
		a, b, c, d, e, f, g, z = t1+t2, a, b, c, d+t1, e, f, g
	}
	// The recovered function feeds the working state back in reverse order.
	h[0] += z
	h[1] += g
	h[2] += f
	h[3] += e
	h[4] += d
	h[5] += c
	h[6] += b
	h[7] += a
}

// digest128 is the recovered one-block 128-bit variant, not standard MD5.
func digest128(input [32]byte) [16]byte {
	var block [64]byte
	copy(block[:], input[:])
	block[32] = 0xda
	binary.LittleEndian.PutUint64(block[56:], uint64(32*8)^0x64130efb)
	var words [16]uint32
	for i := range words {
		b := block[i*4 : i*4+4]
		words[i] = uint32(b[2]) | uint32(b[1])<<8 | uint32(b[0])<<16 | uint32(b[3])<<24
	}
	a, b, c, d := initial128[0], initial128[1], initial128[2], initial128[3]
	for i := 0; i < 64; i++ {
		var f uint32
		var g int
		switch {
		case i < 16:
			f, g = b^c^d, i
		case i < 32:
			f, g = (b&d)|(c & ^b), (5*i+1)%16
		case i < 48:
			f, g = (b & ^d)|(c&d), (3*i+5)%16
		default:
			f, g = c^(d|^b), (7*i)%16
		}
		t := a + f + round128[i] + words[g]
		s := rotation128[(i/16)*4+i%4]
		a, b, c, d = d, b+bits.RotateLeft32(t, -s), b, c
	}
	state := [4]uint32{initial128[0] + d, initial128[1] + b, initial128[2] + c, initial128[3] + a}
	var out [16]byte
	for i, word := range state {
		binary.LittleEndian.PutUint32(out[i*4:], word)
	}
	return out
}
