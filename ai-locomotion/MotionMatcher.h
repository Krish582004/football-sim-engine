#ifndef MOTION_MATCHER_H
#define MOTION_MATCHER_H

#include <cmath>
#include <cstdint>

namespace vectorpitch {

struct PoseFeatureVector {
    uint16_t clipId;
    float velocityX;
    float velocityZ;
    float futureTrajX_200ms;
    float futureTrajZ_200ms;
    float leftFootPhase;
    float rightFootPhase;
};

// HyperMotion-style feature cost function for continuous pose matching
inline float ComputePoseCost(
    const PoseFeatureVector& candidate,
    float queryVelX,
    float queryVelZ,
    float queryTrajX,
    float queryTrajZ,
    float queryPhase,
    float wVel = 1.5f,
    float wTraj = 2.0f,
    float wPhase = 0.8f
) {
    float dvx = candidate.velocityX - queryVelX;
    float dvz = candidate.velocityZ - queryVelZ;
    float velCost = wVel * (dvx * dvx + dvz * dvz);

    float dtx = candidate.futureTrajX_200ms - queryTrajX;
    float dtz = candidate.futureTrajZ_200ms - queryTrajZ;
    float trajCost = wTraj * (dtx * dtx + dtz * dtz);

    float dPhase = std::fabs(candidate.leftFootPhase - queryPhase);
    float phaseCost = wPhase * (dPhase * dPhase);

    return velCost + trajCost + phaseCost;
}

} // namespace vectorpitch

#endif // MOTION_MATCHER_H
