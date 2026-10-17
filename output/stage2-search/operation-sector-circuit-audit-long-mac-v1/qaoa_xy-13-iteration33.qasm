OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.10705360037338756) q[0];
rz(-0.0011329406007593063) q[2];
cx q[0],q[1];
rz(-1.8210639579315304) q[1];
cx q[0],q[1];
rx(7.2478414903554214) q[0];
rx(7.2478414903554214) q[1];
rz(-0.031252639997324957) q[0];
rz(-0.00033074445521110731) q[2];
cx q[0],q[1];
rz(-0.53163140791933472) q[1];
cx q[0],q[1];
rx(10.828406852298018) q[0];
rx(10.828406852298018) q[1];
measure q -> c;
