OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
gate rxx(theta) a,b { h a; h b; cx a,b; rz(theta) b; cx a,b; h a; h b; }
gate ryy(theta) a,b { rx(pi/2) a; rx(pi/2) b; cx a,b; rz(theta) b; cx a,b; rx(-pi/2) a; rx(-pi/2) b; }
h q[0];
h q[1];
x q[2];
rz(-0.019886313668456865) q[0];
rz(-0.00021045543611656294) q[2];
cx q[0],q[1];
rz(-0.33828146789494107) q[1];
cx q[0],q[1];
rx(6.8880693082770579) q[0];
rx(6.8880693082770579) q[1];
rz(-0.08025159111643361) q[0];
rz(-0.00084929685255073751) q[2];
cx q[0],q[1];
rz(-1.3651411969244258) q[1];
cx q[0],q[1];
rx(8.4479951827054283) q[0];
rx(8.4479951827054283) q[1];
measure q -> c;
