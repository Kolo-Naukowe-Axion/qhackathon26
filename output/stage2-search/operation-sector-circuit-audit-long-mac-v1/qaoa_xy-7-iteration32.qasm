OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
x q[1];
rz(-1.3876240765964447) q[0];
rz(-0.0053400459701206946) q[1];
rx(5.5050931347840972) q[0];
rz(-0.40098934864142122) q[0];
rz(-0.0015431424053451955) q[1];
rx(5.3112980209058085) q[0];
measure q -> c;
