#ifndef MATCH_STATE_H
#define MATCH_STATE_H

#include <cstdint>
#include <cstring>

// Contiguous Player State (Fits tightly in CPU cache)
struct PlayerState {
    float posX, posY, posZ;
    float velX, velY, velZ;
    float facingAngleRad;
    float stamina;
    uint16_t currentAnimPoseId;
    uint8_t  tacticalRole;       // 0: GK, 1: DEF, 2: MID, 3: FWD
    uint8_t  hasPossession;
};

// Contiguous Ball State (Supports Magnus force & spin integration)
struct BallState {
    float posX, posY, posZ;
    float velX, velY, velZ;
    float spinX, spinY, spinZ; // Angular velocity vector (rad/s)
};

// Complete Match Frame Snapshot (For Rollback Ring Buffer)
struct MatchFrameState {
    uint32_t tickNumber;
    BallState ball;
    PlayerState players[10];   // 5v5 squad layout (5 per team)
    uint32_t stateChecksum;    // CRC32 hash for desync detection
};

// Helper function to calculate a fast checksum of the match state
inline uint32_t CalculateStateChecksum(const MatchFrameState& state) {
    const uint8_t* ptr = reinterpret_cast<const uint8_t*>(&state.ball);
    size_t size = sizeof(MatchFrameState) - sizeof(uint32_t); // Exclude checksum itself
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < size; ++i) {
        hash ^= ptr[i];
        hash *= 16777619u;
    }
    return hash;
}

#endif // MATCH_STATE_H
