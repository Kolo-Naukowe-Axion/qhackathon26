OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-5.9124897811015984) q[0];
rz(-0.019252755919884564) q[1];
rx(9.9428893437544534) q[0];
rz(-1.0535198888795867) q[0];
rz(-0.0034305617478062665) q[1];
rx(10.882599507606457) q[0];
measure q -> c;
