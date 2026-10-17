OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.69591972958682136) q[0];
rz(-0.69591972958682136) q[1];
rz(-0.00085171148158748723) q[2];
cx q[0],q[1];
rz(0.69591972958682136) q[1];
cx q[0],q[1];
rx(7.3839391419936611) q[0];
rx(7.3839391419936611) q[1];
rz(-2.5247104964683365) q[0];
rz(-2.5247104964683365) q[1];
rz(-0.0030899036571404716) q[2];
cx q[0],q[1];
rz(2.5247104964683365) q[1];
cx q[0],q[1];
rx(7.842873893917365) q[0];
rx(7.842873893917365) q[1];
measure q -> c;
