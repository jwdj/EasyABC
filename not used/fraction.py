#    Copyright (C) 2011 Nils Liberg (mail: kotorinl at yahoo.co.uk)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

def gcd(a,b):	
    if b == 0:
        return a
    else:
        return gcd(b,a%b)

def sign(x):
    if x < 0:
        return -1
    else:
        return 1

class Fraction(object):
    def __init__ (self, numerator=0, denominator=1):        
        self.numerator = numerator
        self.denominator = denominator

    def __repr__(self):
        if self.denominator == 1:
            return "%s" % self.numerator
        elif self.numerator == 0:
            return "0"
        else:
            return "%s/%s" %(self.numerator, self.denominator)

    def __str__(self):
        return repr(self)        

    def __unicode__(self):
        return repr(self)

    def reduce(self):
        divisor = gcd(abs(self.numerator), abs(self.denominator))
        if divisor > 1:
            self.numerator /= divisor
            self.denominator /= divisor
        if self.numerator < 0 and self.denominator < 0:
            self.numerator, self.denominator = abs(self.numerator), abs(self.denominator)
        if self.numerator > 0 and self.denominator < 0:
            self.numerator, self.denominator = -abs(self.numerator), abs(self.denominator)

    def __mul__(self, f):
        if type(f) in [int, long]:
            f = Fraction(f)
        product = Fraction(self.numerator * f.numerator, self.denominator * f.denominator)
        product.reduce()
        return product

    def __neg__(self):
        return Fraction(-self.numerator, self.denominator)

    def __add__(self, f):        
        sum = Fraction(self.numerator * f.denominator + f.numerator * self.denominator,
                       self.denominator * f.denominator)
        sum.reduce()
        return sum

    def __sub__(self, f):
        return self + (-f)

    def recip(self):
        return Fraction(self.denominator, self.numerator)

    def __div__(self, f):
        if type(f) in [int, long]:
            f = Fraction(f)
        return self * f.recip()

    def __iadd__(self, f):        
        return self + f

    def __radd__(self, f):        
        return self + f

    def __rsub__(self, f):
        if type(f) in [int, long]:
            f = Fraction(f)
        return f - self

    def __rdiv__(self, f):
        if type(f) in [int, long]:
            f = Fraction(f)
            return f / self
        elif type(f) is float:
            return f / float(self)
        else:
            raise TypeError("TypeError: unsupported operand type(s) for /")

    def __rmul__(self, f):        
        return self * f    

    def __imul__(self, f):        
        return self * f

    def __idiv__(self, f):
        return self / f

    def __cmp__(self, f):        
        return cmp(float(self), float(f))    

	def __hash__(self):
		return hash((self.denominator, self.numerator))

    def __float__(self):
        return float(self.numerator) / self.denominator

    def __int__(self):
        return self.numerator / self.denominator
        

#print Fraction(3, 4) - Fraction(2, 4)