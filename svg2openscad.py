#!/usr/bin/python
import sys
from svg.path import *
from xml.dom import minidom

def getPathCircuits(path):
    parsedPaths = parse_path(path)
    prevPP = None
    allCircuits = []
    currentCircuit = []
    for eachPP in parsedPaths:
        # first
        if not prevPP:
            currentCircuit.append( eachPP )
            
        # if not first one
        # and its the end of segment
        if prevPP:
            # circuit ended
            if prevPP.end != eachPP.start:
                allCircuits.append( currentCircuit )
                currentCircuit = []
                # print "New Path"
            else:
                # circuit still didn't end
                currentCircuit.append( eachPP )
                
        # last one
        if parsedPaths[-1] == eachPP:
            allCircuits.append( currentCircuit )            
            pass
        
        # print eachPP
        prevPP = eachPP
    return allCircuits

def cbGetPoints(cubicBezier, samples=5):
    points = []
    for i in range(0, samples+1):
        pos = i * 1.0/ samples
        points.append( cubicBezier.point(pos) )
    return points

def getPolyFromCircuit(circuit):
    polyPoints = []
    for each in circuit:
        points = None
        if type(each) == Line:
            points = [each.start, each.end]
        elif type(each) == CubicBezier:
            points = cbGetPoints(each)
            pass
        
        if points:
            # if there are more than one points existing
            if len(polyPoints) > 0:
                # check if its a continuation
                if polyPoints[-1] == points[0]:
                    polyPoints.extend( points[1:] )
                else:
                    # we have a problem maybe?
                    pass
            else:
                # if its the first batch
                polyPoints.extend( points )
                
    # compensate for closed loop
    while polyPoints[-1] == polyPoints[0]:
        del polyPoints[-1]
    
    return polyPoints
    pass

def getXY(imgPt):
    return [imgPt.real,imgPt.imag]

def convertCircuitPoints(points):
    return [getXY(p) for p in points]

def generateOpenSCADCode(polygonsList, moduleName='svg'):
    border = "/" + ("*" * 80) + "/"
    
    def _polyName(i):
        return "%s_poly_%s" % (moduleName, i)

    openSCADCode = """
    %s
    """ % border
    
    for i, eachPolygonGroup in zip( range(len(polygonsList)), polygonsList ):
        openSCADCode += """
    module %s() {
        polygon(%s);
    };
        """ % (_polyName(i), str(eachPolygonGroup))

        
    osIntermediate = ""
    for i in range(1,len(polygonsList)):
        osIntermediate += "%s();" % _polyName(i);

    openSCADCode += """
    module %s() {
        union() {
            difference() {
                // main poly0
                %s();

                // osIntermediate
                %s 
            };
        };
    }
    
    %s

    """ % (moduleName,_polyName(0),osIntermediate,border)
    
    return openSCADCode


def svg2openscad(path):
    svgString = open(path,'r').read()
    svgDoc = minidom.parseString( svgString )
    paths = svgDoc.getElementsByTagName('path')
    paths = [ path.getAttribute('d') for path in paths ]

    allCode = []
    allModules = []

    code = ""

    i = 0
    for eachpath in paths:
        i += 1
        moduleName = "svg_%s" % i
        allModules.append(moduleName)

        circuits = getPathCircuits(eachpath)
        circuitPolygons = []
        for eachCircuit in circuits:
            circuitPoly = getPolyFromCircuit(eachCircuit)
            circuitPoly = convertCircuitPoints(circuitPoly)
            circuitPolygons.append( circuitPoly )
            # print circuitPoly

        code += generateOpenSCADCode(moduleName=moduleName,polygonsList=circuitPolygons)


    for moduleName in allModules:
        code += """
        %s();
        """ % ( moduleName )

    return code
    

from optparse import OptionParser
args = sys.argv

parser = OptionParser()
parser.add_option("-o", "--output", dest="output")
parser.add_option("-i", "--input", dest="input")
kwargs, inputs = parser.parse_args()

if not kwargs.input:
    print "Usage: svg2openscad.py -i input.svg -o output.svg"
    sys.exit(-1)

code = svg2openscad(path = kwargs.input)

if not kwargs.output:
    print code
else:
    fh = open(kwargs.output,'w')
    fh.write(code)
    fh.close()

        
