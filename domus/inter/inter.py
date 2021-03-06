#!/usr/local/bin/python
#

import disass
import domus.const as const
import domus.desc as desc
import domus.inter.lib as inter_lib

class inter(disass.disass):

	def __init__(self, p, name = "inter"):
		disass.disass.__init__(self, p, name)
		self.gc_max = 0

	def render(self, p, ins):

		if type(ins) != disass.instruction:
			# transistional hack
			ins = ins.a['ins']

		s = ins.spec[1] + "("
		t = ""
		for i in ins.args:
			s += t + i
			t = ", "
		s += ")"
		return (s,)

	def do_disass(self, adr, ins):
		assert ins.lo == adr
		assert ins.status == "prospective"

		p = self.p
		try:
			w = p.m.rd(ins.lo)
		except:
			ins.fail("NO MEM")
			return
		q = p.m.rdqual(ins.lo)
		if q != 1:
			ins.fail("reloc %d INTER" % q)
			return
		op = w >> 8
		arg = w & 0xff
		if op not in intins:
			ins.fail("Unknown INT oper %d" % op)
			return
		l = intins[op]
		#print("%04x" % w, l, ins)
		ins.spec = l
		ins.args = list()
		action = list(l[2:])
		for i in action:
			if type(i) != str:
				i = i[0]
			try:
				nxt = p.m.rd(ins.hi)
			except:
				nxt = None
			if i == ">>2":
				arg >>= 2
			elif i == "ADDR":
				ins.args.append("addr: " + p.m.afmt(nxt))
				ins.hi += 1
			elif i == "V":
				if arg & 3 == 0:
					ins.args.append("v0: %x" % nxt)
					ins.hi += 1
				elif arg & 3 == 1:
					ins.args.append("v1: R")
				elif arg & 3 == 2:
					ins.args.append("v2: %x" % nxt)
					ins.hi += 1
				elif arg & 3 == 3:
					ins.args.append("v3: R")
				arg >>= 2
			elif i == "A":
				tq = p.m.rdqual(ins.hi)
				ins.hi += 1
				if tq == 3:
					ax = "%o'*2" % (nxt >> 1)
					if nxt & 1:
						ax += "+1"
				else:
					ax = p.m.afmt(nxt)

				if arg & 3 == 0:
					ins.args.append("a0:int " + ax)
				elif arg & 3 == 1:
					ins.args.append("a1:str " + ax)
				elif arg & 3 == 2:
					ins.args.append("a2:file " + ax)
				else:
					ins.args.append("a3:zone " + ax)
				arg >>= 2

			elif i == "ZONE":
				if p.m.rdqual(nxt) != 1:
					isn.fail("Zone not reloc")
					return
				ins.args.append("zone: " + p.m.afmt(nxt))
				p.todo(nxt, desc.zonedesc)
				ins.hi += 1
				arg >>= 2
				p.c["domus"].disass(p.m.rd(nxt + 3))
				self.disass(p.m.rd(nxt + 3) + 1)
			elif i == "ARG":
				ins.args.append("arg: " + p.m.dfmt(arg))
			elif i == "BITS":
				arg = nxt
				ins.hi += 1
			elif i == "STOP":
				ins.flow("cond","T", None)
			elif i == "CONST":
				ins.args.append("ci: " + p.m.dfmt(nxt))
				ins.hi += 1
			elif i == "CL":
				ins.args.append("i: " + p.m.dfmt(nxt))
				ins.flow("call", "T", nxt + 1)
				ins.hi += 1
				p.c["domus"].disass(nxt)
			elif i == "LN":
				ins.args.append("ret: " + p.m.dfmt(nxt))
				ins.hi += 1
				ins.flow("ret", "T", None)
				x = p.t.add(nxt, ins.hi, "int_func")
			elif i == "RET":
				ins.args.append("ret: " + p.m.dfmt(nxt))
				ins.hi += 1
				ins.flow("ret", "T", None)
				const.word(p, nxt - 1)
				x = p.t.add(nxt - 1, ins.hi, "int_func")
			elif i == "CALL":
				ins.args.append("i: " + p.m.dfmt(nxt))
				ins.flow("call", "T", nxt + 1)
				ins.hi += 1
				p.c["domus"].disass(nxt)
			elif i == "N":
				pass
			elif i == "GC":
				l = inter_lib.ident_gc(p, self, ins, arg)
				ins.args.append("CODEP%d" % arg)

				a = p.a['procdesc'] - arg
				const.word(p, a)
				p.setlabel(a, ".CODEP%d" % arg)

				a = p.m.rd(a)
				p.setlabel(a, "CODEP%d" % arg)
				p.c["domus"].disass(a)

				cp = arg
				arg = nxt
				ins.hi += 1

				action += l

			elif i == "JUMP":
				ins.hi += 1
				ins.args.append("cc: %o" % arg)
				ins.args.append("jmp: " + p.m.afmt(nxt))
				ins.flow("cond", "cc/%o" % arg, nxt)
				ins.flow("cond", "!cc/%o" % arg, ins.hi)
			else:
				print("%04x" % w, l, ins)
				ins.fail("arg unknown '%s'" % i)
				return

		ins.render = self.render

intins = {
    0:	( None, "STOP", "STOP"),

    1:	( None, "ANDD", "ARG"),
    2:	( None, "LOADD", "ARG"),
    3:	( None, "+D", "ARG"),
    4:	( None, "-D", "ARG"),
    5:	( None, "SHIFTD", "ARG"),
    6:	( None, "EXTRACTD", "ARG"),
    7:	( None, "*D", "ARG"),
    8:	( None, "/D", "ARG"),

    9:	( None, "ANDC", "CONST"),
    10:	( None, "LOADC", "CONST"),
    11:	( None, "+C", "CONST"),
    12:	( None, "-C", "CONST"),
    13:	( None, "SHIFTC", "CONST"),
    14:	( None, "EXTRACTC", "CONST"),
    15:	( None, "*C", "CONST"),
    16:	( None, "/C", "CONST"),

    17:	( None, "AND", "ADDR"),
    18:	( None, "LOAD", "ADDR"),
    19:	( None, "+", "ADDR"),
    20:	( None, "-", "ADDR"),
    21:	( None, "SHIFT", "ADDR"),
    22:	( None, "EXTRACT", "ADDR"),
    23:	( None, "*", "ADDR"),
    24:	( None, "/", "ADDR"),

    25:	( None, "LOAD_NEGATIVE", "V"),
    26:	( None,
	"LOAD_BYTE",
	("A", "STRING"),
    ),
    27:	( None,
	"LOAD_BYTEWORD",
	("A", "STRING"),
    ),
    28:	( None, "JUMP", "JUMP"),
    29:	( "int_link", "LINK", "LN"),
    30:	( None,
	"MOVEWORD",
	    ("A", "PTR", "To"),
	    ("V", "INT", "From")
    ),
    31:	( None,
	"MOVESTRING",
	    ("A", "STRING", "From"),
	    ("A", "STRING", "To"),
	    ("V", "INT", "Count")
    ),
    32:	( None, "??COMPAREWORD",),
    33:	( None,
	"COMPARESTRING",
	("A", "STRING"),
	("A", "STRING"),
	("V", "INT", "Count"),
    ),
    34:	( None,
	"STORE_REGISTER",
	("ADDR", "INT"),
    ),
    35:	( None,
	"TRANSLATE",
	("A", "STRING", "From"),
	("A", "STRING", "To"),
	("A", "STRING", "Table"),
    ),
    36:	( None,
	"CONVERT",
	("A", "STRING", "From"),
	("A", "STRING", "To"),
	("A", "STRING", "Table"),
	("V", "INT", "Count"),
    ),
    37:	( "int_opmess",
	"OPMESS",
	    ("A", "TEXT")
    ),
    38:	( None,
	"OPIN",
	("A", "STRING")
    ),
    39:	( None,
	"OPWAIT",
	("ADDR", "STRING"),
    ),
    40:	( None, "CALL", "CL"),
    41:	( None,
	"OPTEST",
	"",
    ),
    42:	( None,
	"MOVE",
	    "BITS",
	    ("A", "STRING", "From"),
	    ("V", "INT", "FromIdx"),
	    ("A", "STRING", "To"),
	    ("V", "INT", "ToIdx"),
	    ("V", "INT", "Count")
    ),
    43:	( None,
	"OPSTATUS",
	    ("V", "INT", "ErrBits"),
	    ("A", "TEXT", "ErrDesc")
    ),
    44:	( None,
	"BINDEC",
	    ("V", "INT", "Nbr"),
	    ("A", "STRING", "Dst"),
    ),
    45:	( None,
	"DECBIN",
	    ("A", "TEXT", "Src"),
	    ("ADDR", "INT", "Dst"),
    ),
    46:	( None,
	"INSERT",
	    ("V", "BYTE", "Val"),
	    ("A", "STRING", "Dst"),
	    ("V", "INT", "Idx"),
    ),
    47:	( None, "GOTO", ),
    48:	( None, "GO_CODE", "GC" ),

    49:	( None, "INCR", ("A", "INT")),
    50:	( None, "DECR", ("A", "INT")),
    51:	( None, "RETURN", "RET", ),
    52:	( None, "PRETURN", "PRET", ),
    53:	( None, "PJUMP", "PJUMP" ),
    54:	( None, "PCALL", "PCALL" ),
    55:	( None, "CALL", "CALL"),
    56:	( None,
	"INCR",
	     ("A", "INT"),
	     ("V", "INT")
    ),
    57:	( None,
	"DECR",
	     ("A", "INT"),
	     ("V", "INT")
    ),

    128: ( None, "GETREC", "ZONE", "ADDR"),
    129: ( None, "PUTREC", "ZONE", "V"),
    130: ( None, "WAITTRANSFER", "ZONE"),
    131: ( None, "REPEATSHARE", "ZONE"),
    132: ( None, "TRANSFER", "ZONE", "V", "V"),
    133: ( None, "INBLOCK", "ZONE"),
    134: ( None, "OUTBLOCK", "ZONE"),
    135: ( None, "INCHAR", "ZONE"),
    136: ( None, "FREESHARE", "ZONE", "ADDR"),
    137: ( None, "OUTSPACE", "ZONE"),
    138: ( None, "OUTCHAR", "ZONE", "V"),
    139: ( None, "OUTNL", "ZONE"),
    140: ( None, "OUTEND", "ZONE", "V"),
    141: ( "int_outtext",
	"OUTTEXT",
	    "ZONE",
	    ("A", "TEXT")
    ),
    142: ( None, "OUTOCTAL", "ZONE", "V"),
    143: ( None, "SETPOSITION",	"ZONE", "V", "V"),
    144: ( None, "CLOSE",	"ZONE", "V"),
    145: ( None, "OPEN",	"ZONE", "V"),
    146: ( None, "WAITZONE",	"ZONE"),
 
    218: ( None, "NEWCAT",	"ZONE", "V"),
    219: ( None, "FREECAT",	"ZONE" ),

    230: ( None, "CREATEENTRY", "ZONE", "V", "V"),
    231: ( None, "LOOKUPENTRY", "ZONE", "A"),
    232: ( None, "CHANGEENTRY", "ZONE", "A"),
    233: ( None, "REMOVEENTRY", "ZONE"),
    234: ( None, "INITCATALOG", "ZONE", "V", "V"),
    235: ( None, "SETENTRY", "ZONE", "A"),
}


if False:
	from __future__ import print_function

	import domus.cpu
	import mem
	import domus.libs


	dl = domus.libs.libs()

	def xxxstr(x):
		if x >= 32 and x < 127:
			return mem.ascii(x)
		return "<%d>" % x

	def musil_str(p, a, l):
		s = ""
		while True:
			b = p.m.rd(a)

			x = b >> 8
			if l == 0 and x == 0:
				break
			s += xxxstr(x)
			if l == 1:
				break
			if l > 0:
				l -= 1

			x = b & 0xff
			if l == 0 and x == 0:
				break
			s += xxxstr(x)
			if l == 1:
				break
			if l > 0:
				l -= 1
			a += 1 
		return s
			

	def int_getparams_desc(p, t):
		l = list()
		for a in range(t.start, t.end, 3):
			b = p.m.rd(a)
			if b >> 8 == 0xff:
				s = ".TXT\t'<255>'"
			else:
				s = ".TXT\t'" + musil_str(p, a, 6) + "'"
				b = p.m.rd(a + 2) & 0xff
				if b < 128:
					s = "%-21s\t\t!Text (STRING(%d))!" % (s, b)
				elif b == 129:
					s = "%-21s\t\t!Bool (STRING(1))!" % s
				elif b == 130:
					s = "%-21s\t\t!Integer (INTEGER)!" % s
				elif b == 134:
					s = "%-21s\t\t!Name (STRING(6))!" % s
				elif b == 140:
					s = "%-21s\t\t!Filename (STRING 12))!" % s
				
			l.append(s.expandtabs())
			l.append("")
			l.append("")
		return l

	def int_getparams_init(p, t):
		l = list()
		l.append(musil_str(p, t.start, t.a['lax']))
		return l

	def int_getparams(p, adr, args):
		print("GETPARMS @%o" % args[0], args)

		a0 = args[0]
		domus.cpu.dot_txt(p, a0 + 0o527, a0 + 0o532)
		domus.cpu.dot_txt(p, a0 + 0o533, a0 + 0o535)
		domus.cpu.dot_txt(p, a0 + 0o536, a0 + 0o540)
		domus.cpu.dot_txt(p, a0 + 0o552, None)

		a0 = args[1] >> 1
		p.setlabel(a0, "ARGDESC")
		a = a0
		la = list()
		lax = 0
		while True:
			b = p.m.rd(a)
			if b >> 8 == 0xff:
				break;
			b = p.m.rd(a + 2) & 0xff
			if b < 128:
				ll = b
			elif b == 129:
				ll = 1
			elif b == 130:
				ll = 2
			elif b == 134:
				ll = 6
			elif b == 140:
				ll = 12
			lax += ll
			la.append((musil_str(p, a, 0), b, ll))
			a += 3
		print(lax, la)

		x = p.t.add(a0, a + 1, "MUSIL_GETPARAM_ARGS")
		x.render = int_getparams_desc

		a0 = args[2] >> 1
		p.setlabel(a0, "ARGINIT")
		x = p.t.add(a0, a0 + ((lax+1)>>1), "MUSIL_GETPARAM_INIT")
		x.render = int_getparams_init
		x.a['lax'] = lax
		x.a['args'] = la

	def int_p0090(p, adr, args):
		a0 = args[0]
		print("P0090(%o)" % a0)
		p.todo(a0 + 4, p.cpu.disass)


	dn = "/rdonly/DDHF/oldcritter/DDHF/DDHF/RC3600/Sw/Rc3600/rc3600/__/"

	libx= ( "CODEP", "CODEX", "ULIB", "FSLIB",)

	codeprocs = {
	"CODEP::AANSW":	(None,	"AANSW", "V", "A"),
	"CODEP::ADMME":	(None,	"ADMME", "A", "A", "V"),
	"CODEP::BUFFE":	(None,	"BUFFE", "A", "V", "A", "A", "V"),
	"CODEP::CASE":	(None,	"CASE", "V", "V", "V"),
	"CODEP::CHANG":	(None,	"CHANG", "A", "A"),
	"CODEP::DELAY":	(None,	"DELAY", "V"),
	"CODEP::FILL":	(None,	"FILL", "V", "A", "V", "V"),
	"CODEP::FINDP":	(None,	"FINDP", "A", "A"),
	"CODEP::GETER": (None, "GETERROR", "A", "V", "A"),
	"CODEP::LOAD": (None, "LOAD", "A", "V"),
	"CODEP::OPERA":	(None,	"OPERA", "A"),
	"CODEP::P0003": (None, "P0003", "A"),
	"CODEP::P0007": (None, "P0007", "A", "A"),
	"CODEP::P0023": (None, "P0023", "V"),
	"CODEP::P0039": (None, "P0039", "A", "A", "A"),
	"CODEP::P0048": (None, "P0048"),
	"CODEP::P0040": (None, "P0040", "A", "V"),
	"CODEP::P0054":	(None,	"P0054", "A", "V"),
	"CODEP::P0076":	(None,	"P0076", "A", "A"),
	"CODEP::P0084": (None, "FINIS", "V",),
	"CODEP::P0085": (None, "GETPARAMS", "A", "A", "A"),
	"CODEP::P0086": (None, "CONNECTFILE", "A", "V", "A"),
	"CODEP::P0087":	(None,	"P0087", "V", "A"),
	"CODEP::P0088": (None, "P0088", "A", "A", "V", "V", "V"),
	"CODEP::P0089":	(None,	"P0089", "A", "V", "V", "V"),
	"CODEP::P0090": (int_p0090, "P0090", "N" ),
	"CODEP::P0091": (None, "P0091", "A", "A", "V"),
	"CODEP::P0092":	(None,	"P0092", "V", "V", "A", "A"),
	"CODEP::P0093":	(None,	"P0093", "V", "A"),
	"CODEP::P0095":	(None,	"P0095", "A", "V", "A"),
	"CODEP::P0098":	(None,	"P0098", "A"),
	"CODEP::P0117":	(None,	"P0117", "A", "A", "A"),
	"CODEP::P0121":	(None,	"P0121", "V", "V", "V"),
	"CODEP::P0122":	(None,	"P0122", "A", "V", "V"),
	"CODEP::P0123":	(None,	"P0123", "A", "A", "V"),
	"CODEP::P0124":	(None,	"P0124", "V", "A", "V"),
	"CODEP::P0127":	(None,	"P0127", "A"),
	"CODEP::P0128":	(None,	"P0128", "A"),
	"CODEP::P0130": (None, "P0130", "A", "V", "V", "V", "V"),
	"CODEP::P0132": (None, "P0132", "A", "A"),
	"CODEP::P0144": (None, "P0144", "V", "A", "A", "V"),
	"CODEP::P0145": (None, "P0145", "A", "V", "V", "A"),
	"CODEP::P0149": (None, "GETTIME", "A"),
	"CODEP::P0150": (None, "GETDATE", "A"),
	"CODEP::P0154": (None, "P0154", "A", "A"),
	"CODEP::P0155": (None, "P0155", "A", "V", "V", "V"),
	"CODEP::P0156": (None, "P0156", "A", "A", "A"),
	"CODEP::P0159": (None, "TAKEADDRESS", "A", "A"),
	"CODEP::P0160": (None, "P0160", "A", "V", "V", "V"),
	"CODEP::P0161": (None, "P0161", "V", "A", "V", "V"),
	"CODEP::P0162": (None, "P0162", "V", "V", "A"),
	"CODEP::P0164": (None, "P0164", "A", "A", "A"),
	"CODEP::P0167": (None, "P0167", "A", "A", "A"),
	"CODEP::P0168": (None, "P0168", "A", "A", "A"),
	"CODEP::P0169": (None, "P0169", "A", "A", "A"),
	"CODEP::P0170": (None, "P0170", "A", "A", "A", "A"),
	"CODEP::P0229": (None, "P0229", "V", "V"),
	"CODEP::P0230": (None, "P0230", "A", "V"),
	"CODEP::P0237": (None, "P0237", "V"),
	"CODEP::P0238": (None, "P0237", "V"),
	"CODEP::P0239": (None, "P0239", "A", "A", "V", "V"),
	"CODEP::P0260": (int_getparams, "GETPARAMS", "A", "A", "A", "A", "V"),
	"CODEP::P0261":	(None, "CONNECTFILE", "A", "V", "A", "A"),
	"CODEP::P0262":	(None, "SPLITSHARE", "A"),
	"CODEP::P0263": (None, "GETNAME", "A", "A", "A"),
	"CODEP::P0272": (None, "P0272", "A"),
	"CODEP::RANDO":	(None,	"RANDO", "A", "V"),
	"CODEP::SPRIO":	(None,	"SPRIO", "A", "A", "V"),
	"CODEP::STORE": (None, "STORE", "A", "V"),
	"CODEP::SW":    (None, "SW", "V", "A"),
	"CODEP::TAKEA": (None, "TAKEA", "A", "A"),
	"CODEP::TESTM": (None, "TESTM", "V", "A"),
	"CODEX::APPEN": (None, "APPEN", "A", "A", "A", "A", "A"),
	"CODEX::SCANC": (None, "SCANC", "A", "A", "V", "V", "V"),
	"CODEX::SEARC": (None, "SEARC", "A", "A", "A", "A", "A"),
	"CODEX::SENDM": (None, "SENDM", "A", "A", "A"),
	"CODEX::SLIDE": (None, "SLIDE", "A", "V", "V", "V"),
	"CODEX::P0013": (None, "P0013", "A", "A"),
	"FSLIB::CHECK":	(None,	"CHECK", "A", "A", "A", "A", "A"),
	"FSLIB::MCORE":	(None,	"MCORE", "V", "A"),
	"FSLIB::P0023":	(None,	"P0023", "V"),
	"FSLIB::RANDM":	(None,	"RANDM", "A"),
	"FSLIB::SINTR":	(None,	"SINTR", "V", "V", "V"),
	"FSLIB::WAITT":	(None,	"WAITT", "A", "V", "A"),
	"FSLIB::FS002":	(None,	"FS002", "V", "A", "V", "A"),
	"FSLIB::FS003":	(None,	"FS003", "V"),
	"FSLIB::FS004":	(None,	"FS004", "V", "V", "A"),
	#CODEP::P0261": (None, "CONNECTFILE", ...RCSL-43-GL-10639
	#CODEP::P0262": (None, "SPLITSHARE", ...RCSL-43-GL-10639
	#CODEP::P0264": (None, "GETERROR", ...RCSL-43-GL-10639
	}

	def ident_code_proc(p, adr):
		mx = dl.match(p.m, adr)
		if mx == None:
			return None
		for i in mx[2]:
			if not i in codeprocs:
				continue
			print("Code proc at %o match %s" % (adr, i))
			x = p.t.add(mx[0], mx[1] + 1, "CodeProc")
			x.blockcmt += "CODE PROCEDURE " + i + "\n"
			x.blockcmt += str(codeprocs[i]) + "\n"
			if False:
				x.render = "[supressed]"
				x.descend = None
			return codeprocs[i]
		print("Code proc at %o not found:" % adr, mx)
		return None

	def int_opmess(p, adr, args):
		a = args[0]>>1
		try:
			b = p.m.rd(a)
			domus.cpu.dot_txt(p, a, None)
		except:
			pass

	def int_outtext(p, adr, args):
		a = args[1]>>1
		try:
			b = p.m.rd(a)
			domus.cpu.dot_txt(p, a, None)
		except:
			pass

	def int_link(p, adr, args):
		# print("LINK %o" % adr, "%o" % args[0])
		x = p.t.add(args[0], adr + 2, "MUSIL_FUNC")
		x.blockcmt += "\nMUSIL FUNCTION\n"
	def disass(p, adr, priv = None):

		#print("INT %o" % adr)
		try:
			x = p.t.find(adr, "domus_int")
			if x != None:
				return
		except:
			pass

		q = p.m.rdqual(adr)
		if q != 1:
			print("INT adr %o qualifier %d" % (adr, q))
			return

		iw = p.m.rd(adr)
		ea = adr + 1
		op = iw >> 8
		arg = iw & 0xff
		if not op in intins:
			print("INT adr %6o iw %6o op %3d arg %3d UNKNOWN" % (adr, iw, op, arg))
			return
		l = intins[op]
		#print("INT adr %o iw %o op %d arg %d:" % (adr, iw, op, arg), l)
		s = l[1] + "("
		x = ""
		j = 2
		args = list()
		while j < len(l):
			i = l[j]
			j += 1
			t = None
			niw = p.m.rd(ea)
			if i == ">>2":
				arg >>= 2
			elif i == "BITS":
				arg = niw
				ea += 1
			elif i == "I":
				args.append(niw)
				t = ">%o" % niw
				ea += 1
				p.todo(niw, p.cpu.disass)
			elif i == "ARG":
				args.append(arg)
				t = "%o" % arg
			elif i == "JUMP":
				args.append(niw)
				t = "CC=%o, %o" % (arg, niw)
				p.todo(niw, disass)
				ea += 1
			elif i == "CONST":
				args.append(niw)
				t = "%o" % niw
				ea += 1
			elif i == "ZONE":
				args.append(niw)
				t = "zone=%o" % niw
				p.todo(niw, p.cpu.zonedesc)
				za = p.m.rd(niw + 3)
				p.todo(za, p.cpu.disass)
				arg >>= 2
				ea += 1
			elif i == "ADDR":
				args.append(niw)
				t = "%o" % niw
				ea += 1
			elif i == "A":
				tq = p.m.rdqual(ea)
				ea += 1
				if tq == 3:
					ax = "%o'*2" % (niw >> 1)
					if niw & 1:
						ax += "+1"
				else:
					ax = "%o" % niw + p.m.qfmt(tq)
				args.append(niw)
				if arg & 3 == 0:
					t = "A0: int=" + ax
				elif arg & 3 == 1:
					t = "A1: string=" + ax
				elif arg & 3 == 2:
					t = "A2: file=" + ax
				else:
					t = "A2: zone=" + ax
				arg >>= 2
			elif i == "V":
				if arg & 3 == 0:
					args.append(niw)
					t = "V0: %o" % niw
					ea += 1
				elif arg & 3 == 1:
					args.append('R')
					t = "V1: R"
				elif arg & 3 == 2:
					args.append(niw)
					t = "V2: (%o)" % niw
					ea += 1
				else:
					args.append('R')
					t = "V3: R"
				arg >>= 2
			elif i == "LN":
				args.append(niw)
				t = "%o" % niw
				ea += 1
			elif i == "CL":
				args.append(niw)
				t = "%o" % niw
				ea += 1
				p.todo(niw, p.cpu.disass)
			elif i == "GC":
				if not 'musil_code' in p.a:
					p.a['musil_code'] = dict()
				y = p.a['musil_code']

				pd = p.a['procdesc']
				ta = p.m.rd(pd - arg)

				func=arg
				t = "[%d]=%o" % (-func, ta)
				arg = niw
				ea += 1
				t += ", %o" % arg
				p.todo(ta, p.cpu.disass)
				if not func in y:
					xx = ident_code_proc(p, ta)
					if xx != None:
						y[func] = xx
				if func in y:
					t += ", " + y[func][1]
					l += y[func][2:]
					l = (y[func][0],) + l[1:]
					args.append(ta)
				else:
					print("CODE %d at %o unknown args" % (func, ta))
			elif i == "N":
				p.todo(ea, disass)
			else:
				print("???", i)
				break

			if t != None:
				s += x
				s += t
				x = ", "
		s += ")"
		#print("INT adr %o iw %o op %d arg %d:" % (adr, iw, op, arg), l, s)
		if l[0] != None:
			l[0](p, adr, args)
		x = p.t.add(adr, ea, "domus_int")
		x.render = s

