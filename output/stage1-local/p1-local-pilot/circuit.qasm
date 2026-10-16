OPENQASM 3.0;
include "stdgates.inc";
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
qubit[4] q;
h q[0];
h q[1];
h q[2];
h q[3];
rz(-0.9359294617530112) q[1];
rz(0.9359294617530112) q[2];
rzz(0.4679647308765056) q[1], q[0];
rzz(-0.4679647308765056) q[2], q[0];
rzz(-0.4679647308765056) q[3], q[1];
rzz(0.4679647308765056) q[3], q[2];
rx(-6.283185334148002) q[0];
rx(-4.712388984717748) q[1];
rx(5*pi/2) q[2];
rx(-2*pi) q[3];
