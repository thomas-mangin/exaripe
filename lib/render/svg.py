import os

from netaddr import CIDR,nrange

class SVG (object):

	def __init__ (self,allocation,prefix,top,left,right,size_y,size_x):
		self.allocation = allocation
		self.prefix = prefix
		self.left = left
		self.right = right
		self.top = top

		self.font = 6
		self.size_y = size_y
		self.size_x = size_x
		self.length = size_x*256

		self.location = {}

		self.name = ''
		self.width = 0
		self.height = 0

	def _svg (self,sx,sy):
		return """\
<?xml version="1.0" encoding="UTF-8"?>
<svg width="%d" height="%d" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
%%s
</svg>
""" % (sx,sy)

	def _line (self,x1,y1,x2,y2,color,stroke=False):
		return """\
<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="rgb%s" stroke-width="1"%s/>
""" % (x1,y1,x2,y2,str(color),' stroke-dasharray="3,2"' if stroke else '')

#<rect x="%d" y="%d" width="%d" height="%d" style="fill:rgb%s;stroke-width:1;stroke:rgb%s"/>
	def _rectangle (self,x,y,sx,sy,color_border=(0,0,0),color_fill=(255,255,255)):
		return"""\
<rect x="%d" y="%d" width="%d" height="%d" fill="rgb%s" stroke-width="1" stroke="rgb%s"/>
""" % (x,y,sx,sy,str(color_fill),str(color_border))

	def _text (self,x,y,font,color,string):
		return """\
<text x="%d" y="%d" fill="rgb%s" font-size="12">
%s
</text>
""" % (x,y,str(color),string)

	def generate (self,rpsl,dir,name):
		self.name = os.path.join(dir,name)
		self.link = os.path.join(self.prefix,name)
		self.width = 1050 + self.left
		self.height = (rpsl.nb24s*self.size_y) + self.top + 1 + 100

		cidr = CIDR(self.allocation)

		per24 = rpsl.fragment()

		slash = {}
		for s in xrange(24,32+1):
			slash[pow(2,32-s)] = s

		color = {
			'white' : (255, 255, 255),
			'grey'	: (100, 100, 100),
			'black' : (  0,   0,   0),
			'blue'  : (  0,   0, 255),
			'red'   : (255,   0,   0),
			'green' : (0,   255,   0),
		}
		
		background = {
			32      : (230, 230,   0),
			31      : (150, 250,   0),
			30      : (  0, 155,   0),
			29      : (  0, 155,  50),
			28      : (  0, 200, 100),
			27      : (  0, 255, 150),
			26      : (  0, 255, 200),
			25      : (  0, 250, 250),
			24      : (  0, 200, 255),
			23      : (  0, 150, 200),
			22      : (  0, 100, 200),
			21      : (  0,  80, 150),
			20      : (  0,  50, 170),
			19      : (255, 100,   0),
			18      : (255, 200,   0),
		}
		
		svg = self._svg(1050 + self.left, (rpsl.nb24s*self.size_y) + self.top + 1 + 100)
		content = ''

		# The outer box
		content += self._rectangle(self.left,self.top, self.length,rpsl.nb24s*self.size_y, color['black'],color['white'])

		# The color legend
		keys = background.keys()
		keys.sort()
		x = self.left + 100
		for k in keys:
			content += self._rectangle(x-1,14, 12,12, color['black'],background[k])
			content += self._text(x+17,24,self.font,color['black'],'/%d' % k)
			x += 50
		
		# The horizontal lines
		y = self.top
		ranges = []
		for n in nrange(cidr[0],cidr[-1],256):
			ranges.append((n,y))
			range = str(n)
			t = y + 12
			content += self._line(self.left,y, self.left+self.length,y, color['black'], False)
			content += self._text(self.left - (self.font * len(range)) - self.font/2, t, self.font,color['black'],range)
			y+=self.size_y
		
		# The horizontal numbering
		yt = self.top - 12
		yb = self.top + rpsl.nb24s*self.size_y
		for n in xrange(16,256,16):
			x = self.left+(n*self.size_x)
			content += self._line(x,yt,x,yb,color['black'],True)
			content += self._text(x+4,yt,self.font,color['black'],str(n))
		
	
		# Each inetnum
		v = 0
		for row in nrange(cidr[0],cidr[-1],256):
			y = self.top + (v*self.size_y)
			for range in per24.get(row,[]):
				start = tuple(range)[-1]
				size = rpsl.inetnum[range]['length']
				descr = ' '.join(rpsl.inetnum[range].get('descr',[]))
				remarks = ' '.join(rpsl.inetnum[range].get('remarks',[]))

				wrap = True
				while wrap:
					wrap = True if start + size > 256 else False
					if wrap:
						xl = self.left + (start*self.size_x)
						xs = 256*self.size_x
						xr = self.left + xs
						incr = (256 - start)
						size -= incr
						start = 0
					else:
						xl = self.left + (start*self.size_x)
						xs = size*self.size_x
						xr = xl + xs
						incr = size

					if remarks == 'INFRA-AW':
						border = color['red']
					else:
						border = color['black']

					try:
						back = background[slash[incr]]
					except KeyError:
						back = color['grey']

					content += self._rectangle(xl,y,xs,self.size_y,border,back)

					if len(descr) * self.font > (xr-xl) - 6:
						descr = descr[:(xr-xl)/self.font -2] + '..'

					content += self._text(xl+4,y+14,self.font,color['black'],descr)

					try:
						self.location[range].append(((xl+1,y+1),(xr-1,y+self.size_y-1)))
					except KeyError:
						self.location[range] = [((xl+1,y+1),(xr-1,y+self.size_y-1))]

					if wrap:
						y += self.size_y
			v += 1
		
		with open(self.name,'w+') as w:
			w.write(svg % content)
		
