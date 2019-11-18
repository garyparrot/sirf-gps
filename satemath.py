import numpy as np

class SatelliteInfo:
    """ Describe satellites information """

    def __init__(self, pseudorange=0, x=0,y=0,z=0,sid=0):
        self.pseudorange = pseudorange
        self.x = x
        self.y = y
        self.z = z
        self.id = sid

def calcCoordinate(sate1, sate2, sate3, sate4):
    """ Calcuate Cartesian coordinate by four given satellites position """
    r = [0, sate1.pseudorange, sate2.pseudorange, sate3.pseudorange, sate4.pseudorange]
    a = [0, sate1.x, sate2.x, sate3.x, sate4.x ]
    b = [0, sate1.y, sate2.y, sate3.y, sate4.y ]
    c = [0, sate1.z, sate2.z, sate3.z, sate4.z ]
    pow2 = lambda x: x*x
    abc2 = lambda i: pow2(a[i]) + pow2(b[i]) + pow2(c[i])

    row1 = [pow2(r[2]) - pow2(r[1]) + abc2(1) - abc2(2)]
    row2 = [pow2(r[3]) - pow2(r[1]) + abc2(1) - abc2(3)]
    row3 = [pow2(r[4]) - pow2(r[1]) + abc2(1) - abc2(4)]
    MatrixR = np.matrix([row1, row2, row3])

    diffwith = lambda l,r: [2*(a[l]-a[r]), 2*(b[l]-b[r]), 2*(c[l]-c[r])]
    row1 = diffwith(1,2)
    row2 = diffwith(1,3)
    row3 = diffwith(1,4)
    MatrixL = np.matrix([row1, row2, row3])

    result = MatrixL.I.dot(MatrixR)

    return int(result[0][0]), int(result[1][0]), int(result[2][0])

if __name__ == "__main__":
    """ Test """

    sate1 = SatelliteInfo(23436374.235093500465155,6851795.302244146354496,13699879.360833428800106,21774242.874906364828348 )
    sate2 = SatelliteInfo(24458117.728789124637842,15025429.764529811218381,20706299.628809131681919,7443203.857247212901711 )
    sate3 = SatelliteInfo(25312421.509830906987190,-25039118.950770277529955,1744925.142200024798512,-9114325.492342397570610)
    sate4 = SatelliteInfo(20992548.322330996394157,-3760777.709140400867909,17580429.489001203328371,19388754.646457456052303)

    print(calcCoordinate(sate1,sate2,sate3,sate4))
