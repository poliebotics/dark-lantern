pragma circom 2.2.3;

include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/poseidon.circom";


template PrivateTensorCommitment() {
    signal input context;
    signal input nonce;
    signal input values[224];
    signal output out;

    component nonceBits = Num2Bits(128);
    nonceBits.in <== nonce;

    signal packed[8];
    for (var word = 0; word < 8; word++) {
        var accumulator = 0;
        for (var slot = 0; slot < 31; slot++) {
            if (word * 31 + slot < 224) {
                accumulator += values[word * 31 + slot] * (1 << (8 * slot));
            }
        }
        packed[word] <== accumulator;
    }

    component digest = Poseidon(12);
    digest.inputs[0] <== context;
    digest.inputs[1] <== nonce;
    digest.inputs[2] <== 224;
    digest.inputs[3] <== 20260823;
    for (var word = 0; word < 8; word++) {
        digest.inputs[word + 4] <== packed[word];
    }
    out <== digest.out;
}


template EpsilonResidual() {
    signal input camera[4][16];
    signal input emission[3][16];
    signal input noiseCode[4][16];
    signal output residual;
    var WX[4][4] = [[106,-1,-1,0],[-1,105,-2,0],[-1,-1,105,0],[0,-1,-1,106]];
    var WE[4][27] = [[139,-2726,323,-124,-2348,-302,152,-921,530,34,620,354,102,-387,-268,-103,-1103,282,255,1111,559,59,86,-317,-40,-1026,653],[715,-646,859,-106,-1084,-480,628,-1765,1088,96,-2086,795,-128,-2423,-595,110,-1843,784,510,885,1096,-107,-36,-498,190,-1539,1123],[719,-608,861,-104,-1057,-476,638,-1768,1089,108,-2084,799,-142,-2432,-593,116,-1842,781,510,846,1096,-108,-55,-504,185,-1533,1123],[400,311,434,-29,4,-184,258,-890,407,154,-130,396,-58,-437,-199,123,-894,366,109,-785,442,-122,-1033,-218,99,-668,470]];
    var BIAS[4] = [-302010,-291521,-291386,-332697];
    signal noised[4][16];
    signal prediction[4][16];
    signal difference[4][16];
    signal squared[4][16];
    var residualAccumulator = 0;

    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            noised[c][p] <== 249 * camera[c][p]
                + 615 * (noiseCode[c][p] - 128);
        }
    }
    for (var outputChannel = 0; outputChannel < 4; outputChannel++) {
        for (var p = 0; p < 16; p++) {
            var y = p \ 4;
            var x = p % 4;
            var accumulator = BIAS[outputChannel];
            for (var inputChannel = 0; inputChannel < 4; inputChannel++) {
                accumulator += WX[outputChannel][inputChannel] * noised[inputChannel][p];
            }
            var patchIndex = 0;
            for (var emissionChannel = 0; emissionChannel < 3; emissionChannel++) {
                for (var dy = -1; dy <= 1; dy++) {
                    for (var dx = -1; dx <= 1; dx++) {
                        if (y + dy >= 0 && y + dy < 4 && x + dx >= 0 && x + dx < 4) {
                            accumulator += WE[outputChannel][patchIndex]
                                * emission[emissionChannel][(y + dy) * 4 + (x + dx)];
                        }
                        patchIndex++;
                    }
                }
            }
            prediction[outputChannel][p] <== accumulator;
            difference[outputChannel][p] <== prediction[outputChannel][p]
                - 65536 * (noiseCode[outputChannel][p] - 128);
            squared[outputChannel][p] <== difference[outputChannel][p]
                * difference[outputChannel][p];
            residualAccumulator += squared[outputChannel][p];
        }
    }
    residual <== residualAccumulator;
}

template ZeeBeamConditionalDiffusion() {
    signal input context;
    signal input nonce;
    signal input cameraT[4][16];
    signal input cameraU[4][16];
    signal input emissionT[3][16];
    signal input emissionU[3][16];

    signal output commitment;
    signal output modelTag;
    signal output residualTT;
    signal output residualUU;
    signal output residualTU;
    signal output residualUT;
    signal output matchedResidual;
    signal output crossedResidual;
    signal output margin;
    signal output passed;

    modelTag <== 304195852289290939525100660671705491;
    component cameraTBits[4][16];
    component cameraUBits[4][16];
    component emissionTBits[3][16];
    component emissionUBits[3][16];
    var NOISE_T[4][16] = [[134,153,126,135,112,166,147,163,88,173,142,114,108,158,108,189],[121,92,120,155,181,104,134,96,170,137,86,176,105,115,167,126],[177,110,102,120,101,89,94,92,102,135,145,105,78,95,97,132],[130,158,108,156,144,100,89,161,115,117,80,117,128,131,105,132]];
    var NOISE_U[4][16] = [[132,116,104,144,100,103,158,150,91,143,133,147,147,113,136,148],[137,124,108,101,62,175,116,152,91,124,143,100,152,170,91,46],[186,130,161,130,195,118,157,134,114,149,94,148,68,145,102,139],[112,150,127,103,116,74,127,159,129,123,85,140,117,160,192,117]];
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            cameraTBits[c][p] = Num2Bits(8);
            cameraUBits[c][p] = Num2Bits(8);
            cameraTBits[c][p].in <== cameraT[c][p];
            cameraUBits[c][p].in <== cameraU[c][p];
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            emissionTBits[e][p] = Num2Bits(8);
            emissionUBits[e][p] = Num2Bits(8);
            emissionTBits[e][p].in <== emissionT[e][p];
            emissionUBits[e][p].in <== emissionU[e][p];
        }
    }

    component binding = PrivateTensorCommitment();
    binding.context <== context;
    binding.nonce <== nonce;
    var cursor = 0;
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) { binding.values[cursor] <== cameraT[c][p]; cursor++; }
    }
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) { binding.values[cursor] <== cameraU[c][p]; cursor++; }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) { binding.values[cursor] <== emissionT[e][p]; cursor++; }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) { binding.values[cursor] <== emissionU[e][p]; cursor++; }
    }
    commitment <== binding.out;

    component tt = EpsilonResidual();
    component uu = EpsilonResidual();
    component tu = EpsilonResidual();
    component ut = EpsilonResidual();
    for (var c = 0; c < 4; c++) {
        for (var p = 0; p < 16; p++) {
            tt.camera[c][p] <== cameraT[c][p]; tt.noiseCode[c][p] <== NOISE_T[c][p];
            tu.camera[c][p] <== cameraT[c][p]; tu.noiseCode[c][p] <== NOISE_T[c][p];
            uu.camera[c][p] <== cameraU[c][p]; uu.noiseCode[c][p] <== NOISE_U[c][p];
            ut.camera[c][p] <== cameraU[c][p]; ut.noiseCode[c][p] <== NOISE_U[c][p];
        }
    }
    for (var e = 0; e < 3; e++) {
        for (var p = 0; p < 16; p++) {
            tt.emission[e][p] <== emissionT[e][p];
            uu.emission[e][p] <== emissionU[e][p];
            tu.emission[e][p] <== emissionU[e][p];
            ut.emission[e][p] <== emissionT[e][p];
        }
    }
    residualTT <== tt.residual;
    residualUU <== uu.residual;
    residualTU <== tu.residual;
    residualUT <== ut.residual;
    matchedResidual <== tt.residual + uu.residual;
    crossedResidual <== tu.residual + ut.residual;
    margin <== crossedResidual - matchedResidual;
    component positive = LessEqThan(62);
    positive.in[0] <== 1;
    positive.in[1] <== margin;
    positive.out === 1;
    passed <== positive.out;
}

component main {public [context]} = ZeeBeamConditionalDiffusion();
