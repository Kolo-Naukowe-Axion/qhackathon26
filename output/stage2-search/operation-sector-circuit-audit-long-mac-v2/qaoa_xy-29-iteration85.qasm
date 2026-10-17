OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-2.7025539348534839) q[0];
rz(-0.018754711553459289) q[1];
rx(5.0639326363480146) q[0];
rz(-1.5507978206655941) q[0];
rz(-0.010761955729809813) q[1];
rx(1.0038159506651401) q[0];
measure q -> c;
