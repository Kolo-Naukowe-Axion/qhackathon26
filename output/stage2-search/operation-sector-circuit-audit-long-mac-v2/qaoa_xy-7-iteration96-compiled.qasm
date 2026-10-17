OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
rz(2.970796326794897) q[0];
sx q[0];
rz(pi/2) q[0];
x q[1];
rz(-1.4) q[1];