OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-3.5029831216596268) q[0];
rz(2.481737909230918) q[1];
rz(-0.0030879328818355927) q[2];
cx q[0],q[1];
rz(-2.481737909230918) q[1];
cx q[0],q[1];
rx(10.469927151804377) q[0];
rx(10.469927151804377) q[1];
rz(-0.7547993186658295) q[0];
rz(0.53474824683345157) q[1];
rz(-0.00066536707553162722) q[2];
cx q[0],q[1];
rz(-0.53474824683345157) q[1];
cx q[0],q[1];
rx(5.9959296084777458) q[0];
rx(5.9959296084777458) q[1];
measure q -> c;
