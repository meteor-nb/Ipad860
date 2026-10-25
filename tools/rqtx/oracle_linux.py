"""Isolated Unicorn execution of original Linux rqtx computation only."""
from pathlib import Path
import struct,hashlib,json,time
from unicorn import *
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[2]
SO=ROOT/'lib/libv08.so';DAT=ROOT/'rqtx.dat'
SO_SHA='c89374360a439abb24bf551eda04c3001fda4b58a2bf33d9e610222382796ddf'
DAT_SHA='57def9708a23be4992fc0024754da9eaa8179651d210a3fe5e72cf3d9cdd2c6d'
IMAGE=0x1000000
BASE,CTX,INP,DESC,TABLE,STACK,END,TLS=0x100000,0x200000,0x300000,0x400000,0x401000,0x800000,0x900000,0xa00000
class Oracle:
 def qwrite(self,a,v): self.uc.mem_write(a,struct.pack('<Q',v))
 def qread(self,a): return struct.unpack('<Q',self.uc.mem_read(a,8))[0]
 def __init__(self):
  f=SO.read_bytes();d=DAT.read_bytes()
  if hashlib.sha256(f).hexdigest()!=SO_SHA: raise ValueError('Unsupported SO identity')
  if hashlib.sha256(d).hexdigest()!=DAT_SHA: raise ValueError('Unsupported rqtx.dat identity')
  if f[:6]!=b'\x7fELF\x02\x01': raise ValueError('Expected little-endian ELF64')
  self.uc=u=Uc(UC_ARCH_X86,UC_MODE_64)
  phoff=struct.unpack_from('<Q',f,32)[0];ents,n=struct.unpack_from('<HH',f,54)
  segs=[struct.unpack_from('<IIQQQQQQ',f,phoff+i*ents) for i in range(n)]
  segs=[s for s in segs if s[0]==1]
  top=max(s[3]+s[6] for s in segs)
  u.mem_map(IMAGE,(top+4095)&~4095,UC_PROT_ALL)
  for _,flags,off,va,pa,sz,ms,align in segs: u.mem_write(IMAGE+va,f[off:off+sz])
  for a,n in [(BASE,0x24000),(CTX,0x81000),(INP,4096),(DESC,8192),(STACK,0x100000),(TLS,4096)]:u.mem_map(a,n,UC_PROT_READ|UC_PROT_WRITE)
  u.mem_map(END,4096,UC_PROT_READ|UC_PROT_EXEC)
  raw=bytes.fromhex(d.decode('ascii'));u.mem_write(BASE,raw[512:]);u.mem_write(TABLE,raw[:512])
  for dst,src in [(0x1c000,0x288),(0x1c0b8,0x210),(0x1c0c0,0x228),(0x1c0c8,0x240),(0x1c0d0,0x258),(0x1c0d8,0x270)]:self.qwrite(BASE+dst,BASE+self.qread(BASE+src))
  self.initial=bytes(u.mem_read(BASE,0x24000))
  self.qwrite(DESC+8,TABLE)
  for off,value in [(0xf480,DESC),(0xf488,BASE),(0xf490,CTX),(0xefa0,IMAGE+0xf468),(0xf438,IMAGE+0x77a1),(0xf170,IMAGE+0x7776),(0xf440,IMAGE+0x75dd),(0xf498,DESC+0x100)]:self.qwrite(IMAGE+off,value)
  # Singleton range tree reconstructed from __init at 0x9369..0x9397.
  for off,value in [(0x100,DESC+0x200),(0x108,DESC+0x200),(0x110,1),(0x210,DESC+0x108),(0x220,BASE),(0x228,0x20000)]:self.qwrite(DESC+off,value)
  u.mem_write(IMAGE+0xf4a0,b'\1');u.reg_write(UC_X86_REG_FS_BASE,TLS)
  def memset(uc,address,size,user):
   dest=uc.reg_read(UC_X86_REG_RDI);val=uc.reg_read(UC_X86_REG_RSI);n=uc.reg_read(UC_X86_REG_RDX)
   if (dest,val,n)!=(CTX,0,0x80400): raise ValueError('Unexpected memset call')
   uc.mem_write(dest,bytes(n));sp=uc.reg_read(UC_X86_REG_RSP)
   uc.reg_write(UC_X86_REG_RAX,dest);uc.reg_write(UC_X86_REG_RIP,self.qread(sp));uc.reg_write(UC_X86_REG_RSP,sp+8)
  # Only allow wrapper, VM dispatcher, original range helpers, approved PLT trampolines, and memset stub.
  def guard(uc,a,size,user):
   r=a-IMAGE
   allowed=((0x96c3,0x98bb),(0x75dd,0x8d9e),(0x5ae0,0x5af0),(0x5be0,0x5bf0),(0x6170,0x6190))
   if not any(lo<=r and r+size<=hi for lo,hi in allowed):
    raise RuntimeError(f'Unapproved executable block {a:#x}')
  u.hook_add(UC_HOOK_CODE,memset,begin=IMAGE+0x5ae0,end=IMAGE+0x5ae0)
  u.hook_add(UC_HOOK_BLOCK,guard)
 def run(self,data):
  if len(data)!=32: raise ValueError('Input must be exactly 32 bytes')
  u=self.uc;u.mem_write(BASE,self.initial);u.mem_write(CTX,bytes(0x80440));u.mem_write(INP,data+b'\0')
  sp=STACK+0xffef8;self.qwrite(sp,END)
  for reg in [UC_X86_REG_RAX,UC_X86_REG_RBX,UC_X86_REG_RCX,UC_X86_REG_RDX,UC_X86_REG_RSI,UC_X86_REG_RDI,UC_X86_REG_RBP,UC_X86_REG_R8,UC_X86_REG_R9,UC_X86_REG_R10,UC_X86_REG_R11,UC_X86_REG_R12,UC_X86_REG_R13,UC_X86_REG_R14,UC_X86_REG_R15]:u.reg_write(reg,0)
  u.reg_write(UC_X86_REG_RSP,sp);u.reg_write(UC_X86_REG_RDI,INP)
  u.emu_start(IMAGE+0x96c3,END,timeout=10_000_000,count=30_000_000)
  if u.reg_read(UC_X86_REG_RIP)!=END:raise TimeoutError('instruction/time budget exhausted')
  return u.reg_read(UC_X86_REG_RAX)&0xffffffff
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--limit',type=int,default=327)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args()
 corpus=ROOT/'clientsdk/rqtx/testdata/oracle-vectors.json'; cases=json.loads(corpus.read_text())['cases']; limit=args.limit
 if not 1<=limit<=len(cases): parser.error('--limit is outside the corpus bounds')
 o=Oracle();results=[];start=time.monotonic()
 for c in cases[:limit]:
  t=time.monotonic();out=o.run(bytes.fromhex(c['input_hex']));results.append(dict(name=c['name'],output=out,expected=c['output'],passed=out==c['output'],seconds=time.monotonic()-t))
  if len(results)%25==0:print(f'progress {len(results)}/{limit}',flush=True)
  if out!=c['output']:break
 report=dict(method='Original Linux ELF x86_64 rqtx/VM machine bytes under Unicorn; modeled initialization; SysV ABI; FS canary; four explicit ELF GOT fixups; original range-query helpers with modeled singleton tree; only memset stub; block allowlist; no native loading, host syscalls/network, or full lifecycle validation',so_sha256=SO_SHA,dat_sha256=DAT_SHA,corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),count=len(results),passed=sum(r['passed'] for r in results),elapsed_seconds=time.monotonic()-start,results=results)
 path=args.output;path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)

 if report['passed']!=limit or report['count']!=limit: raise SystemExit(1)
