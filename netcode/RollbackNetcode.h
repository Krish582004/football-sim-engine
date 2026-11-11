#ifndef ROLLBACK_NETCODE_H
#define ROLLBACK_NETCODE_H

#include <cstdint>
#include <cstring>
#include "../core-sim/MatchState.h"

namespace vectorpitch {

constexpr uint32_t kMaxRollbackFrames = 60;

struct InputFrame {
    uint32_t tickNumber;
    int8_t   moveDx;      // -1, 0, +1
    int8_t   moveDz;      // -1, 0, +1
    uint8_t  actionFlags; // bit0: Sprint, bit1: Shoot, bit2: Pass, bit3: Lofted, bit4: Through, bit5: Finesse
};

class RollbackRingBuffer {
public:
    RollbackRingBuffer() : headTick_(0) {
        std::memset(states_, 0, sizeof(states_));
        std::memset(inputs_, 0, sizeof(inputs_));
    }

    void SaveFrame(const MatchFrameState& state, const InputFrame& input) {
        uint32_t idx = state.tickNumber % kMaxRollbackFrames;
        states_[idx] = state;
        states_[idx].stateChecksum = CalculateStateChecksum(state);
        inputs_[idx] = input;
        headTick_ = state.tickNumber;
    }

    bool VerifyChecksum(uint32_t tick, uint32_t remoteChecksum) const {
        if (headTick_ - tick >= kMaxRollbackFrames) return false;
        uint32_t idx = tick % kMaxRollbackFrames;
        return states_[idx].tickNumber == tick && states_[idx].stateChecksum == remoteChecksum;
    }

    const MatchFrameState& LoadFrame(uint32_t tick) const {
        return states_[tick % kMaxRollbackFrames];
    }

private:
    uint32_t headTick_;
    MatchFrameState states_[kMaxRollbackFrames];
    InputFrame inputs_[kMaxRollbackFrames];
};

} // namespace vectorpitch

#endif // ROLLBACK_NETCODE_H
