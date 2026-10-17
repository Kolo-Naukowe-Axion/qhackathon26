OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-1.67515727457593) q[0];
rz(-0.0077499758250100855) q[1];
rx(4.4390084015238642) q[0];
rz(-3.6199691602492474) q[0];
rz(-0.016747486283827193) q[1];
rx(0.014989193417859847) q[0];
measure q -> c;
