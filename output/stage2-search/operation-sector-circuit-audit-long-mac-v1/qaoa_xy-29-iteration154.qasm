OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(0.65451821021635881) q[0];
rz(-0.0068131666573527979) q[1];
rx(7.3276384001470536) q[0];
rz(4.1887796955017125) q[0];
rz(-0.043602842076700683) q[1];
rx(8.418314407906383) q[0];
measure q -> c;
