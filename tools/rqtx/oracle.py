"""Execute original PE rqtx+dispatcher bytes under Unicorn with modeled init.

No OS/syscalls/network. Only memset is stubbed; original CRT/file initialization
is replaced by explicit loader-equivalent data setup. This is an emulated
computation oracle, not validation of the full Windows DLL lifecycle.
"""
from pathlib import Path
import struct, hashlib, json
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_HOOK_CODE
from unicorn.x86_const import *

ROOT=Path(__file__).resolve().parents[2]
PE=ROOT/'v08.dll'
SOURCE=ROOT/'rqtx.dat'
DLL_SHA256='aeab62515c77dcb3e56ce6180a5635d1c16ecd747f9f9b6366b2005544a3f756'
DAT_SHA256='57def9708a23be4992fc0024754da9eaa8179651d210a3fe5e72cf3d9cdd2c6d'
BASE,CTX,INP,DESC,TABLE,STACK,END=0x100000,0x200000,0x300000,0x400000,0x401000,0x800000,0x900000

class Oracle:
    def __init__(self):
        self.uc=Uc(UC_ARCH_X86,UC_MODE_64); u=self.uc
        f=PE.read_bytes(); self.dll_sha=hashlib.sha256(f).hexdigest()
        if self.dll_sha != DLL_SHA256:
            raise ValueError('Unsupported DLL identity; refusing to execute different machine code')
        dat=SOURCE.read_bytes()
        if hashlib.sha256(dat).hexdigest() != DAT_SHA256:
            raise ValueError('Unsupported rqtx.dat identity')
        pe=struct.unpack_from('<I',f,0x3c)[0];opt=pe+24
        self.image=struct.unpack_from('<Q',f,opt+24)[0]
        size,head=struct.unpack_from('<II',f,opt+56)
        u.mem_map(self.image,(size+4095)&~4095,UC_PROT_READ|UC_PROT_EXEC|UC_PROT_WRITE)
        u.mem_write(self.image,f[:head])
        count=struct.unpack_from('<H',f,pe+6)[0];sh=opt+struct.unpack_from('<H',f,pe+20)[0]
        for i in range(count):
            _,va,sz,off=struct.unpack_from('<IIII',f,sh+i*40+8)
            if sz:u.mem_write(self.image+va,f[off:off+sz])
        for a,n in [(BASE,0x24000),(CTX,0x81000),(INP,4096),(DESC,8192),(STACK,0x100000)]:
            u.mem_map(a,n,UC_PROT_READ|UC_PROT_WRITE)
        u.mem_map(END,4096,UC_PROT_READ|UC_PROT_EXEC)
        raw=bytes.fromhex(dat.decode('ascii'));u.mem_write(BASE,raw[512:]);u.mem_write(TABLE,raw[:512])
        for dest,src in [(0x1c000,0x288),(0x1c0b8,0x210),(0x1c0c0,0x228),(0x1c0c8,0x240),(0x1c0d0,0x258),(0x1c0d8,0x270)]:
            self.qwrite(BASE+dest,BASE+self.qread(BASE+src))
        self.payload_initial=bytes(u.mem_read(BASE,0x24000))
        self.qwrite(DESC+8,TABLE)
        self.qwrite(self.image+0xb458,DESC)
        self.qwrite(self.image+0xb460,BASE)
        self.qwrite(self.image+0xb468,CTX)
        u.mem_write(self.image+0xb478,b'\x01')
        def memset(uc,address,size,user):
            dest=uc.reg_read(UC_X86_REG_RCX); value=uc.reg_read(UC_X86_REG_RDX)&255;n=uc.reg_read(UC_X86_REG_R8)
            if not (dest==CTX and n==0x80400 and value==0): raise ValueError('Unexpected memset call')
            uc.mem_write(dest,bytes(n));rsp=uc.reg_read(UC_X86_REG_RSP)
            uc.reg_write(UC_X86_REG_RAX,dest);uc.reg_write(UC_X86_REG_RIP,self.qread(rsp));uc.reg_write(UC_X86_REG_RSP,rsp+8)
        self._memset=memset
        u.hook_add(UC_HOOK_CODE,memset,begin=self.image+0x6aa4,end=self.image+0x6aa4)

    def qwrite(self,a,v):self.uc.mem_write(a,struct.pack('<Q',v))
    def qread(self,a):return struct.unpack('<Q',self.uc.mem_read(a,8))[0]
    def run(self,data):
        if len(data)!=32:raise ValueError('oracle input must be 32 bytes')
        u=self.uc;u.mem_write(BASE,self.payload_initial);u.mem_write(CTX,bytes(0x80440));u.mem_write(INP,data+b'\0')
        sp=STACK+0xffef8;self.qwrite(sp,END)
        for reg in [UC_X86_REG_RAX,UC_X86_REG_RBX,UC_X86_REG_RDX,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_RBP,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]:u.reg_write(reg,0)
        u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RCX,INP)
        u.emu_start(self.image+0x4ff0,END,timeout=10_000_000,count=30_000_000)
        if u.reg_read(UC_X86_REG_RIP)!=END:raise TimeoutError('native instruction/time budget exhausted')
        return u.reg_read(UC_X86_REG_RAX)&0xffffffff

def generate_vectors():
    """Reproduce the source-bound 327-case corpus without a local DLL loader."""
    import random
    r=random.Random(86020261025)
    cases=[('ascii-zero',b'0'*32),('ascii-f',b'f'*32),('zero-bytes',bytes(32)),
           ('ff-bytes',b'\xff'*32),('ascending',bytes(range(32))),
           ('descending',bytes(range(255,223,-1))),('hex-sequence',b'0123456789abcdef'*2)]
    for pos in range(32):
        for bit in (0,7):
            b=bytearray(32);b[pos]=1<<bit;cases.append((f'bit-{pos}-{bit}',bytes(b)))
    for i in range(128):cases.append((f'md5-{i}',hashlib.md5(r.randbytes(64)).hexdigest().encode()))
    for i in range(128):cases.append((f'raw-{i}',r.randbytes(32)))
    o=Oracle();results=[]
    for name,data in cases:
        results.append({'name':name,'input_hex':data.hex(),'output':o.run(data)})
    return {'method':'Original Windows x86-64 DLL rqtx and dispatcher machine bytes under Unicorn 2.1.4; initialization reconstructed from loader; only memset stubbed; no OS calls or native library lifecycle execution',
            'dll_sha256':DLL_SHA256,'dat_sha256':DAT_SHA256,'seed':86020261025,'cases':results}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--input-hex',help='Exactly 32 input bytes, encoded as 64 hex digits')
    choice.add_argument('--output',type=Path,help='Write the reproducible 327-case corpus to this file')
    args=parser.parse_args()
    if args.input_hex is not None:
        data=bytes.fromhex(args.input_hex)
        if len(data)!=32:parser.error('--input-hex must encode exactly 32 bytes')
        value=Oracle().run(data)
        print(json.dumps({'input_hex':data.hex(),'output':value,'dll_sha256':DLL_SHA256,'dat_sha256':DAT_SHA256}))
    else:
        args.output.write_text(json.dumps(generate_vectors(),indent=2)+'\n')
